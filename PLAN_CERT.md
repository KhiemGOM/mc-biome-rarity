# Certified run: plan

Goal: report mean walk M_b for the rare biomes with a stated total error epsilon, where
epsilon is computed by code, not argued.

## Estimand (exact, no h -> 0 limit)
M_b = sum X / sum E over rays, window [R0, R] = [4000, 20000], first hit D on the
block grid (step h = 1) along a straight ray from estimateSpawn, biome = depth-0 surface layer.
Biomes change only on 4-block cells, so h = 1 visits every cell a ray crosses (apart from
sub-block corner clips). Everything below is relative to this h = 1 definition.

## Estimator (two-phase, bias measured not assumed)
- Main sample: N seeds x 4 rays at h = 8 (nested 8,16,32 in one pass). Richardson r = 2 M_8 - M_16.
- Calibration subsample: first n_c of the same seeds, at h = 1 (nested 1,2,4,8,16,32).
- Estimate: M_hat = r(all) + [ M_1(calib) - r(calib) ].  Asymptotically unbiased for the h = 1 value.
- Variance: seed-cluster influence function z_i, Var = sum z_i^2 (n/(n-1)); cross-checked by
  cluster bootstrap; certificate uses the larger of the two.
- epsilon_b = 1.96 * SE / M_hat (relative 95% half-width). Certified if epsilon_b <= target.

## Sample size without optional stopping
Pilot on separate seeds fixes (N, n_c). Production uses fresh seeds, fixed N, one look.
Pilot data is never reused in the final estimate.

## Independent checks inside the certificate
1. Fold check: split production seeds into 8 folds, chi-square test of fold estimates vs reported SE.
2. Bias curve: M_h / M_1 for h = 2..32 on the calibration set (shows what the raw grid would have said).
3. Flat-hazard check: hazard in 4 equal bins of [R0, R].
4. verify_cert.py recomputes E, X, M_hat from the raw CSV with separate pure-python code.

## Failure modes (each has a test)
| failure | guard |
|---|---|
| nested level m differs from a separate run at step h*2^m | test equality of row sets |
| nested levels not monotone (D_h > D_2h) | test per ray |
| nested without --no-column | refuse with error |
| chunked runs differ from one run | test seed0 offsets concatenate |
| thread count changes results | test 1 vs 2 threads |
| zero events for a biome | uncertified, no NaN |
| calibration seeds not a subset of main seeds | raise |
| duplicate or missing seeds | raise on count mismatch |
| CI under-covers | coverage test on synthetic data with known truth |
| delta SE disagrees with bootstrap | test within 10% |
| variance of combined estimator wrong | test two-phase SE vs bootstrap and vs replication SD |
| planner under-sizes N | test projected half-width on fresh synthetic draw |
| epsilon relative to wrong center | test uses M_hat, not raw |
| happy path: plain ratio estimator recovers 1/lambda | test |

## Still not covered (stated in the report, not hidden)
estimateSpawn vs real spawn, other versions, hazard beyond 20000 (checked to 100k earlier), sub-block corner clips.
