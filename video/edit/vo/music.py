"""Music bed for the rough cut: one track per section (video/edit/music/<section>_*.mp3), ducked under the voice-over,
muted on the cue lines, faded at every section change. Written to work/music_bed.wav and placed on A2.

Cue lines are found by a piece of their text, not their ID, so renumbering the script doesn't break them."""
import glob, os, subprocess, wave
import numpy as np

CR = 100                 # control rate of the gain curve, Hz
DUCK, OPEN = 0.14, 0.4   # music gain under speech / with nobody talking (tracks are first normalised to -20 LUFS)
HOLD = 1.5               # gaps between lines shorter than this stay ducked (no pumping)
ATTACK, RELEASE = 0.15, 0.6
MUTE_FADE = 0.05
FADE_IN, FADE_OUT = 0.3, 1.0   # at section changes

# (text in the line, "start"/"end" of it, text in the line where the music comes back or None = end of section, marker)
CUES = [
    ("Proven, within a margin", "end", None, "MUSIC: hard stop, title card in silence"),
    ("which version of the game my generator was running", "end", "Lesson learned",
     "MUSIC: record scratch, music cuts until 'Lesson learned'"),
    ("And number one.", "start", "Mushroom fields. A hundred", "MUSIC: silence, then a big hit on the reveal"),
]
LEVEL = {"4c": 0.7}      # per-section level: 4c is you talking, keep it low


def section_spans(items, times, length):
    starts = []
    for it in items:
        if it.id in times and (not starts or starts[-1][0] != it.section):
            if any(s == it.section for s, _ in starts):
                continue
            starts.append((it.section, times[it.id][0]))
    return [(s, a, starts[k + 1][1] if k + 1 < len(starts) else length) for k, (s, a) in enumerate(starts)]


def speech_spans(items, times):
    return [tuple(times[it.id]) for it in items if it.kind == "vo" and it.id in times]


def find_line(items, text):
    hits = [it.id for it in items if it.kind == "vo" and text in it.text]
    if not hits:
        raise ValueError(f"music cue: no script line contains {text!r}")
    if len(hits) > 1:
        raise ValueError(f"music cue: {text!r} is in {len(hits)} lines ({', '.join(hits)}), make it longer")
    return hits[0]


def resolve_mutes(cues, items, times, spans):
    out = []
    for cue in cues:
        text, edge, until = cue[:3]
        i = find_line(items, text)
        a = times[i][0 if edge == "start" else 1]
        if until is None:
            b = next(e for _, s, e in spans if s <= a < e)
        else:
            b = times[find_line(items, until)][0]
        if b <= a:
            raise ValueError(f"music cue {text!r}: the music would come back before it stops")
        out.append((a, b))
    return out


def _slew(target, up, down):
    """Follow target, rising at most `up` and falling at most `down` per control step."""
    out = np.empty_like(target)
    v = target[0]
    for k, x in enumerate(target):
        v = min(x, v + up) if x > v else max(x, v - down)
        out[k] = v
    return out


def gain_curve(length, speech, mutes, sections, level):
    n = int(length * CR) + 1
    tt = np.arange(n) / CR
    # ducking: merge short gaps, start ducking a little before each line so the attack is done when the voice starts
    merged = []
    for a, b in sorted(speech):
        if merged and a - merged[-1][1] < HOLD:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    duck = np.full(n, OPEN)
    for a, b in merged:
        duck[(tt >= a - ATTACK) & (tt < b)] = DUCK
    duck = _slew(duck, (OPEN - DUCK) / (RELEASE * CR), (OPEN - DUCK) / (ATTACK * CR))
    mute = np.ones(n)
    for a, b in mutes:
        mute[(tt >= a) & (tt < b)] = 0
    mute = _slew(mute, 1 / (MUTE_FADE * CR), 1 / (MUTE_FADE * CR))
    sec = np.zeros(n)
    for s, a, b in sections:
        m = (tt >= a) & (tt < b)
        fade = np.minimum(np.clip((tt - a) / FADE_IN, 0, 1), np.clip((b - tt) / FADE_OUT, 0, 1))
        sec[m] = (level.get(s, 1.0) * fade)[m]
    return np.clip(duck * mute * sec, 0, OPEN)


def place(track, sr, dur, xfade=2.0):
    """The track cut or looped (with an equal-gain crossfade) to exactly `dur` seconds."""
    n, L = int(round(dur * sr)), len(track)
    if L >= n:
        return track[:n]
    x = min(int(xfade * sr), L // 2)
    up = (np.arange(x) / x)[:, None].astype(track.dtype)
    out = np.zeros((n + L, track.shape[1]), track.dtype)
    pos = 0
    while pos < n:
        seg = track.copy()
        if pos > 0:
            seg[:x] *= up
        if pos + L - x < n:
            seg[L - x:] *= 1 - up
        out[pos:pos + L] += seg
        pos += L - x
    return out[:n]


def decode(path, sr):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-af", "loudnorm=I=-20:TP=-2", "-ac", "2", "-ar", str(sr),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2)


def render_bed(items, times, length, music_dir, out, sr=48000):
    """Writes the bed, returns (markers, notes)."""
    spans = section_spans(items, times, length)
    curve = gain_curve(length, speech_spans(items, times), resolve_mutes(CUES, items, times, spans), spans, LEVEL)
    total = int(length * sr)
    bed = np.zeros((total, 2), np.int16)
    notes = []
    for s, a, b in spans:
        hits = sorted(glob.glob(os.path.join(music_dir, f"{s}_*.mp3")) + glob.glob(os.path.join(music_dir, f"{s}_*.wav")))
        if not hits:
            notes.append(f"no music for section {s} (put {s}_<title>.mp3 in video/edit/music)")
            continue
        i0 = int(a * sr)
        seg = place(decode(hits[0], sr), sr, b - a)[:total - i0]
        g = np.interp((i0 + np.arange(len(seg))) / sr, np.arange(len(curve)) / CR, curve).astype(np.float32)
        bed[i0:i0 + len(seg)] = np.clip(seg * g[:, None] * 32767, -32768, 32767).astype(np.int16)
        notes.append(f"section {s}: {os.path.basename(hits[0])}")
    with wave.open(out, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(bed.tobytes())
    marks = [(times[find_line(items, c[0])][0 if c[1] == "start" else 1], c[3]) for c in CUES]
    return marks, notes
