"""Pilot sizing for the two-phase estimator on the exact capsule model: sparse stride-4 everywhere + exact on a subset."""
import glob, math, sys
import numpy as np, pandas as pd
import certify as ct
R0, R, RAYS = 4000.0, 20000.0, 4
NAMES = {int(a): b for a, b in (l.strip().split(",", 1) for l in open("out/names.csv"))}; INV = {v: k for k, v in NAMES.items()}
files = sorted(glob.glob("out/exact/ex_[0-9]*.csv"), key=lambda p: int(p.split("_")[-1][:-4]))
df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
order = df["seed"].drop_duplicates().to_numpy(); n = len(order)
df["si"] = df["seed"].map(pd.Series(np.arange(n), index=order))
def mat(b, m, lv):
    s = df[(df.biome == b) & (df["mode"] == m) & (df.level == lv)]
    A = np.full((n, RAYS), np.inf); A[s["si"].to_numpy(), s["ray"].to_numpy()] = s["dist"].to_numpy(); return A
EXACT_COST_RATIO = float(sys.argv[1]) if len(sys.argv) > 1 else 12.0     # exact ray cost / stride-4 ray cost (enumeration is not free)
EPS = float(sys.argv[2]) if len(sys.argv) > 2 else 0.02
print(f"pilot {n} seeds; target eps {EPS:.0%}; exact/sparse cost ratio {EXACT_COST_RATIO}")
print(f"{'biome':26s} {'r':>4s} {'M_exact':>9s} {'ev/ray':>6s} {'sd(v)/sd(u)':>11s} {'N seeds':>8s} {'n_exact':>8s} {'exact-only N':>12s} {'saving':>7s}")
for nm in ["mushroom_fields", "pale_garden", "windswept_gravelly_hills", "stony_peaks", "ice_spikes", "eroded_badlands"]:
    b = INV[nm]
    for m in (0, 64, 128):
        D1, D4 = mat(b, m, 1), mat(b, m, 4)
        t1 = ct.Term(1.0, *ct.stats(D1, R0, R)); t4 = ct.Term(1.0, *ct.stats(D4, R0, R))
        est1 = ct.combo([t1])[0]
        u = ct._infl(t4); v = ct._infl(t1) - u
        a, bb, c = float(u.var(ddof=1)), float(v.var(ddof=1)), float(np.cov(u, v)[0, 1])
        vt = (EPS * est1 / 1.96) ** 2
        best = None
        for nc in np.unique(np.geomspace(100, 400000, 200).astype(int)):
            room = vt - bb / nc
            if room <= 0: continue
            N = max((a + 2 * c) / room, nc)
            cost = N + EXACT_COST_RATIO * nc
            if best is None or cost < best[0]: best = (cost, N, nc)
        # exact everywhere: variance of IF_1
        a1 = float(ct._infl(t1).var(ddof=1)); N1 = a1 / vt
        _, N, nc = best
        print(f"{nm:26s} {m:4d} {est1:9.0f} {t1.E.sum() / (n * RAYS):6.3f} {math.sqrt(bb / a):11.2f} {N / RAYS:8.0f} {nc / RAYS:8.0f} {N1 / RAYS:12.0f} {N1 * EXACT_COST_RATIO / best[0]:6.1f}x")
