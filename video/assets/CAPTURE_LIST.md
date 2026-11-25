# Things to capture yourself (in game or on your PC)

These cannot be downloaded or faked. Everything here is real footage you record.

## The filming seed: 279 (Java 26.3)

Seed **279** has every featured biome within about 2,100 blocks of spawn (spawn is at 0, 0), so you can film the whole list in one world. Coordinates come from the cubiomes 26.3 port (surface layer, checked on a 24 block grid). Biome edges can be a few blocks off, so press F3 and check the biome line before you record. `/locate biome minecraft:<name>` in a creative copy of the world also works.

| Biome | Go to (x, z) | Distance from spawn | Used in | Filmed clip (best take) |
|---|---|---|---|---|
| Mushroom fields (do not show in the cold open as "the answer") | 1085, -1020 | 1,489 | 0 (quick cut), 4 #1 reveal | `SPOILER_mushroom_fields_v4_1080p.mp4` |
| Windswept gravelly hills | 1920, 840 | 2,096 | 0, 4 #2 | `windswept_gravelly_hills_1080p.mp4` |
| Stony peaks | -960, 48 | 961 | 0, 4 #3 | `peaks_orbit_1080p.mp4` |
| Ice spikes | 1440, 1368 | 1,986 | 0, 4 #4 | `ice_spikes_v2_1080p.mp4` |
| Eroded badlands | 624, -1560 | 1,680 | 0, 4 #5, 4b | `eroded_badlands_1080p.mp4` |
| Pale garden | -1680, 552 | 1,768 | 0, 3, 4 (falls to #6), 4b | `pale_garden_v2_1080p.mp4` |
| Mangrove swamp | 0, 0 (spawn) | 0 | 4 (#7 mention), 4c | `mangrove_swamp_v5_1080p.mp4` |
| Wooded badlands (a single small patch in seed 279) | -96, -624 | 631 | 4b | `wooded_badlands_v2_1080p.mp4` (weak) |
| Windswept hills | -384, 576 | 692 | 4c (vs cherry grove) | `windswept_hills_v2_1080p.mp4` |
| Cherry grove | -936, 744 | 1,196 | 4c (vs windswept hills) | `cherry_grove_1080p.mp4` |
| River | 72, -192 | 205 | 4c (line catcher) | `river_v2_1080p.mp4` |
| Plains | 24, 0 | 24 | 4c | `plains_v3_1080p.mp4` |
| Forest | -384, -168 | 419 | 4c | `forest_v2_1080p.mp4` |
| Dappled forest (new in 26.3) | 1464, 912 | 1,725 | 4c | `dappled_forest_1080p.mp4` |

Clips are in `D:\Coding\Minecraft\mc-capture\shots\` (about 100 MB each, not in git). Notes on every take are in [`footage/SHOTS.md`](footage/SHOTS.md). Keep the `SPOILER_` prefix on mushroom fields files until the reveal.

Mushroom fields was listed at 888, -1104 before filming. In game that point is open ocean with a ruined portal; the island is at about 1085, -1020. Wooded badlands is essentially one small patch at the edge of the sea.

Cave shots: deep dark sits under most tall mountains (try under stony peaks at -960, 48, around y -40). Ancient city: `/locate structure minecraft:ancient_city`. Sulfur caves, dripstone and lush caves: `/locate biome` from spawn, all within a few thousand blocks on average.

## Shot list

| # | Section | What to capture | Notes | Status |
|---|---|---|---|---|
| C1 | 0 cold open | Fast cuts of each candidate biome (table above), 1 to 2 s each | Do not linger on mushroom fields, no spoiler | Done (filmed): trim the cuts from the clips in the table above (about 20 s each) |
| C2 | 0 cold open | Forum posts and wiki pages each naming a different "rarest biome" | Screen record or screenshot in your browser. Blur usernames | |
| C3 | 1 | Spawning into a fresh world (the spawn moment) | Any seed, 26.3 | No clip listed in `footage/SHOTS.md` |
| C4 | 2, 3, 5 | Optional: scrolling screen recording of the GitHub repo and THEORY.md | Stills are already in `github_screens/` | No clip listed in `footage/SHOTS.md` |
| C9 | 4c, B-roll | Minecraft Wiki biome images | Save by hand, see `wiki_biome_images/SOURCES.md` (the wiki blocks scripted downloads) | |
| C5 | 4 | 5 to 10 s of each top 5 biome for the countdown, plus pale garden and mangrove | Seed 279 coordinates above | Done: `SPOILER_mushroom_fields_v4_1080p.mp4`, `windswept_gravelly_hills_1080p.mp4`, `peaks_orbit_1080p.mp4`, `ice_spikes_v2_1080p.mp4`, `eroded_badlands_1080p.mp4`, `pale_garden_v2_1080p.mp4`, `mangrove_swamp_v5_1080p.mp4` |
| C6 | 4b | Same spot shown at render distance 8 and then 32 | Optional, nice match for the sight band graphic | No clip listed in `footage/SHOTS.md` |
| C7 | 4c | Windswept hills next to cherry grove, deep dark plus an ancient city, a river crossing | Seed 279 | Partly done: `windswept_hills_v2_1080p.mp4` and `cherry_grove_1080p.mp4` (separate clips), `river_v2_1080p.mp4`. No deep dark or ancient city clip listed |
| C8 | 5 | Talking head or outro shot | Yours | |

## Could be generated later from cubiomes if you want them

- A top-down biome map of seed 279 with the filming spots marked (route planner).
- A real "area ranking vs walking ranking" chart (outline open item). Needs an area share run from the same seeds; the spawnratio file already has area shares, so this is a quick script if you want the punch.
- A patch size and count table on 26.3 (outline open item). Not generated, the old 1.21.4 one is superseded.
