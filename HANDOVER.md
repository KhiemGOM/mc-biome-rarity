# HANDOVER: mc-biome-rarity (written 2026-11-27)

For a fresh Claude Code session on the owner's PC (`D:\Coding\Minecraft\mc-biome-rarity`) with no other context. Read this file first, then THEORY.md sections 0 and 8 when you need the maths. Written from the repo and the cloud project folder. Anything I could not check from the cloud is marked **[unverified]**.

## 1. Goal and mission
- Project: find the rarest biome in Minecraft Java **26.3** with a Monte Carlo over world seeds, and prove the numbers are right. The owner is making a YouTube video from it.
- Video headline: "I found the RAREST biome in Minecraft... MATHEMATICALLY".
- Measure of rarity: expected walk length E[D] from spawn to the first sight of the biome, along a straight ray in a random direction, spawn included, no window and no cutoff.
- Mission: the final numbers and the ranking must be right. Every number is reported as **estimate +- epsilon** with non-overlapping ranges where the ranking is certain, and "tied" where it cannot be separated. The failure probability is tiny (1e-6 per sequence, 2e-6 for order statements) and is stated once in plain words. Avoid "95%" framing.
- Every claim is tagged proven, assumed or empirical (tags in THEORY.md: [P], [A], [E], [C]). The maths model is kept separate from the code, and the code is argued to compute the model. Never present an empirical claim as proven.

## 2. Current result (26.3, done)
All use all 96 layers of the column (y -64 to 319, cave biomes included), the tie sandwich (Lemma 30), failure chance 1e-6.
- Radius 0, 215,000 spawn-arm seeds and 53,750 uniform-start seeds. Ranks 1 to 7 separated: mushroom_fields 149,522 +- 3,280, windswept_gravelly_hills 94,893, stony_peaks 83,873, ice_spikes 74,603, eroded_badlands 70,084, pale_garden 62,471, mangrove_swamp 58,464. Rank 8 to 10 is a three-way tie (wooded_badlands, jagged_peaks, frozen_peaks).
- Radius 128 (8 chunks, 10,000 seeds) and 512 (32 chunks, 10,000 seeds), spawn arm only: mushroom_fields is #1 alone at both (73,730 +- 6,048 at 128; 31,630 +- 2,535 at 512). Below it the rankings are mostly ties because the precision target was +-12%.
- Spawn effect: spawn is not closer to rare biomes (spawn bias not separable from 0 for the rare ones; only plains and forest are significantly closer from spawn). Measured as the likelihood ratio rho_b(x) = P(D<=x | spawn) / P(D<=x | random start), area cancels (THEORY 8.11).
- Pale garden fell from #2 on 1.21.4 (about 114k) to #6 on 26.3 (62,471), because 1.21.5 enlarged it. This is a video beat ("I got it wrong twice").
- Patch width and density per biome from the certified walks: `out/patchsize263/patchsize.md` (interval arithmetic, no sampling). 55 of 56 biomes agree across radius pairs, stony_peaks drifts.

## 3. Decisions and standing preferences (owner)
- **Version:** 26.3 (newest). All 1.21.4 results are superseded and live only as history and a video beat.
- **Full column, always:** sampling covers y -64 to 319, caves included. Dropping caves was a regression the owner rejected. A cave biome counts if it is anywhere in the column (assumption, the owner has not explicitly confirmed it). Never silently drop scope from earlier runs.
- **Radii:** r = 0 (headline, least arbitrary), 128 blocks = 8 chunks ("a human would spot it"), 512 blocks = 32 chunks ("pro hunter or cheat client").
- **J = 1 ray per seed** (rays within a seed are positively correlated, so more seeds beat more rays).
- **Headline metric:** full expected walk from spawn, spawn included. No arbitrary cutoffs (the old 4,000 to 20,000 window is retired). Tail beyond the cap is labelled as an assumption, with the lower end of each range needing none.
- **Spawn effect metric:** the likelihood ratio above. The owner rejected "percent of walk" bias because it is unfair to short walks.
- **Plan everything up front.** Choose the final precision and seed counts before the run (`--n-fixed`), no extend-after-looking rounds.
- **Raw data first:** heavy runs save complete raw per-ray data (all biomes, as far as walked). All analysis is in separate scripts over that raw data, so the heavy part never needs rerunning.
- **Git:** commit and push straight to `main`, no PRs. If a change is verified (tests pass, proof intact), just push, do not ask the owner first. Note: his PC has a commit hook that rejected a Co-Authored-By line from an Anthropic account, so check before adding trailers.
- **Style:** no em-dashes anywhere (use "-" or rephrase), no "--" in visible text. Maths in LaTeX. Work order: plan, tests first, implementation. Be direct.
- **Long runs go on his PC** (i9-13900HX, 32 threads in WSL, RTX 4060 8 GB, about 10x one cloud core in practice). A 10 hour run was rejected ("optimize first"), so keep runs short or ask. Convert cloud CPU-hours to PC wall time by dividing by about 10. The PC must stay awake during runs.

## 4. Working rules on the owner's PC
- Share progress: one line before each step (what, which files or folders) and one line after (including failures). While anything long runs, post a status at least every 2 minutes, even "still waiting for X". Never go silent.
- Command line only. Do not open pages, launch apps, or use mouse, keyboard or screen control without showing the plan and getting his yes first.
- minecraft.wiki blocks scripted downloads (Cloudflare 403). Do not bypass it. The owner saves those images by hand.
- Do not edit committed `plan.json` files (a hash check refuses) and do not reuse seed ranges (ledgers).
- Do not rewrite proofs or change results without telling him.

## 5. Repo layout
- `THEORY.md`: the maths model, estimators, proofs, assumption audit. Sections: 0 constants and 26.3 generator (0.1), 1-3 model and estimators, 4 code to model, 6-7 old windowed run, 8 the walk from spawn (certwalk; 8.9 all layers, 8.10 `--until`/extend, 8.11 spawn ratio), 9 paired order. Status note at the top.
- C simulators: `discexact.c` (exact capsule walk, the production sampler, `--layers all`, `--ties`), `raysim.c`, `colsim.c`, `discsim.c` (older), `mapdump.c`. Headers: `c263climate.h` (our bit-exact float port of the 26.3 climate and `NoiseSpawnFinder`), `c263data.h`, `c263cache.h`, `c263ties.h`, `c263world.h`, `fastclimate.h`.
- Python: `certwalk.py` (plan, run, report, verify, order; the certified sampler), `spawnratio.py`, `patchsize.py`, `certrun.py` and `certify.py` (old windowed run), `verify_cert.py`, `rarity.py`, `theory.py`, plus older analysis scripts.
- `gamecheck/`: harness that checks our port against the real 26.3 server jar (`GameCheck.java`, `gamecheck.c`, result in `result_26.3.txt`, README has the steps).
- `tests/`: about 170 tests (pytest). `tests/test_theory.py` is pure numpy.
- `out/`: results (see section 7). `video/`: outline, script, asset index, footage notes.
- Older docs: `HANDOFF.md` (historical, 1.21.4 era), `PLAN*.md` (old plans).

## 6. Build and run
Linux or WSL (the PC uses WSL).
```
./build.sh ~/cubiomes-xp          # clones xpple/cubiomes, pins 304940b (MC_26_3), builds all simulators
pip install -r requirements.txt
CUBIOMES=~/cubiomes-xp python3 -m pytest -q    # a few minutes; test_raysim uses libcubiomes.so as a ctypes oracle
```
- Cubiomes path: first argument to build.sh, else `$CUBIOMES`, else `~/cubiomes-xp`. The old 1.21.4 results used Cubitect/cubiomes `e61f905` with `DX_VERSION=214`; the default now is 263.
- **Known gotcha:** `libcubiomes.so` is needed for the tests, and `build.sh` copies it from the CMake build dir. If tests fail to import the library, rebuild with build.sh and check `CUBIOMES` points at the same checkout. Build flags matter for bit-exactness: `-ffp-contract=off -fno-fast-math -fwrapv`, no FMA, no x87. `-march=native -ffp-contract=off -flto` gave about 8% with byte-identical output (measured 2026-11-22), but keep the pinned flags for certified runs.
- Certified sampler workflow (details in `python3 certwalk.py <cmd> --help`): `plan` (pilot, caps, alpha split, fixed seed counts with `--n-fixed r:n,...`, `--layers all`, `--ties 1`) then `run --threads T` (chunked, resumable, `--until N` to continue) then `report`, `order`, `verify --debug`, and `spawnratio.py`, `patchsize.py` over the raw rows. `verify --debug` is a single-thread brute-force column check and is slow at r=512 (15 to 30 minutes per ray).
- Production runs used: r=0 plan hash `81079ca199874b69`, r=128/512 plan hash `5e61f6a48bc983ed`, seed0 16,000,000,000 for the 128/512 run.

## 7. Where the results are
| Path | What |
|---|---|
| `out/certwalk263_r0/` | **26.3 radius 0**: `report.md` (all 56 biomes), `order.md` (paired ranking, rank ranges), `spawnratio.md`, `certificate.json`, raw rows in `spawn/` and `uniform/`, `plan.json` |
| `out/certwalk263_r128_512/` | **26.3 radius 128 and 512**: `report.md`, `order.md`, `certificate.json`, `spawn/` raw rows |
| `out/patchsize263/` | patch width and density per biome |
| `gamecheck/result_26.3.txt` | our generator versus the real game |
| `out/certwalk_cave_r0`, `out/certwalk_cave_r128_512`, `out/certwalk`, `out/certrun`, `out/cert`, `out/exact` | **1.21.4, superseded**, kept for history and the video |
Note: `.gitignore` excludes `out/**/*.csv`, so the raw per-ray CSVs exist only on the machine that ran them. **[unverified]** whether the full raw data is still on the owner's PC under `out/certwalk263_*`; the cloud only has the committed reports and certificates. Do not delete those folders.

## 8. Done versus open
Done:
- 26.3 port and checks against the real game (climate bit-exact, 0 mismatches on 2.5M cells and 700 spawns), tie sandwich, certified r=0/128/512 runs with caves, spawn ratio, patch table, footage for the video, video outline v5 and script v3.

Open (my read, ask the owner to confirm priorities):
1. **Run the test suite on the PC** and confirm it passes on current `main` **[unverified, not run from the cloud]**.
2. **Radius 128 and 512 precision.** Only +-8% (spawn arm only). The ranks below #1 are mostly ties. Decide whether the video needs sharper 8 and 32 chunk rankings. If yes, plan one fixed larger run up front (cost is roughly proportional to seeds; r=512 is the expensive one).
3. **Known looseness:** 374 rows at r=0 have `D_strict = -1` (scan stops on a hint-free hit), which loosens upper ends slightly (see THEORY 0.1). Uniform arm not run at r=128/512, so no spawn effect there.
4. **Assumptions to keep labelled:** a cave biome counts anywhere in the column at any depth (the owner has not confirmed); constant-hazard tail past the cap (tail share about 1 to 9%, 17 to 23% for river at r=128/512); model is a straight line, no terrain, no line of sight; the game's chunk path (volume sampling) differs from the point path we ported, checked on 1,536,000 chunk cells with 0 mismatches.
5. **Video script finishing** (section 9): open `[CHECK]` items, camman18's distance method unknown, optional area-versus-walk flip (needs an area share run), decide on camera whether to use the patch table.
6. Keep the repo docs in sync when anything changes (README headline, this file, THEORY status note).

## 9. Video status
- Files in the repo: `video/VIDEO_OUTLINE.md` (v5) and `video/VIDEO_SCRIPT.md` (draft v3, about 1,600 words, 10 to 11 minutes), `video/assets/INDEX.md` (every asset by section, with licence notes), `video/assets/CAPTURE_LIST.md`, `video/assets/footage/SHOTS.md` and `README.md`. The generated images and clips themselves (charts, lower thirds, animations, shot sheets) are in the cloud project folder, not in git. **[unverified]** whether the owner has local copies; the generators are in `video/assets/_generator/` in the project folder. Ask him before regenerating.
- **Script rules (owner):** reactions in the script must be his REAL reactions. Polish wording is fine but never drop or summarize his points. If the data contradicts any of his lines, alert him directly in the reply, with his line and what the data shows (a quiet note in the file is not enough). Use the human-voice skill when writing for him. Avoid on-screen maths notation.
- **No spoilers of #1** (mushroom fields) before the reveal. Assets named `SPOILER_` show it and belong after the reveal. Do not show mushroom fields as "the answer" in the cold open.
- Structure: cold open (camman18's four videos, four different answers), what "rare" means, Monte Carlo, how do I know it is right (the 43% sparse-grid bias, then the "wrong game version" beat), countdown 5 to 1, "open your eyes" (8 and 32 chunks), reading the ranking, outro. Takeaway line: "The rarest biome in Minecraft 26.3 is mushroom fields: almost seven and a half hours of sprinting from spawn (at 5.612 blocks/s), and still #1 no matter how far you can see."
- **Footage: DONE.** In `D:\Coding\Minecraft\mc-capture` (Fabric 26.3, Fabric API, MCPFabric bridge, Flashback, Sodium, our own `capturectl` mod for HUD hide, replay export and camera paths; start with `start-capture.ps1`; driver `tools\shoot.mjs`). The world is `capture279` (seed 279). Final 1080p60 clips and `SHOTS.md` are in `mc-capture\shots` (best file per biome). Bridge fix: give the game a private Java tmpdir (`-Djava.io.tmpdir`, `-Djdk.net.unixdomain.tmpdir`). Real mushroom island is at about (1085, -1020), not CAPTURE_LIST's (888, -1104). Wooded badlands is one tiny patch in this world. Files not checked from the cloud **[unverified]**: the clips on disk.
- Wiki pages the owner saved by hand are in `web\` in the repo folder **[unverified, not in git]**; Reddit screenshots for the cold open are in `video/assets/00_cold_open/` of the project folder.
- **Awaiting the owner's OK:** the wiki scroll-render test. A Pale Garden scroll render was made as a test; the other biomes wait for his OK. Show the plan and get his yes before any further page or browser work.
- **Update 2026-11-27 (checked on the PC):** the generated assets are local, in `video/assets/<section>/` (untracked), and all 12 wiki scrolls are rendered in `video/assets/wiki_scrolls/`. The 2026-11-26 extra shots (spawn, render distance 8/32, deep dark, ancient city) exist and are in `footage/SHOTS.md`. Edit prep: `video/edit/EDIT_PLAN.md` (cut sheet per script line, gaps; the script is about 2,450 words, 15 to 16 minutes, and length does not matter to the owner, quality does) and `video/edit/make_bins.ps1` (Resolve bins as hard links in `video/edit/media/`).

## 10. Next steps (suggested order)
1. Pull `main`, run `./build.sh` and the tests on the PC. Report the result to the owner.
2. Ask the owner which of the open items matter (section 8), especially whether 8 and 32 chunk rankings need a sharper run for the video.
3. If a new run is wanted: write the plan first (seed counts fixed up front, `--n-fixed`), get his yes, run on the PC with status lines every 2 minutes, then `report`, `order`, `verify`, commit certificate, reports and order files to `main`.
4. Finish the video script `[CHECK]` items with the owner, with his real reactions preserved.
5. Wiki scroll test for the remaining biomes only after his OK.
6. Keep README, this file and THEORY's status note current after each change.
