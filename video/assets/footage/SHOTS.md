# Footage shot list (seed 279, Minecraft 26.3)

All clips: 1920x1080, 60 fps, about 20 s, H.264 (NVENC, 40 Mbit/s), no audio, HUD hidden, daytime, clear weather.
Each is a camera path (Flashback keyframes) over a live recording in the `capture279` world. Sizes are about 100 MB each.
Frames of every clip were checked before listing. `SPOILER_` files show the mushroom fields biome: keep that prefix until the reveal.

## Best file per biome

| Biome | Best file | Quality | Notes |
|---|---|---|---|
| Stony peaks | `peaks_orbit_1080p.mp4` | OK | In this world it is a modest grey ridge on savanna hills (top about y=140), not a dramatic mountain. Orbit at y=170 under the clouds. |
| Windswept gravelly hills | `windswept_gravelly_hills_1080p.mp4` | OK, mild | Gentle green hills with grey gravel patches and a lake. Less dramatic than the name suggests (terrain tops out near y=80). |
| Ice spikes | `ice_spikes_v2_1080p.mp4` | Great | Tall blue spikes are the hero. `ice_spikes_1080p.mp4` is weaker (snow mountain dominates). `ice_spikes_close_1080p.mp4` is a failed re-shoot of the same view: ignore. |
| Eroded badlands | `eroded_badlands_1080p.mp4` | Great | Striped red and orange spires on an island in turquoise water. |
| Pale garden | `pale_garden_v2_1080p.mp4` | Great | Grey pale oak canopy and grey sky. `pale_garden_1080p.mp4` is mostly dark forest: skip. |
| Mangrove swamp | `mangrove_swamp_v5_1080p.mp4` | OK | Forward flight 9 blocks over the canopy, with rock arches and sky. The swamp is dense canopy in this world. Alternates: `_v3` (closer orbit), `_v2`, base. `_v4` (low flight) is unusable: the camera is inside leaves. |
| Wooded badlands | `wooded_badlands_v2_1080p.mp4` | Weak | This world has essentially one small patch near (-96, -624), at the edge of the sea. Shots are mostly ocean with a terracotta and sand island. `_v3` is identical to `_v2` (a 2000x2000 search found nothing else). |
| Windswept hills | `windswept_hills_v2_1080p.mp4` | Good | Snow-capped rocky peaks over green hills. The base version has no mountain: skip. |
| Cherry grove | `cherry_grove_1080p.mp4` | Good | Clear pink cherry trees on a hill. |
| River | `river_v2_1080p.mp4` | Good | Wide river with jungle on one bank and meadow on the other. |
| Plains | `plains_v3_1080p.mp4` | Good | Big grassy plain with animals and a few rock spires. `_v2` clips into a hillside in one frame: skip. |
| Forest | `forest_v2_1080p.mp4` | Good | Oak and birch forest down to a lake. The base version is mostly mangrove canopy: skip. |
| Dappled forest (new in 26.3) | `dappled_forest_1080p.mp4` | Good | Red, orange and yellow autumn trees on a river island, villages nearby. |
| Mushroom fields | `SPOILER_mushroom_fields_v4_1080p.mp4` | Great | Real island: mycelium, giant red and brown mushrooms. `_v1` to `_v3` show a ruined portal in open ocean (wrong subject): ignore. |

## Extra shots (filmed 2026-11-26)

All 1920x1080, 60 fps, no audio, HUD hidden. Each has a `_sheet.png` check sheet.

| Shot | Best file | Length | Notes |
|---|---|---|---|
| C3 spawn moment | `spawn_1080p.mp4` | 20.0 s | Fresh creative world `spawnshot3`, seed 729643423878493032. First-person look from the spawn point (-628.5, 70, 178.5): savanna hill, turning round to the ocean. |
| C6 render distance 32 | `render_distance_32_1080p.mp4` | 19.7 s | Seed 279, camera from (624, 125, -1215) to z=-1255 looking north. The eroded badlands mesa is on the horizon. |
| C6 render distance 8 | `render_distance_8_1080p.mp4` | 19.7 s | Same recording and camera path as the 32 clip, frame for frame. Only ocean and fog. |
| C6 side by side | `render_distance_side_by_side_1080p.mp4` | 19.7 s | Centre half of each clip, 8 chunks left and 32 right, with labels. |
| C7 ancient city | `ancient_city_1080p.mp4` | 19.3 s | Fly-in to the centre frame of the city at about (-1104, 176). Night vision, plus a light brightening (gamma 1.2) in the edit. |
| C7 ancient city, darker | `ancient_city_dark_1080p.mp4` | 19.3 s | Same shot without the brightening. |
| C7 deep dark cave | `deep_dark_1080p.mp4` | 19.3 s | Natural sculk cave under the stony peaks, from (-896, -42, 68) towards (-915, -43, 45), gliding towards a shrieker. Night vision, gamma 1.25. |
| C7 deep dark cave, darker | `deep_dark_dark_1080p.mp4` | 19.3 s | Same shot without the brightening. |

Notes for re-shoots:
- New `capturectl` commands: `rd <chunks>`, `nightvision on|off` (inside a replay), `newworld <folder> <seed>`, `leave`. The old jar and source are kept in `mod\` as `.bak`.
- Raising the render distance only reaches the game's internal server after leaving and rejoining the world.
- The recorded player is moved far above the shot before or just after recording starts, or its head shows up in frame.
- The first frames of an export can show a loading haze (worst underground, up to about 40 frames), so the render distance and cave clips have their starts trimmed. Those trimmed files are re-encoded with libx264, because the system `ffmpeg` cannot use NVENC with this driver.
- Scripts in `tools\`: `spawn.mjs`, `join.mjs`, `record.mjs`, `export.mjs` (takes a job file from `tmp\jobs\`), `scout.mjs`, `shots_at.mjs`, `airmap.mjs` and `clear.mjs` (checks that a camera path stays out of blocks).
- Unused takes you can delete: replays `spawn`, `spawn_b`, `render_distance` and worlds `spawnshot1`, `spawnshot2`.

## Known problems
- The listed coordinates in `video/assets/CAPTURE_LIST.md` are single points. Several biomes are thin patches there, so each shot was re-centred on the densest nearby patch (`execute if biome` grid, 24 block spacing).
- Wooded badlands and mushroom fields are tiny in this world. Mushroom fields is at about (1085, -1020), not (888, -1104): the listed point is open ocean with a ruined portal.
- Terrain near spawn (x -512..511, z -512..1023) had old random-seed chunks in an early copy of the world. They were deleted and regenerated before the clips listed above were recorded.

## How these were made (for re-shoots)
- Game: `mc-capture` (Fabric 26.3, Sodium, Flashback, MCPFabric, own `capturectl` mod). Launch with `mc-capture\start-capture.ps1`.
- Driver: `mc-capture\tools\shoot.mjs` (`node shoot.mjs record|export|all [name]`). It records live in the world, adds a 9-keyframe orbit, hides the HUD and exports. Log: `mc-capture\ctl\shoot.log`; per-shot data: `mc-capture\ctl\shots.json`.
- Only the command line and in-game APIs are used: no mouse, keyboard or desktop screenshots.
