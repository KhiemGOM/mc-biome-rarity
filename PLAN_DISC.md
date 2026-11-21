# Capsule discovery model with the real voxel limit

## Exact estimand (no lattice)
World at the surface layer = piecewise-constant biome map on 4x4-block cells c = (qx, qz); cell c covers
blocks Q_c = [4qx, 4qx+3] x [4qz, 4qz+3] (block coordinates).  Walker path L(s) = P0 + s*u, 0 <= s <= R.
Discovery radius r >= 0 (r = 0 is the centerline model).
  rho_c = dist(P0, Q_c)
  if rho_c <= r :  D_c = rho_c                       (visible from spawn: straight distance)
  else          :  s_c = min{ s >= 0 : dist(L(s), Q_c) <= r },  D_c = s_c + r   (path + walk to the block)
D_b = min over cells of biome b of D_c.  Triangle inequality gives D_c >= rho_c, and D_c is continuous at rho_c = r.
{ s : dist(L(s), Q) <= r } is an interval (distance to a convex set is convex), so s_c is the first entry of the line
into the rounded rectangle Q (+) disc(r) = union of 2 rectangles and 4 corner discs: closed form, no sampling.
Estimator unchanged: M_hat = sum X / sum E over the window [4000, 20000].

## Hit-rate model (explains the ranking move)
For a stationary field of convex patches with intensity rho (per area) and mean projected width w,
the expected number of patches met per unit path length is rho*(w + 2r)   (Steiner / Cauchy).
So the hazard of first discovery is lambda_r = rho*(w + 2r) and
    M_0 / M_r = 1 + 2r / w        =>  w = 2r / (M_0/M_r - 1).
Biomes made of many narrow patches (small w) gain most from r.  Check: w from r=64 and r=128 must agree.

## What sparse sampling can and cannot do
Sub-sampling cells (stride k in qx and qz, nested) gives D^k >= D pointwise (min over a subset).
 (a) For ANY fixed sampling pattern, M_hat_k -> M_k almost surely at rate N^(-1/2) (iid seed clusters, bounded summands).
 (b) M_k != M in general; the gap does NOT shrink with more seeds or rays, only as k -> 1.
 (c) Therefore sparse sampling is only usable through the two-phase estimator
     M_hat = M_k(all) + [ M_1(calib) - M_k(calib) ]   (calib = exact on a random subset), consistent for the exact M.
 (d) Its variance is Var(u)/N + Var(v)/n_c with v = IF_1 - IF_k: the cheaper the sparse level is wrong, the more exact
     rays are needed.  Measured here as the paired bias curve M_k / M_1.
Decision rule: if the sparse bias is a few percent and rank-irrelevant, use two-phase; otherwise exact everywhere.

## Failure modes (each tested)
| failure | test |
|---|---|
| line entry into rounded rect wrong (corner vs edge) | compare to brute-force numeric root, all geometries |
| a cell inside the capsule is never enumerated | completeness vs brute-force box scan |
| a cell outside is enumerated (extra work only) | exact filter equality |
| r = 0 differs from "cells the line crosses" | r = 0 case |
| spawn cell / visible-from-spawn rule | rho rule tests |
| levels not nested / not monotone | per ray check |
| larger r later than smaller r | monotonicity |
| threads change output | 1 vs 2 threads |
| bad radii / args | CLI rejects |
| vertical / horizontal rays (division by zero) | angle sweep includes axes |

## Ground truth = block-level model (no cell abstraction in the definition)
Every block (i, j) has a biome; blocks are the unit squares [i-1/2, i+1/2] x [j-1/2, j+1/2]. The walker moves on the
continuous path L(s) and block (i, j) is discovered at the first s with dist(L(s), block) <= r (or at once, with D = dist,
if the spawn is already within r).  D_b = min over all blocks of biome b of  D_block.
The 4x4 cell enters only as a property of the MAP (the game assigns one biome per 4x4x4 quart), so the 16 blocks of a cell
share a biome, the union of those 16 blocks is exactly the cell square, and min over its blocks of D_block = D_cell.
That identity is tested (test_cell_model_equals_min_over_its_16_blocks), so the cell code computes the block model exactly.
Vertical: the surface block of each column is the depth-0 layer of the same climate sample; horizontal distance only.

## Convergence theorems (what is proved, what is not)
Let a ray give D (exact) and, for a sub-sample of cells S_k, D^k = min over S_k, with S_4 c S_2 c S_1 (nested).
T1 (monotone).  D^k >= D^(k/2) >= ... >= D pointwise (a min over a subset can only be larger).
T2 (consistency of any fixed sparse scheme for ITS OWN target).  Seeds are iid; per-seed sums (E_i, X_i) are bounded by
   4 and 4(R-R0).  So M_k(N) = sum X / sum E -> M_k = E[X]/E[E] a.s. with sqrt(N) normality (delta method).
T3 (sparse alone is NOT consistent for the exact M).  M_k - M_1 is a deterministic number that does not depend on N;
   it vanishes only as the sample set grows to every cell.  Sampling denser lowers it, more seeds never do.
T4 (two-phase IS consistent for the exact M).  Take calibration seeds = a uniformly random subset (a prefix of iid seeds) of
   size n_c.  M_hat = M_k(all N) + [ M_1(cal) - M_k(cal) ].
   M_k(all) -> M_k, M_k(cal) -> M_k, M_1(cal) -> M_1 as N, n_c -> infinity, hence M_hat -> M_1 = exact.
   Asymptotic variance (per-seed influence u for the sparse level, v = IF_1 - IF_k):
        Var(M_hat) = ( Var(u) + 2 Cov(u,v) ) / N + Var(v) / n_c.
   Var(v) is proportional to how often the sparse level changes a result, so the exact subsample must grow with the miss rate.
T5 (what is NOT proved).  Rate constants depend on the map's small-patch mass; they are measured, not assumed.  The CLT
   interval is asymptotic; it is cross-checked by cluster bootstrap and jackknife and by fold tests.
