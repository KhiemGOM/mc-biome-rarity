"""Exact cell-level capsule model: sparse-sampling bias curve, ranking stability, Steiner width check."""
import glob, json
import numpy as np, pandas as pd
from scipy.stats import spearmanr, kendalltau

R0, R, RAYS = 4000.0, 20000.0, 4
NAMES = {int(a): b for a, b in (l.strip().split(",", 1) for l in open("out/names.csv"))}
files = sorted(glob.glob("out/exact/ex_[0-9]*.csv"), key=lambda p: int(p.split("_")[-1][:-4]))
df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
order = df["seed"].drop_duplicates().to_numpy()
n = len(order)
df["si"] = df["seed"].map(pd.Series(np.arange(n), index=order))
radii = sorted(df["mode"].unique()); levels = sorted(df["level"].unique())

def mat(sub):
    A = np.full((n, RAYS), np.inf)
    A[sub["si"].to_numpy(), sub["ray"].to_numpy()] = sub["dist"].to_numpy()
    return A

def EX(A):
    E = ((A >= R0) & (A <= R)).sum(1).astype(float)
    X = np.where(A >= R0, np.minimum(A, R) - R0, 0.0).sum(1)
    return E, X

rng = np.random.default_rng(3)
W = rng.multinomial(n, np.full(n, 1 / n), size=500).astype(float)
S = {}      # S[(biome, radius, level)] = (E, X)
for (b, m, lv), sub in df.groupby(["biome", "mode", "level"]):
    S[(b, m, lv)] = EX(mat(sub))
biomes = sorted({k[0] for k in S})
def M(b, m, lv):
    E, X = S.get((b, m, lv), (np.zeros(n), np.zeros(n)))
    return X.sum() / E.sum() if E.sum() > 0 else np.nan
def ratio_ci(b, m, lv):     # paired cluster bootstrap of M_lv / M_1
    E1, X1 = S[(b, m, 1)]; E2, X2 = S.get((b, m, lv), (np.zeros(n), np.zeros(n)))
    r = ((W @ X2) / np.maximum(W @ E2, 1)) / ((W @ X1) / np.maximum(W @ E1, 1))
    return np.quantile(r, [0.025, 0.975])

tab = pd.DataFrame(index=[NAMES[b] for b in biomes])
for m in radii:
    for lv in levels:
        tab[f"M_r{m}_k{lv}"] = [M(b, m, lv) for b in biomes]
    tab[f"ev_r{m}"] = [int(S[(b, m, 1)][0].sum()) if (b, m, 1) in S else 0 for b in biomes]
ok = tab[[f"ev_r{m}" for m in radii]].min(axis=1) >= 100
print(f"{n} seeds, {n * RAYS} rays, {int(ok.sum())} biomes with >=100 events in every radius\n")

print("== Sparse-sampling bias: M_stride / M_exact (paired). stride 2 = every 2nd cell, 4 = every 4th (16-block lattice)")
res = {}
for m in radii:
    for lv in (2, 4):
        rat = (tab[f"M_r{m}_k{lv}"] / tab[f"M_r{m}_k1"])[ok] - 1
        res[(m, lv)] = rat
        print(f"r={m:3d} stride {lv}: median bias {100 * rat.median():5.2f}%  mean {100 * rat.mean():5.2f}%  max {100 * rat.max():5.2f}%  min {100 * rat.min():5.2f}%")
print("\n== rare five, bias of the 16-block lattice (stride 4) with 95% paired CI")
five = ["mushroom_fields", "pale_garden", "windswept_gravelly_hills", "stony_peaks", "ice_spikes"]
inv = {v: k for k, v in NAMES.items()}
for nm in five:
    line = []
    for m in radii:
        lo, hi = ratio_ci(inv[nm], m, 4)
        line.append(f"r{m}: {100 * (tab.loc[nm, f'M_r{m}_k4'] / tab.loc[nm, f'M_r{m}_k1'] - 1):+5.1f}% [{100 * (lo - 1):+.1f},{100 * (hi - 1):+.1f}]")
    print(f"{nm:26s}", "  ".join(line))

print("\n== ranking stability: exact (stride 1) vs sparse (stride 4), per radius")
for m in radii:
    a, b = tab.loc[ok, f"M_r{m}_k1"], tab.loc[ok, f"M_r{m}_k4"]
    top = lambda s: list(s.sort_values(ascending=False).index[:5])
    print(f"r={m:3d}: Spearman {spearmanr(a, b)[0]:.4f}  Kendall {kendalltau(a, b)[0]:.4f}  top5 same order: {top(a) == top(b)}")
    print("        exact top5 :", top(a))
    print("        sparse top5:", top(b))

print("\n== exact model ranking: centerline vs capsule")
for m in radii:
    if m == 0:
        continue
    a, b = tab.loc[ok, "M_r0_k1"], tab.loc[ok, f"M_r{m}_k1"]
    print(f"r={m}: Spearman vs centerline {spearmanr(a, b)[0]:.4f}  Kendall {kendalltau(a, b)[0]:.4f}")
    print("   top8:", list(b.sort_values(ascending=False).index[:8]))
print("   centerline top8:", list(tab.loc[ok, "M_r0_k1"].sort_values(ascending=False).index[:8]))

print("\n== Steiner width w = 2r / (M_0/M_r - 1) from the two radii (exact cells)")
for nm in five:
    ws = [2 * m / (tab.loc[nm, "M_r0_k1"] / tab.loc[nm, f"M_r{m}_k1"] - 1) for m in radii if m > 0]
    print(f"{nm:26s} w(r=64) {ws[0]:6.0f}  w(r=128) {ws[1]:6.0f}  ratio {ws[1] / ws[0]:.2f}")
w = {m: 2 * m / (tab.loc[ok, "M_r0_k1"] / tab.loc[ok, f"M_r{m}_k1"] - 1) for m in radii if m > 0}
print("median w128/w64 over biomes:", round(float((w[128] / w[64]).median()), 3))

print("\n== miss rate: fraction of events whose D differs between exact and stride 4 (drives two-phase cost)")
for nm in five:
    b = inv[nm]
    out = []
    for m in radii:
        sub1 = df[(df.biome == b) & (df["mode"] == m) & (df.level == 1)]; sub4 = df[(df.biome == b) & (df["mode"] == m) & (df.level == 4)]
        A1, A4 = mat(sub1), mat(sub4)
        ev1 = (A1 >= R0) & (A1 <= R)
        diff = (np.abs(A4 - A1) > 0.5) & np.isfinite(A1)
        out.append(f"r{m}: {100 * (diff & ev1).sum() / max(ev1.sum(), 1):.0f}%")
    print(f"{nm:26s}", "  ".join(out))
tab.to_csv("out/exact/exact_table.csv")
