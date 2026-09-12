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
scripts/parse_emails.py  reads the weekly .eml files and writes both generated files
```

Everything is static and self-contained: no CDN, no third-party requests, no
network at runtime. Opening `index.html` from disk works too.

## Publishing to GitHub Pages

1. Merge this branch into the branch you publish from (usually `main`).
2. **Settings → Pages → Build and deployment → Deploy from a branch**, pick that
   branch and the `/ (root)` folder.
3. The site goes live at `https://<owner>.github.io/<repo>/`.

`.nojekyll` is committed so Pages serves the files as-is.

> **Note:** a GitHub Pages site on a public repo is public. These are internal
> numbers — keep the repository private (Pages on a private repo requires GitHub
> Enterprise Cloud) or confirm the figures are OK to publish before turning Pages on.

## Updating with a new week

The source emails are **not** committed — they contain every Crooked brand's
numbers, not just Crooked Ideas. Keep them in a local folder and regenerate:

```bash
python3 scripts/parse_emails.py ~/path/to/weekly-emails data/crooked-ideas.json
```

That rewrites `data/crooked-ideas.json` and `assets/data.js` from whatever `.eml`
files it finds (any Python 3, no dependencies). Commit both, and the dashboard
picks the new week up — charts, tiles, table and CSV all read the same file.

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
- **Threads** reports followers only, so it appears just in the follower charts.
- **Engagement rate** is the rate printed in the email, not a recomputed ratio.

## Brand

Colours and type are set once at the top of `assets/styles.css`:

| Token | Value | Used for |
|---|---|---|
| `--surface` | `#f0eee9` | page + card background |
| `--blue` | `#3b5bf5` | impressions, accents, the inverted follower card |
| `--pink` | `#ff8ac5` | engagements |
| `--green` | `#1e6a45` | posts |
| `--yellow` | `#fce94d` | followers |
| `--series-instagram` / `--series-tiktok` / `--series-threads` | `#3b5bf5` / `#e0489b` / `#2f8f5b` | platform lines |

The three platform steps are deliberately not the flat brand colours: they're
adjusted so the lines stay distinguishable under colour-vision deficiency and hold
3:1 contrast against the surface. Change them and check that still holds.
