# 3D biome check: plan

## What the game does (via the Cubiomes port; Mojang's source is not public)
Biome at (x,y,z) = nearest-neighbour lookup of 6 climate values in a table of parameter points
(temperature, humidity, continentalness, erosion, depth, weirdness). Only `depth` depends on y:
  depth = 1 - y/128 - 83/160 + terrain_offset(continentalness, erosion, ridges)   (y in blocks)
so each 4-block layer lowers depth by 1/32. Biomes are stored per 4x4x4 cell, world y = -64..319 = 96 layers.
Table facts (Mojang bug MC-262252 + the port): lush caves and dripstone caves live at depth [0.2, 0.9]
(lush: humidity >= 0.7; dripstone: continentalness >= 0.8), and those two ranges overlap (game behaviour undefined there).
Surface biomes are the depth ~0 entries, so the surface biome = biome at the layer where depth ~ 0.

## Experiment
Same rays as before (K=4, R=20000, spawn from estimateSpawn), but at each sample point compute the
climate once, then evaluate all 96 layers by varying depth. Two outputs per ray:
- surface: biome at the depth-0 layer (replaces the old y=63 shortcut)
- column: set of biomes present anywhere in y=-64..319 (first-hit distance per biome)
Rank by mean walk (1/flat hazard beyond 4000 blocks), same estimator as before.

## Failure modes and tests (written first)
| Failure mode | Test |
|---|---|
| Rebuilt depth layers differ from the game's own lookup | probe: reconstruction == getBiomeAt at every layer (>= 99.9% of cells) |
| Depth not monotone / wrong step | np depth strictly decreasing, ~312 units per layer |
| Wrong surface layer | surface depth within 1/64 of 0 unless clamped to world top/bottom |
| Cave rules misunderstood | lush/dripstone only at depth in [0.2, 0.9]; deep dark only at depth > 0.9 |
| Column missing layers | exactly 96 layers, y = -64..319 |
| Column not superset of surface | every surface hit is also a column hit, never later |
| Determinism, bad args, R=0 | same as raysim |
| Presence != reachable cave | stated limit, not testable |
