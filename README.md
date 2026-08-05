# Chennai Real Estate Intelligence

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An open-source, Claude-refreshed tracker of new RERA-registered projects, upcoming
launches, and early-entry real estate opportunities across the Chennai Metropolitan
Area — published as an interactive dashboard and map on GitHub Pages.

**Live site:** https://snuggiemsk.github.io/rstate/ *(enable GitHub Pages first — see below)*

## What's inside

- **Client-lens personas** — a header switcher re-lenses every page to **Boardroom** (₹3Cr+,
  3–4BHK exclusive), **Executive** (₹1–2.5Cr, 2–3BHK), or **Value & Distressed**, based on a
  transparent per-project segment-fit score.
- **Dashboard** — headline stats, top opportunities by Upside Score, early-entrant watchlist,
  and current Chennai market context.
- **Interactive map** — Leaflet + OpenStreetMap (no API keys), every project color-coded by
  Upside Score with cluster markers, plus overlays for Chennai Metro Phase 2 corridors/stations,
  the Peripheral Ring Road, bank-auction deals, and other infrastructure catalysts.
- **Projects table** — 330+ tracked projects, sortable and filterable by **developer**, zone, type,
  stage, category, risk, score, data source, and RERA status; click a row for the per-factor score
  breakdown and source links; tick up to 3 projects to open the compare drawer (with a
  print-to-PDF brief).
- **Developer intelligence** — 230+ promoters with computed portfolio stats (project count, zones,
  stage mix, average Upside Score, ticket range, RERA coverage) plus researched delivery reputation
  and red flags where they could be sourced.
- **Deals page** — bank e-auction (SARFAESI) listings with a computed discount-to-market %,
  plus stalled/insolvent-project and NCLT/CIRP/SWAMIH-revival records — every listing flagged
  for mandatory legal title verification.
- **Locality Explorer** — price bands, trend direction, rental yields, flood risk, tier badges
  (Prime/Established/Growth/Emerging), and demand drivers for 129 Chennai-area localities across
  every zone, from the city core to the far periphery.
- **Transparent methodology** — the Upside Score and segment-fit scores are a rule-based
  composite computed by [`scripts/score.py`](scripts/score.py); every weight and threshold is
  documented on the [methodology page](docs/methodology.html) and every record carries its
  source URLs and a data-confidence rating.

## Refreshing the data

Open a Claude Code session in this repository and type:

| Command | Effect |
|---|---|
| `refresh` | Research everything new since the last refresh, update data, re-score, commit & push |
| `deep refresh` | Re-verify every record from scratch |
| `refresh <locality>` | Refresh a single micro-market (e.g. `refresh OMR`) |
| `refresh deals` | Refresh only the bank-auction / distressed pipeline (it churns weekly) |

The workflow is defined in [`CLAUDE.md`](CLAUDE.md). Each refresh is a git commit, so all
data changes are reviewable diffs, and GitHub Pages redeploys automatically.

## Enabling GitHub Pages (one-time)

1. Go to the repository **Settings → Pages**.
2. Under *Build and deployment*, choose **Deploy from a branch**.
3. Select the default branch and the **`/docs`** folder, then **Save**.
4. The site appears at `https://<owner>.github.io/rstate/` within a couple of minutes.

## Repository layout

```
docs/                    GitHub Pages site (static HTML/CSS/JS, vendored Leaflet)
docs/data/               All data as JSON: projects, localities, infrastructure,
                         distressed, developers, meta
scripts/score.py         Deterministic scoring: Upside Score, risk, tags, segment fit,
                         locality tiers, developer rollups, auction discounts
scripts/scrape_rera.py   Scrapes the TNRERA registration index (needs BRIGHTDATA_API_KEY)
scripts/merge_rera.py    Folds scraped registrations into projects.json
CLAUDE.md                The refresh contract Claude follows in this repo
PROMPT.md                The original master prompt that built this project
```

## Data honesty

- The official TN RERA portal ([rera.tn.gov.in](https://rera.tn.gov.in)) returns HTTP 503 to all
  automated access and is additionally off-limits to web-unlocker services as a government domain.
  Registry data is therefore read from a public third-party mirror of the same registry, and every
  record is marked `reported` — never `verified` — because the registration number, while real and
  checkable, was not read from the government portal itself. RERA numbers are never inferred.
- Projects carry a `source` field: `curated` (researched, with pricing) or `rera-registry`
  (comprehensive registry coverage, no pricing published). Only curated records can drive the
  persona lenses, since the registry publishes no prices.
- Coordinates are locality-level approximations unless marked exact.
- Flood-risk flags (Pallikaranai, Perumbakkam, low-lying Velachery/OMR/Tambaram pockets) are
  locality-level generalizations from public flood documentation.

## Disclaimer

This project aggregates publicly reported information for research purposes. It is **not
financial advice**. Always verify RERA registration details on the official portal and with
the developer before making any transaction.

## License

[MIT](LICENSE)
