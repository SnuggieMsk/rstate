# Chennai Real Estate Intelligence

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An open-source, Claude-refreshed tracker of new RERA-registered projects, upcoming
launches, and early-entry real estate opportunities across the Chennai Metropolitan
Area — published as an interactive dashboard and map on GitHub Pages.

**Live site:** https://snuggiemsk.github.io/rstate/ *(enable GitHub Pages first — see below)*

## What's inside

- **Dashboard** — headline stats, top opportunities by Upside Score, early-entrant watchlist,
  and current Chennai market context.
- **Interactive map** — Leaflet + OpenStreetMap (no API keys), 57+ projects color-coded by
  Upside Score with cluster markers, plus overlays for Chennai Metro Phase 2 corridors/stations,
  the Peripheral Ring Road, and other infrastructure catalysts.
- **Projects table** — every tracked project, sortable and filterable by corridor, type, stage,
  category, risk, and score; click a row for the per-factor score breakdown and source links.
- **Micro-market intelligence** — price bands, trend direction, rental yields, flood risk, and
  demand drivers for 33 Chennai localities.
- **Transparent methodology** — the Upside Score is a rule-based composite computed by
  [`scripts/score.py`](scripts/score.py); every weight and threshold is documented on the
  [methodology page](docs/methodology.html) and every record carries its source URLs and a
  data-confidence rating.

## Refreshing the data

Open a Claude Code session in this repository and type:

| Command | Effect |
|---|---|
| `refresh` | Research everything new since the last refresh, update data, re-score, commit & push |
| `deep refresh` | Re-verify every record from scratch |
| `refresh <locality>` | Refresh a single micro-market (e.g. `refresh OMR`) |

The workflow is defined in [`CLAUDE.md`](CLAUDE.md). Each refresh is a git commit, so all
data changes are reviewable diffs, and GitHub Pages redeploys automatically.

## Enabling GitHub Pages (one-time)

1. Go to the repository **Settings → Pages**.
2. Under *Build and deployment*, choose **Deploy from a branch**.
3. Select the default branch and the **`/docs`** folder, then **Save**.
4. The site appears at `https://<owner>.github.io/rstate/` within a couple of minutes.

## Repository layout

```
docs/               GitHub Pages site (static HTML/CSS/JS, vendored Leaflet)
docs/data/          All data as JSON: projects, localities, infrastructure, meta
scripts/score.py    Deterministic Upside Score / risk / tag computation
CLAUDE.md           The refresh contract Claude follows in this repo
PROMPT.md           The original master prompt that built this project
```

## Data honesty

- The official TN RERA portal ([rera.tn.gov.in](https://rera.tn.gov.in)) blocks automated
  access (HTTP 503), so records are built from news coverage, property portals, and developer
  announcements, and are marked `reported` or `estimated` — never `verified` — until confirmed
  on the portal. RERA numbers are shown only when actually found in a source; they are never
  inferred.
- Coordinates are locality-level approximations unless marked exact.
- Flood-risk flags (Pallikaranai, Perumbakkam, low-lying Velachery/OMR/Tambaram pockets) are
  locality-level generalizations from public flood documentation.

## Disclaimer

This project aggregates publicly reported information for research purposes. It is **not
financial advice**. Always verify RERA registration details on the official portal and with
the developer before making any transaction.

## License

[MIT](LICENSE)
