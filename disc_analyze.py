"""Compare ranking under centerline (mode 0) vs capsule discovery (r = 64, 128). Paired, same seeds and lattice."""
import glob, json, math
import numpy as np, pandas as pd
from scipy.stats import spearmanr, kendalltau

R0, R, RAYS = 4000.0, 20000.0, 4
NAMES = {int(a): b for a, b in (l.strip().split(",", 1) for l in open("out/names.csv"))}
files = sorted(glob.glob("out/cert/disc_[0-9]*.csv"), key=lambda p: int(p.split("_")[-1][:-4]))
df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
seeds = df["seed"].unique(); n = len(seeds)
sidx = pd.Series(np.arange(n), index=pd.Index(df["seed"].drop_duplicates()))
df["si"] = df["seed"].map(sidx)
modes = sorted(df["mode"].unique())

def per_seed(sub):
    A = np.full((n, RAYS), np.inf)
    A[sub["si"].to_numpy(), sub["ray"].to_numpy()] = sub["dist"].to_numpy()
    D = A
    E = ((D >= R0) & (D <= R)).sum(1).astype(float)
    X = np.where(D >= R0, np.minimum(D, R) - R0, 0.0).sum(1)
    return E, X

rng = np.random.default_rng(7)
B = 400
W = rng.multinomial(n, np.full(n, 1 / n), size=B).astype(float)
res = {}
for b, sub_b in df.groupby("biome"):
    row = {}
    for m in modes:
        E, X = per_seed(sub_b[sub_b["mode"] == m])
        row[m] = (E, X)
    if row[0][0].sum() < 50:
        continue
    res[b] = {}
    for m in modes:
        E, X = row[m]
        est = X.sum() / E.sum() if E.sum() else np.nan
        bs = (W @ X) / np.maximum(W @ E, 1)
        res[b][m] = (est, bs)
tab = pd.DataFrame({NAMES[b]: {m: v[m][0] for m in modes} for b, v in res.items()}).T
tab.columns = [f"M_{m}" for m in modes]
tab["events0"] = {NAMES[b]: int(per_seed(df[(df.biome == b) & (df["mode"] == 0)])[0].sum()) for b in res}
for m in modes:
    if m:
        tab[f"ratio_{m}"] = tab[f"M_{m}"] / tab["M_0"]
for m in modes:
    tab[f"rank_{m}"] = tab[f"M_{m}"].rank(ascending=False).astype(int)
tab = tab.sort_values("M_0", ascending=False)
pd.set_option("display.width", 200); pd.set_option("display.max_rows", 100)
print(f"{n} seeds, {n * RAYS} rays, {len(tab)} biomes with >=50 events")
print(tab.round(3).to_string())
out = {}
for m in modes:
    if m == 0:
        continue
    rho = spearmanr(tab["M_0"], tab[f"M_{m}"])[0]; tau = kendalltau(tab["M_0"], tab[f"M_{m}"])[0]
    top5_0 = list(tab.sort_values("M_0", ascending=False).index[:5]); top5_m = list(tab.sort_values(f"M_{m}", ascending=False).index[:5])
    moves = (tab["rank_0"] - tab[f"rank_{m}"]).abs()
    out[int(m)] = dict(spearman=rho, kendall=tau, top5_center=top5_0, top5_disc=top5_m, max_rank_move=int(moves.max()),
                  biggest_movers={str(k): int(v) for k, v in moves.sort_values(ascending=False).head(6).items()})
    print(f"\nr={m}: Spearman {rho:.4f}  Kendall {tau:.4f}  max rank move {moves.max()}  top5 same set: {set(top5_0) == set(top5_m)}")
    print("  centerline top5:", top5_0); print("  disc top5      :", top5_m)
    print("  biggest movers :", moves.sort_values(ascending=False).head(6).to_dict())
tab.to_csv("out/cert/rank_table_disc.csv")
json.dump(out, open("out/cert/disc_summary.json", "w"), indent=1, default=str)
