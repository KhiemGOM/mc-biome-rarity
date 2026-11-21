# mc-biome-rarity

Quantifying "rarest biome" in Minecraft 1.21 with Monte Carlo over world seeds, using Cubiomes for the real biome generator.

Metric: mean walk M = 1 / (far-field discovery hazard), estimated on the window [4000, 20000] blocks from spawn
as M_hat = sum X / sum E, with seed-cluster standard errors. Two discovery models:
1. centerline: first block biome met along a straight ray from spawn (`raysim`, `colsim`)
2. capsule: walker with discovery radius r sweeping a rectangle plus two semicircles (`discsim` approximate, `discexact` exact)

Start with HANDOFF.md (state, results, exact commands, what is left). Theory is in PLAN*.md.

## Setup
    ./build.sh ~/cubiomes          # clones + pins Cubiomes, builds all simulators
    pip install -r requirements.txt
    CUBIOMES=~/cubiomes python3 -m pytest -q     # ~100 tests, 1-3 min
Run everything from the repo root (scripts use relative paths such as out/names.csv).
