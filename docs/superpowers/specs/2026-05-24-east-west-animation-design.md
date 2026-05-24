# East/West Divide + Growth Time Animation — Design Spec

## Overview

Two features for v1.420 Germany EV Charger Dashboard:
1. East vs West Germany comparison in Regions tab
2. Time-lapse animation of charger deployment on map, synced with growth chart + 2026 x-axis fix

## Feature 1: East vs West Divide

### Data

Split `regions.states[]` client-side:
- **East (ex-DDR)**: state IDs 11 (Berlin), 12 (Brandenburg), 13 (Mecklenburg-Vorpommern), 14 (Sachsen), 15 (Sachsen-Anhalt), 16 (Thüringen)
- **West**: all other state IDs (01–10)

No Python pipeline changes. Computed from existing analytics.json at render time.

### UI

New card row in Regions tab, inserted ABOVE the KPI table. Only visible at national level (stateFilter === null).

Two cards side-by-side: "East (ex-DDR)" | "West"

Each card shows (population-weighted averages):
- Gap score (weighted avg)
- Coverage % at 5km
- Chargers per 100k
- HPC+ %

Small delta indicator on East card showing ratio vs West (e.g., "1.8× gap").

### Behavior

- Visible only when no state selected
- When state selected → cards hidden, KPI table shows districts (existing behavior unchanged)

## Feature 2: Growth Time Animation

### 2a. 2026 X-Axis Fix

**Problem**: Growth chart plots 2026 at full year distance from 2025, but BNetzA data only covers Jan–April 22, 2026 (~31% of year). Makes growth look flat.

**Fix**: Change x-scale from integer years to fractional:
- All years 2010–2025: plotted at their integer position (unchanged)
- 2026: plotted at position 2025.31 (112/365)
- Add "(YTD)" label beneath 2026 tick
- `xS()` function: `pad.l + ((year - minYear) / (maxYear - minYear)) * pw` — maxYear becomes 2025.31 instead of 2026

### 2b. Map Time Animation

**Play button**: Small frosted-glass play/pause control, bottom-left of map (inside iframe). Shows current year when active.

**Mechanics**:
- Play: auto-advances from 2010 to 2026, ~800ms per year step
- Charger dots filtered by `start_year <= activeYear` using MapLibre `setFilter`
- State/district bubbles update charge_point counts for the active year
- Year label displays prominently on map during animation

**Sync with growth chart**:
- Map → parent: `postMessage({ type: "animation-year", year })` on each step
- Parent highlights that year on growth chart (reuses existing hover mechanism: sets `_growthHoverYear` and redraws)
- Growth chart hover → map: `postMessage({ type: "set-year", year })` to iframe
- When animation stops (pause or end): `postMessage({ type: "animation-year", year: null })` → map shows all dots, chart clears highlight

**Data requirement**: Each charger feature in `chargers.geojson` already has `start_date` (format: `dd.MM.yyyy`). Parse to extract year. For bubble counts, precompute year breakdown per state/district in analytics.json.

### 2c. Analytics Pipeline Addition

Add to `build_analytics.py` output → `analytics.json`:

```json
{
  "growth_by_region": {
    "states": {
      "08": { "2010": 5, "2011": 12, ... "2026": 9278 },
      ...
    },
    "districts": {
      "08111": { "2010": 2, "2011": 5, ... "2026": 450 },
      ...
    }
  }
}
```

Cumulative site count per region per year. Used by map to update bubble counts during animation.

## File Changes

| File | Changes |
|------|---------|
| `map-app/tab-regions.js` | Add East/West cards section |
| `map-app/tab-market.js` | Fix 2026 x-axis positioning, add year sync messaging |
| `map-app/index.html` | Add play button UI, animation logic, postMessage handlers, year filter |
| `scripts/build_analytics.py` | Add `growth_by_region` to output |
| `index.html` | Add postMessage relay between growth chart and iframe |

## Agent Assignments

| Agent | Scope |
|-------|-------|
| Agent 1 | `scripts/build_analytics.py` — add growth_by_region |
| Agent 2 | `map-app/tab-regions.js` — East/West cards |
| Agent 3 | `map-app/tab-market.js` — 2026 fix + year sync outbound messaging |
| Agent 4 | `map-app/index.html` + `index.html` — play button, animation, postMessage relay |

Agent 1 runs first (pipeline). Agents 2–4 in parallel after.
