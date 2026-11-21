# Biome rarity Monte Carlo: plan

## Estimand (what the numbers mean)
For a random seed and a random direction, march a straight ray from the
(estimated) spawn in steps of `h` blocks out to cap `R`. `D_b` is the first
distance at which biome `b` is sampled (`inf` if never, censored at `R`).
Reported per biome: S(r)=P(D>r), median D, restricted mean E[min(D,R)],
hazard h(r), far-field mean free path l = c(1-p)/p from chords beyond r0.

## Pieces
1. `raysim` (C, links libcubiomes): seeds x rays -> sparse first-hit CSV and
   far-field chord CSV. One pass records all biomes.
2. `rarity.py`: estimators (empirical survival == Kaplan-Meier under a fixed
   cap), restricted mean, cluster bootstrap over seeds, DKW/Hoeffding sizes,
   variance components and K*, hazard, far-field l.
3. `render_*.py`: real-data frames for the video.

## Conventions (the tests pin these down)
- Sample point: x = sx + floor(r cos t + 0.5), z = sz + floor(r sin t + 0.5),
  biome = getBiomeAt(g, 4, x>>2, 15, z>>2)  (y = 63, quart coordinates).
- Rays of one seed: t_k = 2 pi (k + u)/K, u uniform per seed.
- Seeds: seed_i = splitmix64(seed0 + i), printed as signed int64.
- Spawn: estimateSpawn (fast approximation of the 1.18+ climate search),
  not the grass-based getSpawn.
- A biome seen at r=0 has D=0. Unseen biomes are simply absent (censored).

## Failure modes and the test that covers each
| Failure mode | Test |
|---|---|
| Step too coarse skips thin biomes (river, beach) | refinement property: h=4 first-hit <= h=16 first-hit for every (seed, ray, biome); report how often it differs |
| Off-by-one at r=0 / spawn biome | every ray has exactly one biome at dist 0, shared by all rays of a seed |
| Censored treated as R | R=0 run records only spawn biome; unseen biome absent, not R |
| Wrong coordinate scale / rounding | independent Python+ctypes oracle reproduces the CSV exactly |
| Non-determinism / seed handling (uint64, negative) | same args same bytes; different seed0 differs; seeds round-trip |
| Bad arguments | rays=0, step<=0, rmax<0, unknown version -> nonzero exit |
| Rays not evenly spread | consecutive angle gaps = 2pi/K |
| Estimator bugs | synthetic exponential with known restricted mean; KM == empirical; coverage of bootstrap CI |
| Variance split wrong (seeds vs rays) | synthetic two-level data recovers known sigma_seed^2, sigma_ray^2 |
| Far-field l biased | synthetic alternating-renewal line with known mean gap |
| Over-fixating on edges | happy-path tests first in each file |

## Known limitations (stated in the video)
- y = 63 only: no peaks/caves; surface biomes at sea level.
- Fixed version (1.21). Biome IDs and generator change between versions.
- Step h and cap R are bias, not Monte Carlo error.
- estimateSpawn approximates the true spawn.
