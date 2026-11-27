"""V007 push-ins: start on the whole page, ease in on the highlighted claim, darken the rest with a vignette.
Input: forum_wiki/<name>@2x.png (3840x2160) and claims.json from the capture script. Runs in WSL or anywhere with
numpy + Pillow + ffmpeg:  python3 zoom.py"""
import json, os, subprocess

ASPECT = 16 / 9


def ease(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def frame_box(claim, W, H, fill=0.6, max_zoom=3.0):
    """16:9 crop centred on the claim, with the claim taking `fill` of the crop's width (or height), never zoomed in
    more than max_zoom and never bigger than the image, shifted to stay inside it."""
    x0, y0, x1, y1 = claim
    cw = max((x1 - x0) / fill, (y1 - y0) / fill * ASPECT, W / max_zoom)
    cw = min(cw, W, H * ASPECT)
    ch = cw / ASPECT
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    bx = min(max(cx - cw / 2, 0), W - cw)
    by = min(max(cy - ch / 2, 0), H - ch)
    return (bx, by, bx + cw, by + ch)


def lerp_box(a, b, t):
    if t <= 0:
        return a
    if t >= 1:
        return b
    return tuple(p + (q - p) * t for p, q in zip(a, b))


SITES = {"wikihow": "wikihow.com", "mcseedmap": "mcseedmap.org", "rarest_org": "rarest.org", "oldest_org": "oldest.org"}


def render(folder, secs=3.0, fps=30, hold0=0.1, move=0.7):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    here = os.path.dirname(os.path.abspath(__file__))
    font = ImageFont.truetype(os.path.join(here, "..", "..", "edit", ".tools", "inter", "extras", "ttf", "Inter-Bold.ttf"), 30)
    claims = json.load(open(os.path.join(folder, "claims.json")))
    ys, xs = np.mgrid[0:1080, 0:1920].astype(np.float32)
    for name, claim in claims.items():
        src = Image.open(os.path.join(folder, f"{name}@2x.png")).convert("RGB"); W, H = src.size
        full, tgt = (0, 0, W, H), frame_box(tuple(claim[k] for k in ("x0", "y0", "x1", "y1")), W, H, fill=0.85)
        out = os.path.join(folder, f"{name}_zoom.mp4")
        enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1920x1080",
                                "-r", str(fps), "-i", "-", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        last = None
        for f in range(int(secs * fps)):
            t = ease((f / fps - hold0) / move)
            b = lerp_box(full, tgt, t); s = 1920 / (b[2] - b[0])
            im = src.resize((1920, 1080), Image.LANCZOS, box=b)
            # claim in output pixels, then a soft darkening that grows with distance from it
            cx0, cy0 = (claim["x0"] - b[0]) * s, (claim["y0"] - b[1]) * s
            cx1, cy1 = (claim["x1"] - b[0]) * s, (claim["y1"] - b[1]) * s
            pad = 60
            dx = np.maximum(np.maximum(cx0 - pad - xs, xs - cx1 - pad), 0); dy = np.maximum(np.maximum(cy0 - pad - ys, ys - cy1 - pad), 0)
            dark = (0.78 * t) * np.clip(np.hypot(dx, dy) / 420, 0, 1) ** 0.9
            a = (np.asarray(im, np.float32) * (1 - dark[..., None])).astype(np.uint8)
            im = Image.fromarray(a); d = ImageDraw.Draw(im)
            d.rounded_rectangle([40, 1000, 60 + d.textlength(SITES[name], font=font) + 20, 1050], radius=12, fill=(0, 0, 0))
            d.text((60, 1025), SITES[name], font=font, fill=(255, 225, 77), anchor="lm")
            enc.stdin.write(im.tobytes()); last = im
        enc.stdin.close(); enc.wait(); last.save(os.path.join(folder, f"{name}_zoom_final.png")); print("wrote", out)


if __name__ == "__main__":
    render(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "00_cold_open", "forum_wiki"))
