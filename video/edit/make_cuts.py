"""Writes cuts.csv: which file(s) go under each script line. Paths are relative to video/edit/media.
`file@12.5` starts that clip 12.5 s in. Several files on one line split its time evenly. A line with no files keeps
showing the previous visual. `overlay` files (lower thirds, notes) show on the track above, for that line only.
Edit this file (not cuts.csv) and re-run it, so the choices stay readable."""
import csv, os

C = "00_cold_open/"
J17 = C + "20210713_d9Xmt9vhyRY_the rarest biome in Minecraft 1.17"
PG = C + "20260103_12UgiwOo28k_The REAL Rarest Biome in Minecraft..."
GH = C + "20260628_ZnfLg6UiDYw_the REAL, real rarest biome in Minecraft..."
EB = C + "20261118_HVfXIyuudTY_the REAL, real, real rarest biome in Minecraft..."
RT = C + "20210427_RTu-RkcdXpE_The Rarest Biome in Minecraft #Shorts"
W, M, H, N, Q, R, O = "_wiki_scrolls/", "01_what_is_rare/", "02_monte_carlo/", "03_how_do_i_know/", "04_countdown/", "04b_open_your_eyes/", "04c_reading_the_ranking/"
MUSH = Q + "SPOILER_mushroom_fields_v4_1080p.mp4"

CUTS = {
    # 0. Cold open
    "V001": [RT + ".jpg", J17 + ".jpg", PG + ".jpg", GH + ".jpg", EB + ".jpg"],
    "V002": [J17 + ".mp4@24", J17 + ".mp4@2"],
    "V003": [PG + ".mp4@26"],
    "V004": [GH + ".mp4@39"],
    "V005": [EB + ".mp4@34"],
    "V006": [J17 + ".jpg", PG + ".jpg", GH + ".jpg", EB + ".jpg"],
    "V007": [W + "pale_garden_scroll.mp4", W + "windswept_gravelly_hills_scroll.mp4", W + "eroded_badlands_scroll.mp4", W + "stony_peaks_scroll.mp4"],
    "V008": [C + "seed_counter_0_to_215000.mp4", C + "peaks_orbit_1080p.mp4@5", C + "windswept_gravelly_hills_1080p.mp4@5",
             C + "ice_spikes_v2_1080p.mp4@5", C + "eroded_badlands_1080p.mp4@5", C + "pale_garden_v2_1080p.mp4@5"],
    "V009": [C + "seed_counter_final.png"],
    "C001": [C + "title_card_anim.mp4"],
    # 1. What rare means
    "V010": [O + "plains_v3_1080p.mp4@2"],
    "V011": [W + "forest_scroll.mp4"],
    "V012": [PG + ".mp4@2"],
    "V013": [M + "clumping_same_area_two_panels.png"],
    "V014": [M + "one_world_one_ray.mp4"],
    "V015": [M + "spawn_1080p.mp4"],
    "V016": [M + "spawn_heatmap_vs_random.png"],
    "V017": [M + "spawn_effect_bars.png"],
    "V020": [M + "spawn_effect_vs_distance.png"],
    "V021": [M + "spawn_1080p.mp4@4"],
    "V022": [M + "one_world_one_ray.mp4"],
    "V023": [M + "wander_vs_straight_ray.png"],
    # 2. Monte Carlo
    "V024": [O + "dappled_forest_1080p.mp4@2"],
    "V025": [H + "darts_estimate_pi.mp4", H + "darts_estimate_pi_final.png"],
    "V026": [H + "one_world_one_ray.mp4", H + "one_world_one_ray_final.png"],
    "V027": [H + "many_worlds_grid.png", H + "running_average_settles_DEMO.png"],
    "V028": [H + "xpple_cubiomes.png"],
    # 3. How do I know
    "V029": [C + "title_card.png"],
    "V030": [N + "dot_grid_pale_garden_grid.png"],
    "V031": [N + "dot_grid_pale_garden_reveal.png"],
    "V032": [N + "dartboard_biased.png"],
    "V033": [GH + ".mp4@4"],
    "V034": [N + "old_ranking_1214.png"],
    "V035": [N + "old_ranking_1214_stamped.png"],
    "V036": [N + "dartboard_correct.png"],
    "V037": [N + "theory_md.png"],
    # 4. Countdown
    "V038": [O + "plains_v3_1080p.mp4@8"],
    "V039": [Q + "eroded_badlands_1080p.mp4@2"],
    "V040": [Q + "ice_spikes_v2_1080p.mp4@2"],
    "V041": [Q + "peaks_orbit_1080p.mp4@2"],
    "V042": [Q + "windswept_gravelly_hills_1080p.mp4@2"],
    "V043": [Q + "pale_garden_v2_1080p.mp4@2", Q + "pale_garden_drop_2_to_6_no1hidden.png"],
    "V045": [MUSH],
    "V046": [MUSH + "@10"],
    "V047": [Q + "SPOILER_mushroom_spawn_push.png"],
    "V048": [Q + "SPOILER_ranking_top20_step_on_it.png", Q + "mangrove_swamp_v5_1080p.mp4@4"],
    "V049": [R + "render_distance_8_1080p.mp4@2"],
    # 4b. Open your eyes
    "V050": [R + "sight_band_8_chunks.png", R + "sight_band_32_chunks.png", R + "render_distance_side_by_side_1080p.mp4@2"],
    "V051": [R + "render_distance_32_1080p.mp4@6"],
    "V052": [R + "pale_garden_v2_1080p.mp4@6"],
    "V053": [R + "SPOILER_three_radius_bars.png"],
    "V054": [R + "SPOILER_ranking_top20_8chunks.png"],
    "V055": [R + "SPOILER_slopegraph_rank_0_8_32.png"],
    "V056": [R + "SPOILER_ranking_top20_32chunks.png", R + "eroded_badlands_1080p.mp4@8", R + "wooded_badlands_v2_1080p.mp4@4"],
    "V057": [R + "SPOILER_table_three_radii.png"],
    "V058": [MUSH + "@12"],
    # 4c. Reading the ranking
    "V059": [Q + "SPOILER_ranking_all56_step_on_it.png"],
    "V060": [MUSH + "@4"],
    "V061": [Q + "SPOILER_mushroom_spawn_push.png"],
    "V062": [Q + "SPOILER_ranking_top20_step_on_it.png"],
    "V063": [O + "mangrove_swamp_v5_1080p.mp4", O + "mangrove_swamp_v5_1080p.mp4@6"],
    "V064": [O + "windswept_hills_v2_1080p.mp4@2", O + "cherry_grove_1080p.mp4@2", O + "dappled_forest_1080p.mp4@8"],
    "V065": [Q + "SPOILER_ranking_all56_step_on_it.png"],
    "V066": [R + "render_distance_8_1080p.mp4@10"],
    "V067": [O + "deep_dark_1080p.mp4@1", O + "ancient_city_1080p.mp4@1"],
    "V068": [O + "plains_v3_1080p.mp4@10", O + "forest_v2_1080p.mp4@2"],
    "V070": [O + "river_v2_1080p.mp4", O + "river_v2_1080p.mp4@4"],
    "V071": [PG + ".mp4@26", GH + ".mp4@39", EB + ".mp4@32"],
    "V072": [MUSH + "@12"],
    # 5. Outro
    "V073": [MUSH + "@5"],
    "V074": [R + "render_distance_32_1080p.mp4@1"],
    "V075": ["05_outro/repo_page.png"],
    "V076": [M + "spawn_1080p.mp4@10"],
}

OVERLAY = {
    "V039": [Q + "lowerthird_rank5_eroded_badlands.png"],
    "V040": [Q + "lowerthird_rank4_ice_spikes.png"],
    "V041": [Q + "lowerthird_rank3_stony_peaks.png"],
    "V042": [Q + "lowerthird_rank2_windswept_gravelly_hills.png"],
    "V045": [Q + "SPOILER_lowerthird_rank1_mushroom_fields.png"],
    "V067": [O + "note_caves_count_any_depth_overlay.png"],
}

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cuts.csv")
    ids = sorted(set(CUTS) | set(OVERLAY), key=lambda k: (k[0] != "V", k))
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "files", "overlay"])
        for k in ids:
            w.writerow([k, "; ".join(CUTS.get(k, [])), "; ".join(OVERLAY.get(k, []))])
    print(f"cuts.csv: {len(CUTS)} lines with visuals, {len(OVERLAY)} overlays")
