# Builds video/edit/media/<section>/ as hard links to the best assets and takes, ready to drag into DaVinci Resolve
# (one folder = one bin). Hard links take no extra disk space. Re-run any time: existing links are skipped.
# Source of truth for what goes where: video/assets/INDEX.md and mc-capture/shots/SHOTS.md.
$ErrorActionPreference = 'Stop'
$repo  = Resolve-Path "$PSScriptRoot\..\.."
$A     = Join-Path $repo 'video\assets'
$S     = 'D:\Coding\Minecraft\mc-capture\shots'
$media = Join-Path $PSScriptRoot 'media'

# bin -> list of source files (absolute, or relative to video/assets)
$bins = [ordered]@{
  '00_cold_open' = @(
    '00_cold_open\seed_counter_0_to_215000.mp4', '00_cold_open\seed_counter_final.png', '00_cold_open\title_card*',
    '00_cold_open\camman18\*.mp4', '00_cold_open\camman18\*.jpg',
    "$S\peaks_orbit_1080p.mp4", "$S\windswept_gravelly_hills_1080p.mp4", "$S\ice_spikes_v2_1080p.mp4",
    "$S\eroded_badlands_1080p.mp4", "$S\pale_garden_v2_1080p.mp4", "$S\SPOILER_mushroom_fields_v4_1080p.mp4")
  '01_what_is_rare' = @('01_what_is_rare\*.png', '01_what_is_rare\*.mp4', "$S\spawn_1080p.mp4", '02_monte_carlo\one_world_one_ray.mp4')
  'gags' = @('gags\*.png', 'gags\*.mp4')
  '02_monte_carlo'  = @('02_monte_carlo\*.mp4', '02_monte_carlo\*.png', 'github_screens\xpple_cubiomes.png')
  '03_how_do_i_know' = @('03_how_do_i_know\*.png', 'github_screens\theory_md.png')
  '04_countdown' = @(
    '04_countdown\*.png',
    "$S\eroded_badlands_1080p.mp4", "$S\ice_spikes_v2_1080p.mp4", "$S\peaks_orbit_1080p.mp4",
    "$S\windswept_gravelly_hills_1080p.mp4", "$S\SPOILER_mushroom_fields_v4_1080p.mp4",
    "$S\pale_garden_v2_1080p.mp4", "$S\mangrove_swamp_v5_1080p.mp4")
  '04b_open_your_eyes' = @(
    '04b_open_your_eyes\*.png',
    "$S\render_distance_8_1080p.mp4", "$S\render_distance_32_1080p.mp4", "$S\render_distance_side_by_side_1080p.mp4",
    "$S\eroded_badlands_1080p.mp4", "$S\pale_garden_v2_1080p.mp4", "$S\wooded_badlands_v2_1080p.mp4")
  '04c_reading_the_ranking' = @(
    '04c_reading_the_ranking\*.png',
    "$S\mangrove_swamp_v5_1080p.mp4", "$S\windswept_hills_v2_1080p.mp4", "$S\cherry_grove_1080p.mp4",
    "$S\river_v2_1080p.mp4", "$S\plains_v3_1080p.mp4", "$S\forest_v2_1080p.mp4", "$S\dappled_forest_1080p.mp4",
    "$S\deep_dark_1080p.mp4", "$S\deep_dark_dark_1080p.mp4", "$S\ancient_city_1080p.mp4", "$S\ancient_city_dark_1080p.mp4",
    "$S\old_growth_spruce_taiga_1080p.mp4", "$S\old_growth_pine_taiga_1080p.mp4", "$S\sparse_jungle_1080p.mp4",
    "$S\sulfur_caves_1080p.mp4", "$S\dripstone_caves_1080p.mp4", "$S\lush_caves_1080p.mp4")
  '05_outro' = @('github_screens\repo_page.png')
  '_wiki_scrolls' = @('wiki_scrolls\*.mp4', 'wiki_scrolls\*.png')
}

$made = 0; $missing = @()
foreach ($bin in $bins.Keys) {
  $dir = Join-Path $media $bin
  New-Item -ItemType Directory -Force $dir | Out-Null
  foreach ($pat in $bins[$bin]) {
    $full = if ([IO.Path]::IsPathRooted($pat)) { $pat } else { Join-Path $A $pat }
    $hits = @(Get-ChildItem -Path $full -File -ErrorAction SilentlyContinue)
    if ($hits.Count -eq 0) { $missing += "$bin <- $pat"; continue }
    foreach ($f in $hits) {
      $dst = Join-Path $dir $f.Name
      if (Test-Path -LiteralPath $dst) { continue }
      New-Item -ItemType HardLink -Path $dst -Target $f.FullName | Out-Null
      $made++
    }
  }
}
"linked $made new files into $media"
if ($missing.Count) { "MISSING:"; $missing | ForEach-Object { "  $_" }; exit 1 }
