"""Title card for the cold open (no spoiler). Same palette as video/assets/_generator/common.py, font Inter.

Writes to video/assets/00_cold_open/:
  title_card.png        opaque, dark background
  title_card_alpha.png  transparent, to lay over footage (V2)
  title_card_anim.mp4   4 s, 60 fps: lines punch in one after the other, then hold
"""
import os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, ".tools", "inter", "extras", "ttf")
OUT = os.path.join(HERE, "..", "assets", "00_cold_open")
W, H = 1920, 1080
BG = (14, 17, 22); FG = (242, 244, 248); MUT = (151, 163, 182); YELLOW = (255, 209, 102); ORANGE = (255, 159, 67)


def font(weight, size):
    return ImageFont.truetype(os.path.join(FONT, f"Inter-{weight}.ttf"), size)


def text_w(d, s, f):
    return d.textlength(s, font=f)


def layer(stage):
    """stage: 0..3 lines visible (fractional = the last one scaling in). Returns RGBA, transparent background."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f1, f2, f3 = font("ExtraBold", 84), font("Black", 168), font("SemiBold", 40)
    # line 1: I found the RAREST biome in Minecraft...
    parts = [("I found the ", FG), ("RAREST", ORANGE), (" biome in Minecraft...", FG)]
    lines = [(parts, f1, 300), ([("MATHEMATICALLY", YELLOW)], f2, 440), ([("Minecraft Java 26.3   |   215,000 worlds", MUT)], f3, 720)]
    for i, (pp, f, y) in enumerate(lines):
        a = max(0.0, min(1.0, stage - i))
        if a <= 0:
            continue
        ease = 1 - (1 - a) ** 3
        scale = 1.25 - 0.25 * ease
        tw = sum(text_w(d, s, f) for s, _ in pp)
        tmp = Image.new("RGBA", (int(tw) + 40, f.size + 80), (0, 0, 0, 0))
        td = ImageDraw.Draw(tmp)
        x = 20
        for s, col in pp:
            td.text((x, 20), s, font=f, fill=col + (255,))
            x += text_w(td, s, f)
        if i == 1:  # soft glow behind the big word
            glow = tmp.filter(ImageFilter.GaussianBlur(28))
            tmp = Image.alpha_composite(Image.new("RGBA", tmp.size, (0, 0, 0, 0)), glow)
            tmp.alpha_composite(Image.new("RGBA", tmp.size, (0, 0, 0, 0)))
            td2 = ImageDraw.Draw(tmp)
            x = 20
            for s, col in pp:
                td2.text((x, 20), s, font=f, fill=col + (255,))
                x += text_w(td2, s, f)
        tmp = tmp.resize((int(tmp.width * scale), int(tmp.height * scale)), Image.LANCZOS)
        if a < 1:
            r, g, b, al = tmp.split()
            tmp = Image.merge("RGBA", (r, g, b, al.point(lambda v: int(v * ease))))
        img.alpha_composite(tmp, (int((W - tmp.width) / 2), int(y + (f.size + 80) / 2 - tmp.height / 2)))
    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    full = layer(3)
    full.save(os.path.join(OUT, "title_card_alpha.png"))
    bg = Image.new("RGBA", (W, H), BG + (255,))
    Image.alpha_composite(bg, full).convert("RGB").save(os.path.join(OUT, "title_card.png"))
    fps, secs = 60, 4
    with tempfile.TemporaryDirectory() as tmpd:
        for k in range(fps * secs):
            t = k / fps
            stage = 0 if t < 0.15 else min(3.0, (t - 0.15) / 0.35)  # one line every 0.35 s
            Image.alpha_composite(bg, layer(stage)).convert("RGB").save(os.path.join(tmpd, f"{k:04d}.png"))
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(fps), "-i", os.path.join(tmpd, "%04d.png"),
                        "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", os.path.join(OUT, "title_card_anim.mp4")], check=True)
    print("wrote title_card.png, title_card_alpha.png, title_card_anim.mp4 to", os.path.normpath(OUT))


if __name__ == "__main__":
    sys.exit(main())
