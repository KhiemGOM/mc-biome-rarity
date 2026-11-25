"""Patch width w and patch density rho per biome, from the certified 26.3 walks (analysis only, no sampling).

  python3 patchsize.py            # writes out/patchsize263/{patchsize.json,patchsize.csv,patchsize.md}

MODEL (assumed, PLAN_DISC.md "Hit-rate model", THEORY.md Corollary 5): patches of one biome are convex, sparse, with
intensity rho (patches per block^2) and mean projected width w (blocks). A straight walk with sight radius r then meets
patches at rate lambda_r = rho (w + 2r) per block (Steiner / Cauchy), and with constant hazard E[D_r] = 1 / lambda_r.
  =>  rho = (1/M_b - 1/M_a) / (2 (r_b - r_a)),   w = 2 (r_b - r_a) / (M_a / M_b - 1)  -  2 r_a   (r_a < r_b)
For r_a = 0 this is the old w = 2 r / (M_0 / M_r - 1).

INPUT: the certified ranges M in [M_lo, M_hi] (certwalk, all hold at once except with chance 1e-6 per run, so 2e-6 here).
ERROR BARS: rho and w are monotone in (M_a, M_b), so the interval is exact interval arithmetic on the corners: it holds
whenever the input ranges hold. No extra sampling error. (The model itself is an assumption, checked below.)
MODEL CHECK: the three radius pairs (0,128), (0,512), (128,512) must give overlapping w ranges. Headline = intersection.
AREA CHECK: for convex patches of mean width w, area <= pi w^2 / 4 (Urysohn), so share <= rho pi w^2 / 4.
"""
import csv, json, math, os

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = {0: "certwalk263_r0", 128: "certwalk263_r128_512", 512: "certwalk263_r128_512"}
OUT = os.path.join(ROOT, "out", "patchsize263")
PAIRS = [(0, 128), (0, 512), (128, 512)]
WORLD = 1e8  # 10,000 x 10,000 blocks, for readable counts
INF = float("inf")


def load():
    M = {}
    for r, d in SRC.items():
        c = json.load(open(os.path.join(ROOT, "out", d, "certificate.json")))
        for x in c["results"]:
            if x["radius"] == r:
                M[(x["name"], r)] = (x["ED_lo"], x["ED"], x["ED_hi"])
    return M


def width_rho(ma, mb, ra, rb):
    """(w_lo, w_est, w_hi), (rho_lo, rho_est, rho_hi) from M_a=(lo,est,hi) at ra and M_b at rb. Corner formulas."""
    def w_of(la, lb):  # la = 1/M_a, lb = 1/M_b
        return INF if lb <= la else 2 * (rb - ra) * la / (lb - la) - 2 * ra
    def rho_of(la, lb):
        return (lb - la) / (2 * (rb - ra))
    la = [1 / ma[2], 1 / ma[1], 1 / ma[0]]  # lo, est, hi of lambda_a
    lb = [1 / mb[2], 1 / mb[1], 1 / mb[0]]
    # w increasing in la, decreasing in lb; rho increasing in lb, decreasing in la
    w = (w_of(la[0], lb[2]), w_of(la[1], lb[1]), w_of(la[2], lb[0]))
    rho = (rho_of(la[2], lb[0]), rho_of(la[1], lb[1]), rho_of(la[0], lb[2]))
    return tuple(max(v, 0) if v != INF else v for v in w), rho


def main():
    M = load()
    names = sorted({n for n, _ in M})
    rows = []
    for n in names:
        row = {"biome": n, "M": {str(r): M[(n, r)] for r in (0, 128, 512)}, "pairs": {}}
        for ra, rb in PAIRS:
            w, rho = width_rho(M[(n, ra)], M[(n, rb)], ra, rb)
            row["pairs"][f"{ra}-{rb}"] = {"w": w, "rho": rho}
        # headline = intersection of the pair intervals (valid when the model holds and the pairs overlap)
        wl = max(p["w"][0] for p in row["pairs"].values()); wh = min(p["w"][2] for p in row["pairs"].values())
        rl = max(p["rho"][0] for p in row["pairs"].values()); rh = min(p["rho"][2] for p in row["pairs"].values())
        row["consistent"] = wl <= wh and rl <= rh
        # point estimate: inverse-variance style is not certified, so use the (0,128) estimate for display only
        # and report the intersection as the range. If empty, the model is violated for that biome.
        row["w_range"] = (wl, wh); row["rho_range"] = (rl, rh)
        row["w_est"] = row["pairs"]["0-128"]["w"][1]; row["rho_est"] = row["pairs"]["0-128"]["rho"][1]
        row["w_est_all"] = {k: v["w"][1] for k, v in row["pairs"].items()}
        row["rho_est_all"] = {k: v["rho"][1] for k, v in row["pairs"].items()}
        row["per_100M"] = [v * WORLD for v in row["rho_range"]]
        row["area_share_upper"] = rh * math.pi * wh ** 2 / 4 if wh != INF else None
        rows.append(row)
    os.makedirs(OUT, exist_ok=True)
    json.dump(rows, open(os.path.join(OUT, "patchsize.json"), "w"), indent=1, default=str)
    with open(os.path.join(OUT, "patchsize.csv"), "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["biome", "consistent", "w_lo", "w_hi", "rho_lo", "rho_hi", "w_est_0_128", "w_est_0_512", "w_est_128_512",
                     "rho_est_0_128", "rho_est_0_512", "rho_est_128_512", "area_share_upper"])
        for r in rows:
            wr.writerow([r["biome"], r["consistent"], *r["w_range"], *r["rho_range"], *(r["w_est_all"][k] for k in ("0-128", "0-512", "128-512")),
                         *(r["rho_est_all"][k] for k in ("0-128", "0-512", "128-512")), r["area_share_upper"]])
    # markdown: two headline columns (patch seen from 0 to 128 blocks, from 0 to 512), no intersection, because the radius pairs drift
    def olap(p, q, key):
        return max(p[key][0], q[key][0]) <= min(p[key][2], q[key][2])
    for r in rows:
        p, q = r["pairs"]["0-128"], r["pairs"]["0-512"]
        r["agree_0_128_vs_0_512"] = olap(p, q, "w") and olap(p, q, "rho")
    L = ["# Patch width and patch density, 26.3 (from the certified walks)", "",
         "Per biome: effective patch width w (mean projected width, blocks) and patch density rho (expected patches per 10,000 x 10,000 block square), as ranges that hold whenever the certified E[D] ranges hold (chance of failure at most 1 in 500,000, two runs).",
         "- **Proven** (given the certified inputs): the interval arithmetic, no extra sampling error.",
         "- **Assumed**: patches act like a sparse stationary field of convex patches with constant hazard (Steiner hit rate lambda_r = rho (w + 2r)).",
         "- **Empirical check**: the radius pairs (0,128) and (0,512) should give the same w and rho. Where the ranges do not overlap, or the estimates drift, patches are not isolated (they come in clusters), and w, rho are only effective numbers for that range of sight.",
         "- Area bound: a disc has the largest area for a given mean width, so for convex patches the area share is at most rho pi w^2 / 4. It is a loose upper bound, not an estimate.", "",
         "| biome | w, sight 0 to 128 | w, sight 0 to 512 | patches per 10k x 10k (0 to 128) | patches per 10k x 10k (0 to 512) | check | area share <= (0 to 512) |", "|---|---|---|---|---|---|---|"]
    def fmt(v, f):
        lo, _, hi = v
        return f"{f(lo)} to {f(hi)}" if hi != INF else f">{f(lo)}"
    w0 = lambda v: f"{v:,.0f}"; d0 = lambda v: f"{v * WORLD:.1f}"
    for r in sorted(rows, key=lambda r: r["pairs"]["0-512"]["w"][1]):
        p, q = r["pairs"]["0-128"], r["pairs"]["0-512"]
        qa = q["rho"][2] * math.pi * q["w"][2] ** 2 / 4 if q["w"][2] != INF else None
        r["area_share_upper"] = qa
        L.append(f"| {r['biome']} | {fmt(p['w'], w0)} | {fmt(q['w'], w0)} | {fmt(p['rho'], d0)} | {fmt(q['rho'], d0)} | {'agree' if r['agree_0_128_vs_0_512'] else '**drift**'} | {qa*100:.3f}% |" if qa is not None else f"| {r['biome']} | {fmt(p['w'], w0)} | {fmt(q['w'], w0)} | {fmt(p['rho'], d0)} | {fmt(q['rho'], d0)} | {'agree' if r['agree_0_128_vs_0_512'] else '**drift**'} | - |")
    n = sum(r["agree_0_128_vs_0_512"] for r in rows)
    L += ["", f"Check: {n} of {len(rows)} biomes agree between the (0,128) and (0,512) pairs. Drift direction: w (0,512) minus w (0,128) estimate is positive for {sum(r['pairs']['0-512']['w'][1] > r['pairs']['0-128']['w'][1] for r in rows)} of {len(rows)} biomes."]
    open(os.path.join(OUT, "patchsize.md"), "w").write("\n".join(L) + "\n")
    json.dump(rows, open(os.path.join(OUT, "patchsize.json"), "w"), indent=1, default=str)
    print("\n".join(L))


if __name__ == "__main__":
    main()
