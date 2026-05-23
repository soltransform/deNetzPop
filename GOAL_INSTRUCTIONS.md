# Goal: Population Tiles + Stats Pane for v1.420

## READ FIRST
- C:\Users\KitCat\Desktop\v1.420\CLAUDE.md (project state, constraints, don't-list)
- C:\Users\KitCat\Desktop\v1.420\CLAUDE_HANDOFF.md (Codex handover)
- C:\Users\KitCat\.claude\projects\C--Users-KitCat-Desktop\memory\ (all .md files)

## REFERENCE PIPELINE
Study v1 global pipeline at C:\Users\KitCat\Desktop\tesla semi\scripts\ for patterns:
- extract_pixels.py — GHS-POP TIFF extraction (Mollweide → WGS84), multithreaded strip reading
- compute_distances.py — GPU distance computation (adapt to CPU scipy KD-tree)
- precompute_tiles.py — streaming bottom-up tile pyramid (PNG encoding, memory-bounded). IMPORTANT: study its tile geometry approach — it builds exact 100m cell corners in Mollweide, projects to WebMercator, rasterizes footprints. This is critical for clean aligned output.
- distance_source.py — distance source abstraction
- The v1 CLAUDE.md at C:\Users\KitCat\Desktop\tesla semi\CLAUDE.md has the full tile encoding spec.
Write NEW Germany-specific scripts in C:\Users\KitCat\Desktop\v1.420\scripts\.

## PART 1: TILE PIPELINE

Build single RGBA raster PMTiles for Germany.

### Encoding (per pixel):
- R = population (log2 scale, 8-bit: round(log2(pop+1)*255/16), 0=empty, 255≈65k)
- G = distance to nearest AC charger (0-50km → 0-255, ~196m/step)
- B = distance to nearest DC fast charger (fast_50 + hpc_150, ≥50kW)
- A = distance to nearest ultra-fast charger (ultra_300, ≥300kW)

### Steps:
1. Extract Germany from GHS-POP TIFF (6.2GB, Mollweide ESRI:54009 → EPSG:4326). Bbox: lon 5.5-15.5, lat 47-55.5. Keep x_moll/y_moll for proper tile geometry.
2. Load chargers from map-app/chargers.geojson (63k sites). 3 tiers: AC (ac_normal), DC-fast (fast_50+hpc_150), Ultra (ultra_300).
3. scipy.spatial.cKDTree per tier. Convert to approximate meters for distance.
4. Query nearest per tier → distance km per cell.
5. Render RGBA tiles using v1's tile geometry: Mollweide coords → 100m cell corners → WebMercator → rasterize. z12 first, then z11→z5 bottom-up (population-weighted averaging for distance channels).
6. Package as PMTiles → map-app/germany_pop.pmtiles. Target <500MB, z5-z12.
7. During build, also compute coverage_stats.json (see Part 3 data section).

### Performance:
- ~3-5M populated cells. cKDTree.query < 1 minute.
- Read TIFF in 4096-row strips, filter to Germany Mollweide bbox.
- ~15k tiles at z12. Thread PNG encoding. Total: 5-15 minutes.

## PART 2: MAP INTEGRATION — THRESHOLD RENDERING

The map layer should use THRESHOLD rendering, not a continuous gradient. This is the key design decision — it makes the coverage story binary and powerful: covered vs uncovered.

In map-app/index.html:
- Add pmtiles.js CDN, register PMTiles protocol with MapLibre
- Add a CUSTOM WebGL layer (MapLibre addLayer type:"custom") that reads RGBA tile pixels in a shader. Study how v1 does this at C:\Users\KitCat\Desktop\tesla semi\frontend\index.html — it has a custom WebGL coverage layer with distance thresholding in the shader.
- Shader logic: the user picks a radius (e.g. 5km) and a tier (any/AC/DC-fast/ultra). The shader reads the appropriate channel(s), compares to threshold, colors the pixel:
  - COVERED (distance ≤ radius): soft teal-green (#2DD4BF), alpha from population
  - UNCOVERED (distance > radius): warm amber (#F59E0B), alpha from population
  - EMPTY (no population): transparent
- "Any charger" mode: use min(G,B,A) as distance
- The radius is controlled by pill buttons in the stats pane (1/5/10/25 km). Changing radius updates a shader uniform — instant, no tile re-fetch.
- Layer sits below charger dots, above basemap
- Small toggle pill in top-bar: "Coverage" on/off
- Preserve ALL existing behavior (bubbles, boundaries, selections, popups)

Color note: use teal (#2DD4BF) and amber (#F59E0B) for coverage layer, NOT the charger dot colors (blue/green/amber/red). This avoids visual conflict.

## PART 3: STATS PANE — MINIMALIST "APPLE KEYNOTE" DESIGN

The stats pane is the soul of the dashboard. It should feel like an Apple keynote data slide — one glance tells the whole story. Build in C:\Users\KitCat\Desktop\v1.420\index.html right panel.

Design philosophy: LESS IS MORE. No clutter. Numbers speak. White space breathes.

### SECTION 1: HERO NUMBER (top)
The single most important metric, large and bold:

    94.2%
    of Germans live within 5 km
    of a charger

- The percentage: very large (48-56px), semi-bold, dark charcoal (#1a1a1a)
- The subtitle: small (13-14px), light weight, warm grey (#6b7280)
- Below: 4 pill buttons for radius: [1 km] [5 km] [10 km] [25 km]
  - Styled like Apple segmented controls: rounded, subtle bg, selected state filled
  - Default selected: 5 km
  - Changing radius: number counts up/down with CSS transition (odometer effect)
  - Changing radius also updates the map coverage layer threshold (via postMessage to iframe)
- When a region is selected, show comparison:
    Bayern: 91.3%
    vs 94.2% national  ↓
  Small colored arrow: green ↑ if above national, orange ↓ if below.
  Small "← Germany" back link appears.

### SECTION 2: CUMULATIVE CHART (center, THE STAR)
This chart tells the entire coverage story in one image.

Canvas 2D chart, Apple-quality aesthetics:
- X-axis: distance 0–50 km (only label "0", "25", "50 km" — minimal)
- Y-axis: cumulative % of population (only label "0%", "50%", "100%" — minimal)
- NO grid lines. NO border. Clean white background blending into panel.
- 3 smooth curves with subtle gradient fills underneath:
  - Any charger: 2.5px line, charcoal (#374151), fill fading to transparent
  - DC Fast: 2px line, teal (#0D9488), fill fading to transparent
  - Ultra: 2px line, amber (#D97706), fill fading to transparent
- Curves should be smooth (bezier interpolation between 1km buckets)
- Interactive: on hover/touch, thin vertical crosshair appears, tooltip shows:
  "12 km: 97.3% any · 89.1% DC · 72.4% ultra"
- The currently selected radius (from pills above) shown as a subtle vertical dashed line
- When region selected: national curves become faded (0.25 opacity, dashed), regional curves solid

Below the chart, one auto-computed insight line:
  "95% coverage at 3.2 km (any charger)"
Small text, warm grey. Computed from the data — find the distance where cumulative hits 95%.

### SECTION 3: CHARGER COUNTS (compact)
Single line with colored dots matching map charger colors:
  ● 142k AC   ● 28k Fast   ● 12k HPC   ● 8k Ultra
- Blue (#3b82f6), green (#22c55e), amber (#f59e0b), red (#ef4444)
- Below: "63,653 sites · 11,831 operators" in small grey text
- Updates to region counts on selection

### SECTION 4: MEMORABLE STAT (bottom)
One surprising fact that sticks in the mind:
  Farthest point from any charger:
  23.4 km — Bayerischer Wald
- Small text, italic or light weight
- Auto-computed from tile data: find the cell with max distance (for "any" tier)
- Updates when region changes: shows farthest point within that region

### Styling:
- Background: frosted glass matching top bar (rgba(255,255,255,0.92), backdrop-filter: blur(12px))
- Sections separated by generous whitespace, not lines
- Typography: system font stack (-apple-system, BlinkMacSystemFont, 'Segoe UI', etc.)
- Numbers: tabular-nums for alignment
- Scroll if content overflows on small screens
- Subtle fade-in animations on load (300ms ease-out, staggered by section)

### Data for stats:
- Charger counts/operators: parse from chargers.geojson at load time
- Coverage percentages + cumulative curves: load from map-app/coverage_stats.json
- coverage_stats.json structure (pre-computed during tile build):
  ```json
  {
    "germany": {
      "population": 83200000,
      "buckets_any": [pop_within_0km, pop_within_1km, ..., pop_within_50km],
      "buckets_dc": [...],
      "buckets_ultra": [...],
      "max_distance_any": 23.4,
      "max_distance_location": [lon, lat]
    },
    "states": {
      "Bayern": { same structure },
      "Berlin": { ... }
    },
    "districts": {
      "München, Landeshauptstadt": { same structure }
    }
  }
  ```
  Buckets are CUMULATIVE population counts at each km threshold (0,1,2,...,50).
  Use the BKG boundary GeoJSON files to assign cells to states/districts during tile build.
- PostMessage communication with map iframe for region sync and radius changes

## CONSTRAINTS (CRITICAL)
- NO H3 hexagons — 100m GHS-POP cells as ground truth
- NO v2 ingest_bnetza.py (drops Tesla) — use chargers.geojson
- NO zoom-on-select
- NO red for boundaries/bubbles — grey only. Color for charger dots only.
- Coverage layer uses teal/amber, NOT charger dot colors
- NO removing existing UI elements
- NO broad redesigns — incremental additions only
- Test EVERYTHING in browser before committing

## PYTHON
- Venv: C:\Users\KitCat\Desktop\tesla semi\.venv\Scripts\python.exe
- Packages installed: rasterio, scipy, pyproj, pmtiles, numpy, pillow, shapely
- GHS-POP: C:\Users\KitCat\Desktop\tesla semi\data\GHS_POP_E2030_GLOBE_R2023A_54009_100_V1_0.tif
- Chargers: C:\Users\KitCat\Desktop\v1.420\map-app\chargers.geojson
- BKG boundaries: C:\Users\KitCat\Desktop\v1.420\map-app\boundaries\

## RUN / TEST
Desktop server: `node serve-desktop.js` from `C:\Users\KitCat\Desktop`, port 8020.
App: http://127.0.0.1:8020/v1.420/index.html
Start the server if not running. You may not have browser access — if browser testing tools fail, just verify code correctness by reading it, checking the server starts, and confirming generated files exist. Do NOT block on browser testing.

## WORK ORDER
1. Study v1 pipeline scripts (tile geometry is critical)
2. Build + run tile pipeline → germany_pop.pmtiles + coverage_stats.json
3. Integrate coverage layer in map (custom WebGL, threshold rendering)
4. Build stats pane (hero number → chart → counts → memorable stat)
5. Wire up radius pills ↔ map threshold ↔ hero number sync
6. Test everything in browser — verify coverage layer, stats, region selection
7. Update CLAUDE.md with new state
8. Git commit all changes
9. Write summary to GOAL_SUMMARY.md
