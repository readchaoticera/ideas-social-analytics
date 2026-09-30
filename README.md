# Crooked Ideas — Weekly Social Analytics

An interactive dashboard of Crooked Ideas social performance, built for GitHub Pages.
It plots the numbers reported in the weekly *Weekly Social Analytics* leadership
emails: posts, impressions, engagements, followers and engagement rate — with
Instagram, TikTok and Threads broken out.

## What's here

```
index.html               the dashboard (no build step, no framework)
assets/styles.css        brand tokens — colours, type, layout
assets/dashboard.js      hand-rolled SVG charts, tooltips, filters, table, CSV export
assets/data.js           generated — the dataset as window.CI_DATA
assets/fonts/            Archivo (variable, latin subset), SIL OFL 1.1
data/crooked-ideas.json  generated — the canonical dataset
data/manual-weeks.json   weeks entered by hand rather than parsed (see below)
scripts/parse_emails.py  reads .eml files and writes both generated files
scripts/ingest_email.py  keeps one email's Crooked Ideas section in data/emails/
scripts/gmail-forwarder.gs  Apps Script that forwards the weekly email to GitHub
data/emails/             the stored Crooked Ideas sections, one file per week
.github/workflows/       the Action that ingests an email and rebuilds the data
```

Everything is static and self-contained: no CDN, no third-party requests, no
network at runtime. Opening `index.html` from disk works too.

## Published at

**https://readchaoticera.github.io/ideas-social-analytics/**

Pages deploys from this repository's default branch, root folder; `.nojekyll` is
committed so the files are served as-is. A push republishes the site within a
minute or two, though assets are cached for ten minutes — hard-refresh
(Cmd/Ctrl+Shift+R) if an update looks missing.

> **Note:** a Pages site on a public repo is public. These are internal numbers —
> keep the repository private (Pages on a private repo requires GitHub
> Enterprise Cloud) or confirm the figures are fine to publish.

## Updating with a new week

Automatic, once set up (see below): the weekly email arrives, a Gmail script
forwards it to GitHub, an Action stores the Crooked Ideas section and rebuilds
the data, and Pages redeploys. Nothing to do by hand.

To do it manually — or to backfill — point the parser at a folder of `.eml`
files:

```bash
python3 scripts/parse_emails.py ~/path/to/weekly-emails
```

With no argument it rebuilds from `data/emails/`, the sections already stored
here. Either way it rewrites `data/crooked-ideas.json` and `assets/data.js`
(any Python 3, no dependencies). Commit both and the dashboard picks the week
up — charts, tiles, table and CSV all read the same file.

**Whole emails are never committed.** They carry every Crooked brand's numbers;
`scripts/ingest_email.py` keeps only the Crooked Ideas section, in email form so
the same parser reads it. That is what lives in `data/emails/`, which is why the
full dataset can be rebuilt from this repository alone.

## Automating the weekly email

Three pieces: a Gmail script that forwards the email, a token so it can reach
GitHub, and an Action that does the work.

**1. Create a token.** GitHub → Settings → Developer settings → Personal access
tokens → Fine-grained tokens. Give it access to this repository only, with
**Repository permissions → Contents: Read and write**. Copy the token; set a
calendar reminder for its expiry, since the sync goes quiet when it lapses.

**2. Set up the Gmail script.** At [script.google.com](https://script.google.com),
create a new project and paste in `scripts/gmail-forwarder.gs`. Then:

- Project Settings → Script properties → add `GITHUB_TOKEN` with the token above.
- Check the `CONFIG` block at the top — the repository is already filled in, and
  `query` is the Gmail search that finds the email.
- Run `previewMatches` once. It sends nothing and logs which emails it found,
  so you can confirm the search is right before anything is live. Google will
  ask you to authorise Gmail access on this first run.
- Run `installTrigger` once. That schedules `syncWeeklyAnalytics` daily; it does
  nothing on days with no new email, so the exact hour does not matter.

**3. That's it.** When an email arrives the script posts its subject and plain
text to GitHub, the **Weekly analytics** workflow stores the section, rebuilds
the data and commits, and Pages republishes a few minutes later. The thread gets
the label `Ideas dashboard synced` so it is never sent twice, and re-sending the
same week changes nothing.

### When it breaks

- **The workflow ran and failed** → open it under the repository's Actions tab.
  The ingest step fails loudly rather than committing something wrong: no
  Crooked Ideas section, no week range in the subject, or a section with no
  metrics table. Usually the email's shape changed; the parser is the thing to
  adjust.
- **Nothing happened at all** → run `previewMatches` in Apps Script. Either the
  search missed the email (subjects have varied: "Weekly Social Analytics",
  "Social Weekly Analytics", "Weekly Social Report") or the token expired, which
  shows up as a `401` in the Apps Script execution log.
- **A week needs fixing by hand** → edit its file in `data/emails/`, run
  `python3 scripts/parse_emails.py`, and commit. Or run the workflow manually
  from the Actions tab to rebuild without an email.

The workflow lives on the default branch because `repository_dispatch` only
triggers there. If the default branch is ever renamed, the workflow file has to
move with it.

## Hand-entered weeks

A week with no `.eml` on hand goes in `data/manual-weeks.json`:

```json
{ "week_start": "2026-09-14", "week_end": "2026-09-20", "label": "9/14-9/20",
  "platforms": { "Instagram": { "followers": 17120, "impressions": 1333000 } } }
```

The parser merges it in and derives any totals it can from the platform rows.
Anything not supplied stays `null` and renders as a gap, never as a zero. A
parsed email for the same week always wins, so entries can be left in place
until their email lands.

Entries are **provisional by default** — drawn with a dashed line, hollow markers
and a washed-back fill, labelled in the table and tooltip, and marked
`placeholder` in the CSV. An entry transcribed from a real email should set
`"placeholder": false`; it then renders like any reported week, and a
`"source_note"` explaining where it came from shows on hover in the table and
lands in the JSON. The weeks of 6/15-6/21 and 6/22-6/28 are transcribed this way.

## How the numbers are derived

- **Totals come from each email's TOTALS row**, not from summing its platform rows.
  That's how the figures in the weekly deck were produced, so the charts match.
- **Platform rows and TOTALS rarely agree to the digit.** The parser reconciles them
  and records the gap per metric in `checks`. Anything off by more than 5% is
  flagged: a hollow marker on the chart, a note in the tooltip, a greyed cell in
  the table.
- **The week of 7/13–7/19 is the one real problem.** That email repeats the previous
  week's Instagram and TikTok rows, so its platform split is unreliable — its
  totals are fine.
- **Threads and YouTube** report followers only, so they appear just in the follower
  charts. YouTube's first row is the 9/14-9/20 email.
- **Week-over-week changes are computed** from the plotted totals rather than copied
  from the WoW figures printed in the email, which sometimes disagree with the
  email's own totals.
- **Engagement rate** is the rate printed in the email, not a recomputed ratio.
  Placeholder weeks are the exception: no email printed one, so it is computed as
  engagements ÷ impressions wherever both were supplied.

## Brand

Colours and type are set once at the top of `assets/styles.css`:

| Token | Value | Used for |
|---|---|---|
| `--surface` | `#f0eee9` | page + card background |
| `--blue` | `#3b5bf5` | impressions, accents, the inverted follower card |
| `--pink` | `#ff8ac5` | engagements |
| `--green` | `#1e6a45` | posts |
| `--yellow` | `#fce94d` | followers |
| `--series-instagram` / `--series-tiktok` / `--series-threads` / `--series-youtube` | `#3b5bf5` / `#e0489b` / `#2f8f5b` / `#7a5cd6` | platform lines |

The four platform steps are deliberately not the flat brand colours: they're
adjusted so the lines stay distinguishable under colour-vision deficiency and hold
3:1 contrast against the surface. Change them and check that still holds.
