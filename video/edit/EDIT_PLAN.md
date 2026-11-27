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
  per script line. Keep everything named `SPOILER_` after V056 (the reveal).
- **Tools installed for this** (all local to `video/edit/`, git-ignored): `.venv` (faster-whisper on the GPU, rapidfuzz,
  num2words, pytest), `.tools/inter` (Inter font, same as the charts). Already on the PC: Resolve 18.6, Audacity 3.7,
  ffmpeg 9.
- **Tests:** `.venv\Scripts\python -m pytest` in `video/edit` (parser, take picker, cut list, FCPXML).

## What the rough cut gives you, and what's left to do by hand in Resolve

The import places every visual and the VO. The finishing passes are yours, in this order:

1. **Picture fit:** stills come in scaled to fit. `SPOILER_ranking_all56_step_on_it.png` (V069, V075) is 1920x2160: add a
   slow vertical pan (Inspector > Transform, keyframe Position Y). Vertical camman clips: Inspector zoom to fill, or
   put them over a blurred copy of themselves.
2. **Motion on stills:** a slow push-in (zoom 1.00 to 1.06 over the shot) on every chart keeps them alive.
3. **Gags** (see the list below): Text+ titles and freeze frames.
4. **Music and SFX** (cue sheet below).
5. **Color:** the game footage is clean, so a light contrast bump is enough. Pick one of the bright or `_dark` cave clips
   and use it for both.
6. **Credits in the description:** "Images: Minecraft Wiki", camman18 video links
   (`assets/00_cold_open/camman18/SOURCES.md`), xpple/cubiomes.

## Gags to build (Text+ / freeze frame)

| Line | Gag |
|---|---|
| V006 | The five camman titles stack up one by one, each "real" popping in bigger, then a sixth slot types itself out: "the REAL, real, real, real rarest biome...?" |
| V011 | "SOURCE: trust me bro" stamp slams onto the wiki scroll |
| V023 | Tiny squiggly path doing loops next to the straight ray |
| V032 | "nuanced" flashes on screen |
| V033 | Small "no judgement" with a side-eye icon (on the 2b2t hack client line) |
| V037 | Corner counter: "worlds walked: 215,000", then "blocks walked: a lot" |
| V041 | "43%" slams on screen, small "oops" under it |
| V052 | Freeze frame on the most boring grey rock of the peaks clip, caption "four hours for this" |
| V050 to V054 | Countdown read in a top-ten-list announcer voice ("NUM-BER FIVE"), voice only, no other channel's branding |
| V056 | Crown drops onto the mushroom island |
| V083 | "the REAL, real, real, real rarest biome" title, styled like camman's, with your name |

## Music cue sheet

Source: **YouTube Audio Library** (YouTube Studio > Audio Library). Free and cleared for monetized videos, so no
Content ID claims. Filter by mood and download the WAV. Do not use C418 or Lena Raine (Minecraft's own music is
copyrighted and gets claimed).

| Section | Mood | Notes |
|---|---|---|
| 0 Cold open | Upbeat, quirky, fast | Hard stop on "Proven." then hit the title card |
| 1 What rare means | Light, curious | Drop the volume under the spawn charts |
| 2 Monte Carlo | Playful (pizzicato, marimba) | |
| 3 How do I know | Starts confident, then tense | Record scratch and music cut on "It was 1.21.4." |
| 4 Countdown | Building, drum-led | Silence for "And number one.", big hit on the mushroom reveal |
| 4b Open your eyes | Chill, open | |
| 4c Reading the ranking | Lo-fi, conversational | Keep it low, this is you talking |
| 5 Outro | Warm, resolved | |

SFX worth having: whoosh (cuts between biomes), record scratch, soft "ding" for each rank, a low thud for slams.
The Audio Library has a sound effects tab.

## Gaps

- **VO:** not recorded yet. See `VO_GUIDE.md`.
- **C2:** forum and wiki posts for V007. Stopgap in the cut: four wiki scroll clips.
- **C8:** talking head for the outro (optional, the cut works without it).
- **Section 1 "why this definition" (V024 to V033, added 2026-11-28):** needs a player path heading one way across a
  biome map, a lawnmower grid path vs one straight ray, and smooth noise vs random static with the grid re-hitting the
  same biomes. Stopgaps from existing section 1 and 4b assets are in the cut.
- **V038:** side by side Cubiomes map and real game footage at the same coordinates, a dot following the camera.
- **Mushroom crown (V056):** a crown graphic over the reveal clip.
- **Filled 2026-11-27:** old growth spruce and pine taiga and sparse jungle (V075), sulfur, dripstone and lush caves
  (V078). See `assets/footage/SHOTS.md`.
