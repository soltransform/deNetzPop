# Claude Handoff: Tesla Semi / Germany Charger Access Project

Last updated: 2026-05-22.

This handoff is for continuing the project in a Claude Code session. It summarizes the project goal, what was done in the Codex session, what each nearby project version appears to be, what data decisions were made, and the recommended next technical steps.

## One-Sentence Project Goal

Build a Germany-focused EV charging and population-access dashboard for a Tesla Gigafactory Berlin-Brandenburg dual-study application, showing practical data work with official charger data, official/admin boundaries, and population coverage analysis.

The target role/application context is:

- Tesla Gigafactory Berlin-Brandenburg.
- Dual-study program: `Studium Mobilität Umwelt Logistik (B.Sc.) – TH Wildau`.
- Practical fit: logistics, data science, process analysis, infrastructure planning, supply chain / material-flow thinking.
- Portfolio goal: compensate for limited formal practical experience by showing a concrete, useful, visually understandable geospatial/data project.

## User Preference / Product Direction

The user does not want a generic polished consumer product. They want something that feels like a real analytical/logistics/data dashboard:

- Useful over decorative.
- Plain enough to read as serious data work.
- Recruiter-facing, but not a marketing landing page.
- Germany-focused is preferred over global for the application context.
- Official BNetzA data gives legitimacy.
- Population coverage is the core analytical story.
- Region drilldown should support German administrative geography: Bundesland, Kreis, possibly Gemeinde later.

The user especially wants to preserve the original GHS-POP 100m data model where possible:

```text
GHS-POP 100m cells in Mollweide
-> clip/filter to Germany
-> calculate distance/access against charger locations
-> render/reproject to Web Mercator for the map
```

Important conceptual point: avoid converting the 100m GHS-POP grid into H3 for the final version if the goal is to show the original population ground truth. H3 was useful, but it resamples/aggregates the original grid into a different spatial system.

## Current Working Folder

Current experimental working project:

```text
C:\Users\KitCat\Desktop\v1.420
```

Run server:

```powershell
cd "C:\Users\KitCat\Desktop"
node serve-desktop.js
```

Open:

```text
http://127.0.0.1:8020/v1.420/index.html
```

Git exists in `v1.420`.

Last known commit:

```text
3258fc7 Checkpoint v1.420 prototype
```

Last known git status:

```text
 M index.html
 M map.html
?? data/official_regions.json
?? map-app/
?? scripts/
```

The git warning:

```text
warning: unable to access 'C:\Users\KitCat/.config/git/ignore': Permission denied
```

has been seen repeatedly and appears harmless for this work.

## What We Did In This Codex Session

### 1. Created / used `v1.420` as a safe working copy

The user wanted a new directory on the Desktop and initially only wanted a blank page. There was a misstep where too much old content was copied, then it was reset back toward a cleaner prototype. The folder is now the current scratch/prototype space.

### 2. Built an initial two-column layout

`v1.420/index.html` became a two-column page:

- Left side: map iframe.
- Right side: controls/dashboard area.

The current `index.html` points the iframe to:

```html
<iframe class="map-frame" id="map-frame" title="Germany charger map" src="/v1.420/map-app/index.html"></iframe>
```

This means the active map is **not** the old `map.html`; it is:

```text
C:\Users\KitCat\Desktop\v1.420\map-app\index.html
```

### 3. Added a map shell copied/adapted from the original architecture

The map shell currently uses:

- MapLibre GL JS.
- CARTO Voyager raster basemap.
- BKG boundaries for Germany.
- BNetzA charger points as a first-pass layer.

Active map folder:

```text
C:\Users\KitCat\Desktop\v1.420\map-app
```

Important files:

```text
map-app/index.html
map-app/bnetza_chargers.geojson
map-app/boundaries/bkg_states.geojson
map-app/boundaries/bkg_districts.geojson
map-app/boundaries/bkg_boundaries_summary.json
```

### 4. Added official Bundesland/Kreis dropdowns

Generated:

```text
data/official_regions.json
```

from BKG boundaries.

It contains:

- 16 Bundesländer.
- 400 Kreise.
- Bboxes and IDs usable for zoom/filter.

The page currently has:

- Bundesland dropdown.
- Kreis dropdown.
- Clear button.

Gemeinde was discussed earlier, but the current latest direction is only Bundesland and Kreis for now.

### 5. Wired dropdowns to the map

`index.html` posts messages to the map iframe:

- `fit-bounds`
- `set-charger-filter`
- `select-region`

The map listens for these messages and:

- zooms to selected region,
- highlights selected region,
- filters/reclusters charger points by `state_id` / `district_id`.

### 6. Made map regions clickable

The map now supports clicking:

- Bundesländer.
- Kreise after/within a Bundesland context.

Map click sends:

```js
{ type: "map-region-click", level: "state", id }
{ type: "map-region-click", level: "district", id, stateId }
```

The parent page syncs the dropdowns and applies the selection.

### 7. Added red Kreis outlines when selecting a Bundesland

When a Bundesland is selected, all Kreise inside it are outlined in red. This matches the user request:

> I also want to see all the Kreise outlined in red after selecting a Bundesland.

### 8. Added a rough BNetzA charger layer

Generated:

```text
C:\Users\KitCat\Desktop\v1.420\map-app\bnetza_chargers.geojson
```

using:

```text
C:\Users\KitCat\Desktop\v1.420\scripts\build_bnetza_geojson.py
```

Input CSV:

```text
C:\Users\KitCat\Desktop\tesla semi\data\Ladesaeulenregister_BNetzA_2026-04-22.csv
```

Last known output:

- About 109,646 charger features.
- Includes official `state_id` and `district_id`.
- `metadata.unmatched_official_region_rows = 0`.
- This is currently row-level BNetzA data, not a carefully grouped physical-site dataset.

Important: this rough file should not be treated as the final charger analysis model.

### 9. Investigated the BNetzA CSV

Known facts from earlier inspection:

- CSV path:

```text
C:\Users\KitCat\Desktop\tesla semi\data\Ladesaeulenregister_BNetzA_2026-04-22.csv
```

- Approximately 109,646 rows.
- 47 columns.
- Mostly `In Betrieb`, with a small number `In Wartung`.
- Includes:
  - `Ladeeinrichtungs-ID`
  - `Betreiber`
  - `Anzeigename (Karte)`
  - `Status`
  - `Art der Ladeeinrichtung`
  - `Anzahl Ladepunkte`
  - `Nennleistung Ladeeinrichtung [kW]`
  - `Inbetriebnahmedatum`
  - address fields
  - `Ort`
  - `Kreis/kreisfreie Stadt`
  - `Bundesland`
  - `Breitengrad`
  - `Längengrad`
  - parking/payment/opening-hour fields
  - up to 6 connector slots with connector type, connector power, EVSE-ID, and public key

Important issue discovered:

- The original BNetzA CSV includes Tesla rows.
- Some earlier processed v2 data dropped Tesla rows intentionally to avoid duplicate Tesla stations when using supercharge.info as Tesla source of truth.
- Therefore, any provider/network summary that says Tesla is missing from BNetzA is likely using a processed dataset that intentionally removed Tesla, not the raw BNetzA CSV.

Known Tesla-like BNetzA counts from previous inspection:

```text
Tesla Germany GmbH: 3,657 rows / 3,657 Ladepunkte
Tesla Manufacturing Brandenburg SE: 567 rows / 567 Ladepunkte
Total Tesla-like BNetzA rows: 4,225
```

### 10. Found that a better Germany BNetzA/H3 prototype already exists

Very important folder:

```text
C:\Users\KitCat\Desktop\tesla semi\archive\version 4.20-h3-germany-prototype
```

This version is much more complete than `v1.420` for Germany EV charger access.

Run it with the Desktop server:

```powershell
cd "C:\Users\KitCat\Desktop"
node serve-desktop.js
```

Open:

```text
http://127.0.0.1:8020/tesla%20semi/archive/version%204.20-h3-germany-prototype/frontend/index.html
```

This version is visually strong and already has:

- Germany EV charger access dashboard.
- BNetzA chargers.
- Charger filters: All, 50+, 150+, 300+.
- Access radius controls.
- BKG boundaries.
- H3 population/access layer.
- Map stats:
  - selected sites,
  - charge points,
  - people within selected radius,
  - Germany H3 population.
- Strong "dark brown / red / green coverage" visual identity.

User reaction: v4.20 is "seriously cool", especially the basemap/style.

### 11. Discussed H3 vs 100m grid

H3 v4.20 is analytically good and visually impressive, but the user dislikes the hexagon artifacts and does not want the final population model to be resampled from GHS-POP 100m into H3.

The correct framing:

- H3 is not wrong.
- But it changes the data model.
- GHS-POP is already a 100m population grid in Mollweide.
- The final desired project should preserve those original cells as much as possible.

Preferred final pipeline:

```text
GHS-POP 100m Mollweide source cells
-> Germany clip / region filtering
-> charger distance/access analysis in a metric projection
-> render as Web Mercator tiles / PMTiles in browser
```

Analysis distances should not be computed in Web Mercator. Use a proper metric CRS for Germany/Europe, likely EPSG:3035 or another appropriate equal-area/metric projection, then render output to Web Mercator for MapLibre.

## Version Inventory

This is the current understanding of nearby project versions.

### A. Root project: `C:\Users\KitCat\Desktop\tesla semi`

This is the main/original global Tesla Supercharger Access project.

Root README says it answers:

> What fraction of the world's population lives within X km of an open Tesla Supercharger?

Architecture:

- Static frontend in `frontend/`.
- MapLibre GL JS + CARTO Voyager basemap.
- GHS-POP 2030 global population raster.
- Native source CRS: Mollweide / `ESRI:54009`.
- Nominal source resolution: 100m.
- Precomputed tile pyramid under `frontend/tiles/{z}/{x}/{y}.png`.
- Optional sparse Germany road-distance override tiles under `frontend/tiles_road/`.
- Global stats in `frontend/pop_cumulative.json`.
- Country stats in `frontend/country_stats.json`.
- Charger markers in `frontend/chargers.json`.

Important root data paths:

```text
C:\Users\KitCat\Desktop\tesla semi\data\GHS_POP_E2030_GLOBE_R2023A_54009_100_V1_0.tif
C:\Users\KitCat\Desktop\tesla semi\data\tesla_scrape.json
C:\Users\KitCat\Desktop\tesla semi\data\populated_pixels.npz
C:\Users\KitCat\Desktop\tesla semi\data\chargers.npz
C:\Users\KitCat\Desktop\tesla semi\data\pixel_distances.npz
```

Important generated frontend files:

```text
C:\Users\KitCat\Desktop\tesla semi\frontend\tiles
C:\Users\KitCat\Desktop\tesla semi\frontend\tiles_road
C:\Users\KitCat\Desktop\tesla semi\frontend\pop_cumulative.json
C:\Users\KitCat\Desktop\tesla semi\frontend\country_stats.json
C:\Users\KitCat\Desktop\tesla semi\frontend\chargers.json
```

This root project is the strongest reference for the desired final 100m-GHS/Mollweide-to-WebMercator pipeline.

Run root v1:

```powershell
cd "C:\Users\KitCat\Desktop\tesla semi"
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

### B. Desktop `v2`: `C:\Users\KitCat\Desktop\v2`

This is a separate "middle v2" directly on the Desktop, not the same as `tesla semi\v2`.

It contains:

```text
C:\Users\KitCat\Desktop\v2\data-pipeline
C:\Users\KitCat\Desktop\v2\frontend
```

Important outputs in:

```text
C:\Users\KitCat\Desktop\v2\frontend\public
```

include:

```text
population.pmtiles          ~7.7 GB
germany_coverage.pmtiles    ~179 MB
pop_cumulative.json
chargers.json
```

This version appears directly relevant to the user's PMTiles idea. It already has PMTiles output, including a large `population.pmtiles` file that likely packs 100m-ish population tiles.

Frontend tech:

- React + Vite.
- MapLibre GL.
- `pmtiles` JS package.

Run:

```powershell
cd "C:\Users\KitCat\Desktop\v2\frontend"
npm run dev
```

Likely open:

```text
http://127.0.0.1:5173/
```

Pipeline files:

```text
C:\Users\KitCat\Desktop\v2\data-pipeline\build_db.py
C:\Users\KitCat\Desktop\v2\data-pipeline\compute_stats.py
C:\Users\KitCat\Desktop\v2\data-pipeline\generate_stats.py
C:\Users\KitCat\Desktop\v2\data-pipeline\pack_tiles.py
```

`pack_tiles.py` reads PNG tiles from:

```text
../../frontend/tiles_road
```

and writes:

```text
../frontend/public/germany_coverage.pmtiles
```

This version should be inspected carefully before rebuilding any PMTiles pipeline from scratch.

### C. Repo `v2`: `C:\Users\KitCat\Desktop\tesla semi\v2`

This is different from Desktop `v2`.

Goal from docs:

> How did public EV charging infrastructure grow across the world, and how does that compare to EV adoption?

Architecture:

- Vite + TypeScript + Three.js + three-globe.
- Globe-first, not flat map.
- Multi-network charger ingestion.
- Intended raw data + WebGPU compute direction.

Relevant scripts:

```text
v2/scripts/ingest_supercharge.py
v2/scripts/ingest_bnetza.py
v2/scripts/ingest_irve.py
v2/scripts/ingest_afdc.py
v2/scripts/ingest_nobil.py
v2/scripts/ingest_iea_ev_stock.py
v2/scripts/build_country_catalog.py
v2/scripts/build_network_catalog.py
v2/scripts/build_population_layer.py
v2/scripts/build_station_summary.py
v2/scripts/validate_v2_data.py
```

Important BNetzA warning:

- `v2/scripts/ingest_bnetza.py` intentionally drops Tesla rows.
- Reason: supercharge.info is treated as Tesla source of truth.
- This is fine for global multi-network dedup logic, but not fine if the Germany dashboard wants to use only official BNetzA as source of truth.

Run repo v2:

```powershell
cd "C:\Users\KitCat\Desktop\tesla semi\v2\frontend"
npm run dev
```

Likely open:

```text
http://127.0.0.1:5173/
```

This version is more of a global/globe rewrite and is probably not the foundation for the current Germany application dashboard, but its ingest scripts are useful references.

### D. Repo `v3`: `C:\Users\KitCat\Desktop\tesla semi\v3`

V3 is another globe/projection experiment.

Docs:

```text
C:\Users\KitCat\Desktop\tesla semi\docs\V3_ARCHITECTURE.md
C:\Users\KitCat\Desktop\tesla semi\v3\docs\CODEX_PROMPT_POP_1KM.md
C:\Users\KitCat\Desktop\tesla semi\v3\docs\pop_1km_format.md
```

Known direction:

- 3D globe.
- Mollweide source raster wrapped onto sphere.
- 1km global population layer.
- Berlin-region 100m crop tests.
- Designed around preserving Mollweide data more directly on a globe.

Important files:

```text
v3/scripts/build_pop_mollweide.py
v3/scripts/build_pop_region.py
v3/scripts/build_pop_global_1km.py
v3/scripts/build_pop_1km_display.py
v3/scripts/build_chargers_region.py
v3/frontend/src/main.ts
```

This is useful for understanding population encoding / Mollweide thinking, but it is a globe project and likely not the current Germany flat-map dashboard foundation.

### E. Archived v4.20 H3 Germany prototype

Path:

```text
C:\Users\KitCat\Desktop\tesla semi\archive\version 4.20-h3-germany-prototype
```

This is the most impressive Germany dashboard prototype currently found.

Important files:

```text
frontend/index.html
frontend/data/chargers.geojson
frontend/data/charger_summary.json
frontend/data/h3_access_deu_r8.csv.gz
frontend/data/h3_access_deu_r8_summary.json
frontend/data/h3_population_deu_r8.csv.gz
frontend/data/h3_population_deu_r8.geojson.gz
frontend/data/h3_population_deu_r8_summary.json
frontend/data/h3_tiles_metadata.json
frontend/h3_tiles
scripts/parse_bnetza_chargers.py
scripts/fetch_bkg_boundaries.py
scripts/build_h3_population.py
scripts/build_h3_access.py
scripts/build_h3_vector_tiles.py
```

README states the pipeline:

```text
population cells -> H3 population table
BNetzA chargers  -> classified charger points
distance model   -> nearest charger / access radius by charger class
frontend         -> hex map, charger filters, regional stats
```

Run via Desktop server:

```powershell
cd "C:\Users\KitCat\Desktop"
node serve-desktop.js
```

Open:

```text
http://127.0.0.1:8020/tesla%20semi/archive/version%204.20-h3-germany-prototype/frontend/index.html
```

Or with Python:

```powershell
cd "C:\Users\KitCat\Desktop\tesla semi"
.venv/Scripts/python -m http.server 8010 --directory "archive/version 4.20-h3-germany-prototype/frontend"
```

Open:

```text
http://localhost:8010/
```

Strongest parts to reuse:

- Visual/dashboard feel.
- BNetzA parser.
- BKG boundary fetcher.
- Charger class semantics.
- Charger summary/data aggregation.
- Overall Germany access dashboard concept.

Weakness for final direction:

- Uses H3 resolution 8.
- H3 resamples the 100m GHS-POP source grid.
- User wants final version closer to original 100m Mollweide source cells.

## BNetzA Parser From v4.20

The mature parser is:

```text
C:\Users\KitCat\Desktop\tesla semi\archive\version 4.20-h3-germany-prototype\scripts\parse_bnetza_chargers.py
```

It is better than the quick `v1.420/scripts/build_bnetza_geojson.py`.

Known behavior:

- Uses stdlib only.
- Reads CSV with `cp1252` encoding.
- Filters to in-service rows by default.
- Parses up to 6 connector slots.
- Computes `max_connector_kw`.
- Detects whether a site has DC.
- Groups rows into physical charging sites.
- Aggregates charge points and site power.
- Aggregates connector types.
- Writes:

```text
frontend/data/chargers.geojson
frontend/data/charger_summary.json
```

Charger class logic:

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

This parser should likely be copied/adapted into the final working folder rather than continuing with the rough row-level file.

## Important Data/Source Decisions

### BNetzA vs supercharge.info for Tesla

For the Germany official-data story, use BNetzA as the main source of truth unless explicitly showing a comparison.

What BNetzA gives:

- Official German registry.
- Operator.
- Status.
- Address.
- Coordinates.
- Commissioning date.
- Connector powers and connector metadata.
- Charge point counts.
- Good legitimacy for German application context.

What BNetzA may not give as well as supercharge.info:

- Tesla-specific station identity and naming quality.
- Global Tesla network history.
- Stall generation labels like V2/V3/V4 as clean categorical data.
- Open-to-non-Tesla metadata.
- Possibly better Tesla station lifecycle details.

For this project, the cleanest portfolio story is:

```text
Official BNetzA charger registry + official population/admin geodata.
```

If Tesla-specific comparison is included, document it explicitly:

```text
BNetzA official registry vs supercharge.info community/Tesla-specialized source.
```

Do not silently mix them.

### Charger power categories

Working classes used in v4.20:

```text
ac_normal
fast_50
hpc_150
ultra_300
```

UI labels:

```text
All
50+
150+
300+
```

These are practical analytical classes, not necessarily official BNetzA category names.

Known BNetzA official-ish field:

```text
Art der Ladeeinrichtung
```

with values like:

```text
Normalladeeinrichtung
Schnellladeeinrichtung
```

But for richer analysis, power thresholds from connector kW are more useful than relying only on BNetzA's broad normal/fast category.

### Population data

The original/root project uses:

```text
GHS_POP_E2030_GLOBE_R2023A_54009_100_V1_0.tif
```

Key points:

- GHS-POP 2030.
- Global.
- Mollweide / `ESRI:54009`.
- 100m source cells.

User wants to preserve the 100m source grid rather than converting to H3 for final.

### Projection / distance math

Do not compute distance in Web Mercator.

Better approach:

```text
Source cells: Mollweide / ESRI:54009
Analysis CRS: metric CRS suitable for Germany/Europe, likely EPSG:3035
Browser display: Web Mercator, via raster/vector tiles
```

For the final map:

- Keep cell values grounded in original GHS-POP 100m cells.
- Render via tiled Web Mercator output for MapLibre.
- PMTiles is a good hosting/package format.

## Recommended Next Steps

The recommended direction is **not** to keep iterating deeply inside the current rough `v1.420` charger dump. Instead:

### Step 1: Choose final foundation

Best practical foundation:

```text
Start from v4.20 visual/dashboard concept
+ replace H3 access layer with 100m GHS-POP / PMTiles-style output
+ keep/adapt v4.20 BNetzA cleaner
+ borrow `v1.420` region selector/click behavior if useful
```

Do not discard `v1.420`, but treat it as an experiment for:

- iframe layout,
- Bundesland/Kreis dropdowns,
- region click messaging,
- red Kreis outlines.

### Step 2: Create a fresh final working folder

Suggested new folder:

```text
C:\Users\KitCat\Desktop\tesla-germany-access
```

or:

```text
C:\Users\KitCat\Desktop\v4.21-germany-100m
```

Avoid continuing in too many existing version folders.

### Step 3: Copy v4.20 frontend as baseline

Copy:

```text
C:\Users\KitCat\Desktop\tesla semi\archive\version 4.20-h3-germany-prototype\frontend
```

into the new folder.

Keep the look and map feel initially. Remove/replace H3 layer only after the baseline runs.

### Step 4: Copy/adapt v4.20 BNetzA parser

Copy:

```text
archive/version 4.20-h3-germany-prototype/scripts/parse_bnetza_chargers.py
```

into the new project.

Modify outputs to generate a clean grouped charger dataset for the final app.

Add official region IDs if needed:

- `state_id`
- `district_id`

Use the approach from:

```text
v1.420/scripts/build_bnetza_geojson.py
```

for matching BNetzA text regions to official BKG IDs, but keep the better v4.20 grouping/classification.

### Step 5: Inspect Desktop `v2` PMTiles

Before building PMTiles from scratch, inspect:

```text
C:\Users\KitCat\Desktop\v2\frontend\public\population.pmtiles
C:\Users\KitCat\Desktop\v2\frontend\public\germany_coverage.pmtiles
```

These may already contain the 100m/coverage PMTiles work the user remembers.

Questions to answer:

- What exactly is inside `population.pmtiles`?
- Is it raw population intensity, coverage, or both?
- What zoom levels?
- What tile encoding?
- Does it preserve 100m source-cell appearance?
- Can `germany_coverage.pmtiles` be reused or regenerated with BNetzA chargers?

### Step 6: Define final 100m analysis pipeline

The final analysis should probably produce:

```text
cleaned_bnetza_sites.geojson
population_cells_germany.{parquet/npz/csv.gz}
distance_to_nearest_charger_by_class.{parquet/npz}
coverage_tiles.pmtiles
population_cumulative_by_radius.json
population_cumulative_by_region.json
```

Needed outputs for the UI:

- Map coverage layer.
- Charger point layer.
- Bundesland/Kreis drilldown.
- Cumulative population-distance chart.
- Stats by selected region and charger class.

### Step 7: Build the cumulative graph

User wants a slider-controlled cumulative chart:

- X-axis: distance from charger in km.
- Y-axis: cumulative population of Germany / selected region.
- Slider controls distance.
- A dot moves along the cumulative curve.
- Annotation above dot shows cumulative percentage.
- Y-axis can show actual population.
- As slider moves right, chart fills/colors from left to selected distance.

Important: this chart should be cumulative, not a raw histogram.

Suggested implementation:

- Use D3 or Apache ECharts in frontend.
- Python can generate the cumulative JSON.
- For CV/story value, Python data processing + JS visualization is good.

### Step 8: Add region drilldown to final UI

Borrow ideas/code from `v1.420`:

- Bundesland dropdown.
- Kreis dropdown.
- Click Bundesland/Kreis on map.
- Red Kreis outlines inside selected Bundesland.
- Filtering of chargers/statistics to selected region.

Do this after the data model is clean.

## Suggested Final UI

Visual foundation: v4.20 style, because the user likes it.

Possible layout:

- Full map background or map-dominant layout.
- Left/dark floating control panel from v4.20.
- Controls:
  - charger class: All / 50+ / 150+ / 300+
  - radius selector/slider
  - Bundesland
  - Kreis
  - boundary toggle
- Stats:
  - selected charger sites
  - charge points
  - population within radius
  - share of selected-region population
  - maybe people per charger
- Chart:
  - cumulative population vs distance
  - currently selected radius marker
- Map layers:
  - 100m population/access coverage
  - BNetzA charger dots
  - BKG boundaries

## Open Risks / Things To Verify

1. Current `v1.420/map-app/bnetza_chargers.geojson` is row-level and large (~52 MB). It may be too heavy and semantically wrong for final stats.

2. v4.20 `chargers.geojson` is better but groups by physical site and charger class. Need verify its grouping rules match final dashboard semantics.

3. Desktop `v2` contains PMTiles files that may already solve part of the 100m tiling problem. Inspect before rebuilding.

4. The old `v1.420/README.md` and `PROJECT_NOTES.md` are partly stale. They describe earlier states with `map.html`, a Tesla graph, and removed dashboard attempts. This handoff supersedes them.

5. BNetzA official data is legitimate but not necessarily perfect:
   - It is based on registry notifications.
   - Public availability may be higher/lower in practice.
   - Tesla-specific metadata may be weaker than supercharge.info.

6. The final app should clearly attribute data:
   - BNetzA Ladesäulenregister for chargers.
   - BKG VG250 for boundaries.
   - GHS-POP/JRC for population.
   - Any other sources if used.

## Good Commands

### Serve all Desktop static folders

```powershell
cd "C:\Users\KitCat\Desktop"
node serve-desktop.js
```

Current prototype:

```text
http://127.0.0.1:8020/v1.420/index.html
```

Archived v4.20 Germany H3:

```text
http://127.0.0.1:8020/tesla%20semi/archive/version%204.20-h3-germany-prototype/frontend/index.html
```

Root global v1:

```text
http://127.0.0.1:8020/tesla%20semi/frontend/index.html
```

### Run repo root v1 with Python

```powershell
cd "C:\Users\KitCat\Desktop\tesla semi"
.venv/Scripts/python -m http.server 8001 --directory frontend
```

Open:

```text
http://127.0.0.1:8001/index.html
```

### Run archived v4.20 with Python

```powershell
cd "C:\Users\KitCat\Desktop\tesla semi"
.venv/Scripts/python -m http.server 8010 --directory "archive/version 4.20-h3-germany-prototype/frontend"
```

Open:

```text
http://127.0.0.1:8010/
```

### Run Desktop v2 frontend

```powershell
cd "C:\Users\KitCat\Desktop\v2\frontend"
npm run dev
```

Open whatever Vite reports, likely:

```text
http://127.0.0.1:5173/
```

### Run repo v2 frontend

```powershell
cd "C:\Users\KitCat\Desktop\tesla semi\v2\frontend"
npm run dev
```

Open whatever Vite reports.

## If Claude Continues From Here

Recommended immediate Claude task:

1. Inspect `C:\Users\KitCat\Desktop\v2\frontend\public\population.pmtiles` and `germany_coverage.pmtiles` metadata/rendering.
2. Inspect `C:\Users\KitCat\Desktop\tesla semi\archive\version 4.20-h3-germany-prototype\scripts\parse_bnetza_chargers.py`.
3. Create a clean final project folder based on v4.20 visuals.
4. Replace the H3 layer with a 100m/PMTiles path if Desktop v2 PMTiles are usable.
5. Keep the BNetzA parser and region selector work.

Do not spend more time polishing `v1.420` until the final data architecture is chosen.

