#!/usr/bin/env python3
"""Extract the Crooked Ideas weekly numbers from the Weekly Social Analytics emails.

Usage: python3 scripts/parse_emails.py <dir-of-.eml-files> [out.json]

Writes the canonical JSON (default data/crooked-ideas.json) and a sibling
assets/data.js that assigns the same payload to window.CI_DATA, so the dashboard
works from file:// as well as from GitHub Pages.

Each email carries one "Crooked Ideas" section: a post count plus a per-platform
table (Instagram / Threads / TikTok) and a TOTALS row. The plain-text part of the
email is used; blank-line-separated tokens are walked row by row.
"""
import email
import glob
import json
import os
import re
import sys
from email import policy

PLATFORMS = ["Instagram", "Threads", "TikTok", "Twitter", "Facebook", "Bluesky", "TOTALS"]
METRICS = ["followers", "impressions", "engagements", "engagement_rate"]


def body_text(path):
    msg = email.message_from_file(open(path, encoding="utf-8", errors="replace"), policy=policy.default)
    part = msg.get_body(preferencelist=("plain",))
    return msg["subject"], part.get_content()


def num(tok):
    """'16,360' -> 16360 ; '7.5%' -> 7.5 ; '—' -> None"""
    tok = tok.strip()
    if tok in ("—", "-", "–", ""):
        return None
    if tok.endswith("%"):
        return float(tok[:-1].replace(",", "") or 0)
    tok = tok.replace(",", "")
    return int(tok) if re.fullmatch(r"-?\d+", tok) else None


def section(text, heading="Crooked Ideas"):
    m = re.search(r"^%s\s*$" % re.escape(heading), text, re.M)
    if not m:
        raise ValueError("no %s section" % heading)
    rest = text[m.end():]
    end = re.search(r"^Top 3 Posts", rest, re.M)
    return rest[: end.start()] if end else rest


def parse_table(seg):
    lines = [l.strip() for l in seg.splitlines() if l.strip()]
    try:
        start = lines.index("Engagement Rate")
    except ValueError:
        raise ValueError("no table header")
    rows, current = {}, None
    for tok in lines[start + 1:]:
        if tok in PLATFORMS:
            current = tok
            rows[current] = {"values": [], "wow": []}
            continue
        if current is None:
            continue
        if tok.startswith("("):
            # WoW note trailing the value just recorded
            while len(rows[current]["wow"]) < len(rows[current]["values"]) - 1:
                rows[current]["wow"].append(None)
            rows[current]["wow"].append(tok.strip("()").replace(" WoW", "").replace(" Wow", ""))
        else:
            rows[current]["values"].append(num(tok))
    out = {}
    for name, row in rows.items():
        vals = row["values"][:4]
        vals += [None] * (4 - len(vals))
        out[name] = dict(zip(METRICS, vals))
    return out


def week_dates(subject, year=2026):
    m = re.search(r"(\d{1,2})/(\d{1,2})\s*[-–]\s*(\d{1,2})/(\d{1,2})", subject)
    sm, sd, em, ed = (int(x) for x in m.groups())
    return (
        "%d-%02d-%02d" % (year, sm, sd),
        "%d-%02d-%02d" % (year, em, ed),
        "%d/%d-%d/%d" % (sm, sd, em, ed),
    )


def reconcile(week):
    """Compare the per-platform rows against the TOTALS row the email reports.

    The emails are hand-assembled, so the two rarely agree to the digit. Small
    gaps are noise; a large one means the platform rows are stale (the 7/13-7/19
    email, for one, repeats the previous week's Instagram and TikTok numbers).
    """
    checks, suspect = {}, False
    for metric in ("followers", "impressions", "engagements"):
        reported = week["totals"].get(metric)
        if reported in (None, 0):
            continue
        total = sum(v[metric] or 0 for v in week["platforms"].values())
        pct = (total - reported) / reported * 100
        checks[metric] = {"platform_sum": total, "reported": reported, "diff_pct": round(pct, 1)}
        if abs(pct) > 5:
            suspect = True
    return checks, suspect


def main(src, dest):
    weeks = []
    for path in glob.glob(os.path.join(src, "*.eml")):
        subject, text = body_text(path)
        seg = section(text)
        start, end, label = week_dates(subject)
        posts = re.search(r"published\s+([\d,]+)\s+posts", seg)
        table = parse_table(seg)
        weeks.append(
            {
                "week_start": start,
                "week_end": end,
                "label": label,
                "posts": int(posts.group(1).replace(",", "")) if posts else None,
                "totals": table.get("TOTALS", {}),
                "platforms": {p: table[p] for p in ("Instagram", "Threads", "TikTok") if p in table},
                "source_email": os.path.basename(path),
            }
        )
        weeks[-1]["checks"], weeks[-1]["platform_rows_suspect"] = reconcile(weeks[-1])
    weeks.sort(key=lambda w: w["week_start"])
    payload = {
        "brand": "Crooked Ideas",
        "source": "Crooked Media Weekly Social Analytics emails",
        "generated_from": len(weeks),
        "weeks": weeks,
    }
    with open(dest, "w") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")
    js = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(dest))), "assets", "data.js")
    if os.path.isdir(os.path.dirname(js)):
        with open(js, "w") as fh:
            fh.write("// Generated by scripts/parse_emails.py - do not edit by hand.\n")
            fh.write("window.CI_DATA = " + json.dumps(payload, indent=2) + ";\n")
        print("wrote %s" % js)
    print("wrote %s (%d weeks)" % (dest, len(weeks)))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "data/crooked-ideas.json")
