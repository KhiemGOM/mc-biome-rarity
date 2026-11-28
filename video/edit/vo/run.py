"""Voice-over pipeline. Run from video/edit with the venv python:

  .venv\\Scripts\\python -m vo.run readscript            # VO_READ.md (teleprompter) + work/lines.json
  .venv\\Scripts\\python -m vo.run scratch               # robot scratch VO (offline Windows voice), for testing the cut
  .venv\\Scripts\\python -m vo.run align <rec.wav ...>   # clean, transcribe, keep the last good take of each line,
                                                       # write work/vo_edit.wav (tight VO) + work/vo_edit_map.json
  .venv\\Scripts\\python -m vo.run timeline              # work/rough_cut.fcpxml from cuts.csv + work/music_bed.wav
  .venv\\Scripts\\python -m vo.run all <rec.wav ...>     # align + timeline
"""
import array, json, os, subprocess, sys, wave
from .script_lines import parse, read_script
from .cuts import load, load_overlays, overlay_segments, segments
from .timeline import Clip, build_fcpxml
from . import tweaks as tw

EDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(EDIT, "..", "VIDEO_SCRIPT.md")
WORK = os.path.join(EDIT, "work")
MEDIA = os.path.join(EDIT, "media")
CUTS = os.path.join(EDIT, "cuts.csv")
TWEAKS = os.path.join(EDIT, "tweaks.json")   # edits read back from Resolve (vo.tweaks import)
SR = 48000
GAP, PAUSE, PAD = 0.70, 1.20, 0.06      # seconds between lines, after a [beat], kept around each take
CLIP_GAP = 1.00                          # seconds before and after one of camman's clips (a beat to react)
SECTION_GAP = 1.50                       # before a new section starts
DISSOLVE, SECTION_DISSOLVE = 0.4, 0.8    # cross dissolve between shots, and into a new section
JUMP_GAP = 0.10                          # between two clips from the same video: one jump-cut sentence
CARD = {"title card": 4.0}               # silent cards, by words in their visual; default 3 s
STILLS = (".png", ".jpg", ".jpeg")
PROMPT = ("Minecraft, camman18, mushroom fields, windswept gravelly hills, eroded badlands, stony peaks, ice spikes, "
          "pale garden, mangrove swamp, cherry grove, dappled forest, deep dark, ancient city, Cubiomes, Monte Carlo, SMP.")


def gap_after(it, nxt):
    """Silence after item `it` when `nxt` comes next (None at the end)."""
    g = CLIP_GAP if it.kind == "clip" or (nxt is not None and nxt.kind == "clip") else GAP
    if it.kind == "clip" and nxt is not None and nxt.kind == "clip" and it.clip[0] == nxt.clip[0]:
        g = JUMP_GAP
    if nxt is not None and nxt.section != it.section:
        g = max(g, SECTION_GAP)
    return max(g, PAUSE) if it.pause_after else g


def items():
    return parse(open(SCRIPT, encoding="utf-8").read())


def card_len(it):
    v = " ".join(it.visuals).lower()
    return next((d for k, d in CARD.items() if k in v), 3.0)


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *args], check=True)


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def read_pcm(path):
    with wave.open(path) as w:
        assert w.getframerate() == SR and w.getnchannels() == 1 and w.getsampwidth() == 2, path
        a = array.array("h"); a.frombytes(w.readframes(w.getnframes()))
    return a


def write_pcm(path, a):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(a.tobytes())


def cmd_readscript():
    os.makedirs(WORK, exist_ok=True)
    its = items()
    open(os.path.join(EDIT, "VO_READ.md"), "w", encoding="utf-8").write(read_script(its))
    json.dump([it.__dict__ for it in its], open(os.path.join(WORK, "lines.json"), "w"), indent=1)
    print(f"VO_READ.md: {sum(i.kind == 'vo' for i in its)} lines")


def cmd_scratch(retake="V010"):
    """Offline robot read of every line (Windows SAPI), with one flub + retake to exercise the take picker."""
    os.makedirs(WORK, exist_ok=True)
    vo = [i for i in items() if i.kind == "vo"]
    todo = []
    for it in vo:
        if it.id == retake:
            todo.append(" ".join(it.text.split()[:4]) + ". Uh, wait, let me redo that.")
        todo.append(it.text)
    tmp = os.path.join(WORK, "scratch_parts"); os.makedirs(tmp, exist_ok=True)
    json.dump(todo, open(os.path.join(tmp, "lines.json"), "w", encoding="utf-8"))
    ps = (f"Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Rate = 1; "
          f"$l = Get-Content -Raw -Encoding UTF8 '{tmp}\\lines.json' | ConvertFrom-Json; $i = 0; "
          f"foreach ($t in $l) {{ $s.SetOutputToWaveFile(('{tmp}\\{{0:D3}}.wav' -f $i)); $s.Speak($t); $i++ }}; $s.Dispose()")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
    parts = []
    for k in range(len(todo)):
        p = os.path.join(tmp, f"{k:03d}.wav"); q = p.replace(".wav", "_48k.wav")
        ffmpeg("-i", p, "-ar", str(SR), "-ac", "1", "-sample_fmt", "s16", q)
        parts.append(read_pcm(q))
    out = array.array("h")
    for a in parts:
        out.extend(a); out.extend(array.array("h", bytes(2 * int(SR * 0.9))))  # sloppy 0.9 s gaps, like a real session
    write_pcm(os.path.join(WORK, "scratch_raw.wav"), out)
    print(f"work/scratch_raw.wav: {len(out) / SR:.0f} s, {len(todo)} reads (flub + retake on {retake})")


def transcribe(wav):
    cache = wav + ".words.json"
    if os.path.exists(cache) and os.path.getmtime(cache) > os.path.getmtime(wav):
        return json.load(open(cache))
    # CUDA libraries come from the pip nvidia-* wheels in the venv: put their bin folders on the DLL path
    import site
    for sp in site.getsitepackages():
        for sub in ("cublas", "cudnn"):
            b = os.path.join(sp, "nvidia", sub, "bin")
            if os.path.isdir(b):
                os.add_dll_directory(b)
                os.environ["PATH"] = b + os.pathsep + os.environ["PATH"]
    from faster_whisper import WhisperModel
    try:
        model = WhisperModel("large-v3", device="cuda", compute_type="float16")
    except Exception as e:  # no usable CUDA: CPU is slower but fine
        print("GPU unavailable, using CPU:", str(e)[:120])
        model = WhisperModel("medium.en", device="cpu", compute_type="int8")
    # decode with ffmpeg ourselves (faster-whisper's PyAV loader breaks on newer PyAV): 16 kHz mono float32
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", wav, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    audio = np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0
    segs, _ = model.transcribe(audio, language="en", word_timestamps=True, vad_filter=False, initial_prompt=PROMPT,
                               condition_on_previous_text=False)
    words = [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]
    json.dump(words, open(cache, "w"))
    return words


def cmd_align(*recs):
    os.makedirs(WORK, exist_ok=True)
    if len(recs) == 1:
        rec = recs[0]
    else:  # one file per section: join them in the order given
        rec = os.path.join(WORK, "rec_joined.wav")
        lst = os.path.join(WORK, "rec_list.txt")
        open(lst, "w", encoding="utf-8").write("".join(f"file '{os.path.abspath(r)}'\n" for r in recs))
        ffmpeg("-f", "concat", "-safe", "0", "-i", lst, "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s24le", rec)
    clean = os.path.join(WORK, "vo_clean.wav")
    # high-pass rumble, gentle denoise, broadcast loudness (-16 LUFS, peaks under -1.5 dBTP)
    ffmpeg("-i", rec, "-ac", "1", "-ar", str(SR), "-af",
           "highpass=f=80,afftdn=nf=-25,loudnorm=I=-16:TP=-1.5:LRA=11", "-sample_fmt", "s16", clean)
    its = items()
    ids = [i.id for i in its if i.kind == "vo"]
    src = read_pcm(clean)
    lab = [os.path.splitext(r)[0] + ".labels.json" for r in recs]
    if all(os.path.exists(p) for p in lab):  # recorded with the teleprompter: labels say where every line is
        from .labels import label_takes
        files = [([tuple(x) for x in json.load(open(p))["labels"]], probe(r)) for p, r in zip(lab, recs)]
        res, missing = label_takes(files, ids, src, SR)
        print(f"using teleprompter labels from {len(files)} file(s)")
    else:
        if any(os.path.exists(p) for p in lab):
            print("note: only some recordings have teleprompter labels, so transcribing all of them instead")
        words = transcribe(clean)
        from .align import align
        res, missing = align([(i.id, i.text) for i in its if i.kind == "vo"], words)
    tweaks = tw.load(TWEAKS)
    out, edit_map, t = array.array("h"), {}, 0.0
    fade = int(0.01 * SR)
    for k, it in enumerate(its):
        nxt = its[k + 1] if k + 1 < len(its) else None
        if it.kind == "card":
            n = int(card_len(it) * SR)
            edit_map[it.id] = (t, t + n / SR); out.extend(array.array("h", bytes(2 * n))); t += n / SR
            continue
        if it.kind == "clip":  # someone else's video: its own audio goes in the voice-over track
            from .clips import clip_audio, fade_edges, find_clip
            seg = array.array("h"); seg.frombytes(clip_audio(os.path.join(MEDIA, find_clip(MEDIA, it.clip[0])), it.clip[1], it.clip[2], SR))
            seg = fade_edges(seg, SR, 0.05)  # his background music must not snap on or off
        elif it.id not in res:
            continue
        else:
            a, b = res[it.id]
            i0, i1 = max(0, int((a - PAD) * SR)), min(len(src), int((b + PAD) * SR))
            seg = src[i0:i1]
        for k in range(min(fade, len(seg))):  # 10 ms fades: no clicks at the cuts
            g = k / fade; seg[k] = int(seg[k] * g); seg[-1 - k] = int(seg[-1 - k] * g)
        edit_map[it.id] = (t, t + len(seg) / SR)
        out.extend(seg); t += len(seg) / SR
        gap = int(max(0.0, tw.gap_for(it.id, gap_after(it, nxt), tweaks)) * SR)
        out.extend(array.array("h", bytes(2 * gap))); t += gap / SR
    write_pcm(os.path.join(WORK, "vo_edit.wav"), out)
    json.dump({"source": os.path.abspath(rec), "recs": [os.path.abspath(r) for r in recs], "takes": res, "edit": edit_map, "missing": missing, "length": t},
              open(os.path.join(WORK, "vo_edit_map.json"), "w"), indent=1)
    print(f"work/vo_edit.wav: {t / 60:.1f} min, {len(res)} lines kept")
    if missing:
        print("MISSING (not found in the recording, re-record these):", ", ".join(missing))


def cmd_timeline():
    m = json.load(open(os.path.join(WORK, "vo_edit_map.json")))
    its = items()
    times = {k: tuple(v) for k, v in m["edit"].items()}
    from .clips import clip_cuts
    cuts = {**load(CUTS), **clip_cuts(its, MEDIA)}
    order = [i.id for i in its]
    keyed = [k + (1,) for k in segments(order, times, cuts, end=m["length"], keys=True)]
    keyed += [k + (2,) for k in overlay_segments(order, times, load_overlays(CUTS), keys=True)]
    keyed, tnotes = tw.apply_visuals_keyed(keyed, tw.load(TWEAKS), times)
    for key, rel, *_ in keyed:
        if not os.path.exists(os.path.join(MEDIA, rel)):
            raise FileNotFoundError(f"cuts.csv or tweaks.json: {rel} is not in video/edit/media (run make_bins.ps1?)")
    # dissolve into every shot, a longer one where a new section starts
    sec_of, trans, prev = {i.id: i.section for i in its}, {}, None
    for key, rel, src_in, a, b, lane in sorted((k for k in keyed if k[5] == 1), key=lambda k: k[3]):
        here = sec_of.get(key.split("#")[0], prev)
        trans[key] = SECTION_DISSOLVE if prev is not None and here != prev else DISSOLVE
        prev = here
    # stills on the main track get a slow push-in, baked into a clip per shot
    from .motion import pad, pad_needed, render_all
    jobs = [(os.path.join(MEDIA, rel), b - a) for key, rel, src_in, a, b, lane in keyed if lane == 1 and rel.lower().endswith(STILLS)]
    print(f"push-ins: {len(set(jobs))} stills (cached in work/motion)")
    motion = render_all(jobs, os.path.join(WORK, "motion"))
    clips, durs = [], {}
    for key, rel, src_in, a, b, lane in keyed:
        p = os.path.join(MEDIA, rel)
        kind = "still" if p.lower().endswith(STILLS) else "video"
        if kind == "still" and lane == 1:
            p, src_in, sd = motion[(os.path.join(MEDIA, rel), b - a)]
            kind, durs[p] = "video", sd
        if kind == "video" and p not in durs:
            durs[p] = probe(p)
        if kind == "video" and lane == 1:  # no spare footage for the dissolve, or too short for its slot: hold a frame
            head, tail = pad_needed(src_in, b - a, durs[p])
            if head or tail:
                p = pad(p, head, tail, os.path.join(WORK, "padded"))
                src_in += head
                if p not in durs:
                    durs[p] = probe(p)
        clips.append(Clip(p, a, b, kind=kind, src_dur=durs.get(p, 0.0), src_in=src_in, lane=lane, key=key,
                          trans_in=trans.get(key, 0.0)))
    marks = [(times[i.id][0], f"{i.id} {i.text[:60]}") for i in its if i.id in times and i.kind == "vo"]
    from .music import render_bed
    bed = os.path.join(WORK, "music_bed.wav")
    cues, notes = render_bed(its, times, m["length"], os.path.join(EDIT, "music"), bed)
    xml, warnings = build_fcpxml(clips, vo=(os.path.join(WORK, "vo_edit.wav"), m["length"]),
                                 name="Rarest biome rough cut", markers=sorted(marks + cues),
                                 audio=[(bed, m["length"], -2, "music bed")],
                                 vo_pieces=[(a, b, a, i) for i, (a, b) in sorted(times.items(), key=lambda x: x[1][0])])
    out = os.path.join(WORK, "rough_cut.fcpxml")
    open(out, "w", encoding="utf-8").write(xml)
    print(f"work/rough_cut.fcpxml: {len(clips)} visuals, {len(marks)} line markers, {m['length'] / 60:.1f} min")
    for w in tnotes + notes + warnings:
        print("  note:", w)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    {"readscript": lambda: cmd_readscript(), "scratch": lambda: cmd_scratch(),
     "align": lambda: cmd_align(*a[1:]), "timeline": lambda: cmd_timeline(),
     "all": lambda: (cmd_align(*a[1:]), cmd_timeline())}[a[0]]()
