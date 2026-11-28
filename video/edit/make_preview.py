"""Render work/rough_cut_preview.mp4 (1080p60) from work/rough_cut.fcpxml: shots with their cross dissolves, overlays,
voice-over and the music bed. A watchable rough cut without opening Resolve. Run after `vo.run timeline`:
    .venv\\Scripts\\python make_preview.py                 # full render
    .venv\\Scripts\\python make_preview.py --until 170     # only the first 170 s (builds only what it needs)
The shot track is kept as work/preview_base.mp4; add --reuse-base to skip rebuilding it when only overlays or audio
changed."""
import argparse, os, shutil, subprocess, tempfile, xml.etree.ElementTree as ET
from fractions import Fraction

from vo.tweaks import parse_fcpxml

EDIT = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(EDIT, "work")
W, H, FPS = 1920, 1080, 60   # same as the Resolve timeline: the footage is 60 fps
BG = "0x0E1116"
V = f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color={BG},fps={FPS},format=yuv420p,setsar=1"
STILL = (".png", ".jpg", ".jpeg")
ENC = ["-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS)]


def ff(*a):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *a], check=True)


def fr(x):
    return round(x * FPS)


def src_input(path, src, n):
    """ffmpeg input args for n frames of path from src seconds (None = black)."""
    d = f"{n / FPS + 0.1:.3f}"
    if path is None:
        return ["-f", "lavfi", "-i", f"color=c={BG}:s={W}x{H}:r={FPS}:d={d}"]
    if path.lower().endswith(STILL):
        return ["-loop", "1", "-framerate", str(FPS), "-t", d, "-i", path]
    return ["-ss", f"{max(0.0, src):.3f}", "-t", d, "-i", path]


def build_base(xml, total, out):
    """Main-track shots, black where there's none, and every cross dissolve blended in."""
    root = ET.fromstring(xml)
    T = lambda v: Fraction(v[:-1]) if v and v != "0s" else Fraction(0)
    trans = {fr(float(T(e.get("offset")) + T(e.get("duration")) / 2)): fr(float(T(e.get("duration"))))
             for e in root.find(".//sequence/spine") if e.tag == "transition"}
    shots = sorted([p for p in parse_fcpxml(xml) if p.lane == 0], key=lambda p: p.start)
    n_total, els, cur = fr(total), [], 0   # els: [path or None, start frame, end frame, src seconds at start]
    for p in shots:
        s, e = fr(p.start), min(fr(p.end), n_total)
        if s >= n_total:
            break
        if s > cur:
            els.append([None, cur, s, 0.0])
        els.append([p.path, s, e, p.src_in])
        cur = e
    if n_total > cur:
        els.append([None, cur, n_total, 0.0])
    tmp, parts = tempfile.mkdtemp(), []

    def piece(args, n):
        f = os.path.join(tmp, f"{len(parts):05d}.mp4")
        ff(*args, *ENC, "-frames:v", str(n), f)
        parts.append(f)

    for k, (path, s, e, src) in enumerate(els):
        din = trans.get(s, 0) if k > 0 else 0
        dout = trans.get(e, 0) if k + 1 < len(els) else 0
        b0, b1 = s + din // 2, e - dout // 2
        if b1 > b0:
            piece(src_input(path, src + (b0 - s) / FPS, b1 - b0) + ["-vf", V], b1 - b0)
        if dout:  # blend the end of this shot into the start of the next, centred on the cut
            nxt = els[k + 1]
            a_args = src_input(path, src + (e - dout // 2 - s) / FPS, dout)
            b_args = src_input(nxt[0], nxt[3] - (dout // 2) / FPS, dout)
            piece(a_args + b_args + ["-filter_complex", f"[0:v]{V}[a];[1:v]{V}[b];[a][b]xfade=transition=fade:"
                                     f"duration={dout / FPS:.4f}:offset=0[v]", "-map", "[v]"], dout)
        print(f"\rshots {k + 1}/{len(els)}", end="", flush=True)
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
    xml = open(os.path.join(WORK, "rough_cut.fcpxml"), encoding="utf-8").read()
    root = ET.fromstring(xml)
    total = float(Fraction(root.find(".//sequence").get("duration")[:-1]))
    end = min(total, a.until) if a.until else total
    placed = parse_fcpxml(xml)
    by = lambda name: next((p.path for p in placed if os.path.basename(p.path) == name), None)
    vo, music = by("vo_edit.wav"), by("music_bed.wav")
    over = sorted([p for p in placed if p.lane > 0 and p.start < end], key=lambda p: p.start)
    joined = os.path.join(WORK, "preview_base.mp4" if end == total else "preview_base_part.mp4")
    if not (a.reuse_base and os.path.exists(joined)):
        build_base(xml, end, joined)

    inputs, fc, last = ["-i", joined, "-i", vo], [], "0:v"
    audio, n = "[1:a]aformat=channel_layouts=stereo", 2
    if music:
        inputs += ["-i", music]
        audio += f"[vo];[vo][{n}:a]amix=inputs=2:normalize=0:duration=first"
        n += 1
    audio += "[aout]"
    for k, p in enumerate(over):
        d = p.end - p.start
        if p.path.lower().endswith(STILL):  # a still as a timed stream: exactly its slot, then nothing
            inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.3f}", "-i", p.path]
        else:
            inputs += ["-ss", f"{p.src_in:.3f}", "-t", f"{d:.3f}", "-i", p.path]
        fc.append(f"[{n}:v]fps={FPS},scale={W}:{H}:force_original_aspect_ratio=decrease,format=rgba,"
                  f"setpts=PTS-STARTPTS+{p.start:.3f}/TB[o{k}];[{last}][o{k}]overlay=(W-w)/2:(H-h)/2:eof_action=pass[v{k}]")
        last, n = f"v{k}", n + 1
    out = os.path.join(WORK, "rough_cut_preview.mp4" if end == total else "rough_cut_preview_part.mp4")
    ff(*inputs, "-filter_complex", ";".join(fc + [audio]), "-map", f"[{last}]" if fc else "0:v", "-map", "[aout]",
       "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "192k", "-t", f"{end:.3f}", out)
    print("wrote", out, f"{end / 60:.1f} min")


if __name__ == "__main__":
    main()
