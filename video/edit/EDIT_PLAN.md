# Edit plan (DaVinci Resolve)

Section order and beats follow `video/assets/INDEX.md` (outline v5). Numbers on screen are Minecraft Java 26.3 only.
The old `make_video.py` / `scenes.py` renders show the outdated 1.21 pale garden figure (about 265k): do not use them.

## Setup

1. Run `video/edit/make_bins.ps1` (already run once). It fills `video/edit/media/<section>/` with hard links to the
   best asset or take for each section. Re-run it after adding assets. The folder is git-ignored.
2. In Resolve: new project, timeline **1920x1080, 60 fps** (the game footage is 60 fps; the generated animations are
   30 fps and the camman18 shorts are 59.94 fps vertical, both conform fine). Drag each `media/` folder in as a bin.
3. Media pool: keep anything `SPOILER_` in its own bin or coloured red, so it never lands before the #1 reveal.

## Format notes

- All game footage: 20 s, no audio, HUD hidden. Plan for voice-over plus music on every shot.
- camman18 shorts are 1080x1920 (vertical). Put them in a frame or blurred fill, add an on-screen credit, keep clips short (commentary use).
- `ancient_city` / `deep_dark` come in a brightened and a `_dark` version. Pick one per shot and don't mix them.
- Wooded badlands footage is weak (mostly ocean). Use it only as a brief cutaway.
- Lower thirds and overlays are transparent PNGs. Put them on V2 and above.

## Timeline by section

| # | Section | Visuals in order (bin `media/<section>/`) | Edit notes |
|---|---|---|---|
| 0 | Cold open | camman18 shorts in date order (2021 jungle edge, 2026 pale garden, windswept gravelly hills, 2026-11 eroded badlands), thumbnail wall from the `.jpg`s, fast biome cuts 1 to 2 s each (peaks, gravelly hills, ice spikes, eroded badlands, pale garden), then `seed_counter_0_to_215000.mp4` and hold `seed_counter_final.png` | Mushroom fields at most one very short cut, never framed as the answer. C2 (forum/wiki posts) is still to capture. The 2021-04-27 short `RTu-RkcdXpE` is in the bin but not in INDEX: optional |
| 1 | What "rare" means | `clumping_same_area_two_panels`, `spawn_1080p.mp4` (spawn moment), `spawn_heatmap_vs_random`, `spawn_effect_bars`, `spawn_effect_vs_distance`, `wander_vs_straight_ray` | Spawn effect bars leave mushroom out on purpose: keep it that way |
| 2 | Monte Carlo | `darts_estimate_pi.mp4` then `_final`, `one_world_one_ray.mp4` then `_final`, `many_worlds_grid`, `running_average_settles_DEMO`, `xpple_cubiomes` | The DEMO chart must keep its "not the certified numbers" label on screen |
| 3 | How do I know | `dot_grid_pale_garden_grid` then cut to `_reveal`, `dartboard_biased` (then optional `dartboard_correct`), `old_ranking_1214` then `_stamped` (animate the stamp shattering), `theory_md` | The old ranking hides #1. Keep it hidden |
| 4 | Countdown | Each rank: biome footage plus its lower third. #5 eroded badlands, #4 ice spikes, #3 stony peaks (`peaks_orbit`), #2 windswept gravelly hills, then `pale_garden_drop_2_to_6_no1hidden` (pale garden falls to #6, mangrove #7 mention). Then the reveal: `SPOILER_mushroom_fields_v4` plus `SPOILER_lowerthird_rank1`, `SPOILER_mushroom_spawn_push`, `SPOILER_pale_garden_drop_2_to_6`, end card `SPOILER_ranking_top20_step_on_it` | `SPOILER_ranking_all56` is 1920x2160: slow vertical pan (keyframe Y position) |
| 4b | Open your eyes | `sight_band_8_chunks` then `_32_chunks`, `render_distance_side_by_side` (or the 8 and 32 clips cut back to back, frame for frame), `SPOILER_three_radius_bars`, `SPOILER_slopegraph_rank_0_8_32`, `SPOILER_table_three_radii`, top 20 per radius if needed | Footage for climbers and fallers: eroded badlands, pale garden, wooded badlands (weak) |
| 4c | Reading the ranking | `note_caves_count_any_depth_overlay` over `deep_dark` / `ancient_city`, `windswept_hills_v2` against `cherry_grove` (split screen works), `river_v2` (line catcher), `plains_v3`, `forest_v2`, `dappled_forest`, `mangrove_swamp_v5` | `_wiki_scrolls/` has scrolling wiki pages as B-roll for most of these |
| 5 | Outro | `repo_page`, talking head (C8, yours) | Description credits: "Images: Minecraft Wiki", camman18 video links (`00_cold_open/camman18/SOURCES.md`), xpple/cubiomes |

## Still missing before picture lock

- **Voice-over:** no VO or script file is in the repo yet. Record against this order, then cut picture to the VO.
- **C2:** forum and wiki posts for the cold open (screen capture, blur usernames).
- **C8:** talking head or outro shot.
- **Music and SFX:** none sourced yet.
- **Optional:** `wiki_biome_images/` stills (save by hand, see its `SOURCES.md`). The seed 279 footage and wiki scrolls cover most of them.
