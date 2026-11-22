"""Spawn likelihood ratio rho_b(x) = P(D <= x | start at spawn) / P(D_u <= x | uniform start)  (THEORY.md 8.11).

Analysis only: reads the saved rows of a certwalk run that has both arms at radius 0, never simulates.

  python3 spawnratio.py --out out/certwalk_cave_r0 [--x 0,128,512,2048,8192,32768] [--alpha 1e-6]

At x = 0 the denominator is exactly the biome's area share (Proposition 29), so rho_b(0) is "how many times more or
less likely the spawn spot is to be in b than a random spot". Every interval is an anytime valid betting confidence
sequence (Corollary of 8.2); all 2 x biomes x distances of them hold at once except with chance at most alpha.
Writes spawnratio.json and spawnratio.md next to the run.
"""
import argparse, json, math, os, sys

import numpy as np

import certrun as cr
import certwalk as cw
import theory as th

ROOT = os.path.dirname(os.path.abspath(__file__))
XS = (0, 128, 512, 2048, 8192, 32768)


def counts(A, si, n, J, b, r, x):
    """Per seed Y_i(x) = #rays with D <= x for biome b at radius r (a missing row means not found within the cap)."""
    m = (A[:, 2] == b) & (A[:, 4] == r) & (A[:, 3] <= x)
    return np.minimum(np.bincount(si[m], minlength=n)[:n], J)


def prob_cs(Y, J, alpha, prior_p):
    """Anytime valid interval for F = E[Y]/J with Y in [0, J]: Theorem 16 with E = J, R0 = 0, R = 1."""
    Y = np.asarray(Y, float); p = min(max(prior_p, 1e-4), 0.9)
    lo, hi = th.BettingCS(np.full(Y.size, float(J)), Y, J, 0.0, 1.0, alpha, Y.size, p, (1 - p) / p, p * (1 - p)).interval()
    return max(lo, 0.0), min(hi, 1.0)


def ratio_bounds(ls, us, lu, uu):
    """Bounds on F/F_u when F in [ls, us] and F_u in [lu, uu] (monotone in each)."""
    lo = ls / uu if uu > 0 else math.inf
    hi = us / lu if lu > 0 else math.inf
    return lo, hi


def _pilot_priors(pilot, biomes, xs, r=0):
    if not pilot:
        return {}
    P = cr.load_csv(os.path.join(pilot, "chunk_00000.csv"))
    n = np.unique(P[:, 0]).size * max(1, int(P[:, 1].max()) + 1)
    return {(b, x): float(((P[:, 2] == b) & (P[:, 4] == r) & (P[:, 3] <= x)).sum()) / n for b in biomes for x in xs}


def analyse(plan, xs=XS, alpha=1e-6, pilot=None, r=0):
    xs = sorted(int(x) for x in xs)
    if xs[-1] > plan["cap"]:
        raise ValueError(f"x = {xs[-1]} is beyond the cap {plan['cap']}: rows there are not exact")
    if r not in plan["arm_radii"]["uniform"]:
        raise ValueError(f"radius {r} has no uniform arm")
    data = {arm: cw.load_arm(plan, arm) for arm in ("spawn", "uniform")}
    J, B = plan["rays"], plan["biomes"]
    ns = {arm: cw.n_of(data[arm][2], r) for arm in ("spawn", "uniform")}   # each arm on its own seeds (separate sequences)
    n = ns["spawn"]
    a_each = alpha / (2 * len(B) * len(xs))
    pri = _pilot_priors(pilot, B, xs, r)
    names = {int(k): v for k, v in plan.get("names", {}).items()}
    rows = []
    for b in B:
        for x in xs:
            out = {}
            for arm in ("spawn", "uniform"):
                A, si, _ = data[arm]; na = ns[arm]; keep = si < na
                Y = counts(A[keep], si[keep], na, J, b, r, x)
                lo, hi = prob_cs(Y, J, a_each, pri.get((b, x), 0.05))
                out[arm] = dict(hits=int(Y.sum()), F=float(Y.sum()) / (na * J), lo=lo, hi=hi)
            s, u = out["spawn"], out["uniform"]
            lo, hi = ratio_bounds(s["lo"], s["hi"], u["lo"], u["hi"])
            est = s["F"] / u["F"] if u["F"] > 0 else math.nan
            verdict = "favours" if lo > 1 else "avoids" if hi < 1 else "not separated"
            rows.append(dict(biome=int(b), name=names.get(int(b), str(b)), x=x, est=est, lo=lo, hi=hi, verdict=verdict,
                             spawn_hits=s["hits"], spawn_F=s["F"], spawn_lo=s["lo"], spawn_hi=s["hi"],
                             uniform_hits=u["hits"], uniform_F=u["F"], uniform_lo=u["lo"], uniform_hi=u["hi"]))
    res = dict(plan_hash=plan.get("hash"), radius=r, seeds=n, uniform_seeds=ns["uniform"], rays=J, xs=xs, alpha=alpha, alpha_each=a_each,
               git=cr._git() if os.path.isdir(os.path.join(ROOT, ".git")) else None, rows=rows,
               statement=(f"Except with chance at most {alpha:g} over the seeds (A1, A2), every interval below holds at "
                          f"once (THEORY.md 8.11). At x = 0 the uniform start's chance is the biome's exact area share "
                          f"(Proposition 29)."))
    with open(os.path.join(plan["out"], "spawnratio.json"), "w") as f:
        json.dump(res, f, indent=1, default=float)
    with open(os.path.join(plan["out"], "spawnratio.md"), "w") as f:
        f.write(markdown(res))
    return res


def _r(v):
    if v == math.inf:
        return "∞"
    if isinstance(v, float) and math.isnan(v):
        return "n/a"
    return f"{v:.2f}" if v < 10 else f"{v:.1f}"


def _pct(v):
    return f"{100 * v:.3g}%"


def _in_words(alpha):
    k = round(1 / alpha)
    return f"1 in {k:,}"


def markdown(res):
    rows, xs = res["rows"], res["xs"]
    head = [r for r in rows if r["x"] == 0] if 0 in xs else []
    key = lambda r: (-r["est"] if not math.isnan(r["est"]) else math.inf, -r["lo"])
    L = ["# How much spawn favours or avoids each biome", "",
         f"Spawn likelihood ratio rho(x) = P(found within x blocks, starting at spawn) / P(found within x blocks, "
         f"random start), THEORY.md 8.11. Radius {res['radius']}, {res['seeds']:,} seeds from spawn and "
         f"{res.get('uniform_seeds', res['seeds']):,} from a random start, {res['rays']} ray per seed. "
         f"Except with chance at most {res['alpha']:g} ({_in_words(res['alpha'])}) every range below holds at once.",
         "", f"Plan `{(res['plan_hash'] or '')[:16]}`.", ""]
    if head:
        L += ["## At the spawn point (x = 0)", "",
              "The random start's chance is exactly the biome's area share (Proposition 29), so area cancels. A single "
              "point has no clumping. rho = 2 means the spawn spot is twice as likely as a random spot to be in that biome.",
              "", "| biome | area share | spawn spot in it | rho(0) | range | spawn |", "|---|---|---|---|---|---|"]
        for r in sorted(head, key=key):
            L.append(f"| {r['name']} | {_pct(r['uniform_F'])} | {_pct(r['spawn_F'])} | {_r(r['est'])} | "
                     f"[{_r(r['lo'])}, {_r(r['hi'])}] | {r['verdict']} |")
        L.append("")
    L += ["## How far the effect reaches", "",
          "rho(x) for longer walks. It goes back to 1 once the walk has left the area that spawn selection shaped. For "
          "x > 0 this is a description (empirical), not an exact removal of clumping.", "",
          "| biome | " + " | ".join(f"x = {x:,}" for x in xs) + " |", "|---|" + "---|" * len(xs)]
    by = {}
    for r in rows:
        by.setdefault(r["name"], {})[r["x"]] = r
    order = [r["name"] for r in sorted(head, key=key)] if head else sorted(by)
    for name in order:
        cells = [f"{_r(by[name][x]['est'])} [{_r(by[name][x]['lo'])}, {_r(by[name][x]['hi'])}]" for x in xs]
        L.append(f"| {name} | " + " | ".join(cells) + " |")
    L.append("")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, help="certwalk run directory (with plan.json, spawn/ and uniform/)")
    ap.add_argument("--x", default=",".join(map(str, XS)))
    ap.add_argument("--alpha", type=float, default=1e-6)
    ap.add_argument("--pilot-dir", default=None, help="optional pilot (other seeds) for the bets' prior constants")
    a = ap.parse_args(argv)
    plan = json.load(open(os.path.join(a.out, "plan.json")))
    if plan.get("hash") != cw.plan_hash(plan):
        sys.exit("plan.json was edited after planning: refusing")
    plan["out"] = os.path.join(ROOT, plan["out"])
    analyse(plan, [int(x) for x in a.x.split(",")], a.alpha, a.pilot_dir)
    print(open(os.path.join(plan["out"], "spawnratio.md")).read())


if __name__ == "__main__":
    main()
