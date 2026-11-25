# Video asset index (outline v5, script v3)

Every visual the outline and script call for, grouped by section, with where it comes from. Numbers are Minecraft Java 26.3, from `results/mc263_*`. All generated images are 1920x1080 unless noted.

**Spoilers:** folders `00` to `03` never reveal #1 (where a ranking shows it, #1 is "? ? ?"). Anything named `SPOILER_` shows mushroom fields as #1 and belongs after the reveal.

**Licences, short version**
- Generated here (charts, maps, animations): made from your own results and the cubiomes 26.3 port. Yours to use. Scripts in `_generator/`.
- Minecraft Wiki images (`wiki_biome_images/`): the image files are copyright Mojang Studios, usable under the Minecraft Usage Guidelines (minecraft.net/usage-guidelines), which allow them in videos. The wiki itself is CC BY-NC-SA 3.0. Credit "Images: Minecraft Wiki" in the description. They can show older versions, so use them as fallback or B-roll; your own 26.3 footage is better.
- camman18 clips (`00_cold_open/camman18/`): copyright camman18. Use short clips with on-screen credit, for commentary (fair use). Not cleared for reuse beyond that.

## 0. Cold open

| File | Beat | Source |
|---|---|---|
| `00_cold_open/camman18/20210713_d9Xmt9vhyRY_*` (.mp4, .jpg) | 1.17 answer: modified jungle edge #1, mushroom "not even in the top five" | youtube.com/watch?v=d9Xmt9vhyRY, camman18, 2021-07-13 |
| `00_cold_open/camman18/20260103_12UgiwOo28k_*` | Pale garden by area | youtube.com/shorts/12UgiwOo28k |
| `00_cold_open/camman18/20260628_ZnfLg6UiDYw_*` | Windswept gravelly hills after the pale garden buff | youtube.com/shorts/ZnfLg6UiDYw |
| `00_cold_open/camman18/20261118_HVfXIyuudTY_*` | Eroded badlands by distance from spawn | youtube.com/shorts/HVfXIyuudTY |
| `00_cold_open/camman18/*.jpg` | Thumbnail wall | Same videos. Details in `camman18/SOURCES.md` |
| `00_cold_open/seed_counter_0_to_215000.mp4` (+ `_final.png`) | "So I generated 215,000 real worlds" seed counter | Generated |
| C1 in CAPTURE_LIST | Fast biome cuts | Done: filmed in seed 279, best file per biome in `footage/SHOTS.md` (keep mushroom fields brief) |
| C2 in CAPTURE_LIST | Forum and wiki posts | You capture |

## 1. What does "rare" even mean

| File | Beat | Source |
|---|---|---|
| `01_what_is_rare/clumping_same_area_two_panels.png` | 36 small patches vs one big blob, same area | Generated |
| `01_what_is_rare/spawn_heatmap_vs_random.png` | Heat map of where spawns land vs random points | Generated, seeds 1 to 20,000 on the 26.3 spawn finder. 40% of spawns are exactly 0, 0 |
| `01_what_is_rare/spawn_effect_bars.png` | Bar chart of the spawn effect: land 1.7 to 1.9x, oceans and rivers never. Mushroom left out on purpose (no spoiler) | Generated, `mc263_r0_spawnratio.md` |
| `01_what_is_rare/spawn_effect_vs_distance.png` | Spawn effect curves sliding back to 1 by 2,000 blocks (beach flip included) | Generated, same file |
| `02_monte_carlo/one_world_one_ray.mp4` | Also fits "spawn dot, one ray, counter ticking up" | Generated |
| `01_what_is_rare/wander_vs_straight_ray.png` | Quick note: wandering walk vs straight line | Generated, illustration |

## 2. Monte Carlo

| File | Beat | Source |
|---|---|---|
| `02_monte_carlo/darts_estimate_pi.mp4` (+ `_final.png`) | Darts at a square, pi estimate settling | Generated, 6,000 darts |
| `02_monte_carlo/one_world_one_ray.mp4` (+ `_final.png`) | One real seed (101), one ray, each biome lights up with its distance, caves included | Generated from cubiomes 26.3, all 96 layers |
| `02_monte_carlo/many_worlds_grid.png` | Zoom out: many worlds, one ray each | Generated, 32 real 26.3 seeds |
| `02_monte_carlo/running_average_settles_DEMO.png` | Running averages wobble then settle | Generated from a small 600 world demo run, labelled as not the certified numbers |
| `github_screens/xpple_cubiomes.png` | Tool credit | Screenshot of github.com/xpple/cubiomes |

## 3. How do I know it is right

| File | Beat | Source |
|---|---|---|
| `03_how_do_i_know/dot_grid_pale_garden_grid.png` then `_reveal.png` | Dot grid every 16 blocks, a real pale garden strip slips between the dots | Generated, seed 2002 near x 3411, z -828 |
| `03_how_do_i_know/dartboard_biased.png` | Tight cluster nowhere near the bullseye | Generated |
| `03_how_do_i_know/dartboard_correct.png` | Optional "after the fix" | Generated |
| `03_how_do_i_know/old_ranking_1214.png` then `_stamped.png` | Old ranking with pale garden #2, red 1.21.4 stamp (make it shatter in edit) | Generated from `certwalk_cave_r0_report_53750.md` (1.21.4), #1 hidden |
| `github_screens/theory_md.png` | "The proof is on GitHub" | Screenshot, top of THEORY.md |

## 4. Countdown

| File | Beat | Source |
|---|---|---|
| `04_countdown/lowerthird_rank5..2_*.png`, `SPOILER_lowerthird_rank1_*.png` | Transparent lower thirds: rank, blocks ± range, sprint time at 5.612 blocks/s | Generated |
| `04_countdown/pale_garden_drop_2_to_6_no1hidden.png` | "Where did pale garden go": #2 on 1.21.4 to #6 on 26.3, shown before the reveal | Generated |
| `04_countdown/SPOILER_pale_garden_drop_2_to_6.png` | Same, #1 visible | Generated |
| `04_countdown/SPOILER_mushroom_spawn_push.png` | #1 payoff: never at spawn, about 0.14x within 512 blocks, gone by 2,000 | Generated, spawnratio file |
| `04_countdown/SPOILER_ranking_top20_step_on_it.png` | End card: ranked bars with ± range and tie brackets | Generated, report + order files |
| `04_countdown/SPOILER_ranking_all56_step_on_it.png` | Full 56 biome list, 1920x2160 for a slow scroll | Generated |
| Biome footage: `SPOILER_mushroom_fields_v4_1080p.mp4`, `windswept_gravelly_hills_1080p.mp4`, `peaks_orbit_1080p.mp4`, `ice_spikes_v2_1080p.mp4`, `eroded_badlands_1080p.mp4`, `pale_garden_v2_1080p.mp4`, `mangrove_swamp_v5_1080p.mp4` | Each entry | Done: CAPTURE_LIST C5, filmed in seed 279 (`footage/`) |

## 4b. Now open your eyes

| File | Beat | Source |
|---|---|---|
| `04b_open_your_eyes/sight_band_8_chunks.png`, `sight_band_32_chunks.png` | Same ray with a glowing band 8 then 32 chunks wide | Generated, seed 101 |
| `04b_open_your_eyes/SPOILER_three_radius_bars.png` | Three bar charts side by side (0, 8, 32 chunks) | Generated |
| `04b_open_your_eyes/SPOILER_slopegraph_rank_0_8_32.png` | Lines connecting each biome across the three radii | Generated |
| `04b_open_your_eyes/SPOILER_table_three_radii.png` | On-screen table (9 rows from the outline) | Generated |
| `04b_open_your_eyes/SPOILER_ranking_top20_8chunks.png`, `_32chunks.png` | Full top 20 per radius, if needed | Generated |

## 4c. Reading the ranking

| File | Beat | Source |
|---|---|---|
| `04c_reading_the_ranking/note_caves_count_any_depth_overlay.png` | On-screen note "cave biomes count ... reachable or not" (transparent) | Generated |
| `wiki_biome_images/` (NOT DOWNLOADED, see below) | B-roll for mangrove, windswept hills vs cherry grove, old growth taigas, sparse jungle, deep dark, ancient city, sulfur caves, river, plains, forest | Minecraft Wiki, on your PC |
| C7: `windswept_hills_v2_1080p.mp4`, `cherry_grove_1080p.mp4`, `river_v2_1080p.mp4`; also `plains_v3_1080p.mp4`, `forest_v2_1080p.mp4`, `mangrove_swamp_v5_1080p.mp4`, `dappled_forest_1080p.mp4`, `wooded_badlands_v2_1080p.mp4` (weak, for 4b) | Own footage of the same | Partly done (`footage/`): no deep dark or ancient city clip listed |

## 5. Outro

| File | Beat | Source |
|---|---|---|
| `github_screens/repo_page.png` | "All the code is open source" | Screenshot of the repo page |

## Wiki biome images (28): not downloaded

minecraft.wiki blocks scripted downloads (Cloudflare bot check, HTTP 403), so these need saving by hand: open each File: page listed in `wiki_biome_images/SOURCES.md` in your browser and save the original under the name given there. Your own seed 279 footage can replace most of them.


Mushroom fields, windswept gravelly hills, stony peaks, ice spikes, eroded badlands, pale garden, mangrove swamp, wooded badlands, badlands, windswept hills, cherry grove, deep dark, ancient city, river, plains, forest, sulfur caves, dappled forest, old growth spruce taiga, old growth pine taiga, sparse jungle, dripstone caves, lush caves, ocean, beach, jagged peaks, frozen peaks, desert. Each is the infobox image of that biome's Minecraft Wiki page; `wiki_biome_images/SOURCES.md` lists the exact file URLs.
