# mc-biome-rarity

Which biome in Minecraft Java 26.3 is the rarest, measured as the expected walk from spawn to find it, with a certified error bound on every number. Monte Carlo over world seeds using the real biome generator (xpple/cubiomes, MC_26_3, plus our own bit-exact float port of the 26.3 climate and spawn search).

**Start with [HANDOVER.md](HANDOVER.md).** It has the full current state, decisions, how to build and run, and the next steps. The maths is in [THEORY.md](THEORY.md).

## Headline (26.3, caves included, spawn included, failure chance at most 1 in 500,000)
Sight radius 0, 215,000 seeds: mushroom_fields 149,522 +- 3,280 blocks, then windswept_gravelly_hills 94,893, stony_peaks 83,873, ice_spikes 74,603, eroded_badlands 70,084, pale_garden 62,471, mangrove_swamp 58,464. Ranks 1 to 7 are separated. Mushroom fields is also #1 alone at sight radius 128 and 512 (10,000 seeds each). Full tables: `out/certwalk263_r0/report.md`, `out/certwalk263_r128_512/report.md`, and the `order.md` next to each.

Everything under `out/certwalk`, `out/certwalk_cave_*`, `out/certrun`, `out/cert` and `out/exact` is from Minecraft 1.21.4 worldgen and is superseded (kept for history and for the video's "I got it wrong" beat).

## Setup
    ./build.sh ~/cubiomes-xp        # clones and pins xpple/cubiomes 304940b, builds all simulators
    pip install -r requirements.txt
    CUBIOMES=~/cubiomes-xp python3 -m pytest -q
Run everything from the repo root (scripts use relative paths such as out/names.csv). Linux or WSL.
