# Chennai Real Estate Intelligence

An open-source, Claude-powered pipeline for tracking new RERA-registered projects, upcoming
launches, and early-entry real estate investment opportunities in Chennai — published as an
interactive map and dashboard on GitHub Pages.

## Status

🚧 **Bootstrap stage.** This repo currently contains the master prompt only.

## How to build it

1. Open a Claude Code session in this repository.
2. Copy the prompt block from [`PROMPT.md`](PROMPT.md) and paste it into the chat.
3. Claude researches Tamil Nadu RERA registrations, new launches, micro-market pricing, and
   infrastructure catalysts; scores every project for investment upside; and builds a static
   dashboard + Leaflet map in `/docs` for GitHub Pages.

## How to refresh the data

Once built, open any Claude Code session in this repo and type:

- `refresh` — pull in new registrations/launches and update prices & scores
- `deep refresh` — re-verify every record from scratch
- `refresh <locality>` — refresh a single micro-market (e.g. `refresh OMR`)

Each refresh is a git commit, so all data changes are reviewable diffs, and GitHub Pages
redeploys automatically.

## Disclaimer

This project aggregates publicly reported information for research purposes. It is **not
financial advice**. Always verify RERA registration details on the official portal
([rera.tn.gov.in](https://rera.tn.gov.in)) before making any transaction.

## License

MIT
