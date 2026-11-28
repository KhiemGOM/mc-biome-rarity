"""[CLIP] lines: find the source video in video/edit/media, cut its audio for the voice-over track."""
import array, glob, os, subprocess


def find_clip(media, ref):
    """Path (relative to media) of the one video whose name contains ref. The same file linked into several bins is
    fine; two different files are not."""
    hits = sorted(glob.glob(os.path.join(media, "*", f"*{glob.escape(ref)}*.mp4")))
    if not hits:
        raise FileNotFoundError(f"CLIP {ref}: no video with that in its name in video/edit/media (run make_bins.ps1?)")
    names = {os.path.basename(h) for h in hits}
    if len(names) > 1:
        raise ValueError(f"CLIP {ref}: matches several videos ({', '.join(sorted(names))}), use a longer id")
    return os.path.relpath(hits[0], media)


def clip_cuts(items, media):
    """{clip id: "rel/path.mp4@in"}, in the cuts.csv format, so each clip shows its own video from its in point."""
    return {it.id: f"{find_clip(media, it.clip[0])}@{it.clip[1]:g}" for it in items if it.kind == "clip"}


def clip_audio(path, a, b, sr):
    """Mono 16-bit PCM of path between a and b seconds, at voice-over loudness (-16 LUFS)."""
    return subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", path, "-vn", "-ac", "1",
                           "-ar", str(sr), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-f", "s16le", "-"],
                          capture_output=True, check=True).stdout


def fade_edges(a, sr, sec):
    """Linear fade in and out of `sec` seconds on 16-bit samples (shortened for very short clips)."""
    out = array.array("h", a)
    n = min(int(sec * sr), len(out) // 2)
    for k in range(n):
        g = k / n
        out[k] = int(out[k] * g)
        out[-1 - k] = int(out[-1 - k] * g)
    return out
