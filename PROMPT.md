# Chennai Real Estate Intelligence — Master Prompt

Copy everything inside the block below and paste it into a Claude Code chat opened in this
repository. It builds the entire project. After the first run, just type `refresh` in any
future Claude Code session in this repo to update all data.

---

```
You are building and maintaining an open-source project called "Chennai Real Estate
Intelligence" in this repository. It is a public, GitHub Pages-hosted dashboard that helps
investors and advisors discover new RERA-registered projects, upcoming launches, and
early-entry real estate opportunities in Chennai and its metropolitan area. Follow this
specification exactly. Work autonomously, commit and push when done.

════════════════════════════════════════════════════════════════════
PART 1 — DATA RESEARCH (do this first, and on every "refresh")
════════════════════════════════════════════════════════════════════

Use web search and web fetch extensively to gather CURRENT data (check today's date and
search for the latest information). Cover these areas:

1. TN RERA registrations (primary source: rera.tn.gov.in — the Tamil Nadu Real Estate
   Regulatory Authority). Find projects registered in the last 24 months in the Chennai
   Metropolitan Area. For each project capture: project name, promoter/builder, RERA
   registration number, registration/approval date, project type (apartment / villa /
   plotted / commercial / mixed), locality, total units, expected completion date, and
   status. If the RERA portal blocks direct fetching, recover the same data from news
   coverage, builder announcements, and property portals, and mark those records as
   "secondary source" with a note to verify on the official portal.

2. New launches & pre-launches: projects announced by major Chennai developers (e.g. Casagrand,
   Radiance, TVS Emerald, Brigade, Prestige, Puravankara, Godrej, DRA, Appaswamy, Akshaya,
   Alliance, Urbanrise, Shriram, L&T Realty, Sobha, DAC, Jain Housing, VGN, KG, Baashyaam —
   and any others you find). Pre-launch and newly-registered projects are the "early entrant"
   opportunities; flag them explicitly.

3. Micro-market intelligence for Chennai localities, at minimum: OMR (Sholinganallur,
   Navalur, Siruseri, Kelambakkam, Padur), GST Road (Chromepet, Tambaram, Vandalur,
   Guduvancheri, Singaperumal Koil, Maraimalai Nagar), Pallavaram–Thoraipakkam corridor,
   ECR, Porur & Poonamallee, Mogappair & Ambattur, Anna Nagar, Kilpauk, Nungambakkam,
   Adyar, Velachery, Pallikaranai, Medavakkam, Perumbakkam, Sriperumbudur–Oragadam belt,
   Avadi, Madhavaram, Manapakkam, Kolathur, and Tiruvallur/Ponneri growth areas. For each:
   current price band (₹/sqft), 3–5 year price trend direction, rental yield estimate,
   inventory/demand signals, and key demand drivers.

4. Infrastructure catalysts (these drive upside — capture status and timelines): Chennai
   Metro Phase 2 corridors 3/4/5 and station locations, Chennai Peripheral Ring Road,
   Parandur greenfield airport, OMR IT expansion and new tech parks, Oragadam/Sriperumbudur
   industrial investments (EV, electronics, data centers), elevated corridors and suburban
   rail upgrades, and any new SIPCOT/industrial announcements.

5. Market context: overall Chennai residential market trend, guideline value changes,
   stamp duty/registration policy changes, and any TN government policy affecting real estate.

Data quality rules:
- Every project record must carry: source URLs, a data_confidence field ("verified" for
  official RERA-sourced, "reported" for news/portal-sourced, "estimated" for inferred),
  and a last_checked date.
- Get approximate latitude/longitude for every project and locality (geocode from
  locality knowledge; precision to the neighborhood level is acceptable — mark
  geo_precision as "exact" or "approximate").
- Never fabricate RERA numbers, prices, or dates. If unknown, use null and note it.
- Aim for at least 40–60 project records on the first build; more is better.

════════════════════════════════════════════════════════════════════
PART 2 — INVESTMENT SCORING (transparent, rule-based)
════════════════════════════════════════════════════════════════════

Compute an "Upside Score" (0–100) for every project from these weighted factors, and store
the per-factor breakdown so the site can display WHY a project scores high:

- Entry stage (25%): pre-launch / just-registered scores highest; near-possession lowest.
- Infrastructure proximity (20%): distance to upcoming metro Phase 2 stations, ring road
  interchanges, airport, major employment hubs.
- Locality momentum (20%): price trend, demand signals, new supply absorption in that
  micro-market.
- Relative pricing (15%): project ₹/sqft vs the locality's prevailing band (below band =
  higher score).
- Developer track record (10%): delivery history, scale, known delays or litigation.
- Rental yield potential (10%).

Also assign a Risk flag (Low/Medium/High) considering: RERA status, developer history,
flood-zone exposure (Pallikaranai/Perumbakkam/parts of OMR and Velachery are flood-prone —
research and note this honestly), and oversupply risk.

Tag each project with categories the site can filter by: "Early Entrant", "High Upside",
"Steady/Rental", "Premium", "Plotted/Land", "Watchlist/Risky".

════════════════════════════════════════════════════════════════════
PART 3 — REPOSITORY STRUCTURE & THE SITE
════════════════════════════════════════════════════════════════════

Build a fully static site (no build step, no frameworks requiring bundling — plain HTML,
CSS, and vanilla JS or a CDN-free approach; vendored Leaflet is fine) in the /docs folder
so GitHub Pages can serve it directly:

/docs/index.html        — dashboard: headline stats (projects tracked, new this quarter,
                          top-scoring picks), top-10 upside table, category filters
/docs/map.html          — full-screen interactive Leaflet map (OpenStreetMap tiles — free,
                          no API key). Markers color-coded by Upside Score, clustered;
                          popup shows project card (name, builder, RERA no., price, score
                          breakdown, source links). Overlay toggles for metro Phase 2
                          lines/stations and infrastructure projects.
/docs/projects.html     — sortable/filterable table of ALL projects (filter by locality,
                          type, budget band, score, category, RERA status)
/docs/localities.html   — micro-market pages: price bands, trend, drivers, projects there
/docs/methodology.html  — full scoring methodology, data sources, confidence definitions
/docs/data/projects.json, localities.json, infrastructure.json, meta.json
                        — ALL data lives in these JSON files; the HTML pages load them
                          with fetch(). meta.json holds last_refreshed timestamp and
                          change-log of each refresh.
/README.md              — what this is, live site link, how to run a refresh, how to
                          contribute, license badge
/LICENSE                — MIT
/CLAUDE.md              — the refresh contract (see Part 4)
/PROMPT.md              — keep this file as-is

Design requirements: clean, professional, mobile-responsive, works in light and dark.
Every page shows the last-refreshed date prominently and this disclaimer in the footer:
"Open-source research aggregation. Not financial advice. Verify all RERA details at
rera.tn.gov.in before transacting."

════════════════════════════════════════════════════════════════════
PART 4 — THE "refresh" COMMAND
════════════════════════════════════════════════════════════════════

Create /CLAUDE.md containing standing instructions so that in ANY future Claude Code
session in this repo, when the user says "refresh" (or "refresh data"), Claude will:
1. Re-run the Part 1 research for anything new since meta.json's last_refreshed date.
2. Add new projects, update statuses/prices of existing ones (never delete — mark
   completed/withdrawn projects with a status instead), re-score everything.
3. Update meta.json (new timestamp + summary of what changed).
4. Commit with message "data refresh: <date> — <n> added, <n> updated" and push.
   GitHub Pages redeploys automatically.
Also note in CLAUDE.md: "deep refresh" = full re-research of every record; "refresh
<locality>" = refresh only that micro-market.

════════════════════════════════════════════════════════════════════
PART 5 — PUBLISH
════════════════════════════════════════════════════════════════════

1. Commit everything with clear messages and push.
2. Enable GitHub Pages for this repository (branch: the default branch, folder: /docs)
   via the GitHub API if you have access; if you cannot, print exact click-by-click
   instructions for me to enable it (Settings → Pages → Deploy from a branch → /docs)
   and put the expected live URL in the README.
3. Finish by reporting: number of projects captured, top 5 by Upside Score with one-line
   reasons, the live/expected site URL, and anything you could not verify.
```

---

## Notes

- The map uses Leaflet + OpenStreetMap — completely free, no API keys, safe for a public repo.
- All data is plain JSON in `docs/data/`, so every refresh is a reviewable git diff.
- MIT-licensed and static-only, so anyone can fork it for another city by swapping the research scope.
