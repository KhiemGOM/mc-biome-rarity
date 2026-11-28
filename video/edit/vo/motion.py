"""Slow push-in on stills (charts, screenshots, thumbnails), baked into a short clip per shot so it looks the same in
Resolve and in the preview. Rendered at 4x size and scaled down so the zoom moves smoothly, no pixel stepping.
Cached in work/motion/: the same still at the same length is rendered once."""
import hashlib, os, subprocess
from concurrent.futures import ThreadPoolExecutor

FPS = 60
ZOOM_RATE, ZOOM_MAX = 0.012, 0.06   # zoom per second of shot, and the most a shot ever zooms
HANDLE = 0.4                        # extra seconds before and after, so dissolves have footage to blend
BG = "0x0E1116"


def zoom_amount(dur):
    return min(ZOOM_MAX, ZOOM_RATE * dur)


def motion_filter(frames, zoom, fps=FPS):
    return (f"scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color={BG},"
            f"scale=7680:4320:flags=bicubic,"
            f"zoompan=z='1+{zoom:.4f}*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps={fps},"
            f"format=yuv420p")


def motion_path(still, dur, out_dir, fps=FPS):
    st = os.stat(still)
    h = hashlib.md5(f"{os.path.abspath(still)}|{st.st_size}|{st.st_mtime_ns}|{ZOOM_RATE}|{ZOOM_MAX}".encode()).hexdigest()[:8]
    stem = os.path.splitext(os.path.basename(still))[0]
    return os.path.join(out_dir, f"{stem}_{round(dur * fps)}f_{h}.mp4")


def render(still, dur, out_dir, fps=FPS):
    """-> (path, src_in, src_dur): the clip covers dur plus HANDLE on each side; use it from src_in."""
    os.makedirs(out_dir, exist_ok=True)
    out = motion_path(still, dur, out_dir, fps)
    total = dur + 2 * HANDLE
    n = round(total * fps)
    if not os.path.exists(out):
        tmp = out + ".part.mp4"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(fps), "-t", f"{total:.3f}", "-i", still,
                        "-vf", motion_filter(n, zoom_amount(total), fps), "-frames:v", str(n), "-c:v", "libx264",
                        "-preset", "veryfast", "-crf", "18", tmp], check=True)
        os.replace(tmp, out)
    return out, HANDLE, n / fps


def render_all(jobs, out_dir, fps=FPS, workers=4):
    """jobs: [(still, dur)] -> {(still, dur): (path, src_in, src_dur)}, rendered in parallel."""
    todo = sorted(set(jobs))
    with ThreadPoolExecutor(workers) as ex:
        res = list(ex.map(lambda j: render(j[0], j[1], out_dir, fps), todo))
    return dict(zip(todo, res))


def pad_needed(src_in, slot, src_dur, handle=HANDLE):
    """(head, tail) seconds of held first/last frame a video needs so it has `handle` spare before its in point and
    after its out point, and never runs out before its slot ends. Rounded up to 0.1 s so copies get reused."""
    up = lambda x: 0.0 if x <= 1e-9 else -(-round(x * 1000) // 100) / 10
    head = up(handle - src_in)
    tail = up(src_in + slot + handle - src_dur)
    return head, tail


def pad_path(path, head, tail, out_dir):
    st = os.stat(path)
    h = hashlib.md5(f"{os.path.abspath(path)}|{st.st_size}|{st.st_mtime_ns}".encode()).hexdigest()[:8]
    stem = os.path.splitext(os.path.basename(path))[0]
    return os.path.join(out_dir, f"{stem}_hold{head:.1f}-{tail:.1f}_{h}.mp4")


def pad(path, head, tail, out_dir):
    """Copy of the video with its first frame held for `head` s and its last for `tail` s (no audio)."""
    os.makedirs(out_dir, exist_ok=True)
    out = pad_path(path, head, tail, out_dir)
    if not os.path.exists(out):
        tmp = out + ".part.mp4"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", path, "-an", "-vf",
                        f"fps={FPS},tpad=start_mode=clone:start_duration={head}:stop_mode=clone:stop_duration={tail},format=yuv420p",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", tmp], check=True)
        os.replace(tmp, out)
    return out
