# Claude Memory: Germany EV Charger Access — v1.420

Read first when starting Claude Code session in this folder.

## Project Goal

Germany-focused EV charging + population-access dashboard for Tesla Gigafactory Berlin-Brandenburg dual-study application.

## Hosting

- **Live site**: https://soltransform.github.io/deNetzPop/
- **GitHub repo**: https://github.com/soltransform/deNetzPop/
- **PMTiles CDN**: Cloudflare R2 bucket `denetzpop-tiles`
  - Public URL: `https://pub-3bf2fc3bacfb4d3f8b6ed3debc07a9e1.r2.dev/germany_pop.pmtiles`
  - CORS configured for range requests from any origin
- **GitHub Pages**: main branch, root folder
- **Auto-detect**: `map-app/index.html` uses local file on localhost, R2 URL in production (`PMTILES_URL` constant)

## Current State (2026-05-24)

### What Works

- **Map**: MapLibre, desaturated OSM basemap (v4.20 style)
- **Charger data**: 63,653 grouped sites from v4.20 BNetzA parser (109k CSV rows → grouped by operator/address/class)
- **Zoom progression**:
  - z < 7: State bubbles (16 Bundesländer, grey circles, charge point totals)
  - z 7–10: District bubbles (~400 Kreise, grey circles)
  - z 10+: Individual charger dots, color-coded by class
- **Charger classes**: ac_normal (blue), fast_50 (green), hpc_150 (amber), ultra_300 (red)
- **Boundaries**: Grey BKG state + district outlines
- **Selection**: Click bubble or use top-bar dropdowns. District outlines on state selection.
- **Coverage layer**: Custom WebGL threshold layer reading RGBA PMTiles. Teal (#2DD4BF) = covered, amber (#F59E0B) = uncovered. Radius (1/5/10/25 km) and tier (Any/DC Fast/Ultra) selectable. Below bubbles, above basemap.
- **Tabbed stats pane**: 3-tab right panel, all tabs respond to region selection
  - **Coverage tab**: Hero % number, cumulative distance chart, charger counts, farthest point
  - **Market tab**: Operator rankings (top 50 + Other aggregate), growth stacked area chart (2010–2026), summary stats (11,807 operators, 63,653 sites, 197k CPs)
  - **Regions tab**: KPI table (16 states or ~400 districts), composite gap score, summary cards (worst/best/avg)
- **Analytics pipeline**: `scripts/build_analytics.py` precomputes `analytics.json` from chargers + coverage_stats
- **Gap score**: `0.5*(DC underserved) + 0.3*(density deficit) + 0.2*(ultra gap)`, range 0–100
- **Layout**: Map left (frosted top bar + dropdowns + coverage toggle), tabbed stats pane right

### Key Files

```
index.html                      — main page, tabbed layout + 3-tab stats pane
map-app/index.html              — MapLibre map with WebGL coverage layer (iframe)
map-app/tab-market.js           — Market tab: operators table + growth chart
map-app/tab-regions.js          — Regions tab: KPI table + gap scores
map-app/analytics.json          — precomputed analytics (rebuild with build_analytics.py)
map-app/chargers.geojson        — 44.8 MB, in repo (rebuild with v4.20 parser)
map-app/charger_summary.json    — in repo
map-app/germany_pop.pmtiles     — 467 MB, gitignored, hosted on Cloudflare R2
map-app/coverage_stats.json     — 939 KB, in repo
map-app/boundaries/             — BKG state/district GeoJSON, in repo
map-app/countries.geojson       — 11.9 MB, country outlines, in repo
data/official_regions.json      — Bundesland/Kreis metadata for dropdowns
scripts/build_analytics.py      — chargers + coverage_stats → analytics.json
scripts/build_population_tiles.py — GHS-POP → charger distance → PMTiles pipeline
scripts/upload_pmtiles.py       — S3 multipart upload to R2
scripts/analyze_providers.py    — BNetzA operator analysis
```

### Generated Data

- **germany_pop.pmtiles** (467 MB): RGBA raster tiles z5-z12. R=pop(log2), G=dist AC, B=dist DC-fast, A=dist ultra. Built by `scripts/build_population_tiles.py`.
- **coverage_stats.json** (939 KB): Cumulative pop buckets at 0-50 km for any/dc/ultra, per state+district. Germany: 82.8M pop, 98.2% within 5km.

### Tile Encoding

- R = `round(log2(pop+1)*255/16)` — 0=empty, 255≈65k
- G = dist nearest AC (0–50km → 0–255, ~196m/step)
- B = dist nearest DC-fast (fast_50 + hpc_150)
- A = dist nearest ultra (ultra_300, ≥300kW)

### Run

```powershell
cd "C:\Users\KitCat\Desktop"
node serve-desktop.js
```

Open: `http://127.0.0.1:8020/v1.420/index.html`

`serve-desktop.js` supports HTTP range requests (required for PMTiles).

### Rebuild Pipeline

```powershell
# Rebuild charger data
& "C:\Users\KitCat\Desktop\tesla semi\.venv\Scripts\python.exe" "C:\Users\KitCat\Desktop\tesla semi\archive\version 4.20-h3-germany-prototype\scripts\parse_bnetza_chargers.py" --input "C:\Users\KitCat\Desktop\tesla semi\data\Ladesaeulenregister_BNetzA_2026-04-22.csv" --out-dir "C:\Users\KitCat\Desktop\v1.420\map-app"
```

```powershell
# Rebuild population tiles + coverage stats
& "C:\Users\KitCat\Desktop\tesla semi\.venv\Scripts\python.exe" "C:\Users\KitCat\Desktop\v1.420\scripts\build_population_tiles.py"
```

## Important Folders

- Root global app (100m tile pipeline reference): `C:\Users\KitCat\Desktop\tesla semi`
- v4.20 H3 Germany (visual reference + BNetzA parser): `C:\Users\KitCat\Desktop\tesla semi\archive\version 4.20-h3-germany-prototype`
- BNetzA CSV: `C:\Users\KitCat\Desktop\tesla semi\data\Ladesaeulenregister_BNetzA_2026-04-22.csv`
- GHS-POP TIFF: `C:\Users\KitCat\Desktop\tesla semi\data\GHS_POP_E2030_GLOBE_R2023A_54009_100_V1_0.tif`

## Don't

- No H3 for population layer (100m GHS-POP cells as ground truth)
- No v2 ingest_bnetza.py (drops Tesla rows)
- No zoom-on-select
- No red fills/boundaries (grey only, color for charger dots)
- No clustering — state/district bubbles instead
- Coverage layer uses teal/amber, NOT charger dot colors
