# Chennai Real Estate Intelligence — instructions for Claude

This repository is an open-source tracker of new RERA-registered projects, launches, and
early-entry real estate opportunities in the Chennai Metropolitan Area, published via
GitHub Pages from `/docs`. All data lives in `docs/data/*.json`; the site is static
HTML/JS that reads those files. `scripts/score.py` recomputes scores deterministically.

## The `refresh` command

When the user says **`refresh`** (or "refresh data"), do ALL of the following:

1. Read `docs/data/meta.json` for `last_refreshed`. Research what is NEW since that date
   using web search/fetch: new TN RERA registrations in the Chennai Metropolitan Area
   (try https://rera.tn.gov.in first — it usually returns 503 to automated access; fall
   back to news, property portals, and developer announcements, and mark such records
   `data_confidence: "reported"`), new launches/pre-launches by Chennai developers,
   locality price movements, and infrastructure status changes (Metro Phase 2 openings,
   Peripheral Ring Road, second-airport siting, OMR projects, industrial investments).
2. Update `docs/data/projects.json`: ADD new projects, UPDATE stage/price/RERA status of
   existing ones. NEVER delete a record — set `"status": "withdrawn"` or
   `"stage": "completed"` instead. Update each touched record's `last_checked`.
   Follow the existing record schema exactly. Never invent RERA numbers, prices, or
   dates — use null and note the gap. Every record keeps real `sources` URLs.
3. Update `docs/data/localities.json` price bands/trends and
   `docs/data/infrastructure.json` statuses where research found changes.
4. Run `python3 scripts/score.py` to recompute all Upside Scores, risk flags, and tags.
   Do not hand-edit computed fields (`upside_score`, `score_breakdown`, `risk`, `tags`,
   `score_rationale`) — change the raw inputs and re-run the script.
5. Update `docs/data/meta.json`: set `last_refreshed` to today and PREPEND a changelog
   entry summarizing what changed.
6. Commit with message `data refresh: <date> — <n> added, <n> updated` and push to the
   default branch. GitHub Pages redeploys automatically.
7. Report to the user: how many projects were added/updated, notable new early entrants,
   and any records that could not be verified.

### Variants

- **`deep refresh`** — re-verify EVERY existing record from scratch (not just changes
  since last refresh), then proceed with steps 2–7.
- **`refresh <locality or corridor>`** (e.g. `refresh OMR`, `refresh Madhavaram`) —
  run the same workflow restricted to that micro-market.

## Ground rules

- The Upside Score methodology (weights, bands) is documented in
  `docs/methodology.html`. If you change the methodology, update that page and
  `scripts/score.py` together, and note it in the changelog.
- This is a research aggregation tool, not financial advice. Keep the disclaimers on
  every page intact.
- Parallel research subagents work well for refreshes: one for RERA/news sweeps, one for
  developer launches, one for locality pricing, one for infrastructure. Have each return
  raw JSON and merge here.
- Keep `docs/` fully static and self-contained (vendored Leaflet, OpenStreetMap tiles,
  no API keys, no build step).
