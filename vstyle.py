import json, math, os, subprocess
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, FancyArrowPatch
from PIL import Image

plt.rcParams["font.family"] = "Inter"
plt.rcParams["mathtext.fontset"] = "dejavusans"
BG = "#0E1116"; FG = "#F2F4F8"; MUT = "#97A3B6"; GRID = "#262D38"
ORANGE = "#FF9F43"; TEAL = "#2EC4B6"; PINK = "#FF5D8F"; BLUE = "#5AA9FF"
YELLOW = "#FFD166"; GREEN = "#7BD88F"; PURPLE = "#B197FC"
W, H = 1280, 720
FPS = 30
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out") + os.sep


def pretty(n):
    return n.replace("_", " ")


def canvas():
    fig = plt.figure(figsize=(12.8, 7.2), dpi=100, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W); ax.set_ylim(H, 0); ax.axis("off")
    return fig, ax


def T(ax, x, y, s, size=26, color=FG, weight="normal", ha="left", va="top", **kw):
    return ax.text(x, y, s, fontsize=size, color=color, fontweight=weight,
                   ha=ha, va=va, **kw)


def tag(ax, s):
    T(ax, 60, 34, s.upper(), size=12, color=MUT, weight="bold")


def sub_axes(fig, x, y, w, h):
    ax = fig.add_axes([x / W, 1 - (y + h) / H, w / W, h / H], facecolor=BG)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUT)
    ax.tick_params(colors=MUT, labelsize=13)
    return ax


def grab(fig):
    fig.canvas.draw()
    a = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()
    assert a.shape == (H, W, 3), a.shape
    return a


ENC = ["-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", str(FPS)]


def enc_still(rgb, secs, out, fi=0.35, fo=0.35):
    png = out + ".png"
    Image.fromarray(rgb).save(png)
    tmp = out + ".tmp.mp4"
    vf = (f"format=yuv420p,loop=-1:1,trim=duration={secs},setpts=N/({FPS}*TB),"
          f"fade=t=in:st=0:d={fi},fade=t=out:st={secs - fo}:d={fo}")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", png,
                    "-vf", vf, *ENC, tmp], check=True)
    os.rename(tmp, out)


class AnimWriter:
    def __init__(self, out, secs, fi=0.35, fo=0.35):
        self.out = out; self.tmp = out + ".tmp.mp4"
        vf = f"fade=t=in:st=0:d={fi},fade=t=out:st={secs - fo}:d={fo}"
        self.p = subprocess.Popen(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-vf", vf, *ENC, self.tmp],
            stdin=subprocess.PIPE)

    def write(self, rgb):
        self.p.stdin.write(rgb.tobytes())

    def close(self):
        self.p.stdin.close()
        rc = self.p.wait()
        assert rc == 0
        os.rename(self.tmp, self.out)
