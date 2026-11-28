# Edit plan (DaVinci Resolve 18.6)

No length target: quality first. Script: `video/VIDEO_SCRIPT.md` v4. Numbers on screen are Minecraft Java 26.3 only.

## How the edit is built

```
VIDEO_SCRIPT.md --(vo.run readscript)--> VO_READ.md --(you read it in Audacity)--> rec/*.wav
rec/*.wav --(vo.run all)--> work/vo_edit.wav (tight VO) + work/rough_cut.fcpxml --(File > Import > Timeline)--> Resolve
```

- **Cut list:** `make_cuts.py` (which file under which script line, in points, overlays). Edit it and run
  `.venv\Scripts\python make_cuts.py`, then `.venv\Scripts\python -m vo.run timeline` to rebuild the timeline without
  re-recording.
- **Bins:** `make_bins.ps1` hard-links the best assets into `media/<section>/`. Drag the folders into Resolve as bins.
- **Timeline:** 1920x1080, 60 fps. V1 empty (the import's base gap), V2 visuals, V3 overlays, A1 voice-over, a marker
  per script line. Keep everything named `SPOILER_` after V064 (the reveal).
- **Tools installed for this** (all local to `video/edit/`, git-ignored): `.venv` (faster-whisper on the GPU, rapidfuzz,
  num2words, pytest), `.tools/inter` (Inter font, same as the charts). Already on the PC: Resolve 18.6, Audacity 3.7,
  ffmpeg 9.
- **Watchable rough cut:** `.venv\Scripts\python make_preview.py` renders `work/rough_cut_preview.mp4` (visuals, overlays, VO, music) from the timeline; `--until 130` for a quick check, `--reuse-base` when only overlays or audio changed.
- **Tweak it in Resolve and keep the tweaks:** import `work/rough_cut.fcpxml` (File > Import > Timeline). A1 has one
  clip per script line, named V011, K003..., so you can drag lines apart for more room. Move shot edges, swap or add
  shots, trim camman's clips. Then File > Export > Timeline > FCPXML 1.9 into `work/`, and run
  `.venv\Scripts\python -m vo.tweaks import work\<export>.fcpxml`. Your edits go into `tweaks.json`, each anchored to
  a script line, and get applied on every rebuild (also after you record). Shots you don't touch keep following
  their lines. Color, effects, keyframes, transitions, titles and volume don't carry over: do those last, in Resolve.
- **Tests:** `.venv\Scripts\python -m pytest` in `video/edit` (parser, take picker, cut list, FCPXML).

## What the rough cut gives you, and what's left to do by hand in Resolve

The import places every visual and the VO. The finishing passes are yours, in this order:

1. **Picture fit:** stills come in scaled to fit. `SPOILER_ranking_all56_step_on_it.png` (V077, V083) is 1920x2160: add a
   slow vertical pan (Inspector > Transform, keyframe Position Y). Vertical camman clips: Inspector zoom to fill, or
   put them over a blurred copy of themselves.
2. **Motion on stills:** a slow push-in (zoom 1.00 to 1.06 over the shot) on every chart keeps them alive.
3. **Gags** (see the list below): Text+ titles and freeze frames.
4. **Music** is already on A2 (see below); add SFX.
5. **Color:** the game footage is clean, so a light contrast bump is enough. Pick one of the bright or `_dark` cave clips
   and use it for both.
6. **Credits in the description:** the music block below, "Images: Minecraft Wiki", camman18 video links
   (`assets/00_cold_open/camman18/SOURCES.md`), xpple/cubiomes.

## Gags (ready-made in `media/gags/`, already on the overlay track; restyle in Resolve if you like)

| Line | Gag |
|---|---|
| V010 | The five camman titles stack up one by one, each "real" popping in bigger, then a sixth slot types itself out: "the REAL, real, real, real rarest biome...?" |
| V019 | "SOURCE: trust me bro" stamp slams onto the wiki scroll |
| V031 | Tiny squiggly path doing loops next to the straight ray |
| V040 | "nuanced" flashes on screen |
| V041 | Small "no judgement" with a side-eye icon (on the 2b2t hack client line) |
| V045 | Corner counter: "worlds walked: 215,000", then "blocks walked: a lot" |
| V049 | "43%" slams on screen, small "oops" under it |
| V060 | Freeze frame on the most boring grey rock of the peaks clip, caption "four hours for this" |
| V058 to V062 | Countdown read in a top-ten-list announcer voice ("NUM-BER FIVE"), voice only, no other channel's branding |
| V064 | Crown drops onto the mushroom island |
| V091 | "the REAL, real, real, real rarest biome" title, styled like camman's, with your name |

## Music

Already on the timeline: `vo.run timeline` writes `work/music_bed.wav` (A2), one Kevin MacLeod track per section from
`video/edit/music/` (git-ignored), ducked about 22 dB under the voice, up between lines, faded at each section change.
Cue points are markers named `MUSIC: ...`. To swap a track, drop `<section>_<title>.mp3` in `music/` (remove the old
one) and rerun `vo.run timeline`. Cues, duck level and per-section level are at the top of `vo/music.py`. Do not use
C418 or Lena Raine (Minecraft's own music gets Content ID claimed).

| Section | Track | Cue |
|---|---|---|
| 0 Cold open | Fluffing a Duck | Hard stop after "Proven, within a margin I get to pick.", title card in silence |
| 1 What rare means | Easy Lemon | |
| 2 Monte Carlo | Investigations | |
| 3 How do I know | Thinking Music | Cut after "...my generator was running." (add a record scratch SFX there), back on "Lesson learned" |
| 4 Countdown | Volatile Reaction | Silence from "And number one." to the reveal, comes back on "Mushroom fields." (add a hit SFX) |
| 4b Open your eyes | Airport Lounge | |
| 4c Reading the ranking | Local Forecast - Elevator | 30% quieter, this is you talking |
| 5 Outro | Inspired | |

SFX worth adding by hand: whoosh (cuts between biomes), record scratch, soft "ding" for each rank, a low thud for slams.

**Description credits (required, CC BY 4.0):**

```
Music by Kevin MacLeod (incompetech.com), licensed under Creative Commons: By Attribution 4.0
http://creativecommons.org/licenses/by/4.0/
"Fluffing a Duck", "Easy Lemon", "Investigations", "Thinking Music", "Volatile Reaction",
"Airport Lounge", "Local Forecast - Elevator", "Inspired"
```

## Gaps

- **VO:** not recorded yet. See `VO_GUIDE.md`.
- **C8:** talking head for the outro (optional, the cut works without it).
- **Filled 2026-11-28:** V015 forum and wiki screenshots (`assets/00_cold_open/forum_wiki/`, sources and credits in its
  SOURCES.md).
- **Filled 2026-11-28:** section 1 "why this definition" visuals (player path, grid walk vs straight line on a real
  world plus the 400-world comparison chart, noise vs static, made-up turn settings, three ways to count "found"), V046
  Cubiomes vs the real game (seed 279 river orbit, dot synced to the clip), and the gag overlays. Generator:
  `assets/_generator/justify.py`, numbers in `assets/_generator/out/walk_compare.json`.
- **Filled 2026-11-27:** old growth spruce and pine taiga and sparse jungle (V083), sulfur, dripstone and lush caves
  (V086). See `assets/footage/SHOTS.md`.
