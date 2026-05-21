# Project Notes

## Purpose

This project is meant to support an application for a dual-study logistics/data science path at Tesla Gigafactory Berlin-Brandenburg. The goal is not to build a polished consumer product. The goal is to show practical data handling, geospatial thinking, and a useful analysis interface around German charging infrastructure and population coverage.

## Current Direction

The project direction has narrowed to a Germany-focused dashboard:

- use official BNetzA charger data for legitimacy;
- combine charger infrastructure with population coverage analysis;
- keep the interface plain and data-oriented;
- eventually support Bundesland, Kreis, and Gemeinde drilldown;
- use the 100m population grid for final analysis work, not H3.

## What Exists In v1.420

- `index.html`
  - two-column layout;
  - map iframe on the left;
  - graph and controls on the right;
  - region dropdowns above the graph.
- `map.html`
  - v1 map embedded as the left pane;
  - listens for `fit-bounds` messages from `index.html`;
  - listens for `set-radius` messages from the graph slider.
- `data/regions.json`
  - generated region metadata for German Bundesländer, Kreise, and Gemeinden;
  - used for dropdowns and map zoom bounds.
- `data/bnetza_charger_summary.json`
  - generated intermediate file;
  - currently unused by the page;
  - should be treated as suspect until rebuilt from the original CSV with clear semantics.

## Data Findings So Far

Original BNetzA CSV:

```text
C:\Users\KitCat\Desktop\tesla semi\data\Ladesaeulenregister_BNetzA_2026-04-22.csv
```

The CSV has:

- 109,646 rows;
- 47 columns;
- 109,606 rows with status `In Betrieb`;
- 40 rows with status `In Wartung`;
- 80,876 `Normalladeeinrichtung` rows;
- 28,770 `Schnellladeeinrichtung` rows;
- 197,527 total `Anzahl Ladepunkte`;
- coordinates for every row;
- up to 6 connector slots per charging installation.

Important columns:

- `Ladeeinrichtungs-ID`
- `Betreiber`
- `Anzeigename (Karte)`
- `Status`
- `Art der Ladeeinrichtung`
- `Anzahl Ladepunkte`
- `Nennleistung Ladeeinrichtung [kW]`
- `Inbetriebnahmedatum`
- street/address fields
- `Ort`
- `Kreis/kreisfreie Stadt`
- `Bundesland`
- `Breitengrad`
- `Längengrad`
- parking information
- payment systems
- opening hours
- connector type, connector power, EVSE-ID, public key for slots 1-6

## Tesla/BNetzA Issue

The original BNetzA CSV includes Tesla:

```text
Tesla Germany GmbH: 3,657 rows / 3,657 Ladepunkte
Tesla Manufacturing Brandenburg SE: 567 rows / 567 Ladepunkte
Total Tesla-like BNetzA rows: 4,225
```

But v2's BNetzA ingest script intentionally removes Tesla:

```text
C:\Users\KitCat\Desktop\tesla semi\v2\scripts\ingest_bnetza.py
```

Reason in the script: supercharge.info is treated as the global Tesla source of truth, so Tesla rows are dropped from BNetzA to avoid duplicates.

That is why Tesla disappeared from the first v1.420 provider table attempt. The page-level dashboard was removed until the data model is rebuilt correctly.

## Recommended Next Step

Build a new Germany charger analysis dataset directly from the original BNetzA CSV, preserving more fields than v2 currently keeps.

Suggested output fields:

- id
- operator raw
- operator normalized
- status
- charger type
- number of charge points
- total power kW
- opening date
- full address
- Bundesland
- Kreis
- Gemeinde or Ort
- lat/lon
- parking info
- payment systems
- opening hours
- connector list with type, power, EVSE-ID, and public key presence

Then decide explicitly how to handle Tesla:

1. BNetzA official Tesla rows only.
2. supercharge.info Tesla rows only.
3. both, shown as separate sources.
4. merged/deduplicated Tesla, with documented rules.

Do not silently mix these sources in a dashboard table.

