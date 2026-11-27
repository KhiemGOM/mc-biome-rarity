"""Visuals for section 1b ("why this definition"), V038 (Cubiomes vs the real game) and the gag overlays.
Runs in WSL (needs ~/viz2/viz built from viz.c with Cubiomes, see the commit that added this file):

  python3 justify.py compare        # grid walk vs straight line vs wandering, on real 26.3 worlds -> out/walk_compare.json
  python3 justify.py charts         # the curves chart from that json
  python3 justify.py maps           # path animation, grid vs ray animation, noise vs static, turn settings, three ways
  python3 justify.py side           # V038: Cubiomes map with a dot that follows the river_v2 orbit, next to the clip
  python3 justify.py gags           # transparent overlays: nuanced, no judgement, trust me bro, 43% oops, ...
"""
import json, math, os, random, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from walks import straight, lawnmower, wander, distinct_curve

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ASSETS = os.path.join(REPO, "video", "assets")
S1, S2, S4, GAGS = (os.path.join(ASSETS, d) for d in ("01_what_is_rare", "02_monte_carlo", "04_countdown", "gags"))
OUTJ = os.path.join(HERE, "out")
VIZ = os.path.expanduser("~/viz2/viz")
SHOTS = "/mnt/d/Coding/Minecraft/mc-capture/shots"
FONTS = os.path.join(REPO, "video", "edit", ".tools", "inter", "extras", "ttf")
BG, FG, MUT = (14, 17, 22), (242, 244, 248), (151, 163, 182)
ORA, TEAL, PINK, YEL, RED, BLUE = (255, 159, 67), (46, 196, 182), (255, 93, 143), (255, 209, 102), (255, 77, 77), (90, 169, 255)


def F(sz, w="Medium"):
    return ImageFont.truetype(os.path.join(FONTS, f"Inter-{w}.ttf"), sz)


NAMES, PAL = {}, np.zeros((256, 3), np.uint8)
for l in subprocess.run([VIZ, "names"], capture_output=True, text=True).stdout.splitlines():
    i, n, r, g, b = l.split(","); NAMES[int(i)] = n; PAL[int(i)] = (int(r), int(g), int(b))


def pretty(n):
    return n.replace("_", " ").capitalize()


class World:
    """Talks to `viz pts`: set a seed, then ask the surface biome at many points in one round trip."""
    def __init__(self):
        self.p = subprocess.Popen([VIZ, "pts"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1 << 20)

    def seed(self, s):
        self.p.stdin.write(f"S {s}\n"); self.p.stdin.flush()
        _, x, z = self.p.stdout.readline().split(); return int(x), int(z)

    def biomes(self, pts, y=None, batch=4000):
        """Batched: the answers go back through a pipe too, and a huge single write deadlocks once both fill up."""
        out = []
        for i in range(0, len(pts), batch):
            part = pts[i:i + batch]
            cmd = "".join(f"P {x:.3f} {z:.3f}\n" for x, z in part) if y is None else "".join(f"Q {x:.3f} {y} {z:.3f}\n" for x, z in part)
            self.p.stdin.write(cmd + "F\n"); self.p.stdin.flush()
            out += [int(self.p.stdout.readline()) for _ in part]
        return out

    def grid(self, cx, cz, half, step):
        xs = np.arange(cx - half, cx + half, step)
        pts = [(x, z) for z in np.arange(cz - half, cz + half, step) for x in xs]
        return np.array(self.biomes(pts), np.int32).reshape(len(xs), len(xs))


def mapimg(ids, size):
    return Image.fromarray(PAL[np.clip(ids, 0, 255)]).resize((size, size), Image.NEAREST)


# ---------------------------------------------------------------- the comparison (real numbers behind V027/V028)
STEP, BUDGET, EVERY = 2, 16000, 250
STRATS = {  # name -> (label, path function of (x, z, angle, seed))
    "straight": ("Straight line", lambda x, z, a, s: straight(x, z, a, BUDGET, STEP)),
    "grid128": ("Grid walk, strips 128 apart (8 chunks)", lambda x, z, a, s: lawnmower(x, z, a, BUDGET, STEP, leg=2000, gap=128)),
    "grid512": ("Grid walk, strips 512 apart (32 chunks)", lambda x, z, a, s: lawnmower(x, z, a, BUDGET, STEP, leg=2000, gap=512)),
    "wander": ("Wandering (heading drifts)", lambda x, z, a, s: wander(x, z, a, BUDGET, STEP, turn=0.05, seed=s)),
}


def compare(n=400, seed0=1):
    w, rng = World(), random.Random(2026)
    cps = [int(d / STEP) for d in range(0, BUDGET + 1, EVERY)]
    per = {k: [] for k in STRATS}
    for s in range(seed0, seed0 + n):
        x, z = w.seed(s); a = rng.uniform(0, 2 * math.pi)
        for k, (_, fn) in STRATS.items():
            per[k].append(distinct_curve(w.biomes(fn(x + 0.5, z + 0.5, a, s)), cps))
        if (s - seed0) % 50 == 49:
            print(f"{s - seed0 + 1}/{n} seeds", flush=True)
    res = {"seeds": [seed0, seed0 + n - 1], "budget": BUDGET, "step": STEP, "every": EVERY, "version": "26.3 surface (y=60)",
           "dist": [c * STEP for c in cps], "labels": {k: v[0] for k, v in STRATS.items()},
           "mean": {k: np.mean(v, 0).tolist() for k, v in per.items()},
           "se": {k: (np.std(v, 0, ddof=1) / math.sqrt(n)).tolist() for k, v in per.items()}}
    st = np.array(per["straight"])
    res["paired"] = {k: {"mean_diff_at_end": float(np.mean(st[:, -1] - np.array(v)[:, -1])),
                         "se": float(np.std(st[:, -1] - np.array(v)[:, -1], ddof=1) / math.sqrt(n))}
                     for k, v in per.items() if k != "straight"}
    os.makedirs(OUTJ, exist_ok=True)
    json.dump(res, open(os.path.join(OUTJ, "walk_compare.json"), "w"), indent=1)
    for k in STRATS:
        print(f"{k:9s} at {BUDGET}: {res['mean'][k][-1]:.2f} biomes (se {res['se'][k][-1]:.2f})")
    print("straight minus others at the end:", res["paired"])


COL = {"straight": YEL, "grid128": PINK, "grid512": ORA, "wander": TEAL}


def hexc(c):
    return "#%02x%02x%02x" % c


def charts():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    for f in ("Medium", "Bold"):
        font_manager.fontManager.addfont(os.path.join(FONTS, f"Inter-{f}.ttf"))
    plt.rcParams["font.family"] = "Inter"
    r = json.load(open(os.path.join(OUTJ, "walk_compare.json")))
    f = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor=hexc(BG))
    ax = f.add_axes([0.07, 0.12, 0.62, 0.66]); ax.set_facecolor(hexc(BG))
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_color(hexc(MUT))
    ax.tick_params(colors=hexc(MUT), labelsize=18)
    d = np.array(r["dist"]) / 1000
    order = ("straight", "wander", "grid512", "grid128")
    ys, prev = {}, None
    for k in order:  # labels top to bottom, at least 3.6 biomes apart so two-line labels never overlap
        y = r["mean"][k][-1]; ys[k] = y if prev is None else min(y, prev - 3.6); prev = ys[k]
    shift = max(0, max(r["mean"][k][-1] for k in order) + 1.2 - ys["straight"])
    for k in order:
        m, se = np.array(r["mean"][k]), np.array(r["se"][k])
        ax.fill_between(d, m - 2 * se, m + 2 * se, color=hexc(COL[k]), alpha=0.18, lw=0)
        ax.plot(d, m, color=hexc(COL[k]), lw=5 if k == "straight" else 3.5)
        ax.text(d[-1] + 0.25, ys[k] + shift, f"{r['labels'][k]}\n{m[-1]:.1f} biomes", color=hexc(COL[k]), fontsize=19,
                fontweight="bold" if k == "straight" else "normal", va="center")
    ax.set_xlim(0, d[-1]); ax.set_ylim(0, None)
    ax.set_xlabel("blocks walked (thousands)", color=hexc(MUT), fontsize=20)
    ax.set_ylabel("different biomes found", color=hexc(MUT), fontsize=20)
    f.text(0.07, 0.93, "Same distance, more biomes: walk straight", color=hexc(FG), fontsize=40, fontweight="bold", va="top")
    f.text(0.07, 0.865, f"{r['seeds'][1] - r['seeds'][0] + 1} real Minecraft 26.3 worlds, every walk {r['budget']:,} blocks from spawn, "
           f"surface biomes.\nGrid legs are 2,000 blocks long, so all walks match until the first turn. Bands: 95% range of the average.",
           color=hexc(MUT), fontsize=19, va="top", linespacing=1.5)
    os.makedirs(S1, exist_ok=True)
    f.savefig(os.path.join(S1, "grid_vs_ray_curves.png"), facecolor=hexc(BG)); plt.close(f); print("wrote grid_vs_ray_curves.png")


# ---------------------------------------------------------------- maps and animations
def encoder(out, fps=30):
    return subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1920x1080",
                             "-r", str(fps), "-i", "-", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", out],
                            stdin=subprocess.PIPE)


def draw_path(d, pts, P, upto, col, width=5):
    xy = [P(*p) for p in pts[:upto + 1]]
    if len(xy) > 1:
        d.line(xy, fill=(0, 0, 0), width=width + 4, joint="curve"); d.line(xy, fill=col, width=width, joint="curve")


def first_hits(ids, step):
    seen, out = set(), []
    for k, b in enumerate(ids):
        if b not in seen:
            seen.add(b); out.append((b, k * step, k))
    return out


SEED, HALF = 101, 6000


def path_anim(w, base_ids, sx, sz, secs=16, fps=30):
    """V026: a player heads roughly one way, biomes light up as they show up."""
    M = 1000; sc = M / (2 * HALF); cx = cy = 40 + M / 2
    P = lambda x, z: (cx + (x - sx) * sc, cy + (z - sz) * sc)
    pts = wander(sx + 0.5, sz + 0.5, 0.35, 5600, 4, turn=0.012, seed=11)
    ids = w.biomes(pts); hits = first_hits(ids, 4)
    base = Image.new("RGB", (1920, 1080), BG); base.paste(mapimg(base_ids, M), (40, 40)); bd = ImageDraw.Draw(base)
    bd.text((1080, 50), "How players actually look for a biome", font=F(40, "Bold"), fill=FG)
    bd.text((1080, 105), "Pick a direction. Keep going. Write down what shows up.", font=F(24), fill=MUT)
    enc, n, last = encoder(os.path.join(S1, "player_path_anim.mp4"), fps), secs * fps, None
    for k in range(n):
        prog = min(1, max(0, (k / fps - 1) / (secs - 3))); upto = int(prog * (len(pts) - 1))
        im = base.copy(); d = ImageDraw.Draw(im)
        draw_path(d, pts, P, upto, (255, 255, 255), 7)
        X, Y = P(*pts[upto]); d.ellipse([X - 13, Y - 13, X + 13, Y + 13], fill=YEL, outline=(0, 0, 0), width=3)
        d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(255, 255, 255), outline=(0, 0, 0), width=3)
        for i, (b, dist, kk) in enumerate([h for h in hits if h[2] <= upto][:26]):
            col, row = divmod(i, 13); Xb, Yb = 1080 + col * 420, 180 + row * 60
            d.rectangle([Xb, Yb, Xb + 34, Yb + 34], fill=tuple(PAL[b]), outline=(255, 255, 255), width=2)
            d.text((Xb + 48, Yb + 2), pretty(NAMES[b]), font=F(22), fill=FG)
            d.text((Xb + 400, Yb + 2), f"{dist:,.0f}", font=F(22, "Bold"), fill=ORA, anchor="ra")
        d.text((1080, 990), f"walked: {upto * 4:,} blocks", font=F(34, "Bold"), fill=YEL)
        enc.stdin.write(im.tobytes()); last = im
    enc.stdin.close(); enc.wait(); last.save(os.path.join(S1, "player_path_anim_final.png")); print("wrote player_path_anim")


def grid_vs_ray(w, secs=22, fps=30):
    """V027/V028: the same world twice. Left a grid walk, right a straight line, same blocks walked, live counters."""
    half, M, budget = 3000, 860, 12000
    sx, sz = w.seed(SEED); ids = w.grid(sx, sz, half, 6)
    a = 0.35
    paths = {"grid512": lawnmower(sx + 0.5 - 1000 * math.cos(a), sz + 0.5 - 1000 * math.sin(a), a, budget, 4, leg=2000, gap=512),
             "straight": straight(sx + 0.5 - 2900 * math.cos(a), sz + 0.5 - 2900 * math.sin(a), a, budget, 4)}
    # the straight walk is 12,000 blocks: shown from its middle third outward would leave the map, so it starts at the
    # far edge and the map is centred on spawn; only what fits is drawn, the counter counts all of it
    found = {k: w.biomes(p) for k, p in paths.items()}
    sc = M / (2 * half)
    panels = {"grid512": (60, 170), "straight": (1000, 170)}
    titles = {"grid512": ("Grid walk", PINK), "straight": ("Straight line", YEL)}
    base = Image.new("RGB", (1920, 1080), BG); bd = ImageDraw.Draw(base)
    bd.text((960, 40), "Same world, same number of blocks walked", font=F(44, "Bold"), fill=FG, anchor="ma")
    for k, (X, Y) in panels.items():
        base.paste(mapimg(ids, M), (X, Y)); bd.text((X, Y - 50), titles[k][0], font=F(32, "Bold"), fill=titles[k][1])
    enc, n, last = encoder(os.path.join(S1, "grid_vs_ray_anim.mp4"), fps), secs * fps, None
    curve = {k: distinct_curve(found[k], list(range(len(found[k])))) for k in paths}
    pbase = mapimg(ids, M)
    for f in range(n):
        prog = min(1, max(0, (f / fps - 1) / 14)); im = base.copy(); d = ImageDraw.Draw(im)
        for k, (X, Y) in panels.items():
            P = lambda x, z: (M / 2 + (x - sx) * sc, M / 2 + (z - sz) * sc)  # panel-local, drawn on its own map: clipped
            upto = int(prog * (len(paths[k]) - 1))
            panel = pbase.copy(); draw_path(ImageDraw.Draw(panel), paths[k], P, upto, titles[k][1], 4)
            im.paste(panel, (X, Y))
            d.text((X, Y + M + 20), f"walked {upto * 4:,} blocks", font=F(26), fill=MUT)
            d.text((X + M, Y + M + 12), f"{curve[k][upto]} biomes", font=F(40, "Bold"), fill=titles[k][1], anchor="ra")
        enc.stdin.write(im.tobytes()); last = im
    enc.stdin.close(); enc.wait(); last.save(os.path.join(S1, "grid_vs_ray_anim_final.png")); print("wrote grid_vs_ray_anim")


def noise_vs_static(w):
    sx, sz = w.seed(SEED); ids = w.grid(sx, sz, 1600, 16)
    rnd = np.random.default_rng(3).permutation(ids.ravel()).reshape(ids.shape)
    im = Image.new("RGB", (1920, 1080), BG); d = ImageDraw.Draw(im)
    d.text((960, 40), "Biomes stick together", font=F(46, "Bold"), fill=FG, anchor="ma")
    for k, (arr, lab, sub) in enumerate([(ids, "Real Minecraft", "made from smooth noise maps"),
                                         (rnd, "If every spot were random", "same biomes, shuffled")]):
        X = 140 + k * 880; im.paste(mapimg(arr, 760), (X, 150))
        d.text((X + 380, 935), lab, font=F(34, "Bold"), fill=FG, anchor="ma")
        d.text((X + 380, 985), sub, font=F(24), fill=MUT, anchor="ma")
    im.save(os.path.join(S1, "noise_vs_static.png")); print("wrote noise_vs_static.png")


def turn_settings(w):
    sx, sz = w.seed(SEED); ids = w.grid(sx, sz, 2000, 8)
    M, half = 760, 2000; sc = M / (2 * half)
    im = Image.new("RGB", (1920, 1080), BG); d = ImageDraw.Draw(im)
    d.text((960, 40), "Every made-up setting is a choice I'd have to defend", font=F(42, "Bold"), fill=FG, anchor="ma")
    rng = random.Random(4)
    for k, X in enumerate((140, 1020)):
        im.paste(mapimg(ids, M), (X, 150)); P = lambda x, z, X=X: (X + M / 2 + (x - sx) * sc, 150 + M / 2 + (z - sz) * sc)
        if k == 0:
            pts, a, x, z, turns = [(sx, sz)], 0.4, sx, sz, []
            for leg in range(7):
                L = 380; x += L * math.cos(a); z += L * math.sin(a); pts.append((x, z)); turns.append((x, z)); a += rng.uniform(-1.3, 1.3)
            xy = [P(*p) for p in pts]; d.line(xy, fill=(0, 0, 0), width=9); d.line(xy, fill=TEAL, width=5)
            for t in turns[:-1]:
                X0, Y0 = P(*t); d.ellipse([X0 - 9, Y0 - 9, X0 + 9, Y0 + 9], fill=YEL, outline=(0, 0, 0), width=2)
            d.text((X + 380, 935), "Turn every ??? blocks, by ??? degrees", font=F(30, "Bold"), fill=TEAL, anchor="ma")
            d.text((X + 380, 985), "and which way? how random? says who?", font=F(24), fill=MUT, anchor="ma")
        else:
            x1, z1 = sx + 2400 * math.cos(0.4), sz + 2400 * math.sin(0.4)
            d.line([P(sx, sz), P(x1, z1)], fill=(0, 0, 0), width=9); d.line([P(sx, sz), P(x1, z1)], fill=YEL, width=5)
            d.text((X + 380, 935), "Straight line: settings needed: none", font=F(30, "Bold"), fill=YEL, anchor="ma")
            d.text((X + 380, 985), "just a random direction", font=F(24), fill=MUT, anchor="ma")
        Xs, Ys = P(sx, sz); d.ellipse([Xs - 10, Ys - 10, Xs + 10, Ys + 10], fill=(255, 255, 255), outline=(0, 0, 0), width=3)
    im.save(os.path.join(S1, "turn_settings.png")); print("wrote turn_settings.png")


def three_ways(w):
    """V030: what counts as found. Same scale as the 4b sight bands (6 km wide)."""
    sx, sz = w.seed(SEED); half, M = 3000, 560; ids = w.grid(sx, sz, half, 12)
    sc, ang = M / (2 * half), 3.6513788485261798
    im = Image.new("RGB", (1920, 1080), BG); d = ImageDraw.Draw(im)
    d.text((960, 40), "What counts as \"found\"?", font=F(46, "Bold"), fill=FG, anchor="ma")
    for k, (rad, lab, sub) in enumerate([(0, "Stand in it", "the main ranking"), (128, "Within 8 chunks", "128 blocks"),
                                         (512, "Within 32 chunks", "512 blocks, max Java render distance")]):
        X, Y = 70 + k * 610, 190; base = mapimg(ids, M).convert("RGBA")
        ov = Image.new("RGBA", (M, M), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        c = M / 2; ex, ey = c + math.cos(ang) * half * 1.5 * sc, c + math.sin(ang) * half * 1.5 * sc
        if rad:
            od.line([(c, c), (ex, ey)], fill=(255, 240, 150, 110), width=int(2 * rad * sc))
            od.ellipse([c - rad * sc, c - rad * sc, c + rad * sc, c + rad * sc], fill=(255, 240, 150, 110))
        panel = Image.alpha_composite(base, ov).convert("RGB"); pd = ImageDraw.Draw(panel)
        pd.line([(c, c), (ex, ey)], fill=(0, 0, 0), width=6); pd.line([(c, c), (ex, ey)], fill=(255, 255, 255), width=3)
        pd.ellipse([c - 8, c - 8, c + 8, c + 8], fill=(255, 255, 255), outline=(0, 0, 0), width=2)
        im.paste(panel, (X, Y))
        d.text((X + M / 2, Y + M + 40), lab, font=F(34, "Bold"), fill=YEL if k == 0 else FG, anchor="ma")
        d.text((X + M / 2, Y + M + 90), sub, font=F(24), fill=MUT, anchor="ma")
    im.save(os.path.join(S1, "three_ways_found.png")); print("wrote three_ways_found.png")


def maps():
    w = World(); sx, sz = w.seed(SEED); base = w.grid(sx, sz, HALF, 12)
    path_anim(w, base, sx, sz); grid_vs_ray(w); noise_vs_static(w); turn_settings(w); three_ways(w)


# ---------------------------------------------------------------- V038: Cubiomes vs the real game, same coordinates
def side(secs=20, fps=30):
    """river_v2 (seed 279): Flashback orbit, keyframe k at 45k degrees and tick 50k, camera at
    (176 + 50 sin a, 110, -200 + 50 cos a) looking at the centre (mc-capture/tools/shoot.mjs, ctl/shots.json)."""
    w = World(); w.seed(279); cx, cz, R, half, M = 176, -200, 50, 240, 820
    ids = w.grid(cx, cz, half, 2); sc = M / (2 * half)
    clip = os.path.join(SHOTS, "river_v2_1080p.mp4")
    X0, Y0 = 1060, 140
    base = Image.new("RGB", (1920, 1080), BG); bd = ImageDraw.Draw(base)
    base.paste(mapimg(ids, M), (X0, Y0))
    bd.text((60, 40), "Same seed, same spot: the real game and Cubiomes", font=F(42, "Bold"), fill=FG)
    bd.text((60, 100), "Seed 279, x 176, z -200. Left: Minecraft 26.3. Right: Cubiomes' map of the same world.", font=F(24), fill=MUT)
    present = sorted(set(ids.ravel().tolist()), key=lambda b: -(ids == b).sum())[:5]
    for i, b in enumerate(present):
        Xl, Yl = 60 + (i % 3) * 330, 860 + (i // 3) * 56
        bd.rectangle([Xl, Yl, Xl + 30, Yl + 30], fill=tuple(PAL[b]), outline=(255, 255, 255), width=2)
        bd.text((Xl + 44, Yl), pretty(NAMES[b]), font=F(24), fill=FG)
    P = lambda x, z: (X0 + M / 2 + (x - cx) * sc, Y0 + M / 2 + (z - cz) * sc)
    tmp = tempfile.mkdtemp(); ov = os.path.join(tmp, "overlay.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1920x1080",
                            "-r", str(fps), "-i", "-", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", ov], stdin=subprocess.PIPE)
    for f in range(secs * fps):
        a = math.radians(360 * f / (secs * fps)); x, z = cx + R * math.sin(a), cz + R * math.cos(a)
        im = base.copy(); d = ImageDraw.Draw(im)
        tr = [P(cx + R * math.sin(math.radians(t)), cz + R * math.cos(math.radians(t))) for t in range(0, 361, 6)]
        d.line(tr, fill=(255, 255, 255), width=2)
        X, Y = P(x, z); Xc, Yc = P(cx, cz)
        vx, vy = Xc - X, Yc - Y; L = math.hypot(vx, vy); vx, vy = vx / L, vy / L
        for s in (-0.45, 0.45):  # view cone toward the centre
            cs, sn = math.cos(s), math.sin(s)
            d.line([(X, Y), (X + 70 * (vx * cs - vy * sn), Y + 70 * (vx * sn + vy * cs))], fill=YEL, width=3)
        d.ellipse([X - 11, Y - 11, X + 11, Y + 11], fill=YEL, outline=(0, 0, 0), width=3)
        d.text((X0, Y0 + M + 16), f"camera x {x:.0f}  z {z:.0f}", font=F(26, "Bold"), fill=YEL)
        enc.stdin.write(im.tobytes())
    enc.stdin.close(); enc.wait()
    out = os.path.join(S2, "cubiomes_vs_game.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", ov, "-i", clip, "-filter_complex",
                    "[1:v]scale=960:540,fps=30[g];[0:v][g]overlay=60:220:shortest=1", "-c:v", "libx264", "-crf", "18",
                    "-pix_fmt", "yuv420p", "-an", out], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-sseof", "-0.1", "-i", out, "-frames:v", "1",
                    os.path.join(S2, "cubiomes_vs_game_final.png")], check=True)
    print("wrote cubiomes_vs_game.mp4")


# ---------------------------------------------------------------- gag overlays (transparent PNGs, 1920x1080)
def canvas():
    return Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))


def outlined(d, xy, text, font, fill, stroke=8, anchor="mm"):
    d.text(xy, text, font=font, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0))


def stamp(text, sub, path, col=RED, angle=-12):
    im = Image.new("RGBA", (1400, 500), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([20, 20, 1380, 480], radius=30, outline=col + (255,), width=18)
    d.text((700, 210), text, font=F(150, "Black"), fill=col + (255,), anchor="mm")
    if sub:
        d.text((700, 370), sub, font=F(80, "Black"), fill=col + (255,), anchor="mm")
    im = im.rotate(angle, expand=True, resample=Image.BICUBIC)
    c = canvas(); c.alpha_composite(im, ((1920 - im.width) // 2, (1080 - im.height) // 2)); c.save(path)


def side_eye(d, cx, cy, r):
    for dx in (-r * 1.25, r * 1.25):
        d.ellipse([cx + dx - r, cy - r * 0.62, cx + dx + r, cy + r * 0.62], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=6)
        d.ellipse([cx + dx + r * 0.25, cy - r * 0.3, cx + dx + r * 0.85, cy + r * 0.3], fill=(20, 20, 20, 255))
        d.line([(cx + dx - r, cy - r * 0.55), (cx + dx + r, cy - r * 0.75)], fill=(0, 0, 0, 255), width=10)


def crown(path):
    c = canvas(); d = ImageDraw.Draw(c); u = 26; X, Y = 960 - 8 * u, 300  # pixel-art crown, 16x10 units
    gold, dark, gem = (255, 205, 60, 255), (190, 130, 20, 255), (230, 40, 70, 255)
    rows = ["X......XX......X", "XX....XXXX....XX", "XXX..XXXXXX..XXX", "XXXXXXXXXXXXXXXX", "XXXXXXXXXXXXXXXX",
            "XXGXXXXGGXXXXGXX", "XXXXXXXXXXXXXXXX", "DDDDDDDDDDDDDDDD"]
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != ".":
                col = {"X": gold, "D": dark, "G": gem}[ch]
                d.rectangle([X + i * u, Y + j * u, X + (i + 1) * u - 1, Y + (j + 1) * u - 1], fill=col)
    c.save(path)


def titles_stack(fps=30, secs=16):
    """V006: the five titles stack up, each "real" bigger, then a sixth one types itself."""
    titles = [("The Rarest Biome in Minecraft", 0), ("the rarest biome in Minecraft 1.17", 0),
              ("The REAL Rarest Biome in Minecraft", 1), ("the REAL, real rarest biome in Minecraft", 2),
              ("the REAL, real, real rarest biome in Minecraft", 3)]
    sixth = "the REAL, real, real, real rarest biome...?"
    enc, last = encoder(os.path.join(GAGS, "V006_titles_stack.mp4"), fps), None
    for f in range(secs * fps):
        t = f / fps; im = Image.new("RGB", (1920, 1080), BG); d = ImageDraw.Draw(im)
        for i, (txt, reals) in enumerate(titles):
            if t < 0.6 + i * 0.9:
                continue
            pop = min(1, (t - 0.6 - i * 0.9) / 0.25); sz = int((40 + reals * 9) * (0.6 + 0.4 * pop))
            Y = 120 + i * 140
            d.rounded_rectangle([200, Y - 10, 1720, Y + 100], radius=18, fill=(28, 33, 42))
            d.text((240, Y + 45), txt, font=F(sz, "Bold"), fill=YEL if reals else FG, anchor="lm")
        if t > 6.0:
            n = min(len(sixth), int((t - 6.0) * 22)); Y = 120 + 5 * 140
            d.rounded_rectangle([200, Y - 10, 1720, Y + 100], radius=18, outline=RED, width=4)
            d.text((240, Y + 45), sixth[:n] + ("|" if f % 20 < 10 else ""), font=F(54, "Bold"), fill=RED, anchor="lm")
        enc.stdin.write(im.tobytes()); last = im
    enc.stdin.close(); enc.wait(); last.save(os.path.join(GAGS, "V006_titles_stack_final.png"))


def gags():
    os.makedirs(GAGS, exist_ok=True); G = lambda n: os.path.join(GAGS, n)
    stamp("SOURCE:", "trust me bro", G("V011_trust_me_bro_stamp.png"))
    c = canvas(); d = ImageDraw.Draw(c); outlined(d, (960, 470), "43%", F(330, "Black"), RED + (255,), 14)
    outlined(d, (960, 700), "oops", F(90, "Bold"), FG + (255,), 8); c.save(G("V041_43_percent_oops.png"))
    c = canvas(); d = ImageDraw.Draw(c); outlined(d, (960, 470), "nuanced", F(220, "Black"), YEL + (255,), 12)
    d.text((960, 650), "(very)", font=F(60, "Bold"), fill=MUT + (255,), anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0))
    c.save(G("V032_nuanced.png"))
    c = canvas(); d = ImageDraw.Draw(c); side_eye(d, 1640, 900, 60)
    outlined(d, (1640, 1010), "no judgement", F(44, "Bold"), FG + (255,), 6); c.save(G("V033_no_judgement.png"))
    c = canvas(); d = ImageDraw.Draw(c)
    d.rounded_rectangle([560, 870, 1360, 1000], radius=24, fill=(0, 0, 0, 190))
    d.text((960, 935), "four hours for this", font=F(64, "Bold"), fill=FG + (255,), anchor="mm"); c.save(G("V052_four_hours_for_this.png"))
    for k, sub in enumerate(("", "blocks walked: a lot")):
        c = canvas(); d = ImageDraw.Draw(c); d.rounded_rectangle([1400, 40, 1880, 170 if sub else 110], radius=18, fill=(0, 0, 0, 190))
        d.text((1430, 75), "worlds walked: 215,000", font=F(34, "Bold"), fill=YEL + (255,), anchor="lm")
        if sub:
            d.text((1430, 135), sub, font=F(30), fill=FG + (255,), anchor="lm")
        c.save(G(f"V037_counter_{k + 1}.png"))
    crown(G("SPOILER_V056_crown.png"))
    c = canvas(); d = ImageDraw.Draw(c)
    d.rounded_rectangle([160, 380, 1760, 700], radius=30, fill=(18, 18, 18, 235))
    d.text((960, 500), "the REAL, real, real, real rarest biome", font=F(72, "Bold"), fill=FG + (255,), anchor="mm")
    d.text((960, 610), "Khiem  ·  Minecraft 26.3, proven", font=F(40), fill=MUT + (255,), anchor="mm")
    c.save(G("V083_real_real_real_real_title.png"))
    titles_stack()
    print("wrote gags to", GAGS)


if __name__ == "__main__":
    what = sys.argv[1:]
    if "compare" in what:
        compare()
    if "charts" in what:
        charts()
    if "maps" in what:
        maps()
    if "side" in what:
        side()
    if "gags" in what:
        gags()
