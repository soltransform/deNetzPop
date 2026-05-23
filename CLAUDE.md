# Claude Memory: Germany EV Charger Access — v1.420

Read this first when starting a Claude Code session in this folder.

## Project Goal

Build a Germany-focused EV charging and population-access dashboard for a Tesla Gigafactory Berlin-Brandenburg dual-study application.

## Current State (2026-05-23)

### What Works

- **Map**: MapLibre with desaturated OSM basemap (v4.20 style)
- **Charger data**: 63,653 grouped physical sites from v4.20 BNetzA parser (109k CSV rows → grouped by operator/address/class)
- **Zoom progression**:
  - Zoom < 7: State bubbles (16 Bundesländer, grey circles showing total charge points)
  - Zoom 7–10: District bubbles (~400 Kreise, grey circles showing total charge points)
  - Zoom 10+: Individual charger dots, color-coded by class
- **Charger classes**: ac_normal (blue), fast_50 (green), hpc_150 (amber), ultra_300 (red)
- **Boundaries**: Grey BKG state and district outlines
- **Selection**: Click state/district bubble or use top-bar dropdowns. District outlines appear on state selection.
- **Layout**: Map on left with frosted top bar (dropdowns), empty right pane for future stats

### Key Files

```
index.html                  — main page, two-column layout + top bar
map-app/index.html          — MapLibre map (iframe)
map-app/chargers.geojson    — generated, gitignored (rebuild with v4.20 parser)
map-app/charger_summary.json — generated, gitignored
map-app/boundaries/         — BKG state/district GeoJSON, gitignored
data/official_regions.json  — Bundesland/Kreis metadata for dropdowns
scripts/                    — data build scripts (from Codex session)
```

### Run

```powershell
cd "C:\Users\KitCat\Desktop"
node serve-desktop.js
```

Open: `http://127.0.0.1:8020/v1.420/index.html`

### Rebuild Charger Data

```powershell
& "C:\Users\KitCat\Desktop\tesla semi\.venv\Scripts\python.exe" "C:\Users\KitCat\Desktop\tesla semi\archive\version 4.20-h3-germany-prototype\scripts\parse_bnetza_chargers.py" --input "C:\Users\KitCat\Desktop\tesla semi\data\Ladesaeulenregister_BNetzA_2026-04-22.csv" --out-dir "C:\Users\KitCat\Desktop\v1.420\map-app"
```

## What's Next

1. **Population/distance tiles** — adapt root v1 pipeline (100m GHS-POP Mollweide → charger distance → WebMercator tiles) for Germany+BNetzA. Check Desktop v2 PMTiles first.
2. **Stats pane** — wire right panel with coverage stats, charger counts, population within radius
3. **Cumulative chart** — distance vs. cumulative population
4. **Polish** — attribution, final styling

## Important Folders

- Root global app (100m tile pipeline reference): `C:\Users\KitCat\Desktop\tesla semi`
- v4.20 H3 Germany (visual reference + BNetzA parser): `C:\Users\KitCat\Desktop\tesla semi\archive\version 4.20-h3-germany-prototype`
- Desktop v2 (PMTiles experiment): `C:\Users\KitCat\Desktop\v2`
- BNetzA CSV: `C:\Users\KitCat\Desktop\tesla semi\data\Ladesaeulenregister_BNetzA_2026-04-22.csv`
- GHS-POP TIFF: `C:\Users\KitCat\Desktop\tesla semi\data\GHS_POP_E2030_GLOBE_R2023A_54009_100_V1_0.tif`

## Don't

- Don't use H3 for final population layer (user wants 100m GHS-POP cells)
- Don't use v2 ingest_bnetza.py (drops Tesla rows)
- Don't add zoom-on-select behavior
- Don't add red fills or red boundaries (grey only, color reserved for charger dots)
- Don't add clustering — use state/district bubbles instead
