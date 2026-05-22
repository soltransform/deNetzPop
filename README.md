# v1.420 Germany Charger Dashboard Prototype

This folder is the current clean prototype checkpoint for the Germany-focused charger/population dashboard.

For the full continuation handoff, read:

```text
C:\Users\KitCat\Desktop\v1.420\CLAUDE_HANDOFF.md
```

That file supersedes older notes in this folder where they disagree with the current state.

## Run

From PowerShell:

```powershell
cd "C:\Users\KitCat\Desktop"
node serve-desktop.js
```

Open:

```text
http://127.0.0.1:8020/v1.420/index.html
```

## Current Page State

- Left side: embedded `map.html`, copied/adapted from the v1 map work.
- Right side: region selectors and the Tesla Supercharger cumulative population graph.
- Region dropdowns: Bundesland, Kreis, Gemeinde, loaded from `data/regions.json`.
- Selecting a region sends bounds to the map iframe and zooms the map.
- The graph is controlled by the distance slider and shows cumulative German population within distance of a Tesla Supercharger.

## Important Reset

The BNetzA/network provider dashboard was removed from the page because the intermediate summary was misleading. In particular, the v2 BNetzA JSON intentionally removed Tesla rows, while the original BNetzA CSV does include Tesla.

The next data step should use the original BNetzA CSV as the source of truth for Germany analytics, or rebuild a clearer processed dataset from it.
