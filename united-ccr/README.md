# United CCR RFP Radar

A daily scanner that finds public bid opportunities United CCR can respond to, checks eligibility, and ranks them with jobs near the Cypress, TX headquarters first. Nothing inside the service area is dropped for distance; distance only changes rank.

- **RFP Radar page** (published on Claude): four tabs. *Opportunities* (scan results), *Company file* (the questionnaire for Cody; answers save to the page's shared store), *Draft a response* (analyzes an RFP against the company file, writes a draft, then scores it as an evaluator would), and *Portfolio* (rebuilt from the company file).
- `PORTFOLIO.md` — company research, capability statement, RFP metrics scorecard, eligibility actions.
- `portfolio/projects.csv` — past-performance log to fill from company records.
- `rfp_scanner/` — the scanner (Python 3.10+, standard library only).
- `docs/index.html` — the dashboard, regenerated each run (works as a GitHub Pages site or opened directly).
- `data/opportunities.json` — the running results store.

## How opportunities are judged

**Not eligible** (hidden by default, shown with the toggle):
- Place of performance outside the service states (TX, LA, OK, AR, NM, MS, AL, FL, GA, TN, SC).
- Set-aside United CCR is not certified for (8(a), HUBZone, WOSB, SDVOSB…). Small-business set-asides count as eligible.
- Deadline passed, or the notice is an award/justification rather than a solicitation.

**Eligible, check first**: needs a human look before bidding, e.g. Texas mold work without a TDLR license on file, bonding language, federal award without SAM registration, no stated location.

**Priority (0–100)** = 45% fit + 40% proximity + 15% time to deadline.
- Fit: NAICS match, facility service codes, scope keywords, sectors United CCR already serves; off-scope terms subtract.
- Proximity: 100 at HQ falling to 0 at 700 miles. Tiers: home turf ≤60 mi, Houston region ≤150, statewide reach ≤450, long haul beyond.

All of this is set in `rfp_scanner/config.json`. The company file's **Export for scanner** button saves `profile.json`; commit it to `portfolio/profile.json` and each scan applies Cody's certifications, licenses, SAM status, states and travel limit on top of the config. When United CCR gets a certification or license, add it there (`certifications_held`, `licenses_held`, `sam_registered`) and the affected opportunities become eligible on the next run.

## Sources

| Source | Setup |
|---|---|
| SAM.gov (federal) | Free API key: sign in at sam.gov → Account Details → API Key. Add it as repository secret `SAM_API_KEY`. A personal key allows 10 requests/day; the scanner uses 9 (6 primary NAICS codes daily, secondary codes rotate). |
| Agency bid RSS feeds | Many Texas cities and counties publish bid postings as RSS (CivicPlus sites: `/RSSFeed.aspx?ModID=76&CID=All-bids.xml`). Add each to `sources.rss_feeds` in the config with its city and state. |
| CSV exports | Drop any CSV export into `imports/` (Texas ESBD, BidNet, co-op portals, a manual list). Column names are matched automatically (title, agency, due date, city, state, URL…). `imports/web-research-leads-2026-10-22.csv` holds leads found by web research on Oct 22, 2026; confirm each on the agency's site. |

Portals without a feed or API, worth registering on so notices arrive by email: Texas ESBD and CMBL, City of Houston, Harris County, Fort Bend and Montgomery counties, HISD, Cy-Fair ISD, Katy ISD, Lone Star College, University of Houston, Texas A&M University System, Port Houston, METRO, TIPS, BuyBoard, Choice Partners.

## Running it

```
cd united-ccr
python -m unittest discover -s rfp_scanner/tests -t .
SAM_API_KEY=... python -m rfp_scanner.scan
```

The GitHub Action `.github/workflows/rfp-scan.yml` runs this every morning at 6:17 a.m. Central, downloads Census ZIP/city coordinates for distance, and commits the refreshed `data/` and `docs/`. `docs/index.html` carries its data inside the file, so it opens straight from a download or a checkout. The dashboard's **Load scan file** button opens any `opportunities.json`.
