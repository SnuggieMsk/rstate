# Chennai Real Estate Intelligence — instructions for Claude

This repository is an open-source tracker of new RERA-registered projects, launches, and
early-entry real estate opportunities in the Chennai Metropolitan Area, published via
GitHub Pages from `/docs`. All data lives in `docs/data/*.json`; the site is static
HTML/JS that reads those files. `scripts/score.py` recomputes scores deterministically.

The site serves three client-lens personas (Boardroom ₹3Cr+ 3-4BHK, Executive ₹1-2.5Cr
2-3BHK, Value & Distressed) via the persona switcher in the header, a locality explorer
covering 125+ Chennai-area micro-markets with price/trend/tier data, a Developers page
with per-promoter portfolio intelligence, and a Deals page tracking bank e-auctions and
stalled/insolvent projects. See `docs/methodology.html` for how segment fit, locality
tiers, developer rollups, and discount-to-market are computed.

Projects come from two streams, distinguished by the `source` field: `curated` records
(researched, WITH pricing — these drive the persona lenses) and `rera-registry` records
(the full TNRERA registration index, comprehensive but price-free). Never conflate them.

## The `refresh` command

When the user says **`refresh`** (or "refresh data"), do ALL of the following:

1. Read `docs/data/meta.json` for `last_refreshed`. Research what is NEW since that date
   using web search/fetch: new TN RERA registrations in the Chennai Metropolitan Area
   (try https://rera.tn.gov.in first — it usually returns 503 to automated access; fall
   back to news, property portals, and developer announcements, and mark such records
   `data_confidence: "reported"`), new launches/pre-launches by Chennai developers,
   locality price movements, and infrastructure status changes (Metro Phase 2 openings,
   Peripheral Ring Road, second-airport siting, OMR projects, industrial investments).
2. Re-scrape the TNRERA registration index for comprehensive coverage:
   `export BRIGHTDATA_API_KEY=<key>` then `python3 scripts/scrape_rera.py` followed by
   `python3 scripts/merge_rera.py`. This pulls BOTH registry streams — buildings and
   plotted layouts (TNRERA registers them separately). The scraper caches pages under `.cache/` (gitignored),
   so only new registrations cost a fetch; the merge adds new registry records as
   `source: "rera-registry"` and never overwrites a curated record — it only backfills a
   missing RERA number. If the key is unavailable, skip this step and say so in the report.
3. Update `docs/data/projects.json`: ADD new projects, UPDATE stage/price/RERA status of
   existing ones. NEVER delete a record — set `"status": "withdrawn"` or
   `"stage": "completed"` instead. Update each touched record's `last_checked`.
   Follow the existing record schema exactly. Never invent RERA numbers, prices, or
   dates — use null and note the gap. Every record keeps real `sources` URLs.
   Enriching `curated` records with price/config/ticket data is the highest-value work
   here — registry records have no pricing, so they cannot drive the persona lenses.
4. Update `docs/data/localities.json` price bands/trends and
   `docs/data/infrastructure.json` statuses where research found changes. Each locality
   keeps its `segment_fit` array (which personas it serves) and its `tier` is
   recomputed automatically by the score — never hand-set `tier`.
5. Update `docs/data/distressed.json`: refresh bank e-auction listings (`record_type:
   "auction"`) since they churn weekly — banks post new listings and past-date ones
   should get checked for re-auction, never deleted (an expired auction is still useful
   history; the UI dims it automatically once its date passes). Add any newly reported
   stalled projects, CIRP/insolvency developments, or SWAMIH-fund revivals
   (`record_type: "stalled-project" | "cirp-developer" | "liquidation" | "revoked-rera"
   | "distressed-sale"`). Never state a developer's solvency status without a source.
6. Run `python3 scripts/score.py` to recompute all Upside Scores, risk flags, tags,
   `segment_fit` (Boardroom/Executive/Value), locality `tier`, canonical `developer`
   names, per-developer portfolio rollups in `developers.json`, and distressed
   `discount_pct`. Do not hand-edit any computed field — change the raw inputs and
   re-run the script.
7. Update `docs/data/meta.json`: set `last_refreshed` to today and PREPEND a changelog
   entry summarizing what changed.
8. Commit with message `data refresh: <date> — <n> added, <n> updated` and push to the
   default branch. GitHub Pages redeploys automatically.
9. Report to the user: how many projects/localities/deals were added or updated, notable
   new early entrants or auction bargains, and any records that could not be verified.

### Variants

- **`deep refresh`** — re-verify EVERY existing record from scratch (not just changes
  since last refresh), then proceed with steps 2–9.
- **`refresh <locality or corridor>`** (e.g. `refresh OMR`, `refresh Madhavaram`) —
  run the same workflow restricted to that micro-market.
- **`refresh deals`** — refresh only `docs/data/distressed.json` (auctions churn much
  faster than the rest of the dataset; useful for a quick between-refresh top-up).

## Ground rules

- The Upside Score methodology (weights, bands) is documented in
  `docs/methodology.html`. If you change the methodology, update that page and
  `scripts/score.py` together, and note it in the changelog.
- This is a research aggregation tool, not financial advice. Keep the disclaimers on
  every page intact.
- Parallel research subagents work well for refreshes: one for RERA/news sweeps, one for
  developer launches, one for locality pricing, one for infrastructure, one for bank
  e-auctions (SARFAESI aggregators — try a web unlocker if available for sites that block
  automated access; never bypass access controls on government domains), one for
  stalled/insolvent projects. Have each return raw JSON and merge here.
- Never fabricate a bank-auction reserve price, EMD, or auction date, and never include
  a borrower's personal details beyond what the public notice states.
- In `developers.json`, keep adjudicated regulatory or court action strictly separate from
  unadjudicated buyer complaints — say which a red flag is, and attribute it. An empty
  `red_flags` array means nothing adverse was found, never that nothing exists. Do not
  assert a developer's solvency, or lack of it, without a source.
- Keep `docs/` fully static and self-contained (vendored Leaflet, OpenStreetMap tiles,
  no API keys, no build step).
