from vstyle import *
import matplotlib.patheffects as pe

res = json.load(open(D + "results.json"))
lam = {r["name"]: r for r in json.load(open(D + "lam.json"))}
vd = json.load(open(D + "video_data.json"))
resn = {r["name"]: r for r in res}
names = {int(a): b for a, b in (l.strip().split(",", 1) for l in open(D + "names.csv"))}
inv = {v: k for k, v in names.items()}
COL = np.fromfile(D + "colors.bin", dtype=np.uint8).reshape(256, 3)


def bcol(name):
    c = COL[inv[name]] / 255.0
    return tuple(c)


def fmt(n):
    return f"{int(round(n)):,}"


# ---------------------------------------------------------------- scene 0
def s_title():
    fig, ax = canvas()
    T(ax, 640, 215, "How rare is a", size=48, weight="bold", ha="center")
    T(ax, 640, 285, "Minecraft biome?", size=64, weight="bold", color=ORANGE, ha="center")
    T(ax, 640, 440, "A Monte Carlo on 20,000 real worlds", size=26, color=FG, ha="center")
    T(ax, 640, 492, "Cubiomes  |  Minecraft 1.21  |  80,000 straight-line walks", size=17, color=MUT, ha="center")
    return grab(fig)


# ---------------------------------------------------------------- scene 1
def s_two_things():
    fig, ax = canvas(); tag(ax, "1 / The problem")
    T(ax, 640, 78, "Two biomes, same area share. Same rarity?", size=34, weight="bold", ha="center")
    rng = np.random.default_rng(3)
    p = 0.12
    for k, (x0, label) in enumerate([(130, "A: 36 small patches"), (690, "B: 1 big patch")]):
        pax = fig.add_axes([x0 / W, 1 - 560 / H, 460 / W, 400 / H], facecolor="#171C24")
        pax.set_xlim(0, 1.15); pax.set_ylim(0, 1); pax.set_xticks([]); pax.set_yticks([])
        for s in pax.spines.values():
            s.set_color(GRID)
        if k == 0:
            n = 36; r = math.sqrt(p / n / math.pi) * 1.0
            pts = []
            while len(pts) < n:
                c = rng.uniform(0.05, 0.95, 2) * np.array([1.15, 1.0])
                if all(np.hypot(*(c - q)) > 2.4 * r for q in pts):
                    pts.append(c)
            for c in pts:
                pax.add_patch(Circle(c, r * 1.07, color=TEAL, alpha=0.95))
        else:
            r = math.sqrt(p / math.pi)
            pax.add_patch(Circle((0.62, 0.45), r * 1.07, color=ORANGE, alpha=0.95))
        T(ax, x0 + 230, 580, label, size=22, weight="bold", ha="center")
    T(ax, 640, 640, "Same area share p. B is far harder to stumble on.", size=26, ha="center")
    T(ax, 640, 682, "Area alone is not rarity: size and clumping matter too.", size=20, color=MUT, ha="center")
    return grab(fig)


# ---------------------------------------------------------------- scene 2
def s_definition():
    fig, ax = canvas(); tag(ax, "2 / The idea")
    T(ax, 640, 90, "Rarity = how far you have to walk", size=42, weight="bold", ha="center")
    T(ax, 90, 210, "Start at spawn. Walk in a straight line.", size=30)
    T(ax, 90, 262, r"$D$ = distance to the first block of the biome you want", size=30)
    T(ax, 90, 380, r"$S(r)=P(D>r)$", size=40, color=ORANGE)
    T(ax, 480, 392, "chance you still have not found it after r blocks", size=24, color=MUT)
    T(ax, 90, 480, r"$h(r)$", size=40, color=TEAL)
    T(ax, 480, 492, "chance per block of finding it now, given you have not yet", size=24, color=MUT)
    T(ax, 90, 600, "Spawn is not uniform, so near spawn and far from spawn can differ.", size=24)
    T(ax, 90, 645, "Keeping the whole curve keeps both.", size=24, color=FG, weight="bold")
    return grab(fig)


# ---------------------------------------------------------------- scene 3 (anim)
class MapScene:
    secs = 17.0

    def __init__(self):
        fig, ax = canvas(); self.fig = fig; self.ax = ax
        tag(ax, "3 / One real seed, four rays")
        raw = np.fromfile(D + "map.bin", dtype=np.int32)
        n = int(raw[0]); ids = raw[4:].reshape(n, n)
        img = COL[np.clip(ids, 0, 255)]
        m = fig.add_axes([40 / W, 1 - 700 / H, 620 / W, 620 / H])
        m.imshow(img, extent=[-10000, 10000, 10000, -10000], interpolation="nearest")
        m.axis("off"); self.m = m
        m.plot([0], [0], "o", color="white", ms=9, mec="black", mew=2, zorder=6)
        base = 0.27455432669486657
        self.angles = [base + k * math.pi / 2 for k in range(4)]
        self.lines = []
        for k, a in enumerate(self.angles):
            ln, = m.plot([0, 0], [0, 0], color="white" if k == 0 else "#FFFFFF",
                         lw=3.2 if k == 0 else 1.4, alpha=1.0 if k == 0 else 0.55,
                         solid_capstyle="round", zorder=5,
                         path_effects=[pe.withStroke(linewidth=5.5 if k == 0 else 3, foreground="black")])
            self.lines.append(ln)
        self.hits = [("jungle", 304), ("desert", 4640), ("mushroom_fields", 5776),
                     ("ice_spikes", 8752), ("snowy_plains", 9232)]
        T(ax, 710, 80, "First hit along the ray", size=28, weight="bold")
        T(ax, 710, 124, "the thick white line, walked from spawn", size=18, color=MUT)
        self.markers = []; self.rows = []
        for i, (nm, d) in enumerate(self.hits):
            a = self.angles[0]
            mk, = m.plot([d * math.cos(a)], [d * math.sin(a)], "o", ms=13, mfc=bcol(nm), mec="white",
                         mew=2.5, zorder=7, visible=False)
            self.markers.append(mk)
            y = 185 + i * 72
            chip = Rectangle((710, y), 36, 36, facecolor=bcol(nm), edgecolor="white", lw=2, visible=False)
            ax.add_patch(chip)
            t1 = T(ax, 760, y, pretty(nm), size=22, visible=False)
            t2 = T(ax, 1240, y, f"D = {fmt(d)}", size=22, color=ORANGE, ha="right", weight="bold", visible=False)
            self.rows.append((chip, t1, t2))
        self.foot = T(ax, 710, 585, "Mushroom fields: first seen\nat D = 5,776 blocks on this ray.",
                      size=22, color=FG, visible=False)
        self.foot2 = T(ax, 710, 660, "Other rays from the same spawn give other D.", size=17, color=MUT, visible=False)

    def frame(self, t):
        prog = min(1.0, max(0.0, (t - 0.8) / 11.0))
        rmax = 9600 * prog
        for k, ln in enumerate(self.lines):
            a = self.angles[k]
            ln.set_data([0, rmax * math.cos(a)], [0, rmax * math.sin(a)])
        for (nm, d), mk, (chip, t1, t2) in zip(self.hits, self.markers, self.rows):
            vis = rmax >= d
            mk.set_visible(vis); chip.set_visible(vis); t1.set_visible(vis); t2.set_visible(vis)
        done = t > 12.5
        self.foot.set_visible(done); self.foot2.set_visible(t > 13.8)
        return grab(self.fig)


# ---------------------------------------------------------------- scene 4
def _rw():
    p = D + "rw.npz"
    if os.path.exists(p):
        z = np.load(p); return z["t"], z["ratio"], z["path"]
    rng = np.random.default_rng(11)
    n = 4_000_000
    st = rng.integers(0, 4, n)
    dx = np.array([1, -1, 0, 0]); dy = np.array([0, 0, 1, -1])
    x = np.cumsum(dx[st]); y = np.cumsum(dy[st])
    key = (x + 2**20) * (2**22) + (y + 2**20)
    _, first = np.unique(key, return_index=True)
    first = np.sort(first)
    ts = np.unique(np.logspace(1.5, math.log10(n - 1), 120).astype(int))
    vis = np.searchsorted(first, ts, side="right") + 1
    ratio = vis / (ts + 1)
    np.savez(p, t=ts, ratio=ratio, path=np.stack([x[:60000], y[:60000]]))
    return ts, ratio, np.stack([x[:60000], y[:60000]])


def s_walk_choice():
    ts, ratio, path = _rw()
    fig, ax = canvas(); tag(ax, "4 / Why a straight line, not Brownian motion")
    T(ax, 640, 78, "A random walk keeps re-covering its own ground", size=34, weight="bold", ha="center")
    pax = fig.add_axes([60 / W, 1 - 520 / H, 400 / W, 380 / H], facecolor="#171C24")
    pax.plot(path[0], path[1], color=TEAL, lw=0.5, alpha=0.9)
    L = np.hypot(*(path[:, -1] - path[:, 0]))
    pax.set_aspect("equal"); pax.set_xticks([]); pax.set_yticks([])
    for s in pax.spines.values():
        s.set_color(GRID)
    T(ax, 260, 538, "random walk, 60,000 steps", size=18, color=TEAL, ha="center")
    lax = fig.add_axes([60 / W, 1 - 640 / H, 400 / W, 50 / H], facecolor="#171C24")
    lax.plot([0, 60000], [0, 0], color=ORANGE, lw=3); lax.set_xlim(0, 60000); lax.set_xticks([]); lax.set_yticks([])
    for s in lax.spines.values():
        s.set_color(GRID)
    T(ax, 260, 650, "straight line, same 60,000 steps", size=18, color=ORANGE, ha="center")
    cax = sub_axes(fig, 560, 140, 660, 340)
    cax.set_xscale("log")
    cax.plot(ts, ratio, color=TEAL, lw=3.2, label="random walk")
    cax.axhline(1.0, color=ORANGE, lw=3.2, label="straight line")
    cax.set_ylim(0, 1.08); cax.set_xlim(30, 4e6)
    cax.set_xlabel("steps taken", color=MUT, fontsize=15); cax.set_ylabel("new ground per step", color=MUT, fontsize=15)
    cax.grid(color=GRID, lw=0.8)
    cax.legend(facecolor=BG, edgecolor=GRID, labelcolor=FG, fontsize=15, loc="lower left")
    T(ax, 560, 560, r"New ground grows like $t/\ln t$, not $t$.", size=26)
    T(ax, 560, 610, "And the result would depend on step size.", size=22, color=MUT)
    T(ax, 560, 652, "Real exploring is closer to a line, so use a line.", size=22, color=MUT)
    return grab(fig)


# ---------------------------------------------------------------- scene 5
def s_pipeline():
    fig, ax = canvas(); tag(ax, "5 / The Monte Carlo")
    T(ax, 640, 80, "One pass finds every biome at once", size=36, weight="bold", ha="center")
    boxes = [("20,000\nrandom seeds", BLUE), ("spawn point\n(Cubiomes)", TEAL),
             ("4 rays\n16-block steps\nout to 20,000", ORANGE), ("first-hit D\nfor every biome", PINK)]
    x0, w, gap = 55, 265, 38
    for i, (s, c) in enumerate(boxes):
        x = x0 + i * (w + gap)
        ax.add_patch(FancyBboxPatch((x, 190), w, 190, boxstyle="round,pad=0,rounding_size=18",
                                    facecolor="#171C24", edgecolor=c, lw=3))
        T(ax, x + w / 2, 285, s, size=22, color=FG, ha="center", va="center", weight="bold", linespacing=1.3)
        if i < 3:
            ax.add_patch(FancyArrowPatch((x + w + 6, 285), (x + w + gap - 6, 285), arrowstyle="-|>",
                                         mutation_scale=22, color=MUT, lw=2.5))
    stats = [("80,000", "rays"), ("~100 million", "biome lookups"), ("4 min 43 s", "on 2 CPU cores")]
    for i, (a, b) in enumerate(stats):
        x = 210 + i * 380
        T(ax, x, 450, a, size=38, weight="bold", color=ORANGE, ha="center")
        T(ax, x, 505, b, size=20, color=MUT, ha="center")
    T(ax, 640, 610, "Biome sampled at y = 63. Walks that never find a biome are censored at 20,000.", size=19,
      color=MUT, ha="center")
    return grab(fig)


# ---------------------------------------------------------------- scene 6 (anim)
class SurvScene:
    secs = 17.0
    order = [("plains", TEAL), ("forest", GREEN), ("jungle", YELLOW), ("desert", ORANGE),
             ("snowy_plains", BLUE), ("ice_spikes", PURPLE), ("mushroom_fields", PINK)]

    def __init__(self):
        fig, ax = canvas(); self.fig = fig
        tag(ax, "6 / The survival curve S(r), from real worlds")
        T(ax, 640, 66, "Chance you still have not found it after r blocks", size=30, weight="bold", ha="center")
        a = sub_axes(fig, 110, 125, 950, 440); self.a = a
        a.set_xlim(0, 20000); a.set_ylim(0, 1.02)
        a.set_xlabel("blocks walked from spawn", color=MUT, fontsize=16)
        a.set_yticks([0, 0.25, 0.5, 0.75, 1.0]); a.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
        a.set_xticks(range(0, 20001, 5000)); a.set_xticklabels(["0", "5,000", "10,000", "15,000", "20,000"])
        a.grid(color=GRID, lw=0.8)
        self.grid = np.array(vd["grid"])
        self.lines = []; self.labels = []
        for nm, c in self.order:
            ln, = a.plot([], [], color=c, lw=3.6); self.lines.append(ln)
            y = vd["curves"][nm][-1]
            ly = 125 + 440 * (1 - (y / 1.02))
            lab = "plains, forest" if nm == "plains" else pretty(nm)
            self.labels.append(ax.text(1072, ly, lab, color=c, fontsize=16, fontweight="bold", va="center", visible=(False if nm != "forest" else False)))
            if nm == "forest": self.labels[-1].set_text("")
        self.note = T(ax, 640, 640, "", size=24, ha="center")
        self.note2 = T(ax, 640, 682, "", size=19, color=MUT, ha="center")

    def frame(self, t):
        prog = min(1.0, max(0.0, (t - 0.6) / 11.0))
        k = int(prog * (len(self.grid) - 1)) + 1
        for (nm, c), ln in zip(self.order, self.lines):
            ln.set_data(self.grid[:k], vd["curves"][nm][:k])
        if prog >= 1.0:
            for lb in self.labels:
                lb.set_visible(True)
        mush = vd["curves"]["mushroom_fields"][-1]
        if t > 12.8:
            self.note.set_text(f"Mushroom fields: {mush*100:.0f}% of walks found none in 20,000 blocks.")
            self.note.set_color(PINK)
        if t > 14.5:
            self.note2.set_text("Plains and forest die off within a few thousand blocks.")
        return grab(self.fig)


# ---------------------------------------------------------------- scene 7
def s_hazard():
    fig, ax = canvas(); tag(ax, "7 / Both numbers, in one picture")
    T(ax, 640, 70, "Near spawn it is biased. After ~2,000 blocks it is flat.", size=32, weight="bold", ha="center")
    a = sub_axes(fig, 100, 130, 760, 470)
    mid = np.array(vd["haz_mid"])
    spec = [("desert", ORANGE, 12000), ("plains", TEAL, 6000), ("ice_spikes", PURPLE, 12000), ("mushroom_fields", PINK, 12000)]
    for nm, c, lim in spec:
        M = lam[nm]["M"]
        h = [None if x is None else x * M for x in vd["hazard"][nm]]
        xs = [m for m, v in zip(mid, h) if v is not None and m <= lim]
        ys = [v for m, v in zip(mid, h) if v is not None and m <= lim]
        a.plot(xs, ys, "-o", color=c, lw=3, ms=7)
    a.axhline(1.0, color=MUT, lw=1.5, ls="--")
    a.set_ylim(0, 2.0); a.set_xlim(0, 14800)
    a.set_xlabel("blocks from spawn", color=MUT, fontsize=15)
    a.set_ylabel("hazard relative to the flat level", color=MUT, fontsize=14)
    a.grid(color=GRID, lw=0.8)
    T(ax, 900, 150, "Number 1", size=22, color=MUT, weight="bold")
    T(ax, 900, 188, "spawn factor", size=30, weight="bold", color=ORANGE)
    T(ax, 900, 236, "hazard near spawn / flat hazard", size=17, color=MUT)
    rows = [("desert", "desert", ORANGE), ("plains", "plains", TEAL), ("ice_spikes", "ice spikes", PURPLE), ("mushroom_fields", "mushroom fields", PINK)]
    for i, (nm, lab, c) in enumerate(rows):
        sp = lam[nm]["spawn"]
        T(ax, 900, 276 + i * 36, f"{lab}", size=20, color=c, weight="bold")
        T(ax, 1240, 276 + i * 36, f"x{sp:.2f}", size=20, ha="right", weight="bold", color=c)
    T(ax, 900, 440, "Number 2", size=22, color=MUT, weight="bold")
    T(ax, 900, 478, "mean walk", size=30, weight="bold", color=ORANGE)
    T(ax, 900, 526, "1 / flat hazard, in blocks", size=17, color=MUT)
    T(ax, 900, 572, "Spawn is picked on land-like\nclimate, so oceans start rarer.", size=18, color=FG)
    return grab(fig)


# ---------------------------------------------------------------- scene 8
def s_ranking():
    fig, ax = canvas(); tag(ax, "8 / The ranking")
    T(ax, 640, 62, "Expected blocks to walk in a straight line", size=32, weight="bold", ha="center")
    order = ["pale_garden", "mushroom_fields", "windswept_gravelly_hills", "stony_peaks", "ice_spikes",
             "eroded_badlands", "mangrove_swamp", "cherry_grove", "desert", "snowy_plains", "jungle",
             "plains", "forest"]
    a = sub_axes(fig, 330, 130, 700, 510)
    a.set_xscale("log"); a.set_xlim(1e3, 6e5)
    ys = np.arange(len(order))[::-1]
    for y, nm in zip(ys, order):
        r = lam[nm]
        a.barh(y, r["M"] - 1e3, left=1e3, color=ORANGE if y > 8 else (TEAL if y > 3 else BLUE), height=0.68)
        a.plot([r["M_lo"], r["M_hi"]], [y, y], color="white", lw=2)
        a.text(r["M"] * 1.12 if r["M"] < 2.5e5 else r["M"] * 0.45, y, f"{r['M']/1000:.1f}k" if r["M"] >= 1e4 else f"{r['M']/1000:.1f}k",
               color=FG if r["M"] < 2.5e5 else BG, fontsize=14, va="center", fontweight="bold")
        a.text(1.30, y, f"x{r['spawn']:.2f}", transform=a.get_yaxis_transform(), clip_on=False, fontsize=15,
               ha="right", va="center", color=PINK if r["spawn"] < 1 else MUT)
    a.set_yticks(ys); a.set_yticklabels([pretty(n) for n in order], color=FG, fontsize=15)
    a.tick_params(axis="y", length=0)
    a.set_xticks([1e3, 1e4, 1e5]); a.set_xticklabels(["1k", "10k", "100k"])
    a.grid(color=GRID, lw=0.8, axis="x")
    T(ax, 1240, 108, "spawn factor", size=15, ha="right", color=MUT, weight="bold")
    T(ax, 60, 686, "Underground biomes (deep dark, lush caves, dripstone) left out: y = 63 cannot measure them.",
      size=15, color=MUT)
    return grab(fig)


# ---------------------------------------------------------------- scene 9
def s_twist():
    fig, ax = canvas(); tag(ax, "9 / A correction")
    T(ax, 640, 66, "My first metric, the mean free path, was wrong", size=34, weight="bold", ha="center")
    T(ax, 640, 120, "Expected: flat hazard = 1 / (mean gap between patches). Data disagrees.", size=20, color=MUT, ha="center")
    heads = [("biome", 90, "left"), ("mean gap", 560, "right"), ("mean walk", 800, "right"), ("gap / walk", 1100, "right")]
    for h, x, al in heads:
        T(ax, x, 175, h, size=20, color=MUT, weight="bold", ha=al)
    ax.plot([80, 1120], [212, 212], color=GRID, lw=2)
    rows = ["plains", "desert", "snowy_plains", "jungle", "ice_spikes", "mushroom_fields"]
    for i, nm in enumerate(rows):
        ell = resn[nm]["ell"]; M = lam[nm]["M"]; y = 228 + i * 50
        T(ax, 90, y, pretty(nm), size=26)
        T(ax, 560, y, fmt(ell), size=26, ha="right")
        T(ax, 800, y, fmt(M), size=26, ha="right")
        T(ax, 1100, y, f"{ell/M:.2f}", size=26, ha="right", weight="bold", color=ORANGE)
    T(ax, 90, 560, "Likely reason: patches cluster, so gaps are very uneven.", size=24)
    T(ax, 90, 604, "A walker is likelier to start inside a long gap (inspection paradox).", size=24)
    T(ax, 90, 652, r"waiting time $=E[g^2]\,/\,(2E[g])$, much larger than the mean gap $E[g]$", size=22, color=MUT)
    return grab(fig)


# ---------------------------------------------------------------- scene 10
def s_proof():
    fig, ax = canvas(); tag(ax, "10 / Does it converge?  Yes, with a proof")
    T(ax, 90, 80, r"For one seed let  $X_i=\min(D_i,R)\in[0,R]$,   i.i.d. across seeds", size=28)
    T(ax, 90, 150, r"Restricted mean  $\mu=E[X]=\int_0^R S(r)\,dr$", size=28)
    T(ax, 90, 238, "Hoeffding (bounded, no CLT needed):", size=22, color=MUT)
    T(ax, 90, 276, r"$P\left(|\hat\mu-\mu|\geq\varepsilon\right)\leq 2\exp\left(-\frac{2N\varepsilon^2}{R^2}\right)$", size=32, color=ORANGE)
    T(ax, 90, 362, r"$\Rightarrow\; N\geq \frac{R^2\ln(2/\delta)}{2\varepsilon^2}$", size=32, color=ORANGE)
    T(ax, 90, 468, "DKW for the whole curve:", size=22, color=MUT)
    T(ax, 90, 506, r"$\sup_r|\hat S(r)-S(r)|\leq\sqrt{\ln(2/\delta)/(2N)}$", size=30, color=TEAL)
    T(ax, 90, 632, "The cap R is fixed, so Kaplan-Meier is just the empirical survival.", size=18, color=MUT)
    T(ax, 90, 666, "Error falls like 1/sqrt(N): O(N^(-1/2)). Cost is O(N K R / h) lookups.", size=18, color=MUT)
    return grab(fig)


def s_converge():
    fig, ax = canvas(); tag(ax, "10 / Does it converge?  Measured")
    T(ax, 640, 62, "Error vs number of seeds, measured on the real data", size=32, weight="bold", ha="center")
    a = sub_axes(fig, 100, 120, 780, 500)
    a.set_xscale("log"); a.set_yscale("log")
    Ns = np.array(vd["conv"]["mushroom_fields"]["N"], float)
    for nm, c in [("mushroom_fields", PINK), ("desert", ORANGE)]:
        cv = vd["conv"][nm]
        a.plot(Ns, cv["rms"], "o-", color=c, lw=3, ms=8, label=f"{pretty(nm)}  slope {cv['slope']:.2f}")
    ref = vd["conv"]["desert"]["rms"][0] * (Ns / Ns[0]) ** -0.5
    a.plot(Ns, ref, "--", color=MUT, lw=2, label="theory  slope -0.50")
    hb = 20000 * np.sqrt(np.log(40) / (2 * Ns))
    a.plot(Ns, hb, ":", color=TEAL, lw=3, label="Hoeffding worst case")
    a.set_xlabel("seeds N", color=MUT, fontsize=16); a.set_ylabel("RMS error of mean walk (blocks)", color=MUT, fontsize=15)
    a.grid(color=GRID, lw=0.8, which="both")
    a.legend(facecolor=BG, edgecolor=GRID, labelcolor=FG, fontsize=14, loc="lower left")
    T(ax, 920, 150, "Measured slope", size=20, color=MUT)
    T(ax, 920, 188, "-0.52 and -0.52", size=32, weight="bold", color=ORANGE)
    T(ax, 920, 240, "theory says -0.5", size=20, color=MUT)
    T(ax, 920, 320, "100x more seeds\n= 10x less error", size=26)
    T(ax, 920, 430, "Worst-case bound for\n+-100 blocks at 95%:", size=19, color=MUT)
    T(ax, 920, 500, f"{fmt(vd['hoeffding']['n_100'])} seeds", size=30, weight="bold", color=TEAL)
    T(ax, 920, 556, "The real spread is far smaller,\nso 20,000 seeds gave about\n+-25 to 65 blocks.", size=17, color=MUT)
    return grab(fig)


# ---------------------------------------------------------------- scene 11
def s_rays():
    fig, ax = canvas(); tag(ax, "11 / More seeds or more rays?")
    T(ax, 640, 62, "I guessed seeds dominate. The pilot said no.", size=34, weight="bold", ha="center")
    v = vd["varcomp"]
    a = sub_axes(fig, 120, 140, 520, 430)
    a.bar([0, 1], [v["med_sd_seed"], v["med_sd_ray"]], color=[BLUE, ORANGE], width=0.55)
    a.set_xticks([0, 1]); a.set_xticklabels(["between seeds", "between rays\nin one seed"], color=FG, fontsize=16)
    a.set_ylabel("spread of D (blocks)", color=MUT, fontsize=15); a.grid(color=GRID, axis="y")
    for i, val in enumerate([v["med_sd_seed"], v["med_sd_ray"]]):
        a.text(i, val + 120, fmt(val), ha="center", color=FG, fontsize=18, fontweight="bold")
    T(ax, 700, 140, r"$\mathrm{Var}(\hat\mu)=\frac{\sigma_{seed}^2}{N}+\frac{\sigma_{ray}^2}{NK}$", size=32, color=ORANGE)
    T(ax, 700, 230, r"$K^*=\sqrt{\frac{c_0}{c_1}\cdot\frac{\sigma_{ray}^2}{\sigma_{seed}^2}}$", size=32, color=ORANGE)
    T(ax, 700, 372, f"ray spread is {v['ratio']:.1f}x seed spread", size=24)
    T(ax, 700, 414, "seed setup costs about one ray (4.3 ms vs 4.6 ms)", size=17, color=MUT)
    T(ax, 700, 470, f"best K = {v['kstar_median']:.1f}", size=34, weight="bold", color=TEAL)
    T(ax, 700, 526, "so I used 4 rays per seed.", size=24)
    T(ax, 700, 580, "Directions from one spawn see\nnearly independent terrain.", size=19, color=MUT)
    return grab(fig)


# ---------------------------------------------------------------- scene 12
def s_trust():
    fig, ax = canvas(); tag(ax, "12 / How I know the code is not lying")
    T(ax, 640, 70, "26 tests, written before the code", size=36, weight="bold", ha="center")
    items = [("An independent Python + ctypes oracle", "reproduces the simulator's output exactly"),
             ("Finer step never finds a biome later", "checked for every seed, ray and biome"),
             ("Biome at spawn is D = 0, one per ray", "and every ray of a seed agrees"),
             ("Censored walks are not recorded as R", "R = 0 keeps only the spawn biome"),
             ("Estimators vs synthetic data", "known restricted mean, variance split, bootstrap coverage"),
             ("Bad arguments fail loudly", "zero rays, bad step, unknown version")]
    for i, (a_, b_) in enumerate(items):
        y = 150 + i * 88
        ax.add_patch(Circle((100, y + 18), 11, color=TEAL))
        T(ax, 130, y - 4, a_, size=25, weight="bold")
        T(ax, 130, y + 32, b_, size=19, color=MUT)
    return grab(fig)


# ---------------------------------------------------------------- scene 13
def s_caveats():
    fig, ax = canvas(); tag(ax, "13 / What this does not tell you")
    T(ax, 640, 70, "Honest limits", size=38, weight="bold", ha="center")
    items = [("Only y = 63.", "No caves, no real mountain peaks. Underground biomes need a depth measure."),
             ("Step 16 misses thin biomes.", "Finer steps raise hit rates by about 1 to 3 points (meadow 36.4 to 39.4 at R = 6,000)."),
             ("Spawn is approximate.", "estimateSpawn, not the grass-based exact spawn."),
             ("One version.", "1.21 with its new biomes. Other versions generate differently."),
             ("Means above 20,000 are extrapolated.", "They assume the flat hazard continues past the cap (it held from 4,000 to 20,000)."),
             ("MC converges to what I defined.", "Step, cap and the straight-ray choice are bias, not Monte Carlo error.")]
    for i, (a_, b_) in enumerate(items):
        y = 150 + i * 90
        T(ax, 90, y, a_, size=26, weight="bold", color=ORANGE)
        T(ax, 90, y + 37, b_, size=18, color=FG)
    return grab(fig)


# ---------------------------------------------------------------- scene 14
def s_outro():
    fig, ax = canvas(); tag(ax, "Summary")
    T(ax, 640, 120, "Rarity is a curve, summarised by two numbers", size=38, weight="bold", ha="center")
    T(ax, 640, 230, "1. spawn factor: how spawn bends the odds near the start", size=26, ha="center", color=TEAL)
    T(ax, 640, 285, "2. mean walk: blocks to expect, once spawn stops mattering", size=26, ha="center", color=ORANGE)
    T(ax, 640, 400, f"Rarest biome measured at sea level: pale garden, about {lam['pale_garden']['M']/1000:.0f}k blocks.", size=26, ha="center")
    T(ax, 640, 452, f"Mushroom fields: about {lam['mushroom_fields']['M']/1000:.0f}k blocks, and spawn makes it x{lam['mushroom_fields']['spawn']:.2f}.",
      size=26, ha="center")
    T(ax, 640, 580, "Maths cannot give you everything.", size=24, color=MUT, ha="center")
    T(ax, 640, 622, "It can tell you exactly how much you do not know.", size=24, color=FG, ha="center", weight="bold")
    return grab(fig)


# registry: (name, kind, builder, secs)
STILLS = [
    ("s00_title", s_title, 6),
    ("s01_two", s_two_things, 11),
    ("s02_def", s_definition, 14),
    ("s04_walk", s_walk_choice, 15),
    ("s05_pipe", s_pipeline, 13),
    ("s07_haz", s_hazard, 17),
    ("s08_rank", s_ranking, 17),
    ("s09_twist", s_twist, 18),
    ("s10a_proof", s_proof, 20),
    ("s10b_conv", s_converge, 18),
    ("s11_rays", s_rays, 17),
    ("s12_trust", s_trust, 15),
    ("s13_cav", s_caveats, 17),
    ("s14_out", s_outro, 13),
]
