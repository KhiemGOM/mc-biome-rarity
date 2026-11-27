# Recording the voice-over

What to read: [`VO_READ.md`](VO_READ.md). It's the v4 script with only the spoken lines, numbered V001 to V087,
grouped by section. *(pause)* means take a beat before the next line. Don't say the numbers out loud.

## The short version (with the teleprompter)

1. **One-time setup:** open Audacity, Edit > Preferences > Modules, set **mod-script-pipe** to **Enabled**, restart
   Audacity. Set the project rate (bottom left) to **48000 Hz**.
2. Open Audacity (an empty project), then from `video/edit` start the teleprompter:
   ```
   .venv\Scripts\python -m vo.prompter part1
   ```
   or start from a later line: `.venv\Scripts\python -m vo.prompter part2 --from V034`
3. In the teleprompter window: **S** starts recording (record about 10 s of silence first, then press **R** to
   mark line 1 again), read the big line, **Space** for the next one. Flubbed it? **R** and read the line again. **Left**
   goes back a line. **S** again stops and saves `rec/part1.labels.json`. Then export the audio once: in Audacity
   **Ctrl+Shift+E**, save the whole project (don't trim anything) as `rec\part1.wav`. Audacity 3.7's scripted export
   fails on this PC, so the teleprompter reminds you. Esc quits.
4. Record in as many parts as you like (one Audacity project per part, close it without saving after the export). Then run the parts in script order:
   ```
   .venv\Scripts\python -m vo.run all rec\part1.wav rec\part2.wav rec\part3.wav
   ```
   With labels, every line is found exactly where you pressed the key, the last take wins, and changed wording or
   ad-libs are fine. Only lines you never reached show up as `MISSING`.
5. In Resolve: **File > Import > Timeline**, pick `video/edit/work/rough_cut.fcpxml`.

Tip: press Space right before you start the line, not after you finish the previous one mid-breath. The tool trims the
silence and the key click, so a small pause after the press is fine.

## Without the teleprompter (plain Audacity)

1. Open **Audacity** (already installed). Set the project rate (bottom left) to **48000 Hz** and the track to **mono**.
2. Record **10 seconds of silence** first (room tone, handy in the edit).
3. Read the script **in order**. Flub a line? Stop, breathe, and **re-read the whole line from the start**. Don't
   stop the recording. The pipeline keeps the last good take of every line and throws the rest away, chatter included.
4. Export: File > Export Audio > WAV, to `video/edit/rec/`. One file is fine, or one per section named
   `0.wav, 1.wav, 2.wav, 3.wav, 4.wav, 4b.wav, 4c.wav, 5.wav`.
5. Run (from `video/edit`):
   ```
   .venv\Scripts\python -m vo.run all rec\vo.wav
   ```
   or with section files, in script order:
   ```
   .venv\Scripts\python -m vo.run all rec\0.wav rec\1.wav rec\2.wav rec\3.wav rec\4.wav rec\4b.wav rec\4c.wav rec\5.wav
   ```
   It prints any line it couldn't find (`MISSING: V0xx`). Re-record just those lines and run it again with the extra file
   placed in order.
6. In Resolve: **File > Import > Timeline**, pick `video/edit/work/rough_cut.fcpxml`. You get the tight VO on A1, the
   visuals on V2, lower thirds and notes on V3, and a marker with the script line at every line start.

Before the real session, do a **2 minute test**: read section 2, run the pipeline, and listen to `work/vo_edit.wav`.
That catches level and noise problems before you've read 15 minutes.

## Sound

- **Room:** the smallest, softest room you have. A wardrobe full of clothes or a bed and curtains behind the mic kills
  echo better than anything you can buy. Avoid bare walls and desks right in front of you.
- **Noise:** close Unity, Opera, the game and any long runs. The laptop fans are the loudest thing in the room. Phone on
  silent, aircon off if you can stand it for 20 minutes.
- **Mic:** about a fist (10 to 15 cm) away, slightly off to the side of your mouth so "p" and "b" don't pop. A sock over
  the mic works as a pop filter.
- **Level:** loud lines should peak around **-12 dB** on Audacity's meter. Never touching 0. Too quiet is fixable, clipped
  is not.
- The pipeline already does high-pass, gentle denoise and YouTube loudness (-16 LUFS) for you. Don't add effects in
  Audacity.

## Performance

- **Energy up.** Read about 20% bigger than you'd talk to a friend. It sounds normal once it's under music.
- **Smile on the jokes.** You can hear it. The cold open, the camman bits, "four hours for this", "participation
  trophy" and "Fell off, honestly" want a grin.
- **Pauses are part of the joke.** Respect every *(pause)*, especially before "And number one." and after "Except.
  They're not the most common."
- **4c is you talking.** Those are your real reactions, so ad-lib if something better comes out. The pipeline matches
  lines loosely (about 80% of the words need to match). If you change a line a lot, it shows up as MISSING. That's
  fine, just tell me and I'll update the script to what you said.
- **Numbers:** read them the way the script spells them out ("two hundred and fifteen thousand").
- **Water:** sip between sections, not mid-line.
- If you're stiff at the start, do the cold open again at the end of the session and use the second take (record it
  as `0.wav` and keep the order in the command).

## Before you record

Two `[CHECK]`s in the script are still open:
- **Pink sheep odds** (section 3): 0.164 percent on the Minecraft Wiki, about 1 in 610. Check the current wiki page.
- **camman's distance method:** his short never says how he measured "average distance from spawn" (captions checked).
  The script doesn't describe his method, so it's safe either way.
