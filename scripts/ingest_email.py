#!/usr/bin/env python3
"""Turn one Weekly Social Analytics email into a stored Crooked Ideas section.

Usage: python3 scripts/ingest_email.py payload.json [outdir]

The payload is {"subject": "...", "body": "..."} — the plain-text body of the
email, as posted by the Gmail forwarder (see scripts/gmail-forwarder.gs).

Only the Crooked Ideas section is kept. The weekly email covers every Crooked
brand, and none of the rest belongs in this repository, so the stored file holds
the subject line and that one section — nothing else. It is written in email
form so scripts/parse_emails.py reads it with no special case, which keeps the
full dataset rebuildable from what is committed here.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_emails import section, week_dates  # noqa: E402

HEADING = "Crooked Ideas"
TEMPLATE = 'Subject: %s\nContent-Type: text/plain; charset="utf-8"\n\n' + HEADING + '\n\n%s'


def main(payload_path, outdir="data/emails"):
    with open(payload_path) as fh:
        payload = json.load(fh)

    subject = (payload.get("subject") or "").strip()
    body = payload.get("body") or ""
    if not subject or not body:
        raise SystemExit("payload needs both a subject and a body")

    start, end, label = week_dates(subject)   # raises if the subject has no date range
    seg = section(body)                       # raises if there is no Crooked Ideas section
    if "Engagement Rate" not in seg:
        raise SystemExit("Crooked Ideas section for %s has no metrics table" % label)

    os.makedirs(outdir, exist_ok=True)
    dest = os.path.join(outdir, "%s.eml" % end)
    new = TEMPLATE % (subject, seg.strip() + "\n")
    existing = open(dest).read() if os.path.exists(dest) else None

    if existing == new:
        print("unchanged: %s (%s)" % (dest, label))
        return 0

    with open(dest, "w") as fh:
        fh.write(new)
    print("%s: %s (%s)" % ("updated" if existing else "wrote", dest, label))
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
