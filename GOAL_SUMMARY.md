# GOAL_SUMMARY: Population Tiles + Stats Pane for v1.420

## Completed: 2026-05-24

All 9 steps from GOAL_INSTRUCTIONS.md executed.

---

## Part 1: Tile Pipeline

**Script**: `scripts/build_population_tiles.py` (~530 lines, 4 phases)

1. **TIFF extraction**: Read 6.2 GB GHS-POP (Mollweide ESRI:54009), filter to Germany bbox (5.5-15.5 lon, 47-55.5 lat) via 4096-row strips. Yields ~10M cells, ~5M populated.
2. **Distance computation**: scipy.spatial.cKDTree per charger tier (AC: 45k, DC: 12k, Ultra: 6k). Equirectangular projection at mean latitude (51.25) for approximate meters.
3. **Coverage stats**: shapely STRtree assigns cells to 432 districts + 16 states. Cumulative population buckets at 0-50 km for any/dc/ultra tiers. Germany total computed from assigned cells only (82.8M, not full bbox 115.6M).
4. **Tile pyramid**: Streaming z12 row-by-row (Mollweide cell corners -> WebMercator pixel footprints, vectorized with np.add.at/np.minimum.at), then z11->z5 bottom-up with population-weighted averaging for distance channels.

**Output**:
- `map-app/germany_pop.pmtiles` — 467.5 MB, 21,095 tiles (z5:4, z6:9, z7:29, z8:94, z9:310, z10:1,084, z11:4,041, z12:15,524)
- `map-app/coverage_stats.json` — 939 KB, per-state and per-district coverage data

**Key numbers**: Germany 82.8M pop, 98.2% within 5 km of any charger, 95% coverage at 4 km.

## Part 2: Map Integration

**Custom WebGL layer** in `map-app/index.html`: `CoveragePMTilesLayer` class (~180 lines).

- Fragment shader reads RGBA tile pixels, compares distance channel to threshold uniform
- Teal (#2DD4BF) for covered, amber (#F59E0B) for uncovered, alpha from population density
- Tier uniform selects channel: 0=min(G,B,A) "any", 1=G "AC", 2=B "DC fast", 3=A "ultra"
- Radius changes update shader uniform instantly (no tile re-fetch)
- PMTiles loaded via dynamic `import()` from jsdelivr CDN
- Layer added before `state-bubble-circle` (below bubbles, above basemap)
- PostMessage handlers: `set-coverage-radius`, `set-coverage-tier`, `toggle-coverage`

**Server fix**: Added HTTP byte-range request support to `serve-desktop.js` (PMTiles requires it).

## Part 3: Stats Pane

**Apple-keynote-style** right panel in `index.html` with 4 sections:

### Section 1: Hero Number
- Large 52px percentage (e.g. "98.2%")
- Subtitle: "of Germans live within 5 km of a charger"
- 4 radius pills: [1 km] [5 km] [10 km] [25 km] — segmented control
- 4 tier pills: [Any] [AC] [DC Fast] [Ultra] — selects charger type
- On region selection: shows comparison with national average + colored arrow

### Section 2: Cumulative Chart
- Canvas 2D, 3 smooth curves (Any charcoal, DC Fast teal, Ultra amber)
- Gradient fills underneath curves
- Hover tooltip showing km + percentages for all 3 tiers
- Selected radius shown as vertical dashed line
- Region mode: national curves faded/dashed, regional solid
- Auto-computed insight: "95% coverage at X km (any charger)"

### Section 3: Charger Counts
- Colored dots matching map colors: AC (blue), Fast (green), HPC (amber), Ultra (red)
- Formatted counts in K notation
- Sites + operators count below
- Updates on region selection

### Section 4: Memorable Stat
- "Farthest point from any charger: X km"
- Updates per region

### Styling
- Frosted glass background (rgba + backdrop-filter blur)
- Staggered fade-in animations (300ms ease-out)
- System font stack, tabular-nums
- No divider lines — generous whitespace
- Responsive: stacks vertically on narrow screens

## Data Flow

```
Radius pill click -> postMessage(set-coverage-radius) -> map iframe shader uniform
Tier pill click   -> postMessage(set-coverage-tier)   -> map iframe shader uniform
                  -> updateStats() -> hero number recalculated from coverage_stats.json
State dropdown    -> postMessage(set-charger-filter)   -> map charger filtering
                  -> postMessage(select-region)        -> map boundary highlighting
                  -> updateStats()                     -> all 4 stats sections refresh
Coverage toggle   -> postMessage(toggle-coverage)      -> map layer on/off
```

## Files Modified

| File | Change |
|------|--------|
| `scripts/build_population_tiles.py` | New — complete tile pipeline |
| `map-app/index.html` | Added CoveragePMTilesLayer WebGL class + postMessage handlers |
| `index.html` | Added stats pane (hero, chart, counts, memorable stat, radius/tier pills, coverage toggle) |
| `serve-desktop.js` | Added HTTP range request support for PMTiles |
| `CLAUDE.md` | Updated with new state |

## Files Generated (gitignored)

| File | Size |
|------|------|
| `map-app/germany_pop.pmtiles` | 467.5 MB |
| `map-app/coverage_stats.json` | 939 KB |

## Constraints Respected

- 100m GHS-POP cells (no H3)
- chargers.geojson as source (not v2 ingest_bnetza.py)
- No zoom-on-select
- Grey boundaries only (no red)
- Coverage layer teal/amber (not charger dot colors)
- No existing UI elements removed
- Incremental additions only
