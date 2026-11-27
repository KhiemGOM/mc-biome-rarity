# Handoff to Claude Code (historical, see HANDOVER.md)

> **STATUS 2026-11-27: this file is historical.** It describes the 1.21.4 era (window [4000, 20000], 4 rays per seed, radii 0/64/128, surface layer only). All of that is superseded by the 26.3 certwalk work. The current state, decisions and next steps are in [HANDOVER.md](HANDOVER.md). The style rules and layout notes below are still valid.


Owner: the channel owner. Style rules: never use em-dashes (only "-"); maths in LaTeX; code work order is
plan -> tests first (plan lists failure modes, tests cover them) -> implementation; code edits need anchor context; be direct.

## Layout
- C simulators (need Cubiomes, pinned commit in build.sh): raysim.c (y=63 rays), colsim.c (3D column / surface-layer rays,
  `--nested L` records first hits for steps h, 2h, 4h, ...), discsim.c (rotated 16-block lattice capsule, approximate),
  discexact.c (EXACT capsule model on 4x4 cells), mapdump.c.
- Python: rarity.py (estimators), certify.py (two-phase estimator, delta SE, bootstrap, planner, fold test, hazard bins),
  cert_pipeline.py (plan/run/report for the certified centerline run), verify_cert.py (independent re-derivation, no shared code),
  disc_analyze.py, exact_analyze.py, exact_plan.py, stepbias.py, richardson.py, flat.py, size.py, ...
- tests/: ~100 tests (C CLIs, geometry vs brute force, estimators on synthetic worlds with known truth).
- Video scripts (scenes.py, make_video.py, ...) are old; the video still shows an outdated pale-garden number (~265k, truth ~114k).

## Definitions
- Window R0 = 4000, cap R = 20000. Per ray D = first-hit distance (inf if none). E = 1{R0<=D<=R}, X = (min(D,R)-R0) 1{D>=R0}.
  M_hat = sum X / sum E over rays; SE by seed clusters (4 rays per seed). Seed i = splitmix64(seed0 + i). Spawn = Cubiomes estimateSpawn.
- Surface biome = biome at the depth-0 layer of the 1.18+ multi-noise climate sample (not a fixed y). Lookup is hint-free
  (hinted lookup made results path dependent on exact ties).
- Exact capsule model (PLAN_DISC.md): cells tile the plane, cell (qx,qz) = [4q-0.5, 4q+3.5]^2 in block coordinates.
  D_c = dist(spawn, cell) if that is <= r else (first path length s with dist(path(s), cell) <= r) + r. D_b = min over cells.
  Equals the pure block-level model because the 16 blocks of a cell share a biome (tested).

## Results so far (all 1.21.4, surface layer, SUPERSEDED by 26.3 results, kept for history)
Centerline, CERTIFIED (out/cert/cert.json is committed; to regenerate it run cert_pipeline.py, ~40 min on 2 cores):
mean walk +- 95%: mushroom_fields 144,479 (1.85%), pale_garden 113,877 (1.93%), windswept_gravelly_hills 94,501 (1.84%),
stony_peaks 83,795 (1.70%), ice_spikes 75,689 (1.56%), eroded_badlands 70,390 (1.44%). 38,100 seeds x 4 rays at step 8,
plus step 1 on 3,300 seeds (two-phase). Richardson alone was 2% off for pale garden (bias not linear in step). verify_cert.py: 25/25 checks.

Capsule (exploratory, 4,000 seeds, rotated 16-block lattice, out/cert/disc_report.txt): ranking correlation with centerline
Spearman 0.987 (r=64), 0.969 (r=128). Effective patch width w = 2r/(M_0/M_r - 1) agrees across radii within ~13% (Steiner hit-rate model).

Exact capsule (600 seeds, 2,400 rays, out/exact/exact_table.csv, noise about +-8% on rare biomes):
- Sparse sampling is BIASED, and more seeds do not fix it. Bias of the 16-block lattice (stride 4) vs exact: centerline median +21%
  (pale garden +43%), r=64 median +4.1% (pale garden +9%), r=128 median +3.5%. Stride 2 (8-block): +4.4% / +1.2% / +1.0%.
- Exact ranking r=64 top 5: mushroom_fields, pale_garden, eroded_badlands, windswept_gravelly_hills, stony_peaks.
  r=128 top 5: mushroom_fields, eroded_badlands, windswept_gravelly_hills, ice_spikes, pale_garden (pale garden falls). Not yet resolved statistically.
- Exact-everywhere cost to reach +-2% (pilot estimate): about 2,000-4,300 seeds x 4 rays per radius for the rare biomes
  (about 1.1 s CPU per ray with radii 0,64,128 together). Two-phase (stride 4 everywhere + exact subset) saves 2.5-4.7x for r>0.
  `python3 exact_plan.py 12 0.02` prints the table.

## Theory status (PLAN_DISC.md T1-T5)
T1 monotone nested subsets; T2 any fixed sparse scheme converges to ITS OWN target at N^-1/2; T3 so sparse alone is NOT consistent for the exact value;
T4 two-phase M_k(all) + [M_1(cal) - M_k(cal)] IS consistent for the exact value with variance (Var(u)+2Cov(u,v))/N + Var(v)/n_c;
T5 constants are measured not assumed. certify.build_terms_stride implements T4 (tested on synthetic worlds).

## Next steps (OLD, done or replaced, see HANDOVER.md for the current list)
0. CERTIFIED WALK FROM SPAWN (supersedes the certrun window run below): `python3 certwalk.py plan|run|report|verify`. Headline E[D] from spawn, no window, plus spawn bias vs a uniform random start on the same seeds. THEORY.md sections 0 (constants and assumption audit) and 8. Report as estimate +- epsilon with ties where ranges overlap.
0b. (OLD) CERTIFIED EXACT RUN (supersedes 1-2 below): THEORY.md section 6, certrun.py. The plan is already fixed and committed
   (out/certrun/plan.json: betting confidence sequences, alpha split toward 6 rare biomes x 3 radii, per radius seed counts
   n* = 12,635 / 6,427 / 5,530 for r = 0 / 64 / 128 from index 9,000,000,000, +-5% target, K = 282, alpha = 0.05;
   expected 7.2 CPU hours, stops by itself when every target is met, cap 2 n*). THEORY.md section 7.
   On the many-thread PC: `./build.sh && python3 certrun.py run --threads <T>` (sequential and resumable, chunks of 500), then
   `python3 certrun.py report` and `python3 certrun.py verify --samples 5`. Commit out/certrun/certificate.json and report.md.
   Do not edit plan.json (the hash check refuses) and do not reuse its seed ranges (ledger.json).
1. Production exact run (the speed-up the owner wants: run on his PC with many threads):
   `./discexact --seeds 1000 --rays 4 --radii 0,64,128 --seed0 <S> --threads <T> --out out/exact/ex_<S>.csv` in chunks of 100-1000 seeds
   with seed0 offsets so chunks never overlap; fresh seeds (not 7,000,000,000..+600 which the pilot used; use e.g. 9,000,000,000).
2. Certify with certify.py: either exact everywhere (use stats + combo + certificate on level-1 rows) or two-phase via build_terms_stride
   (sparse level 4 on all seeds, level 1 on a prefix). Fix N once from the pilot (no optional stopping), then verify with an independent
   recomputation like verify_cert.py (jackknife + plain loops) and the 8-fold chi-square check.
3. Decide radii (64 and 128 are placeholders); report ranking with CIs and pairwise rank-swap significance.
4. Not covered: estimateSpawn vs real spawn, other versions, hazard beyond 20000 (flat to 100k only for 12 biomes, centerline), vertical visibility/line of sight.
5. Optional: fix the video's outdated pale-garden figure.
