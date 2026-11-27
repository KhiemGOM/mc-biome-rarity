# Edit plan (DaVinci Resolve)

Cut sheet for `video/VIDEO_SCRIPT.md` (draft v3), one row per `[VISUAL]` beat, with the file to use from
`video/edit/media/<section>/`. Script line numbers are given as `L<n>`. Numbers on screen are Minecraft Java 26.3 only.
The old `make_video.py` / `scenes.py` slides show the outdated pale garden figure: do not use them.

## Setup

1. `video/edit/make_bins.ps1` (already run once) fills `video/edit/media/<section>/` with hard links to the best
   asset or take for each section. Re-run it after adding assets. The folder is git-ignored.
2. Resolve: new project, timeline **1920x1080, 60 fps**. The game footage is 60 fps, the generated animations 30 fps,
   and the camman18 shorts 59.94 fps vertical (1080x1920). Drag each `media/` folder in as a bin.
3. Keep everything named `SPOILER_` in its own red bin, so it never lands before the #1 reveal (L161).
4. Record the VO first, then cut picture to it. All game footage is 20 s with no audio.

## Length

No length target: quality first (Khiem, 2026-11-27). The full script is about 2,450 words of VO, roughly 15 to 16
minutes at 155 words per minute. Do not trim beats to save time; cut only what is weak.

## Cut sheet

### 0. Cold open (`00_cold_open/`)
| Script | Visual | File | Notes |
|---|---|---|---|
| L15-17 | Thumbnail wall | camman18 `*.jpg` (5) | Credit camman18 on screen |
| L19 | 1.17 answer | `20210713_d9Xmt9vhyRY_...1.17.mp4` | Vertical: frame it or use a blurred fill |
| L21-23 | Pale garden by area | `20260103_12UgiwOo28k_...mp4` | Short clip only (fair use) |
| L25-27 | Gravelly hills | `20260628_ZnfLg6UiDYw_...mp4` | |
| L29-31 | Eroded badlands by distance | `20261118_HVfXIyuudTY_...mp4` | |
| L33-35 | "Cry for help" beat | four shorts side by side, or titles stacking up | Comedy beat. Let it breathe |
| L37-39 | Forum and wiki posts | **missing (C2)**. Stopgap: `_wiki_scrolls/*_scroll.mp4` | Blur usernames |
| L41-43 | Seed counter | `seed_counter_0_to_215000.mp4` (4 s), hold `seed_counter_final.png` | Fast biome cuts (1 to 2 s each) over "walked through every one": peaks, gravelly hills, ice spikes, eroded badlands, pale garden. At most a flash of mushroom |
| L45 | Title card | **missing**: make it in Resolve (Text+) | "I found the RAREST biome in Minecraft... MATHEMATICALLY" |

### 1. What "rare" means (`01_what_is_rare/`)
| Script | Visual | File | Notes |
|---|---|---|---|
| L51-53 | Wiki / community opinion | `_wiki_scrolls/*` | |
| L55-59 | Same area, different clumping | `clumping_same_area_two_panels.png` | Slow push-in |
| L61-63 | Random start vs spawn | `spawn_1080p.mp4` | The spawn moment |
| L65-67 | Spawn heat map | `spawn_heatmap_vs_random.png` | |
| L69-73 | Spawn effect bars | `spawn_effect_bars.png` | Mushroom is left out on purpose: keep it out |
| L75-77 | Effect fades by 2,000 blocks | `spawn_effect_vs_distance.png` | |
| L79-83 | The metric | `one_world_one_ray.mp4` (first seconds) or `spawn_1080p.mp4` | |
| L85-87 | Straight vs wandering | `one_world_one_ray.mp4`, then `wander_vs_straight_ray.png` | |

### 2. Monte Carlo (`02_monte_carlo/`)
| Script | Visual | File | Notes |
|---|---|---|---|
| L95-97 | Darts, pi settles | `darts_estimate_pi.mp4` (12 s), hold `_final.png` | |
| L99-101 | One real world, one ray | `one_world_one_ray.mp4` (16 s), hold `_final.png` | |
| L103-105 | Many worlds, averages settle | `many_worlds_grid.png` then `running_average_settles_DEMO.png` | Keep the DEMO label visible |
| L107 | Cubiomes credit | `xpple_cubiomes.png` | |

### 3. How do I know it is right (`03_how_do_i_know/`)
| Script | Visual | File | Notes |
|---|---|---|---|
| L115-117 | Dot grid every 16 blocks | `dot_grid_pale_garden_grid.png` | |
| L119-121 | Patch slips between the dots, 43% | `dot_grid_pale_garden_reveal.png` | Cross-dissolve grid to reveal |
| L123-125 | Biased dartboard | `dartboard_biased.png` (then optional `dartboard_correct.png`) | |
| L127-131 | Wrong version, stamp shatters | `old_ranking_1214.png` then `_stamped.png` | Animate the shatter in Fusion. #1 stays hidden |
| L133-137 | Proof on GitHub | `theory_md.png` | |

### 4. Countdown (`04_countdown/`)
| Script | Visual | File | Notes |
|---|---|---|---|
| L143 | Intro | (any wide biome shot) | |
| L147 | #5 eroded badlands | `eroded_badlands_1080p.mp4` + `lowerthird_rank5_eroded_badlands.png` | Lower thirds on V2 |
| L149 | #4 ice spikes | `ice_spikes_v2_1080p.mp4` + `lowerthird_rank4_ice_spikes.png` | |
| L151 | #3 stony peaks | `peaks_orbit_1080p.mp4` + `lowerthird_rank3_stony_peaks.png` | |
| L153 | #2 gravelly hills | `windswept_gravelly_hills_1080p.mp4` + `lowerthird_rank2_...png` | |
| L155-157 | Pale garden falls #2 to #6 | `pale_garden_drop_2_to_6_no1hidden.png` over `pale_garden_v2_1080p.mp4` | |
| L159 | "And number one." | hold, music drop | |
| L161-163 | **Reveal** | `SPOILER_mushroom_fields_v4_1080p.mp4` + `SPOILER_lowerthird_rank1_mushroom_fields.png` | First spoiler on the timeline |
| L165 | Spawn pushes it away | `SPOILER_mushroom_spawn_push.png` | |
| L167-169 | Full ranking with ranges | `SPOILER_ranking_top20_step_on_it.png` | Mangrove #7: flash `mangrove_swamp_v5_1080p.mp4` |

### 4b. Open your eyes (`04b_open_your_eyes/`)
| Script | Visual | File | Notes |
|---|---|---|---|
| L177-179 | Sight band 8 then 32 chunks | `sight_band_8_chunks.png` then `sight_band_32_chunks.png`, then `render_distance_side_by_side_1080p.mp4` | Or cut the 8 and 32 clips back to back (frame for frame) |
| L181 | Small patches easy to spot | `pale_garden_v2_1080p.mp4` | |
| L183-185 | Three radii, lines across | `SPOILER_three_radius_bars.png`, then `SPOILER_slopegraph_rank_0_8_32.png` | |
| L187 | Everything below #1 collapses | `SPOILER_ranking_top20_8chunks.png` | |
| L189 | Pale garden keeps falling | slopegraph, highlight pale garden | |
| L191 | Eroded badlands climbs at 32 | `SPOILER_ranking_top20_32chunks.png`, `eroded_badlands_1080p.mp4`, `wooded_badlands_v2_1080p.mp4` (weak, keep brief) | |
| L193-197 | Table | `SPOILER_table_three_radii.png` | |
| L199-201 | Looks like camman's ranking | camman18 HVfXIyuudTY clip, brief | |

### 4c. Reading the ranking (`04c_reading_the_ranking/`)
Run `04_countdown/SPOILER_ranking_all56_step_on_it.png` (1920x2160) as a slow vertical pan under this whole section,
cutting away to footage at each beat.
| Script | Visual | File | Notes |
|---|---|---|---|
| L213-215 | Mushroom, spawn push | `SPOILER_mushroom_fields_v4_1080p.mp4` | |
| L217 | Two to five | ranking pan | |
| L219 | Mangrove at #7 | `mangrove_swamp_v5_1080p.mp4` | |
| L221-223 | Windswept hills vs cherry grove | `windswept_hills_v2_1080p.mp4` beside `cherry_grove_1080p.mp4` (split screen), `dappled_forest_1080p.mp4` | |
| L225 | Old growth taigas, sparse jungle | **no footage**. Stopgap: ranking pan, or hand-saved wiki images | |
| L227 | Ocean is common | `render_distance_8_1080p.mp4` (open ocean) | |
| L229-231 | Deep dark, ancient city | `deep_dark_1080p.mp4`, `ancient_city_1080p.mp4` + `note_caves_count_any_depth_overlay.png` | Pick the bright or the `_dark` version and use it for both |
| L233 | Sulfur, dripstone, lush caves | **no footage**. Stopgap: ranking pan | |
| L235 | Plains and forest | `plains_v3_1080p.mp4`, `forest_v2_1080p.mp4` | |
| L237-239 | River, the line catcher | `river_v2_1080p.mp4` | |
| L241-245 | camman callback | camman18 clips | |

### 5. Outro (`05_outro/`)
| Script | Visual | File | Notes |
|---|---|---|---|
| L251 | Takeaway | `SPOILER_mushroom_fields_v4_1080p.mp4` | |
| L253 | Limits | talking head (**C8, yours**) | |
| L255-257 | Open source | `repo_page.png` | End screen |

## Gaps before picture lock

- **VO:** not recorded.
- **Script `[CHECK]`s (L81, L245):** camman's distance method is still unknown. Resolve before recording.
- **C2:** forum and wiki posts for L37-39.
- **C8:** talking head for the outro.
- **Title card:** build in Resolve.
- **No footage for:** old growth taigas, sparse jungle, sulfur, dripstone and lush caves (4c L225, L233). Use the ranking pan, or film them in seed 279 (needs a game launch: plan first and get Khiem's yes).
- **Music and SFX:** none sourced.
- **Description credits:** "Images: Minecraft Wiki", camman18 links (`00_cold_open/camman18/SOURCES.md`), xpple/cubiomes.
