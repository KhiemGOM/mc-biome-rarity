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
G = "gags/"
FW = C  # forum_wiki/*.png, linked flat into the bin

CUTS = {
    # 0. Cold open
    # K00x lines are camman's own clips: they show themselves (vo/clips.py), so only your lines need shots here
    "V001": [RT + ".jpg", J17 + ".jpg", PG + ".jpg", GH + ".jpg", EB + ".jpg"],
    "V002": [RT + ".jpg"],
    "V003": [J17 + ".jpg"],
    "V004": [J17 + ".jpg"],
    "V005": [PG + ".jpg"],
    "V006": [PG + ".jpg"],
    "V007": [GH + ".jpg"],
    "V008": [GH + ".jpg"],
    "V009": [EB + ".jpg"],
    "V010": [G + "V006_titles_stack.mp4"],
    "V011": [FW + "wikihow_zoom.mp4"],
    "V012": [FW + "mcseedmap_zoom.mp4"],
    "V013": [FW + "rarest_org_zoom.mp4"],
    "V014": [FW + "oldest_org_zoom.mp4"],
    "V015": [FW + "wikihow_zoom_final.png", FW + "mcseedmap_zoom_final.png", FW + "rarest_org_zoom_final.png",
             FW + "oldest_org_zoom_final.png"],
    "V016": [C + "seed_counter_0_to_215000.mp4", C + "peaks_orbit_1080p.mp4@5", C + "windswept_gravelly_hills_1080p.mp4@5",
             C + "ice_spikes_v2_1080p.mp4@5", C + "eroded_badlands_1080p.mp4@5", C + "pale_garden_v2_1080p.mp4@5"],
    "V017": [C + "seed_counter_final.png"],
    "C001": [C + "title_card_anim.mp4"],
    # 1. What rare means
    "V018": [O + "plains_v3_1080p.mp4@2"],
    "V019": [W + "forest_scroll.mp4"],
    "V020": [PG + ".mp4@2"],
    "V021": [M + "clumping_same_area_two_panels.png"],
    "V022": [M + "one_world_one_ray.mp4"],
    "V023": [M + "spawn_1080p.mp4"],
    "V024": [M + "spawn_heatmap_vs_random.png"],
    "V025": [M + "spawn_effect_bars.png"],
    "V028": [M + "spawn_effect_vs_distance.png"],
    "V029": [M + "spawn_1080p.mp4@4"],
    "V030": [M + "one_world_one_ray.mp4"],
    "V031": [M + "wander_vs_straight_ray.png"],
    # 1b. Why this definition (the owner's part). Generator: assets/_generator/justify.py
    "V032": [M + "spawn_1080p.mp4", M + "spawn_heatmap_vs_random.png"],
    "V034": [M + "player_path_anim.mp4"],
    "V035": [M + "grid_vs_ray_anim.mp4"],
    "V036": [M + "noise_vs_static.png", M + "grid_vs_ray_curves.png"],
    "V037": [M + "turn_settings.png"],
    "V038": [M + "three_ways_found.png"],
    "V039": [M + "spawn_1080p.mp4"],
    "V040": [R + "sight_band_32_chunks.png"],
    "V041": [R + "render_distance_32_1080p.mp4"],
    # 2. Monte Carlo
    "V042": [O + "dappled_forest_1080p.mp4@2"],
    "V043": [H + "darts_estimate_pi.mp4", H + "darts_estimate_pi_final.png"],
    "V044": [H + "one_world_one_ray.mp4", H + "one_world_one_ray_final.png"],
    "V045": [H + "many_worlds_grid.png", H + "running_average_settles_DEMO.png"],
    "V046": [H + "xpple_cubiomes.png", H + "cubiomes_vs_game.mp4"],
    # 3. How do I know
    "V047": [C + "title_card.png"],
    "V048": [N + "dot_grid_pale_garden_grid.png"],
    "V049": [N + "dot_grid_pale_garden_reveal.png"],
    "V050": [N + "dartboard_biased.png"],
    "V052": [GH + ".mp4@4"],
    "V053": [N + "old_ranking_1214.png"],
    "V054": [N + "old_ranking_1214_stamped.png"],
    "V055": [N + "dartboard_correct.png"],
    "V056": [N + "theory_md.png"],
    # 4. Countdown
    "V057": [O + "plains_v3_1080p.mp4@8"],
    "V058": [Q + "eroded_badlands_1080p.mp4@2"],
    "V059": [Q + "ice_spikes_v2_1080p.mp4@2"],
    "V060": [Q + "peaks_orbit_1080p.mp4@2"],
    "V061": [Q + "windswept_gravelly_hills_1080p.mp4@2"],
    "V062": [Q + "pale_garden_v2_1080p.mp4@2", Q + "pale_garden_drop_2_to_6_no1hidden.png"],
    "V064": [MUSH],
    "V065": [MUSH + "@10"],
    "V066": [Q + "SPOILER_mushroom_spawn_push.png"],
    "V067": [Q + "SPOILER_ranking_top20_step_on_it.png", Q + "mangrove_swamp_v5_1080p.mp4@4"],
    "V068": [R + "render_distance_8_1080p.mp4@2"],
    # 4b. Open your eyes
    "V069": [R + "render_distance_side_by_side_1080p.mp4@2"],
    "V070": [R + "pale_garden_v2_1080p.mp4@6"],
    "V071": [R + "SPOILER_three_radius_bars.png"],
    "V072": [R + "SPOILER_ranking_top20_8chunks.png"],
    "V073": [R + "SPOILER_slopegraph_rank_0_8_32.png"],
    "V074": [R + "SPOILER_ranking_top20_32chunks.png", R + "eroded_badlands_1080p.mp4@8", R + "wooded_badlands_v2_1080p.mp4@4"],
    "V075": [R + "SPOILER_table_three_radii.png"],
    "V076": [MUSH + "@12"],
    # 4c. Reading the ranking
    "V077": [Q + "SPOILER_ranking_all56_step_on_it.png"],
    "V078": [MUSH + "@4"],
    "V079": [Q + "SPOILER_mushroom_spawn_push.png"],
    "V080": [Q + "SPOILER_ranking_top20_step_on_it.png"],
    "V081": [O + "mangrove_swamp_v5_1080p.mp4", O + "mangrove_swamp_v5_1080p.mp4@6"],
    "V082": [O + "windswept_hills_v2_1080p.mp4@2", O + "cherry_grove_1080p.mp4@2", O + "dappled_forest_1080p.mp4@8"],
    "V083": [Q + "SPOILER_ranking_all56_step_on_it.png", O + "old_growth_spruce_taiga_1080p.mp4@2",
             O + "old_growth_pine_taiga_1080p.mp4@2", O + "sparse_jungle_1080p.mp4@2"],
    "V084": [R + "render_distance_8_1080p.mp4@10"],
    "V085": [O + "deep_dark_1080p.mp4@1", O + "ancient_city_1080p.mp4@1", O + "sulfur_caves_1080p.mp4@1",
             O + "dripstone_caves_1080p.mp4@1", O + "lush_caves_1080p.mp4@1"],
    "V087": [O + "plains_v3_1080p.mp4@10", O + "forest_v2_1080p.mp4@2"],
    "V089": [O + "river_v2_1080p.mp4", O + "river_v2_1080p.mp4@4"],
    "V090": [PG + ".mp4@26", GH + ".mp4@39", EB + ".mp4@32"],
    "V091": [MUSH + "@12"],
    # 5. Outro
    "V092": [MUSH + "@5"],
    "V093": [R + "render_distance_32_1080p.mp4@1"],
    "V094": ["05_outro/repo_page.png"],
    "V095": [M + "spawn_1080p.mp4@10"],
}

OVERLAY = {
    "V019": [G + "V011_trust_me_bro_stamp.png"],
    "V040": [G + "V032_nuanced.png"],
    "V041": [G + "V033_no_judgement.png"],
    "V045": [G + "V037_counter_1.png", G + "V037_counter_2.png"],
    "V049": [G + "V041_43_percent_oops.png"],
    "V091": [G + "V083_real_real_real_real_title.png"],
    "V058": [Q + "lowerthird_rank5_eroded_badlands.png"],
    "V059": [Q + "lowerthird_rank4_ice_spikes.png"],
    "V060": [Q + "lowerthird_rank3_stony_peaks.png", G + "V052_four_hours_for_this.png"],
    "V061": [Q + "lowerthird_rank2_windswept_gravelly_hills.png"],
    "V064": [G + "SPOILER_V056_crown.png", Q + "SPOILER_lowerthird_rank1_mushroom_fields.png"],
    "V085": [O + "note_caves_count_any_depth_overlay.png"],
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
