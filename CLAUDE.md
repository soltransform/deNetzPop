# Claude Memory: Germany EV Charger Access

Read this first when starting a Claude Code session in this folder.

This project is part of a larger Tesla Supercharger / EV charging infrastructure project spread across several folders on the Desktop. The current user-facing goal is **not** to continue every historical branch. The current goal is:

```text
Build a Germany-focused EV charging and population-access dashboard for a Tesla Gigafactory Berlin-Brandenburg dual-study application.
```

The detailed memory is in:

```text
C:\Users\KitCat\Desktop\v1.420\CLAUDE_PROJECT_MEMORY.md
```

The previous Codex handoff is in:

```text
C:\Users\KitCat\Desktop\v1.420\CLAUDE_HANDOFF.md
```

## Current Strategic Direction

Use the archived v4.20 Germany dashboard as the visual/product foundation, but replace its H3 population/access layer with a pipeline closer to the original v1/global app:

```text
GHS-POP 100m Mollweide source cells
-> Germany clip / charger-distance analysis
-> Web Mercator display tiles / PMTiles
-> MapLibre dashboard
```

Reason: the user wants to preserve the actual 100m GHS-POP ground-truth cells rather than resampling population into H3 hexagons.

## Most Important Folders

Current scratch/prototype:

```text
C:\Users\KitCat\Desktop\v1.420
```

Original/root global 100m Tesla access app:

```text
C:\Users\KitCat\Desktop\tesla semi
```

Archived Germany H3 dashboard, visually strongest prototype:

```text
C:\Users\KitCat\Desktop\tesla semi\archive\version 4.20-h3-germany-prototype
```

Desktop PMTiles experiment that may already contain useful 100m/PMTiles work:

```text
C:\Users\KitCat\Desktop\v2
```

Repo V2 multi-network globe rewrite:

```text
C:\Users\KitCat\Desktop\tesla semi\v2
```

Repo V3 Mollweide/globe population experiment:

```text
C:\Users\KitCat\Desktop\tesla semi\v3
```

## Immediate Advice

Do not blindly continue polishing `v1.420`. First inspect/reuse:

1. v4.20 for visual/dashboard design and BNetzA parsing.
2. root `tesla semi` for the correct 100m GHS-POP Mollweide -> WebMercator tile pipeline.
3. Desktop `v2` for existing PMTiles files.
4. `v1.420` for Bundesland/Kreis dropdown and clickable-region experiments.

Keep changes in a new final working folder once the data architecture is chosen.

