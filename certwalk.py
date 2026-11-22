"""Certified expected walk from spawn, E[D] (THEORY.md section 8). No window: every metre from spawn counts.

  python3 certwalk.py plan   [--target 0.05]      # caps per radius, alpha split, bets, budget (from the 20k pilot)
  python3 certwalk.py run    [--threads T]        # per radius, sequential, resumable, stops when every target is met
  python3 certwalk.py report                      # certificate.json + report.md
  python3 certwalk.py verify [--samples 3]        # independent geometry re-derivation on production rays

For each (biome b, radius r) with simulation cap C_r:
  E[D] = A + S * T,   A = E[min(D, C)],   S = P(D > C),   T = E[D - C | D > C].
  A and S are certified with no assumption (betting confidence sequences, Theorem 16), so E[D] >= A_lo always.
  T is certified only under H_C (constant hazard from C/2 on), from the far half [C/2, C] of the same rays; it carries
  the tail share S*T/E[D], planned below 5% by choosing C_r from the pilot.
"""
import argparse, json, math, os, sys

import numpy as np

import certify as ct
import certrun as cr
import theory as th

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out", "certwalk")
KAPPA = 1.2                 # betting width / leading term, measured in section 7.2 (planning only)
ARMS = ("spawn", "uniform")  # same seeds, same angles; uniform = start uniform in [-L, L]^2 (THEORY.md 8.5)
ROUNDING = 0.5              # hard bound on |stored distance - D| (THEORY.md 8.6, Proposition 21)
SEQS = 7                    # confidence sequences per (biome, radius): A, S, T for each arm, plus the paired A difference


def qkey(b, r):
    return f"{int(b)}@{int(r)}"


# ------------------------------------------------------------------ per seed statistics from rows
def walk_terms(A, si, n, rays, b, r, C):
    """Per seed W = sum_rays min(D, C), K = #rays with D > C, and window (E, X) on [C/2, C]. Missing ray = D > C."""
    m = (A[:, 2] == b) & (A[:, 4] == r)
    d = A[m, 3].astype(float); s = si[m]
    inside = d <= C
    W = rays * C - np.bincount(s, weights=np.where(inside, C - d, 0.0), minlength=n)
    K = rays - np.bincount(s, weights=inside.astype(float), minlength=n)
    E, X = cr.per_seed_EX(s, d, n, rays, C / 2, C)
    return W, K, E, X


def _sim_priors(T, C, rays, rng, n=4000):
    """Prior constants for the bets from an exponential world with mean T (any constant is valid; Theorem 16)."""
    D = rng.exponential(T, size=(n, rays))
    W = np.minimum(D, C).sum(1); K = (D > C).sum(1).astype(float)
    E, X = ct.stats(D, C / 2, C)
    pm = lambda V, s: th.BettingCS.pilot_priors(np.full(n, float(rays)), V, rays, 0.0, s)
    pa = pm(W, C); ps = pm(K, 1.0)
    pt = th.BettingCS.pilot_priors(E, X, rays, C / 2, C) if E.sum() > 0 else (T, 0.25, 0.25)
    D2 = rng.exponential(T, size=(n, rays))
    V = W - np.minimum(D2, C).sum(1) + rays * C
    pd = th.BettingCS.pilot_priors(np.full(n, float(rays)), V, rays, 0.0, 2.0 * C)
    cv2 = float(np.minimum(D, C).var() / np.minimum(D, C).mean() ** 2)
    return dict(A=list(pa), S=list(ps), T=list(pt), dA=list(pd), cv2=cv2, T_hat=T)


def _cs(kind, V, E, inc, plan, b, r):
    q = plan["priors"][qkey(b, r)]; J = plan["rays"]; C = plan["caps"][str(r)]
    if kind == "dA":                                             # V = W_spawn - W_uniform + J C, in [0, 2 J C]
        a = plan["alpha_each"][qkey(b, r)]; ns = plan["n_star"][str(r)]
        lo, hi = th.BettingCS(J * inc.astype(float), V, J, 0.0, 2.0 * C, a, ns, *q["dA"], include=inc).interval()
        return lo - C, hi - C
    a = plan["alpha_each"][qkey(b, r)]; ns = plan["n_star"][str(r)]
    if kind == "A":
        return th.BettingCS(J * inc.astype(float), V, J, 0.0, C, a, ns, *q["A"], include=inc).interval()
    if kind == "S":
        lo, hi = th.BettingCS(J * inc.astype(float), V, J, 0.0, 1.0, a, ns, *q["S"], include=inc).interval()
        return lo, min(hi, 1.0)
    return th.BettingCS(E, V, J, C / 2, C, a, ns, *q["T"], include=inc).interval()


def bias(qs, qu, plan, b, r, n, inc=None):
    """Spawn bias Delta = E[D_spawn] - E[D_uniform] (Theorem 21). The capped part is paired and assumption free."""
    J, C = plan["rays"], plan["caps"][str(r)]
    inc = np.ones(n, bool) if inc is None else inc
    lo, hi = _cs("dA", qs["_W"] - qu["_W"] + J * C, None, inc, plan, b, r)
    d = qs["ED"] - qu["ED"]
    return dict(bias=d, bias_A=qs["A"] - qu["A"], bias_A_lo=lo, bias_A_hi=hi,
                bias_lo=lo + qs["S_lo"] * qs["T_lo"] - qu["S_hi"] * qu["T_hi"],
                bias_hi=hi + qs["S_hi"] * qs["T_hi"] - qu["S_lo"] * qu["T_lo"],
                bias_rel=d / qu["ED"] if qu["ED"] > 0 else math.nan)


def quantity(A_rows, si, n, plan, b, r, inc=None):
    W, K, E, X = walk_terms(A_rows, si, n, plan["rays"], b, r, plan["caps"][str(r)])
    return quantity_from(W, K, E, X, plan, b, r, inc)


def quantity_from(W, K, E, X, plan, b, r, inc=None):
    """Theorem 20 sets for one arm from per seed (W, K, E, X)."""
    J, n = plan["rays"], len(W)
    inc = np.ones(n, bool) if inc is None else inc
    a = _cs("A", W, None, inc, plan, b, r)
    s = _cs("S", K, None, inc, plan, b, r)
    t = _cs("T", X, E, inc, plan, b, r)
    w = inc.sum()
    A_hat = W[inc].sum() / (J * w); S_hat = K[inc].sum() / (J * w)
    T_hat = X[inc].sum() / E[inc].sum() if E[inc].sum() > 0 else math.inf
    ED = A_hat + S_hat * T_hat if S_hat > 0 else A_hat
    lo = a[0] + s[0] * t[0]
    hi = a[1] + s[1] * t[1] if s[1] > 0 else a[1]
    return dict(_W=W, A=A_hat, A_lo=a[0], A_hi=a[1], S=S_hat, S_lo=s[0], S_hi=s[1], T=T_hat, T_lo=t[0], T_hi=t[1],
                ED=ED, ED_lo=lo, ED_hi=hi, ED_lower_no_assumption=a[0],
                tail_share=(S_hat * T_hat / ED) if ED > 0 and S_hat > 0 else 0.0,
                rel_half=(hi - lo) / 2 / ED if math.isfinite(hi) and ED > 0 else math.inf, events_window=int(E[inc].sum()),
                eps_MC=max(ED - lo, hi - ED), eps_rounding=ROUNDING)


# ------------------------------------------------------------------ plan
def group_plan(plan, r, arm="spawn"):
    """The certrun-style plan of one (radius, arm) group: radius r only, cap C_r, its own chunk folder."""
    return dict(seed0=plan["seed0"], rays=plan["rays"], radii=[int(r)], rmax=int(plan["caps"][str(r)]),
                R0=0.0, R=float(plan["caps"][str(r)]), chunk=plan["chunk"], threads=plan.get("threads", 1),
                origin="spawn" if arm == "spawn" else f"uniform:{int(plan['uniform_L'])}",
                out=os.path.join(plan["out"], f"r{int(r)}_{arm}"))


def make_plan(P, pilot_seed0, n_pilot, rays, radii, biomes, targets, target, alpha, alpha_rest, seed0, chunk, out, tail_max=0.05,
              uniform_L=1_000_000):
    rng = np.random.default_rng(12345)
    idx = {cr.signed(cr.seed_of(pilot_seed0 + i)): i for i in range(n_pilot)}
    si = np.fromiter((idx[s] for s in P[:, 0]), np.int64, P.shape[0])
    T_hat = {}
    for r in radii:
        for b in biomes:
            m = (P[:, 2] == b) & (P[:, 4] == r)
            D = np.full((n_pilot, rays), np.inf); D[si[m], P[m, 1]] = P[m, 3]
            E, X = ct.stats(D, 4000.0, 20000.0)         # pilot only: a rough far-field rate for the tail of the plan
            M = X.sum() / E.sum() if E.sum() >= 5 else 2e6
            T_hat[qkey(b, r)] = float(np.minimum(D, 20000.0).mean() + (D > 20000).mean() * M)
    caps = {}
    for r in radii:
        worst = max(T_hat[qkey(b, r)] for b in targets)
        caps[str(r)] = int(math.ceil(worst * math.log(1 / tail_max) / 10000.0) * 10000)
    priors = {qkey(b, r): _sim_priors(min(T_hat[qkey(b, r)], 50 * caps[str(r)]), caps[str(r)], rays, rng)
              for r in radii for b in biomes}
    tq = [qkey(b, r) for r in radii for b in targets]
    rest = [qkey(b, r) for r in radii for b in biomes if qkey(b, r) not in tq]
    a_t, a_r = (alpha - alpha_rest) / (SEQS * len(tq)), alpha_rest / (SEQS * max(len(rest), 1))
    aeach = {q: (a_t if q in tq else a_r) for q in tq + rest}
    n_star = {}
    for r in radii:
        cv2 = max(priors[qkey(b, r)]["cv2"] for b in targets)
        n_star[str(r)] = int(math.ceil(2 * KAPPA ** 2 * math.log(2 / a_t) * cv2 / (rays * (0.9 * target) ** 2)))
    cost = len(ARMS) * sum(n_star[str(r)] * rays * cr.sec_per_ray(r, caps[str(r)]) for r in radii)
    plan = dict(seed0=seed0, rays=rays, uniform_L=uniform_L, radii=list(radii), caps=caps, chunk=chunk, alpha=alpha, alpha_rest=alpha_rest,
                biomes=list(biomes), target_biomes=list(targets), target=target, tail_max=tail_max, alpha_each=aeach,
                priors=priors, n_star=n_star, n_max={k: 2 * v for k, v in n_star.items()}, expected_cpu_s=cost,
                pilot=dict(seed0=pilot_seed0, n=n_pilot), out=out)
    plan["hash"] = plan_hash(plan)
    return plan


def plan_hash(plan):
    import hashlib
    keys = ["seed0", "rays", "uniform_L", "radii", "caps", "chunk", "alpha", "alpha_rest", "biomes", "target_biomes", "target",
            "alpha_each", "priors", "n_star", "n_max"]
    return hashlib.sha256(json.dumps({k: plan[k] for k in keys}, sort_keys=True).encode()).hexdigest()


def check_alpha(plan):
    n_q = len(plan["biomes"]) * len(plan["radii"])
    if len(plan["alpha_each"]) != n_q or SEQS * sum(plan["alpha_each"].values()) > plan["alpha"] * (1 + 1e-9):
        raise ValueError(f"alpha_each must cover every (biome, radius); {SEQS} sequences each must sum to at most alpha")


# ------------------------------------------------------------------ run (sequential per radius, both arms in lockstep)
def load_arms(plan, r):
    """Both arms of radius r, integrity checked, cut to the seeds both have (pairing needs the same seeds)."""
    out = {}
    for arm in ARMS:
        g = group_plan(plan, r, arm)
        if not cr.load_manifest(g):
            return None
        out[arm] = cr.load_all(g)
    n = min(sum(c["n"] for c in man) for _, _, man in out.values())
    for arm, (A, si, man) in out.items():
        keep = si < n
        out[arm] = (A[keep], si[keep])
    return out, n


def stats_at(plan, r, data, n, b):
    qs = quantity(*data["spawn"], n, plan, b, r)
    qu = quantity(*data["uniform"], n, plan, b, r)
    return qs, qu, bias(qs, qu, plan, b, r, n)


def active(plan, r):
    """Predictable stopping rule of radius r: uses only completed chunks of this radius."""
    got = load_arms(plan, r)
    if got is None:
        return True
    data, n = got
    if n >= plan["n_max"][str(r)]:
        return False
    if n < plan["chunk"]:
        return True
    for b in plan["target_biomes"]:
        qs, qu, _ = stats_at(plan, r, data, n, b)
        if not (qs["rel_half"] <= plan["target"] and qu["rel_half"] <= plan["target"]):
            return True
    return False


def _run_chunk(g, k, s0, log):
    man = cr.load_manifest(g)
    if len(man) > k:
        return
    if len(man) != k:
        raise ValueError(f"{g['out']}: manifest has {len(man)} chunks, expected {k}")
    p = cr.chunk_path(g, k)
    cr.discexact(s0, g["chunk"], g["radii"], g, p)
    cr.check_integrity(cr.load_csv(p), s0, g["chunk"], g["rays"], g["radii"])
    man.append(dict(k=k, seed0=s0, n=g["chunk"], radii=g["radii"]))
    json.dump(man, open(cr.manifest_path(g) + ".tmp", "w"), indent=1)
    os.replace(cr.manifest_path(g) + ".tmp", cr.manifest_path(g))
    log(f"r={g['radii'][0]} {g['origin']}: chunk {k} done (seeds {s0}..{s0 + g['chunk'] - 1}, cap {g['rmax']})")


def run(plan, log=print):
    for r in plan["radii"]:
        for arm in ARMS:
            os.makedirs(group_plan(plan, r, arm)["out"], exist_ok=True)
        while active(plan, r):
            k = min(len(cr.load_manifest(group_plan(plan, r, a))) for a in ARMS)
            for arm in ARMS:
                _run_chunk(group_plan(plan, r, arm), k, plan["seed0"] + k * plan["chunk"], log)
        log(f"r={r}: done")


# ------------------------------------------------------------------ report
def report(plan, names=None):
    check_alpha(plan)
    names = names or {}
    results, cpu, by_r = [], 0.0, {}
    for r in plan["radii"]:
        got = load_arms(plan, r)
        if got is None:
            raise ValueError(f"r={r}: no chunk in the manifest")
        data, n = got
        C = plan["caps"][str(r)]
        cpu += len(ARMS) * n * plan["rays"] * cr.sec_per_ray(r, C)
        for b in plan["biomes"]:
            qs, qu, bi = stats_at(plan, r, data, n, b)
            row = dict(biome=int(b), name=names.get(int(b), str(b)), radius=int(r), cap=C, seeds=n,
                       **{k: v for k, v in qs.items() if not k.startswith("_")},
                       uniform={k: v for k, v in qu.items() if not k.startswith("_")}, **bi)
            if int(b) in plan["target_biomes"]:
                row["target_met"] = bool(qs["rel_half"] <= plan["target"] and qu["rel_half"] <= plan["target"])
                row["hazard_bins_far_half"] = {}
                for arm in ARMS:
                    A, si = data[arm]
                    m = (A[:, 2] == b) & (A[:, 4] == r)
                    D = np.full((n, plan["rays"]), np.inf); D[si[m], A[m, 1]] = A[m, 3]
                    row["hazard_bins_far_half"][arm] = ct.bin_hazards(D, C / 2, C, bins=4)
            results.append(row)
            by_r.setdefault(int(r), {})[row["name"]] = dict(lo=row["ED_lo"] - ROUNDING, hi=row["ED_hi"] + ROUNDING)
    order = {str(r): cr.certified_order(v) for r, v in by_r.items()}
    cert = dict(plan_hash=plan_hash(plan), alpha=plan["alpha"], est_cpu_s=cpu, results=results, certified_order=order,
                git=cr._git(), discexact_sha256=cr._sha(cr.EXE) if os.path.exists(cr.EXE) else None,
                statement=(f"Under A1 and A2, with probability >= {1 - plan['alpha']:.2f} all {SEQS * len(results)} confidence "
                           f"sequences hold at once (Theorem 20). Then every E[D] >= A_lo and every capped spawn bias is in "
                           f"[bias_A_lo, bias_A_hi] with no further assumption; E[D] is in [ED_lo, ED_hi] and the full spawn "
                           f"bias in [bias_lo, bias_hi] if also H_C holds (constant hazard from C/2 on; it only affects the "
                           f"tail share S*T/E[D]). Certified orders use the H_C intervals."))
    with open(os.path.join(plan["out"], "certificate.json"), "w") as f:
        json.dump(cert, f, indent=1, default=float)
    with open(os.path.join(plan["out"], "report.md"), "w") as f:
        f.write(_markdown(cert, plan))
    return cert


def _fmt(x):
    return f"{x:,.0f}" if math.isfinite(x) else "inf"


def tie_groups(rows):
    """Rarest first. A new group starts only where the range is entirely below every range of the group above."""
    rows = sorted(rows, key=lambda x: -x["ED"])
    groups = []
    for x in rows:
        if groups and any(x["ED_hi"] + ROUNDING >= y["ED_lo"] - ROUNDING for y in groups[-1]):
            groups[-1].append(x)
        else:
            groups.append([x])
    return groups


def _markdown(cert, plan):
    d = plan["alpha"]
    out = ["# Walk from spawn to each biome\n",
           f"Every number is **estimate ± ε**. The true model value is inside every range at once, except with chance at "
           f"most {d:g} over the random seeds (1 in {1 / d:,.0f}). Geometry error is 0 and rounding at most ±0.5 blocks "
           f"(both certain, included in ε). The part past the cap rests on the constant hazard assumption and is shown "
           f"as the tail share; the lower end of each range needs no assumption at all.\n",
           f"About {cert['est_cpu_s'] / 3600:.1f} CPU hours. Plan `{cert['plan_hash'][:16]}`, code `{(cert['git'] or '')[:10]}`.\n"]
    for r in plan["radii"]:
        rows = [x for x in cert["results"] if x["radius"] == r]
        top = sorted(rows, key=lambda x: -x["ED"])[:15]
        out.append(f"\n## Sight radius {r}, cap {plan['caps'][str(r)]:,} blocks (rarest 15)\n\n"
                   "| rank | biome | E[D] from spawn | ± ε | guaranteed at least | tail share | from a random start | spawn bias | seeds |"
                   "\n|---|---|---|---|---|---|---|---|---|")
        rank = 1
        for g in tie_groups(top):
            lab = str(rank) if len(g) == 1 else f"{rank} (tied)"
            for x in g:
                u = x["uniform"]; e = x["eps_MC"] + x["eps_rounding"]
                out.append(f"| {lab} | {x['name']} | {_fmt(x['ED'])} | {_fmt(e)} | {_fmt(x['ED_lower_no_assumption'] - ROUNDING)} | "
                           f"{100 * x['tail_share']:.1f}% | {_fmt(u['ED'])} ± {_fmt(u['eps_MC'] + ROUNDING)} | "
                           f"{_fmt(x['bias'])} [{_fmt(x['bias_lo'] - 1)}, {_fmt(x['bias_hi'] + 1)}] | {x['seeds']} |")
            rank += len(g)
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------ CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["plan", "run", "report", "verify"])
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--threads", type=int, default=os.cpu_count() or 1)
    ap.add_argument("--seed0", type=int, default=10_000_000_000)
    ap.add_argument("--pilot-dir", default=os.path.join(ROOT, "out", "certrun", "pilot"))
    ap.add_argument("--pilot-seed0", type=int, default=8_000_000_000)
    ap.add_argument("--pilot-seeds", type=int, default=200)
    ap.add_argument("--radii", default="0,64,128")
    ap.add_argument("--rays", type=int, default=4)
    ap.add_argument("--target", type=float, default=0.05)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--alpha-rest", type=float, default=0.005)
    ap.add_argument("--tail-max", type=float, default=0.05)
    ap.add_argument("--target-biomes", default=",".join(cr.RARE))
    ap.add_argument("--chunk", type=int, default=250)
    ap.add_argument("--uniform-L", type=int, default=1_000_000)
    ap.add_argument("--samples", type=int, default=3)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    pp = os.path.join(a.out, "plan.json")
    names = cr._names(); inv = {v: k for k, v in names.items()}
    if a.cmd == "plan":
        if os.path.exists(pp):
            sys.exit(f"{pp} exists: a plan is fixed once")
        radii = [int(x) for x in a.radii.split(",")]
        P = cr.load_csv(os.path.join(a.pilot_dir, "chunk_00000.csv"))
        cr.check_integrity(P, a.pilot_seed0, a.pilot_seeds, a.rays, radii)
        biomes = sorted(names)
        plan = make_plan(P, a.pilot_seed0, a.pilot_seeds, a.rays, radii, biomes, [inv[t] for t in a.target_biomes.split(",")],
                         a.target, a.alpha, a.alpha_rest, a.seed0, a.chunk, os.path.relpath(a.out, ROOT), a.tail_max, a.uniform_L)
        lp = os.path.join(ROOT, "out", "certrun", "ledger.json")
        ledger = json.load(open(lp)) if os.path.exists(lp) else []
        nmax = max(plan["n_max"].values())
        cr.check_fresh(a.seed0, nmax, ledger)
        ledger.append(dict(seed0=a.seed0, n=nmax, purpose=f"certwalk production {plan['hash'][:12]} (all radius groups)"))
        json.dump(plan, open(pp, "w"), indent=1)
        json.dump(ledger, open(lp, "w"), indent=1)
        print(json.dumps(dict(caps=plan["caps"], n_star=plan["n_star"], expected_cpu_hours=plan["expected_cpu_s"] / 3600), indent=1))
        return
    plan = json.load(open(pp))
    if plan.get("hash") != plan_hash(plan):
        sys.exit("plan.json was edited after planning: refusing")
    plan["threads"] = a.threads
    plan["out"] = os.path.join(ROOT, plan["out"])
    if a.cmd == "run":
        run(plan)
    elif a.cmd == "report":
        report(plan, names)
        print(open(os.path.join(plan["out"], "report.md")).read())
    else:
        rng = np.random.default_rng()
        print(json.dumps({f"r{r}_{arm}": cr.verify(group_plan(plan, r, arm), a.samples, rng)
                          for r in plan["radii"] for arm in ARMS}, indent=1))


if __name__ == "__main__":
    main()
