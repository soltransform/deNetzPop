# Full Project Memory For Claude

Last updated: 2026-05-22.

This document consolidates the README, CLAUDE, Codex, architecture, status, runbook, and version notes from the project folders. It is intended to teach Claude Code the project context before continuing.

## 1. Human Goal

The user is applying for a dual-study program at Tesla Gigafactory Berlin-Brandenburg:

```text
Studium Mobilität Umwelt Logistik (B.Sc.) – TH Wildau
Praxisort: Gigafactory Berlin-Brandenburg
Field: Supply Chain / Logistics / Data Science
```

The project is meant to strengthen the application by showing practical ability in:

- data handling,
- geospatial analysis,
- logistics/infrastructure thinking,
- charger-network interpretation,
- population coverage analysis,
- making a useful dashboard from real data.

The user has limited formal practical experience, so the project is intended as concrete evidence of initiative and analytical ability.

The desired message to a recruiter is:

```text
I can take messy infrastructure/population data, clean it, analyze it spatially, and turn it into a usable decision-support dashboard.
```

This is especially aligned with Tesla logistics/process/data roles where one might later manage flows of materials, vehicles, charging infrastructure, robotaxi/semitruck fleets, Optimus manufacturing systems, or AI/digital agents.

## 2. Product Direction

The project direction has narrowed to Germany.

Reasons:

- Germany matches the Tesla Gigafactory Berlin-Brandenburg application.
- BNetzA charger data is official and gives legitimacy.
- Germany has rich charger infrastructure data and clean administrative geography.
- Germany scope is achievable and defensible.
- A focused Germany dashboard is stronger for this application than a vague global project.

The user does **not** want a glossy generic consumer product. They prefer a dashboard/tool that feels:

- analytical,
- data-oriented,
- useful,
- credible,
- somewhat plain or operational,
- closer to a logistics/BI dashboard than a marketing page.

Avoid turning the final product into a landing page. Build the actual tool.

## 3. Core Analytical Story

The intended final story:

```text
Using official German charger data and high-resolution population data,
show how much of Germany's population has access to public EV charging
within a selected distance, charger class, and administrative region.
```

Key dimensions:

- Charger class:
  - all public chargers,
  - 50 kW+,
  - 150 kW+,
  - 300 kW+.
- Radius:
  - interactive distance threshold.
- Region:
  - all Germany,
  - Bundesland,
  - Kreis,
  - maybe Gemeinde later.
- Output:
  - map coverage layer,
  - charger points,
  - selected region stats,
  - cumulative population-distance chart.

## 4. Preferred Final Data Model

The user prefers the original 100m GHS-POP cell model, not H3.

Reason:

- GHS-POP source data is already a 100m population grid in Mollweide.
- Converting it to H3 resamples/aggregates the source into a different grid.
- H3 creates visually skewed/abstract hexagons in Web Mercator.
- The user wants to say the map shows the original population ground truth as directly as possible.

Preferred conceptual pipeline:

```text
GHS-POP 100m Mollweide cells
-> keep populated cells / clip to Germany
-> compute charger access using a proper metric method
-> render/reproject output to Web Mercator for MapLibre
-> package as tiles or PMTiles
```

Important correction:

- Do not compute analytical distances in Web Mercator.
- Use a metric CRS suitable for Germany/Europe, likely EPSG:3035, or another defensible distance method.
- Web Mercator is for browser display only.

## 5. Current Working Folder: `v1.420`

Path:

```text
C:\Users\KitCat\Desktop\v1.420
```

Run:

```powershell
cd "C:\Users\KitCat\Desktop"
node serve-desktop.js
```

Open:

```text
http://127.0.0.1:8020/v1.420/index.html
```

Git:

```text
3258fc7 Checkpoint v1.420 prototype
fc25049 docs: add Claude handoff
```

Known uncommitted state after the Codex session:

```text
 M index.html
 M map.html
?? data/official_regions.json
?? map-app/
?? scripts/
```

The `.git` ownership may be mismatched because the repo was created by a different Windows identity. Git may need:

```powershell
git -c safe.directory=C:/Users/KitCat/Desktop/v1.420 status
```

or an explicit safe-directory config if Claude needs to commit.

### What `v1.420` Contains

`index.html`:

- two-column layout,
- left iframe map,
- right controls/dashboard area,
- Bundesland dropdown,
- Kreis dropdown,
- clear selection button.

Current active map iframe:

```html
src="/v1.420/map-app/index.html"
```

Active map:

```text
C:\Users\KitCat\Desktop\v1.420\map-app\index.html
```

Data:

```text
C:\Users\KitCat\Desktop\v1.420\data\official_regions.json
C:\Users\KitCat\Desktop\v1.420\map-app\bnetza_chargers.geojson
C:\Users\KitCat\Desktop\v1.420\map-app\boundaries\bkg_states.geojson
C:\Users\KitCat\Desktop\v1.420\map-app\boundaries\bkg_districts.geojson
```

Scripts:

```text
C:\Users\KitCat\Desktop\v1.420\scripts\build_official_regions.py
C:\Users\KitCat\Desktop\v1.420\scripts\build_bnetza_geojson.py
```

### What Was Implemented In `v1.420`

- MapLibre map shell with CARTO Voyager basemap.
- Official BKG Bundesland and Kreis boundaries.
- `official_regions.json` generated from BKG boundaries:
  - 16 Bundesländer,
  - 400 Kreise.
- Bundesland/Kreis dropdowns.
- Map selection messages:
  - `fit-bounds`,
  - `set-charger-filter`,
  - `select-region`.
- Map -> parent click messages:
  - `map-region-click` for states,
  - `map-region-click` for districts.
- Clickable Bundesländer.
- Clickable Kreise.
- Red Kreis outlines after selecting a Bundesland.
- Rough BNetzA charger points loaded and clustered.
- Charger filtering by `state_id` / `district_id`.

### Limitations Of `v1.420`

The `bnetza_chargers.geojson` file is a rough row-level dump:

- about 109,646 features,
- around 52 MB,
- one BNetzA row per feature,
- not grouped into physical sites,
- not final analytics quality.

Use it as a quick visual layer only. For final charger modeling, reuse/adapt the v4.20 parser.

`README.md` and `PROJECT_NOTES.md` in `v1.420` contain older intermediate wording. This memory file and `CLAUDE_HANDOFF.md` supersede them where they disagree.

## 6. Root Project: `C:\Users\KitCat\Desktop\tesla semi`

This is the original/root global Tesla Supercharger Access app.

Goal from README/CLAUDE:

```text
What fraction of the world's population lives within X km of an open Tesla Supercharger?
```

This is the strongest reference for the **100m GHS-POP Mollweide -> WebMercator tile pipeline**.

### Root Architecture

Static frontend:

```text
C:\Users\KitCat\Desktop\tesla semi\frontend\index.html
```

Tech:

- MapLibre GL JS.
- CARTO Voyager basemap.
- Custom MapLibre WebGL coverage layer.
- Precomputed PNG tile pyramid.
- Shader-side radius thresholding.

Main data:

```text
data/GHS_POP_E2030_GLOBE_R2023A_54009_100_V1_0.tif
data/tesla_scrape.json
data/populated_pixels.npz
data/chargers.npz
data/pixel_distances.npz
frontend/tiles/{z}/{x}/{y}.png
frontend/pop_cumulative.json
frontend/countries.geojson
frontend/country_stats.json
frontend/chargers.json
```

The population source:

- GHS-POP 2030.
- CRS: Mollweide / `ESRI:54009`.
- Nominal resolution: 100m.
- Values: population per source cell.

Critical design:

- The project does not resample the whole TIFF into Web Mercator first.
- It keeps source-cell centers plus `x_moll` / `y_moll`.
- `precompute_tiles.py` projects each source cell's true Mollweide corners into Web Mercator.
- Then it rasterizes the actual projected footprint.

This is exactly the idea the user wants for Germany: preserve original 100m source cells as much as possible.

### Root Pipeline

Run from:

```powershell
cd "C:\Users\KitCat\Desktop\tesla semi"
```

Full pipeline:

```powershell
.venv/Scripts/python scripts/extract_pixels.py
.venv/Scripts/python scripts/extract_chargers.py
.venv/Scripts/python scripts/compute_distances.py
$env:TILE_ENCODE_WORKERS = "16"
.venv/Scripts/python scripts/precompute_tiles.py 11
.venv/Scripts/python scripts/build_outputs.py
.venv/Scripts/python scripts/precompute_viewport_stats.py
.venv/Scripts/python scripts/precompute_country_stats.py
.venv/Scripts/python scripts/validate_outputs.py
```

Run app:

```powershell
.venv/Scripts/python -m http.server 8001 --directory frontend
```

Open:

```text
http://127.0.0.1:8001/index.html
```

Or with Desktop server:

```text
http://127.0.0.1:8020/tesla%20semi/frontend/index.html
```

### Root Tile Encoding

Current tile format:

```text
R/G = 16-bit distance code
B   = reserved
A   = log-scaled population alpha
```

Distance code:

```text
code = ceil(clamp(distance_km / 500, 0, 1) * 65535)
```

Browser threshold:

```text
radius_code = ceil(radius_km / 500 * 65535)
covered if code <= radius_code
```

This RG16 encoding is important. Do not revert to older 8-bit distance encoding. The 8-bit version made `0 km` visually wrong because small positive distances collapsed to zero.

Stats use:

```text
bucket = ceil(distance_km)
```

So radius `0 km` means only cells with true zero distance.

### Root Tile Geometry

Important caches:

```text
data/npy/wm_z11_x0.npy
data/npy/wm_z11_x1.npy
data/npy/wm_z11_y0.npy
data/npy/wm_z11_y1.npy
data/npy/wm_z11_row_offsets.npy
data/npy/wm_z11_row_indices.npy
```

These caches support exact source-cell WebMercator footprint rasterization.

Do not approximate 100m cells as lat/lon rectangles.

Correct path:

1. Keep `x_moll` and `y_moll`.
2. Build exact 100m source-cell corners in Mollweide.
3. Project those corners to Web Mercator.
4. Rasterize projected footprints into z11 Web Mercator tile pixels.
5. Build lower zooms bottom-up.

### Root Road-Distance Work

Germany road-distance outputs exist:

```text
data/pixel_road_distances_DEU.npz
data/pixel_distances_road.npz
frontend/tiles_road/
frontend/pop_cumulative_road.json
frontend/country_stats_road.json
```

Road-distance tiles are sparse Germany overrides.

Do not run full global road tile generation on this laptop:

```powershell
scripts/precompute_tiles.py 11 --source road
```

Use:

```powershell
.venv/Scripts/python scripts/precompute_road_region_tiles.py --region DEU --workers 1 --max-pending 2
```

The frontend in road mode samples base great-circle tiles and sparse `tiles_road` overrides.

### Root Country Stats

Uses Natural Earth Admin 0 `10m` boundaries.

Current caveats:

- Country population assignment by source-cell center.
- Natural Earth sovereign features may include overseas territories.
- France may not reach 100% at 500 km because Natural Earth France includes overseas territories.
- About 76.4M people are unassigned to country polygons globally.
- Charger country assignment has manual overrides and currently assigns all extracted Tesla chargers.

## 7. Archived v4.20 Germany H3 Prototype

Path:

```text
C:\Users\KitCat\Desktop\tesla semi\archive\version 4.20-h3-germany-prototype
```

Run with Desktop server:

```powershell
cd "C:\Users\KitCat\Desktop"
node serve-desktop.js
```

Open:

```text
http://127.0.0.1:8020/tesla%20semi/archive/version%204.20-h3-germany-prototype/frontend/index.html
```

Or:

```powershell
cd "C:\Users\KitCat\Desktop\tesla semi"
.venv/Scripts/python -m http.server 8010 --directory "archive/version 4.20-h3-germany-prototype/frontend"
```

Open:

```text
http://localhost:8010/
```

### Why v4.20 Matters

This is the visually strongest Germany dashboard prototype.

It has:

- polished dark panel / strong map visual identity,
- Germany EV charger access dashboard,
- official BNetzA charger data,
- BKG boundaries,
- H3 population/access layer,
- charger filters,
- access radius controls,
- selected site and charge-point stats,
- population within radius stats.

The user specifically liked this version and said it was seriously cool.

### v4.20 Pipeline

README pipeline:

```text
population cells -> H3 population table
BNetzA chargers  -> classified charger points
distance model   -> nearest charger / access radius by charger class
frontend         -> hex map, charger filters, regional stats
```

Scripts:

```text
scripts/parse_bnetza_chargers.py
scripts/fetch_bkg_boundaries.py
scripts/build_h3_population.py
scripts/build_h3_access.py
scripts/build_h3_vector_tiles.py
```

Data:

```text
frontend/data/chargers.geojson
frontend/data/charger_summary.json
frontend/data/bkg_germany.geojson
frontend/data/bkg_states.geojson
frontend/data/bkg_regions.geojson
frontend/data/bkg_districts.geojson
frontend/data/bkg_municipalities.geojson
frontend/data/h3_access_deu_r8.csv.gz
frontend/data/h3_population_deu_r8.csv.gz
frontend/data/h3_population_deu_r8.geojson.gz
frontend/h3_tiles/
```

Run commands from README:

```powershell
cd "C:\Users\KitCat\Desktop\tesla semi"
.venv/Scripts/python "version 4.20/scripts/parse_bnetza_chargers.py"
.venv/Scripts/python "version 4.20/scripts/fetch_bkg_boundaries.py"
.venv/Scripts/python "version 4.20/scripts/build_h3_population.py" --resolution 8
.venv/Scripts/python "version 4.20/scripts/build_h3_access.py" --resolution 8
.venv/Scripts/python "version 4.20/scripts/build_h3_vector_tiles.py" --resolution 8 --min-zoom 7 --max-zoom 8 --min-population 25
```

Because the folder is archived, adjust paths to:

```text
archive/version 4.20-h3-germany-prototype
```

### v4.20 Charger Classes

The parser creates:

```text
ac_normal       normal/AC or below 50 kW
fast_50         DC or max connector power >= 50 kW
hpc_150         max connector power >= 150 kW
ultra_300       max connector power >= 300 kW
```

UI filters:

```text
All
Fast 50+
HPC 150+
Ultra 300+
```

### v4.20 BNetzA Parser

Important script:

```text
C:\Users\KitCat\Desktop\tesla semi\archive\version 4.20-h3-germany-prototype\scripts\parse_bnetza_chargers.py
```

This is better than the quick `v1.420` BNetzA dump.

Known behavior:

- stdlib only,
- reads BNetzA CSV with `cp1252`,
- filters to in-service rows by default,
- parses up to six connector slots,
- computes max connector kW,
- detects DC,
- groups BNetzA rows into physical charging sites,
- sums charge points and site power,
- aggregates connector types,
- writes `chargers.geojson` and `charger_summary.json`.

Class logic:

```python
if max_connector_kw >= 300:
    "ultra_300"
elif max_connector_kw >= 150:
    "hpc_150"
elif has_dc or max_connector_kw >= 50 or "Schnell" in kind:
    "fast_50"
else:
    "ac_normal"
```

Grouping key:

```python
normalize(operator), postcode, city, street, house_number, class
```

This parser should be reused/adapted for the final Germany dashboard.

### Weakness Of v4.20

It uses H3 resolution 8.

H3 is useful and visually compelling, but it resamples the GHS-POP 100m grid into hexagons. The user wants final population coverage to stay closer to the original 100m GHS-POP cells.

Use v4.20 for:

- visual style,
- dashboard shape,
- BNetzA parser,
- boundary work.

Do not necessarily use H3 for final population/access layer.

## 8. Desktop `v2`: PMTiles Experiment

Path:

```text
C:\Users\KitCat\Desktop\v2
```

This is **not** the same as:

```text
C:\Users\KitCat\Desktop\tesla semi\v2
```

Desktop `v2` has:

```text
data-pipeline/
frontend/
```

Important files:

```text
frontend/public/population.pmtiles
frontend/public/germany_coverage.pmtiles
frontend/public/pop_cumulative.json
frontend/public/chargers.json
```

Known sizes:

```text
population.pmtiles          ~7.7 GB
germany_coverage.pmtiles    ~179 MB
```

This version may already contain the PMTiles work the user remembers.

Frontend:

- React + Vite.
- MapLibre GL.
- `pmtiles` JS package.

Run:

```powershell
cd "C:\Users\KitCat\Desktop\v2\frontend"
npm run dev
```

Open Vite's URL, likely:

```text
http://127.0.0.1:5173/
```

Pipeline:

```text
data-pipeline/build_db.py
data-pipeline/compute_stats.py
data-pipeline/generate_stats.py
data-pipeline/pack_tiles.py
```

`pack_tiles.py` packs PNG tiles from root project road tiles into:

```text
frontend/public/germany_coverage.pmtiles
```

Before rebuilding PMTiles from scratch, inspect this version:

- What exactly is encoded in `population.pmtiles`?
- Is it population intensity only, access coverage, or both?
- What zoom levels?
- What tile encoding?
- Is `germany_coverage.pmtiles` reusable for the current BNetzA Germany work?

## 9. Repo V2: Multi-Network Globe Rewrite

Path:

```text
C:\Users\KitCat\Desktop\tesla semi\v2
```

Goal:

```text
How did public EV charging infrastructure grow across the world, and how does that compare to EV adoption?
```

This is a broader global/globe rewrite, not the current Germany flat-map dashboard, but it contains useful ingest scripts.

### V2 Intent

Audience:

- EV enthusiast spending 5-15 minutes.
- Secondary: Tesla recruiter.

Product:

- tool, not story,
- no autoplay/scrollytelling,
- honest about data coverage,
- timeline only where authoritative dates exist.

Architecture:

- Vite + TypeScript.
- Three.js / three-globe.
- WebGPU compute planned/partly implemented.
- Multi-network charger schema.
- Country/region filters.
- EV stock comparison.

Data sources:

- supercharge.info for Tesla global.
- BNetzA for Germany.
- IRVE for France.
- Nobil for Norway.
- AFDC for US/Canada.
- UK NCR archive if obtained.
- Open Charge Map as fallback/today spine if no authoritative data.
- IEA/OWID EV stock.
- GHS-POP year-matched population epochs.

### V2 Status From Docs/Log

Ingested station files:

- Tesla: 8,962 stations.
- BNetzA: 105,381 stations.
- IRVE: 63,217 stations.
- AFDC: 86,137 stations.
- Nobil scaffolded but blocked by API key/datadump.

Validator expected:

```text
263,697 station records
0 validation failures
Nobil optional/missing
```

EV stock:

- OWID/IEA total electric car stock.
- 30 countries.
- 2010-2024.
- BEV/PHEV split not available from that source.

Population prototype:

- 0.25-degree global population grid.
- 2030 only.
- `pop_025deg_world_2030.bin`.
- Prototype only, not final 100m/1km layer.

WebGPU coverage:

- `coverageGPU.ts`.
- Uses 1440 x 720 0.25-degree grid.
- One thread per population cell.
- 1-degree charger bucket pruning.
- Atomic totals scaled to kilopeople to avoid u32 overflow.
- World coverage stat wired.
- Region coverage pending country mask.

Coverage layer:

- GPU mask readback to WebGL texture.
- Globe coverage overlay implemented in a Claude shift.

Deployment:

- GitHub Pages deployment existed at:

```text
https://consciousautomaton.github.io/supercharger-availability/
```

### V2 Scripts

Useful scripts:

```text
v2/scripts/ingest_supercharge.py
v2/scripts/ingest_bnetza.py
v2/scripts/ingest_irve.py
v2/scripts/ingest_afdc.py
v2/scripts/ingest_nobil.py
v2/scripts/ingest_iea_ev_stock.py
v2/scripts/build_network_catalog.py
v2/scripts/build_country_catalog.py
v2/scripts/build_station_summary.py
v2/scripts/build_population_layer.py
v2/scripts/build_v2_data.py
v2/scripts/validate_v2_data.py
```

Run V2 data pipeline:

```powershell
cd "C:\Users\KitCat\Desktop\tesla semi"
.venv/Scripts/python v2/scripts/build_v2_data.py
```

Fast derived-data rebuild:

```powershell
.venv/Scripts/python v2/scripts/build_v2_data.py --skip-ingests
```

Validation:

```powershell
.venv/Scripts/python v2/scripts/validate_v2_data.py
```

Frontend:

```powershell
cd "C:\Users\KitCat\Desktop\tesla semi\v2\frontend"
npm run dev
npm run build
```

### Critical V2 BNetzA Warning

`v2/scripts/ingest_bnetza.py` intentionally drops Tesla rows.

Reason:

```text
supercharge.info is treated as Tesla source of truth, so Tesla rows from BNetzA are removed to avoid duplicates.
```

This is acceptable for V2 global multi-network dedup, but wrong if the current Germany application dashboard wants to be based only on official BNetzA.

For the Germany dashboard, do not silently use V2's BNetzA output as the source of truth.

## 10. Repo V3: Mollweide/Globe Population Experiment

Path:

```text
C:\Users\KitCat\Desktop\tesla semi\v3
```

V3 is a globe/projection experiment. It is useful for understanding population formats and preserving Mollweide source data, but probably not the final Germany flat-map foundation.

### V3 Direction

North star:

- clear, beautiful, accurate data visualization,
- tool, not story,
- honest math,
- equal-area population source,
- real km distances,
- no projection trickery.

Display:

- 3D globe.
- Sphere mesh.
- Mollweide source raster wrapped on sphere by shader.
- No WebMercator tile-on-sphere trick.

Important current state from docs:

- 1km global population layer rendering on a Mollweide-on-sphere shader.
- Custom globe drag.
- `pop_1km.bin.zst` raw archive format.
- Display strips to avoid browser pixel-count caps.
- Berlin-region 100m crop pipeline working.

### POP1 Format

V3 introduced a browser-readable lossless 1km population archive:

```text
v3/frontend/public/data/pop_1km.bin.zst
```

Format:

```text
[64-byte POP1 header][dense uint32 little-endian population cells]
```

Compressed with Zstd.

Cells are row-major:

```text
index = y * width + x
```

Each 1km cell is the rounded sum of up to 100 underlying GHS-POP 100m cells, with nodata/negative values treated as zero.

Header:

```text
0  magic POP1
4  version u8
5  dtype tag
6  header length u16
8  width u32
12 height u32
16 raw data byte length u64
24 aggregation factor u16
26 reserved
```

Scripts:

```text
v3/scripts/build_pop_global_1km.py
v3/scripts/check_pop_global_1km.py
v3/scripts/build_pop_mollweide.py
v3/scripts/build_pop_region.py
v3/scripts/build_pop_1km_display.py
v3/scripts/build_chargers_region.py
```

Docs:

```text
v3/docs/pop_1km_format.md
v3/docs/CODEX_PROMPT_POP_1KM.md
docs/V3_ARCHITECTURE.md
```

Useful concept for final Germany work:

- The GHS-POP raster is huge; use windowed reads.
- Do not load the full TIFF into RAM.
- Use progress logging.
- Keep browser-readable compressed formats where useful.
- Berlin-region 100m crop code may be a useful reference for regional 100m work.

## 11. BNetzA Data Facts

Original CSV:

```text
C:\Users\KitCat\Desktop\tesla semi\data\Ladesaeulenregister_BNetzA_2026-04-22.csv
```

Known facts from inspection:

- 109,646 rows.
- 47 columns.
- 109,606 rows with `Status = In Betrieb`.
- 40 rows with `Status = In Wartung`.
- 80,876 `Normalladeeinrichtung`.
- 28,770 `Schnellladeeinrichtung`.
- 197,527 total `Anzahl Ladepunkte`.
- Coordinates for every row.
- Up to six connector slots per row.

Important columns:

```text
Ladeeinrichtungs-ID
Betreiber
Anzeigename (Karte)
Status
Art der Ladeeinrichtung
Anzahl Ladepunkte
Nennleistung Ladeeinrichtung [kW]
Inbetriebnahmedatum
Ort
Kreis/kreisfreie Stadt
Bundesland
Breitengrad
Längengrad
Stecker-Typen
P1 [kW] ... P6 [kW]
EVSE-ID fields
payment / parking / opening-hour fields
```

Tesla rows in raw BNetzA:

```text
Tesla Germany GmbH: 3,657 rows / 3,657 Ladepunkte
Tesla Manufacturing Brandenburg SE: 567 rows / 567 Ladepunkte
Total Tesla-like BNetzA rows: 4,225
```

If Tesla is missing, the data source is probably a processed output that intentionally removed Tesla for dedup.

## 12. Data Source Strategy

For the Germany application dashboard, the cleanest story is:

```text
Official BNetzA charger registry + official/high-quality population/admin geodata.
```

Use:

- BNetzA Ladesäulenregister for chargers.
- BKG VG250 for boundaries.
- GHS-POP for population.

Optional comparison:

- supercharge.info for Tesla-specific comparison only.

Do not silently mix BNetzA Tesla rows and supercharge.info Tesla rows. If both are used, show them as different sources or document dedup rules.

## 13. Desired Cumulative Chart

The user wants a slider-controlled cumulative population chart.

Chart design:

- X-axis: distance from charger in km.
- Y-axis: cumulative population.
- Slider controls selected x-value.
- Dot moves along the curve.
- Annotation above dot shows cumulative percentage.
- Y-axis can show actual population.
- Filled/colored portion of curve extends from zero to selected radius.

Important:

- This is cumulative population, not a histogram.
- A histogram would show population per distance bucket and would not naturally "reach the peak".
- The cumulative curve reaches 100% / total selected-region population.

Suggested stack:

- Python generates cumulative JSON.
- D3 or Apache ECharts renders the chart.
- ECharts may look more BI/dashboard-like.
- D3 gives more control.

## 14. Recommended Final Architecture

Use a new final folder, for example:

```text
C:\Users\KitCat\Desktop\v4.21-germany-100m
```

or:

```text
C:\Users\KitCat\Desktop\tesla-germany-access
```

Recommended composition:

```text
v4.20 visual/dashboard baseline
+ v4.20 BNetzA parser
+ root v1 100m GHS-POP tile/PMTiles pipeline concepts
+ Desktop v2 PMTiles experiments if reusable
+ v1.420 Bundesland/Kreis selector/click behavior
```

Avoid:

- continuing random edits in too many version folders,
- relying on row-level `v1.420` charger GeoJSON,
- resampling final population into H3,
- mixing Tesla data sources without documentation.

## 15. Immediate Next Technical Steps

1. Inspect Desktop `v2` PMTiles:

```text
C:\Users\KitCat\Desktop\v2\frontend\public\population.pmtiles
C:\Users\KitCat\Desktop\v2\frontend\public\germany_coverage.pmtiles
```

Find out:

- layers,
- zoom levels,
- tile type,
- encoding,
- whether the data is reusable.

2. Inspect v4.20 parser and outputs:

```text
C:\Users\KitCat\Desktop\tesla semi\archive\version 4.20-h3-germany-prototype\scripts\parse_bnetza_chargers.py
C:\Users\KitCat\Desktop\tesla semi\archive\version 4.20-h3-germany-prototype\frontend\data\chargers.geojson
C:\Users\KitCat\Desktop\tesla semi\archive\version 4.20-h3-germany-prototype\frontend\data\charger_summary.json
```

3. Create a new final working folder.

4. Copy v4.20 frontend as visual baseline.

5. Replace/adapt charger data with clean grouped BNetzA output.

6. Decide how to generate final 100m population/access tiles:

- reuse Desktop v2 PMTiles if valid,
- or adapt root v1 `precompute_tiles.py` to Germany/BNetzA,
- or build a new PMTiles packer around the root tile output.

7. Add Bundesland/Kreis selectors and clickable boundaries from `v1.420`.

8. Add cumulative distance/population chart.

## 16. Important Run Commands

Desktop server:

```powershell
cd "C:\Users\KitCat\Desktop"
node serve-desktop.js
```

Current `v1.420`:

```text
http://127.0.0.1:8020/v1.420/index.html
```

Root global v1:

```text
http://127.0.0.1:8020/tesla%20semi/frontend/index.html
```

Archived v4.20:

```text
http://127.0.0.1:8020/tesla%20semi/archive/version%204.20-h3-germany-prototype/frontend/index.html
```

Root Python server:

```powershell
cd "C:\Users\KitCat\Desktop\tesla semi"
.venv/Scripts/python -m http.server 8001 --directory frontend
```

Desktop v2:

```powershell
cd "C:\Users\KitCat\Desktop\v2\frontend"
npm run dev
```

Repo v2:

```powershell
cd "C:\Users\KitCat\Desktop\tesla semi\v2\frontend"
npm run dev
```

## 17. Attribution To Preserve

Final app should clearly cite:

- BNetzA Ladesäulenregister for German public charger registry.
- BKG VG250 for German administrative boundaries.
- GHS-POP / JRC for population grid.
- Natural Earth only if using root global country stats.
- supercharge.info only if using Tesla-specific data.

## 18. Claude Behavioral Notes

The user values directness and hates wasted work.

Important:

- Do not overbuild before checking existing versions.
- Do not silently remove UI elements unless asked.
- Do not make broad redesigns without confirming direction.
- Prefer inspecting old versions before rebuilding.
- Keep explanations short unless asked for detail.
- When asked to act, act; when asked for steps only, do not edit files.
- If changing files, state exactly what will be edited before editing.

The user has been frustrated by previous incorrect assumptions around:

- copying too much old UI into `v1.420`,
- confusing map vs graph work,
- assuming H3 was desired,
- using processed BNetzA data where Tesla rows had been removed,
- producing provider stats before understanding raw CSV semantics.

Avoid repeating those mistakes.

