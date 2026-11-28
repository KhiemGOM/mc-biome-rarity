"""Render work/rough_cut_preview.mp4 (1080p60) from work/rough_cut.fcpxml: base visuals, overlays, voice-over and the
music bed. A watchable rough cut without opening Resolve. Run after `vo.run timeline`:
    .venv\\Scripts\\python make_preview.py                 # full render
    .venv\\Scripts\\python make_preview.py --until 130     # only the first 130 s (quick check)
The base track is kept as work/preview_base.mp4; add --reuse-base to skip rebuilding it when only overlays or audio
changed."""
import argparse, os, shutil, subprocess, tempfile, xml.etree.ElementTree as ET
from urllib.parse import unquote

EDIT = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(EDIT, "work")
W, H, FPS = 1920, 1080, 60   # same as the Resolve timeline: the footage is 60 fps
BG = "0x0E1116"
V = f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color={BG},fps={FPS},format=yuv420p,setsar=1"
STILL = (".png", ".jpg", ".jpeg")


def ff(*a):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *a], check=True)


def sec(v):
    return 0.0 if v == "0s" else int(v.split("/")[0]) / int(v.split("/")[1][:-1])


def build_base(base, src, total, out):
    tmp = tempfile.mkdtemp()
    parts, t = [], 0.0

    def black(d):
        p = os.path.join(tmp, f"{len(parts):04d}.mp4")
        ff("-f", "lavfi", "-i", f"color=c={BG}:s={W}x{H}:r={FPS}:d={d:.3f}", "-pix_fmt", "yuv420p", p)
        parts.append(p)

    for k, c in enumerate(base):
        o, d, s = sec(c.get("offset")), sec(c.get("duration")), sec(c.get("start"))
        if o > t + 0.01:
            black(o - t)
        f = src[c.get("ref")]
        inp = ["-loop", "1", "-t", f"{d:.3f}", "-i", f] if f.lower().endswith(STILL) else ["-ss", f"{s:.3f}", "-t", f"{d:.3f}", "-i", f]
        p = os.path.join(tmp, f"{len(parts):04d}.mp4")
        ff(*inp, "-vf", V, "-an", "-t", f"{d:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", p)
        parts.append(p)
        t = o + d
        print(f"\rbase {k + 1}/{len(base)}", end="", flush=True)
    if total > t + 0.01:
        black(total - t)
    print()
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    ff("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out)
    shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--until", type=float)
    ap.add_argument("--reuse-base", action="store_true")
    a = ap.parse_args()
    root = ET.parse(os.path.join(WORK, "rough_cut.fcpxml")).getroot()
    src = {x.get("id"): unquote(x.find("media-rep").get("src")[len("file:///"):]) for x in root.iter("asset")}
    clips = list(root.iter("asset-clip"))
    lane = lambda n: sorted([c for c in clips if c.get("lane") == n], key=lambda c: sec(c.get("offset")))
    base, over, vo, music = lane("1"), lane("2"), lane("-1")[0], lane("-2")
    total = sec(vo.get("duration"))
    end = min(total, a.until) if a.until else total
    joined = os.path.join(WORK, "preview_base.mp4")
    if not (a.reuse_base and os.path.exists(joined)):
        build_base(base, src, total, joined)

    inputs, fc, last = ["-i", joined, "-i", src[vo.get("ref")]], [], "0:v"
    audio = "[1:a]aformat=channel_layouts=stereo"
    n = 2
    if music:
        inputs += ["-i", src[music[0].get("ref")]]
        audio += f"[vo];[vo][{n}:a]amix=inputs=2:normalize=0:duration=first"
        n += 1
    audio += "[aout]"
    for k, c in enumerate(c for c in over if sec(c.get("offset")) < end):
        o, d, s = sec(c.get("offset")), sec(c.get("duration")), sec(c.get("start"))
        f = src[c.get("ref")]
        if f.lower().endswith(STILL):  # a still as a timed stream: exactly its slot, then nothing
            inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.3f}", "-i", f]
        else:
            inputs += ["-ss", f"{s:.3f}", "-t", f"{d:.3f}", "-i", f]
        fc.append(f"[{n}:v]fps={FPS},scale={W}:{H}:force_original_aspect_ratio=decrease,format=rgba,"
                  f"setpts=PTS-STARTPTS+{o:.3f}/TB[o{k}];[{last}][o{k}]overlay=(W-w)/2:(H-h)/2:eof_action=pass[v{k}]")
        last, n = f"v{k}", n + 1
    out = os.path.join(WORK, "rough_cut_preview.mp4" if end == total else "rough_cut_preview_part.mp4")
    vmap = f"[{last}]" if fc else "0:v"
    ff(*inputs, "-filter_complex", ";".join(fc + [audio]), "-map", vmap, "-map", "[aout]",
       "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "192k", "-t", f"{end:.3f}", out)
    print("wrote", out, f"{end / 60:.1f} min")


if __name__ == "__main__":
    main()
