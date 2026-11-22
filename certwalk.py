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


_PRI = {}


def cap_of(plan, b, r):
    """Per biome cap C_b = min(C, cap_mult x pilot E[D_b]), rounded up to 1,000 (THEORY.md 8.8). A function of the
    pilot only, so the guarantee is unchanged; it gives every biome the same small tail share and a far window
    [C_b/2, C_b] that common biomes actually reach."""
    if "cap" not in plan:
        return plan["caps"][str(r)]
    t = plan["priors"][qkey(b, r)]["T_hat"]
    return int(min(plan["cap"], math.ceil(plan.get("cap_mult", 4.0) * t / 1000.0) * 1000))


def priors_of(plan, b, r):
    """Bets' prior constants for cap C_b, recomputed deterministically from the pilot estimate (any constant is valid)."""
    C = cap_of(plan, b, r); q = plan["priors"][qkey(b, r)]
    if "cap" not in plan or C == plan["cap"]:
        return q
    key = (plan.get("hash"), b, r)
    if key not in _PRI:
        _PRI[key] = _sim_priors(q["T_hat"], C, plan["rays"], np.random.default_rng(1000003 * int(b) + int(r)))
    return _PRI[key]


def _cs(kind, V, E, inc, plan, b, r):
    q = priors_of(plan, b, r); J = plan["rays"]; C = cap_of(plan, b, r)
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
    J, C = plan["rays"], cap_of(plan, b, r)
    inc = np.ones(n, bool) if inc is None else inc
    lo, hi = _cs("dA", qs["_W"] - qu["_W"] + J * C, None, inc, plan, b, r)
    d = qs["ED"] - qu["ED"]
    return dict(bias=d, bias_A=qs["A"] - qu["A"], bias_A_lo=lo, bias_A_hi=hi,
                bias_lo=lo + qs["S_lo"] * qs["T_lo"] - qu["S_hi"] * qu["T_hi"],
                bias_hi=hi + qs["S_hi"] * qs["T_hi"] - qu["S_lo"] * qu["T_lo"],
                bias_rel=d / qu["ED"] if qu["ED"] > 0 else math.nan)


def quantity(A_rows, si, n, plan, b, r, inc=None):
    W, K, E, X = walk_terms(A_rows, si, n, plan["rays"], b, r, cap_of(plan, b, r))
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
REACH = 256                 # discexact row marker: per (seed, ray, radius) the scan reach rho (THEORY.md 8.7)


def arm_plan(plan, arm):
    """The certrun-style plan of one arm: all its radii in one pass, one cap, early stop on the stop set."""
    return dict(seed0=plan["seed0"], rays=plan["rays"], radii=list(plan["arm_radii"][arm]), rmax=int(plan["cap"]),
                R0=0.0, R=float(plan["cap"]), chunk=plan["chunk"], threads=plan.get("threads", 1),
                origin="spawn" if arm == "spawn" else f"uniform:{int(plan['uniform_L'])}", stopset=plan["biomes"],
                layers=plan.get("layers", "surface"), out=os.path.join(plan["out"], arm))


def reach_cost(T_targets, C, r, rng, n=20000):
    """Planning only: mean scan length per ray, E[max_b min(D_b, C)], for independent exponential targets."""
    D = np.column_stack([rng.exponential(t, n) for t in T_targets])
    return float(np.minimum(D.max(1), C).mean())


def make_plan(P, pilot_seed0, n_pilot, rays, radii, names, targets, target, alpha, alpha_rest, seed0, chunk, out,
              cap_mult=4.0, uniform_L=1_000_000, uniform_radii=(0,), layers="surface"):
    """target: {radius: relative half width}. The stop set is every biome seen in the pilot (it must be found or
    capped before a ray stops, so every one of them gets exact rows). cap = cap_mult x the largest target E[D]."""
    rng = np.random.default_rng(12345)
    idx = {cr.signed(cr.seed_of(pilot_seed0 + i)): i for i in range(n_pilot)}
    si = np.fromiter((idx[s] for s in P[:, 0]), np.int64, P.shape[0])
    biomes = sorted(int(b) for b in np.unique(P[:, 2]) if 0 <= b < 256)
    T_hat = {}
    for r in radii:
        for b in biomes:
            m = (P[:, 2] == b) & (P[:, 4] == r)
            D = np.full((n_pilot, rays), np.inf); D[si[m], P[m, 1]] = P[m, 3]
            E, X = ct.stats(D, 4000.0, 20000.0)         # pilot only: a rough far-field rate for the tail of the plan
            M = X.sum() / E.sum() if E.sum() >= 5 else 1e6
            T_hat[qkey(b, r)] = float(np.minimum(D, 20000.0).mean() + (D > 20000).mean() * M)
    if targets is None:                                 # the 8 rarest in the pilot at any radius
        targets = sorted({b for r in radii for b in sorted(biomes, key=lambda b: -T_hat[qkey(b, r)])[:8]})
    worst = max(T_hat[qkey(b, r)] for r in radii for b in targets)
    cap = int(math.ceil(cap_mult * worst / 10000.0) * 10000)
    caps = {str(r): cap for r in radii}
    priors = {qkey(b, r): _sim_priors(min(T_hat[qkey(b, r)], 50 * cap), cap, rays, rng) for r in radii for b in biomes}
    tq = [qkey(b, r) for r in radii for b in targets]
    rest = [qkey(b, r) for r in radii for b in biomes if qkey(b, r) not in tq]
    a_t, a_r = (alpha - alpha_rest) / (SEQS * len(tq)), alpha_rest / (SEQS * max(len(rest), 1))
    aeach = {q: (a_t if q in tq else a_r) for q in tq + rest}
    n_star, reach = {}, {}
    for r in radii:
        cv2 = max(priors[qkey(b, r)]["cv2"] for b in targets)
        n_star[str(r)] = int(math.ceil(2 * KAPPA ** 2 * math.log(2 / a_t) * cv2 / (rays * (0.9 * target[r]) ** 2)))
        reach[str(r)] = reach_cost([T_hat[qkey(b, r)] for b in biomes if T_hat[qkey(b, r)] < cap], cap, r, rng)
    # one pass: a ray costs the widest still active radius over its stretch (planning estimate, independent radii)
    order = sorted(radii, reverse=True)
    def ray_cost(active):
        c, done = 0.0, 0.0
        for r in sorted(active, reverse=True):
            L = max(reach[str(r)] - done, 0.0); c += L * cr.SEC_PER_CELL * (5573 + 2510 * r) / 20000.0; done = max(done, reach[str(r)])
        return c
    ns = sorted(set(n_star.values())); cost, prev = 0.0, 0
    for nv in ns:
        act = [r for r in radii if n_star[str(r)] >= nv]
        cost += (nv - prev) * rays * (ray_cost(act) + (ray_cost([0]) if 0 in act and 0 in uniform_radii else 0.0))
        prev = nv
    plan = dict(seed0=seed0, rays=rays, uniform_L=uniform_L, radii=list(radii), cap=cap, caps=caps, chunk=chunk, alpha=alpha,
                alpha_rest=alpha_rest, biomes=biomes, names={str(b): names.get(b, str(b)) for b in biomes},
                target_biomes=list(targets), target={str(r): target[r] for r in radii}, cap_mult=cap_mult, alpha_each=aeach,
                priors=priors, n_star=n_star, n_max={k: 2 * v for k, v in n_star.items()}, expected_cpu_s=cost,
                arm_radii={"spawn": list(radii), "uniform": [r for r in radii if r in uniform_radii]},
                pilot=dict(seed0=pilot_seed0, n=n_pilot), out=out)
    if layers != "surface":
        plan["layers"] = layers
    plan["hash"] = plan_hash(plan)
    return plan


def plan_hash(plan):
    import hashlib
    keys = ["seed0", "rays", "uniform_L", "radii", "cap", "caps", "chunk", "alpha", "alpha_rest", "biomes", "target_biomes",
            "target", "alpha_each", "priors", "n_star", "n_max", "arm_radii"] + (["layers"] if "layers" in plan else [])
    return hashlib.sha256(json.dumps({k: plan[k] for k in keys}, sort_keys=True).encode()).hexdigest()


def check_alpha(plan):
    n_q = len(plan["biomes"]) * len(plan["radii"])
    if len(plan["alpha_each"]) != n_q or SEQS * sum(plan["alpha_each"].values()) > plan["alpha"] * (1 + 1e-9):
        raise ValueError(f"alpha_each must cover every (biome, radius); {SEQS} sequences each must sum to at most alpha")


# ------------------------------------------------------------------ data: early stop integrity (THEORY.md 8.7)
def check_reach(A, n, rays, radii, stopset, cap):
    """Every (seed, ray, radius) has one reach row rho; if rho < cap every stop set biome has a row with D <= rho.
    Under that, every stop set row is the exact full scan minimum and a missing one means D > cap (Proposition 22)."""
    R = A[A[:, 2] == REACH]
    if R.shape[0] != n * rays * len(radii) or np.unique(R[:, [0, 1, 4]], axis=0).shape[0] != R.shape[0]:
        raise ValueError("reach rows: one per (seed, ray, radius) expected")
    early = R[R[:, 3] < cap]
    if early.size:
        rho = {(a, b, c): d for a, b, c, d in early[:, [0, 1, 4, 3]].tolist()}
        S = A[np.isin(A[:, 2], np.asarray(stopset))]
        cnt = {}
        for s_, k, b, d, r in S[:, [0, 1, 2, 3, 4]].tolist():
            key = (s_, k, r)
            if key in rho and d <= rho[key]:
                cnt[key] = cnt.get(key, 0) + 1
        short = [key for key in rho if cnt.get(key, 0) != len(stopset)]
        if short:
            raise ValueError(f"{len(short)} rays stopped early without every stop set biome found: data not exact")


def load_arm(plan, arm):
    g = arm_plan(plan, arm)
    if not cr.load_manifest(g):
        return None
    A, si, man = cr.load_all(g)
    i = 0
    for c in man:
        m = (si >= i) & (si < i + c["n"])
        check_reach(A[m], c["n"], plan["rays"], c["radii"], plan["biomes"], plan["cap"]); i += c["n"]
    return A, si, man


def n_of(man, r):
    """Seeds that include radius r. Radii are only ever dropped, so these are a prefix of the seed order."""
    return sum(c["n"] for c in man if r in c["radii"])


def extension(plan):
    """The recorded spawn arm extension past n_max (THEORY.md 8.10, Proposition 27b), or None."""
    if "out" not in plan:
        return None
    p = os.path.join(plan["out"], "extension.json")
    ext = json.load(open(p)) if os.path.exists(p) else None
    if ext and ext["plan_hash"] != plan_hash(plan):
        raise ValueError(f"{p} belongs to another plan")
    return ext


def limit_of(plan, r, arm="spawn"):
    """Most seeds radius r may reach in this arm: n_max, or the reserved extension (spawn arm only)."""
    ext = extension(plan) if arm == "spawn" else None
    return max(plan["n_max"][str(r)], ext["n"]) if ext else plan["n_max"][str(r)]


def reserve_extension(plan, n, ledger_path):
    """Reserve seed indices [seed0 + max n_max, seed0 + n) for the spawn arm before any of them is simulated.
    Refuses an overlap with any used range (A1: fresh seeds). Idempotent for the same or a smaller n."""
    ext = extension(plan)
    if ext and ext["n"] >= n:
        return ext
    lo = plan["seed0"] + (ext["n"] if ext else max(plan["n_max"].values()))
    ledger = json.load(open(ledger_path)) if os.path.exists(ledger_path) else []
    cr.check_fresh(lo, plan["seed0"] + n - lo, ledger)
    ledger.append(dict(seed0=lo, n=plan["seed0"] + n - lo, purpose=f"certwalk extension {plan_hash(plan)[:12]} (spawn arm)"))
    ext = dict(n=int(n), arms=["spawn"], plan_hash=plan_hash(plan), ranges=(ext["ranges"] if ext else []) + [[lo, plan["seed0"] + n]])
    json.dump(ledger, open(ledger_path, "w"), indent=1)
    json.dump(ext, open(os.path.join(plan["out"], "extension.json"), "w"), indent=1)
    return ext


def stats_at(plan, data, r, b):
    """(spawn quantity, uniform quantity or None, bias or None) for (b, r) on the seeds both arms share."""
    A, si, man = data["spawn"]; n = n_of(man, r)
    keep = si < n
    qs = quantity(A[keep], si[keep], n, plan, b, r)
    if r not in plan["arm_radii"]["uniform"] or data.get("uniform") is None:
        return qs, None, None
    Au, siu, manu = data["uniform"]; nu = n_of(manu, r)
    if nu > n:
        raise ValueError(f"r={r}: uniform arm has more seeds than the spawn arm ({nu} vs {n})")
    keep = siu < nu
    qu = quantity(Au[keep], siu[keep], nu, plan, b, r)
    qu["seeds"] = nu
    if nu == n:
        return qs, qu, bias(qs, qu, plan, b, r, n)
    keep = si < nu                    # paired bias on the seeds both arms share
    qp = quantity(A[keep], si[keep], nu, plan, b, r)
    return qs, qu, bias(qp, qu, plan, b, r, nu)


def active_radii(plan, data, until=None):
    """Predictable stopping rule: decided from completed chunks only. A radius once dropped stays dropped.
    until: continue every radius to at least min(until, n_max) seeds, met target or not. The sequences cover at every
    stopping time (Theorem 20), so deciding to continue after seeing results keeps the guarantee (THEORY.md 8.10)."""
    if data.get("spawn") is None:
        return list(plan["radii"])
    man = data["spawn"][2]
    out = []
    for r in man[-1]["radii"]:
        n = n_of(man, r)
        if n >= limit_of(plan, r):
            continue
        if until is not None and n < until:
            out.append(r); continue
        if n < plan["chunk"]:
            out.append(r); continue
        for b in plan["target_biomes"]:
            qs, qu, _ = stats_at(plan, data, r, b)
            if not (qs["rel_half"] <= plan["target"][str(r)] and (qu is None or qu["rel_half"] <= plan["target"][str(r)])):
                out.append(r); break
    return out


def _run_chunk(g, k, s0, radii, log):
    man = cr.load_manifest(g)
    if len(man) > k:
        return
    if len(man) != k:
        raise ValueError(f"{g['out']}: manifest has {len(man)} chunks, expected {k}")
    p = cr.chunk_path(g, k)
    cr.discexact(s0, g["chunk"], radii, g, p)
    A = cr.load_csv(p)
    cr.check_integrity(A, s0, g["chunk"], g["rays"], radii)
    man.append(dict(k=k, seed0=s0, n=g["chunk"], radii=list(radii)))
    json.dump(man, open(cr.manifest_path(g) + ".tmp", "w"), indent=1)
    os.replace(cr.manifest_path(g) + ".tmp", cr.manifest_path(g))
    log(f"{g['origin']}: chunk {k} done (seeds {s0}..{s0 + g['chunk'] - 1}, radii {radii})")


def run(plan, log=print, until=None):
    for arm in ARMS:
        if plan["arm_radii"][arm]:
            os.makedirs(arm_plan(plan, arm)["out"], exist_ok=True)
    while True:
        g = arm_plan(plan, "uniform"); ms, mu = cr.load_manifest(arm_plan(plan, "spawn")), cr.load_manifest(g)
        for c in ms[len(mu):]:                                     # resume after a crash between the two arms
            ur = [r for r in c["radii"] if r in plan["arm_radii"]["uniform"] and c["seed0"] - plan["seed0"] < plan["n_max"][str(r)]]
            if ur:
                _run_chunk(g, c["k"], c["seed0"], ur, log)
        data = {arm: load_arm(plan, arm) for arm in ARMS}
        act = active_radii(plan, data, until)
        if not act:
            log("done"); return
        k = len(data["spawn"][2]) if data["spawn"] else 0
        s0 = plan["seed0"] + k * plan["chunk"]
        _run_chunk(arm_plan(plan, "spawn"), k, s0, act, log)
        ur = [r for r in act if r in plan["arm_radii"]["uniform"] and s0 - plan["seed0"] < plan["n_max"][str(r)]]
        if ur:
            g = arm_plan(plan, "uniform")
            _run_chunk(g, k, s0, ur, log)


# ------------------------------------------------------------------ report
def report(plan, names=None):
    check_alpha(plan)
    names = names or {int(k): v for k, v in plan.get("names", {}).items()}
    data = {arm: load_arm(plan, arm) for arm in ARMS}
    if data["spawn"] is None:
        raise ValueError("no chunk in the manifest")
    results, by_r = [], {}
    for r in plan["radii"]:
        n = n_of(data["spawn"][2], r)
        for b in plan["biomes"]:
            qs, qu, bi = stats_at(plan, data, r, b)
            row = dict(biome=int(b), name=names.get(int(b), str(b)), radius=int(r), cap=cap_of(plan, b, r), seeds=n,
                       **{k: v for k, v in qs.items() if not k.startswith("_")})
            if qu is not None:
                row["uniform"] = {k: v for k, v in qu.items() if not k.startswith("_")}; row.update(bi)
            if int(b) in plan["target_biomes"]:
                row["target_met"] = bool(qs["rel_half"] <= plan["target"][str(r)])
                A, si, _ = data["spawn"]; keep = si < n; A, si = A[keep], si[keep]
                m = (A[:, 2] == b) & (A[:, 4] == r)
                D = np.full((n, plan["rays"]), np.inf); D[si[m], A[m, 1]] = A[m, 3]
                C = cap_of(plan, b, r)
                row["hazard_bins_far_half"] = ct.bin_hazards(D, C / 2, C, bins=4)
            results.append(row)
            by_r.setdefault(int(r), {})[row["name"]] = dict(lo=row["ED_lo"] - ROUNDING, hi=row["ED_hi"] + ROUNDING)
    cpu = 0.0
    order = {str(r): cr.certified_order(v) for r, v in by_r.items()}
    cert = dict(plan_hash=plan_hash(plan), alpha=plan["alpha"], results=results, certified_order=order,
                git=cr._git(), discexact_sha256=cr._sha(cr.EXE) if os.path.exists(cr.EXE) else None,
                statement=(f"Model: one walk from spawn in a uniformly random direction (THEORY.md 1). Hard bounds: geometry "
                           f"error 0, rounding at most 0.5 blocks (included). Random part: except with chance at most "
                           f"{plan['alpha']:g} over the seeds (A1, A2), every range below holds at once (Theorem 20). "
                           f"The lower end of every E[D] range needs nothing more; the upper end also uses H_C (constant "
                           f"hazard from C/2 on), which affects only the tail share."))
    with open(os.path.join(plan["out"], "certificate.json"), "w") as f:
        json.dump(cert, f, indent=1, default=float)
    with open(os.path.join(plan["out"], "report.md"), "w") as f:
        f.write(_markdown(cert, plan))
    return cert


# ------------------------------------------------------------------ pairwise order (THEORY.md 9.1)
def _pair_prior(Ta, Ca, Tb, Cb, J, seed, n=4000):
    """Bet constants for V = W_a - W_b + J C_b in [0, J (C_a + C_b)], from independent exponential worlds with the
    pilot means (any constant is valid, Theorem 16; these depend on the pilot only)."""
    rng = np.random.default_rng(seed)
    Da = rng.exponential(Ta, size=(n, J)); Db = rng.exponential(Tb, size=(n, J))
    V = np.minimum(Da, Ca).sum(1) - np.minimum(Db, Cb).sum(1) + J * Cb
    return th.BettingCS.pilot_priors(np.full(n, float(J)), V, J, 0.0, float(Ca + Cb))


def pair_order(plan, alpha_pair, names=None, radii=None, log=None):
    """Every unordered pair of stop set biomes at every radius gets one more sequence on the paired per seed
    difference, at level alpha_pair / (#pairs x #radii). The family is all pairs, fixed by the plan, so nothing here
    depends on production data. On the event that these and Theorem 20's sets all hold (chance >= 1 - alpha -
    alpha_pair), Delta_ab = E[D_a] - E[D_b] lies in [lo, hi] for every pair at once (Theorem 23, Proposition 28)."""
    names = names or {int(k): v for k, v in plan.get("names", {}).items()}
    data = load_arm(plan, "spawn")
    if data is None:
        raise ValueError("no chunk in the manifest")
    A0, si0, man = data
    J, bs = plan["rays"], [int(b) for b in plan["biomes"]]
    radii = list(plan["radii"]) if radii is None else radii
    npairs = len(bs) * (len(bs) - 1) // 2
    a_each = alpha_pair / (npairs * len(plan["radii"]))
    out = dict(plan_hash=plan_hash(plan), alpha=plan["alpha"], alpha_pair=alpha_pair, alpha_each_pair=a_each, radii={})
    for r in radii:
        n = n_of(man, r); keep = si0 < n; A, si = A0[keep], si0[keep]
        inc = np.ones(n, bool)
        W, Q = {}, {}
        for b in bs:
            C = cap_of(plan, b, r)
            Wb, Kb, Eb, Xb = walk_terms(A, si, n, J, b, r, C)
            W[b] = Wb; Q[b] = quantity_from(Wb, Kb, Eb, Xb, plan, b, r)
        pairs = []
        for i, a in enumerate(bs):
            for b in bs[i + 1:]:
                Ca, Cb = cap_of(plan, a, r), cap_of(plan, b, r)
                Ta, Tb = plan["priors"][qkey(a, r)]["T_hat"], plan["priors"][qkey(b, r)]["T_hat"]
                pr = _pair_prior(Ta, Ca, Tb, Cb, J, 7919 * a + 104729 * b + int(r))
                V = W[a] - W[b] + J * Cb
                lo, hi = th.BettingCS(J * inc.astype(float), V, J, 0.0, float(Ca + Cb), a_each, plan["n_star"][str(r)],
                                      *pr, include=inc).interval()
                qa, qb = Q[a], Q[b]
                tail = lambda S, T: S * T if S > 0 else 0.0
                d_lo = (lo - Cb) + tail(qa["S_lo"], qa["T_lo"]) - tail(qb["S_hi"], qb["T_hi"]) - 2 * ROUNDING
                d_hi = (hi - Cb) + tail(qa["S_hi"], qa["T_hi"]) - tail(qb["S_lo"], qb["T_lo"]) + 2 * ROUNDING
                pairs.append(dict(a=a, b=b, diff=qa["ED"] - qb["ED"], lo=float(d_lo), hi=float(d_hi),
                                  dA_lo=float(lo - Cb), dA_hi=float(hi - Cb)))
        rarer = {b: set() for b in bs}                    # rarer[x] = biomes certified rarer than x
        for p in pairs:
            if p["lo"] > 0: rarer[p["b"]].add(p["a"])
            elif p["hi"] < 0: rarer[p["a"]].add(p["b"])
        commoner = {b: {x for x in bs if b in rarer[x]} for b in bs}
        rows = []
        for b in sorted(bs, key=lambda x: -Q[x]["ED"]):
            rows.append(dict(biome=b, name=names.get(b, str(b)), ED=Q[b]["ED"], ED_lo=Q[b]["ED_lo"], ED_hi=Q[b]["ED_hi"],
                             rank_lo=1 + len(rarer[b]), rank_hi=len(bs) - len(commoner[b]),
                             unresolved=[names.get(x, str(x)) for x in bs if x != b and x not in rarer[b] and x not in commoner[b]]))
        out["radii"][str(r)] = dict(seeds=n, pairs=pairs, ranks=rows)
        if log:
            log(f"r={r}: {sum(p['lo'] > 0 or p['hi'] < 0 for p in pairs)} of {len(pairs)} pairs ordered")
    with open(os.path.join(plan["out"], "order.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    with open(os.path.join(plan["out"], "order.md"), "w") as f:
        f.write(_order_md(out, plan))
    return out


def _order_md(o, plan):
    tot = o["alpha"] + o["alpha_pair"]
    s = [f"# Certified ranking from paired differences\n",
         f"Every biome pair is compared on the same seeds and rays (THEORY.md 9.1). A rank range says where the biome "
         f"can be: rank 3 to 5 means exactly 2 biomes are certified rarer and the others in between are not separated "
         f"from it. Except with chance at most {tot:g} (1 in {1 / tot:,.0f}) every statement below and every range of "
         f"report.md hold at once.\n",
         f"Plan `{o['plan_hash'][:16]}`.\n"]
    for r, v in o["radii"].items():
        s.append(f"\n## Sight radius {r} ({v['seeds']} seeds)\n\n| rank | biome | E[D] from spawn | not separated from |\n|---|---|---|---|")
        for x in v["ranks"]:
            rk = f"{x['rank_lo']}" if x["rank_lo"] == x["rank_hi"] else f"{x['rank_lo']} to {x['rank_hi']}"
            un = ", ".join(x["unresolved"]) if len(x["unresolved"]) <= 6 else f"{len(x['unresolved'])} biomes"
            s.append(f"| {rk} | {x['name']} | {_fmt(x['ED'])} | {un or 'none'} |")
    return "\n".join(s) + "\n"


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


def _seeds(x, u):
    """Seed count column; the random start arm may have fewer seeds after a spawn only extension (Proposition 27b)."""
    nu = u.get("seeds", x["seeds"])
    return str(x["seeds"]) if nu == x["seeds"] else f"{x['seeds']} ({nu} random start, bias on those)"


def _markdown(cert, plan):
    d = plan["alpha"]
    out = ["# Walk from spawn to each biome\n",
           f"Every number is **estimate ± ε**. The true model value is inside every range at once, except with chance at "
           f"most {d:g} over the random seeds (1 in {1 / d:,.0f}). Geometry error is 0 and rounding at most ±0.5 blocks "
           f"(both certain, included in ε). The part past the cap rests on the constant hazard assumption and is shown "
           f"as the tail share; the lower end of each range needs no assumption at all.\n",
           f"Plan `{cert['plan_hash'][:16]}`, code `{(cert['git'] or '')[:10]}`.\n",
           ("**Layers (assumption, THEORY.md 8.9):** a biome counts in a 4x4 column if it is at any of the 96 layers from "
            "y = -64 to 319, so a cave biome counts as found when you pass within the radius of its column, at any depth, "
            "reachable or not.\n" if plan.get("layers", "surface") == "all" else
            "**Layers:** surface layer only (no cave biomes).\n")]
    for r in plan["radii"]:
        rows = [x for x in cert["results"] if x["radius"] == r]
        top = sorted(rows, key=lambda x: -x["ED"])
        out.append(f"\n## Sight radius {r}, cap {plan['cap']:,} blocks, per biome cap 4x its pilot walk (all {len(top)} biomes, rarest first, most common last)\n\n"
                   "| rank | biome | E[D] from spawn | ± ε | guaranteed at least | tail share | from a random start | spawn bias | seeds |"
                   "\n|---|---|---|---|---|---|---|---|---|")
        rank = 1
        for g in tie_groups(top):
            lab = str(rank) if len(g) == 1 else f"{rank} (tied)"
            for x in g:
                u = x.get("uniform"); e = x["eps_MC"] + x["eps_rounding"]
                if u is None:
                    out.append(f"| {lab} | {x['name']} | {_fmt(x['ED'])} | {_fmt(e)} | {_fmt(x['ED_lower_no_assumption'] - ROUNDING)} | "
                               f"{100 * x['tail_share']:.1f}% | not run | | {x['seeds']} |")
                    continue
                out.append(f"| {lab} | {x['name']} | {_fmt(x['ED'])} | {_fmt(e)} | {_fmt(x['ED_lower_no_assumption'] - ROUNDING)} | "
                           f"{100 * x['tail_share']:.1f}% | {_fmt(u['ED'])} ± {_fmt(u['eps_MC'] + ROUNDING)} | "
                           f"{_fmt(x['bias'])} [{_fmt(x['bias_lo'] - 1)}, {_fmt(x['bias_hi'] + 1)}] | "
                           f"{_seeds(x, u)} |")
            rank += len(g)
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------ verify (independent of the early stop)
def verify(plan, arm, samples=3, rng=None):
    """For random production (seed, ray): rerun discexact --debug (a full scan, no early stop) up to just past the
    ray's reach, recompute every cell's D with theory.cell_D, and check that every production row with D <= reach is
    the full scan minimum and that no full scan minimum <= reach is missing (Proposition 22)."""
    import subprocess
    rng = rng or np.random.default_rng()
    data = load_arm(plan, arm)
    A, si, man = data
    J = plan["rays"]; n_total = sum(c["n"] for c in man)
    g = arm_plan(plan, arm)
    st = dict(rays_checked=0, cells_checked=0, max_abs_D_err=0.0, rows_mismatch=0, rows_checked=0)
    for _ in range(samples):
        i, k = int(rng.integers(n_total)), int(rng.integers(J))
        radii = next(c["radii"] for c in man if c["seed0"] <= plan["seed0"] + i < c["seed0"] + c["n"])
        s = cr.signed(cr.seed_of(plan["seed0"] + i))
        rows = A[(A[:, 0] == s) & (A[:, 1] == k)]
        reach = {int(r): int(d) for d, r in rows[rows[:, 2] == REACH][:, [3, 4]]}
        rm = int(min(plan["cap"], max(reach.values()) + 16))
        cmd = [cr.EXE, "--seed0", str(plan["seed0"]), "--rays", str(J), "--rmax", str(rm),
               "--radii", ",".join(map(str, radii)), "--debug", f"{i},{k}"]
        if arm != "spawn":
            cmd += ["--origin", g["origin"]]
        if plan.get("layers", "surface") != "surface":
            cmd += ["--layers", plan["layers"]]
        out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.splitlines()
        _, sx, sz, sang = out[0].split()
        px, pz, ang = float(sx), float(sz), float(sang)
        Cm = np.array([[float(v) for v in l.split(",")] for l in out[1:]])
        qx, qz, bio, Dc = Cm[:, 0].astype(int), Cm[:, 1].astype(int), Cm[:, 2].astype(int), Cm[:, 3:]
        for j, r in enumerate(radii):
            Dp = th.cell_D(px, pz, ang, qx, qz, float(r), cap=float(rm))
            fin = Dc[:, j] >= 0
            if (np.isfinite(Dp) != fin).any():
                st["max_abs_D_err"] = math.inf
            else:
                st["max_abs_D_err"] = max(st["max_abs_D_err"], float(np.max(np.abs(Dp[fin] - Dc[fin, j]), initial=0)))
            want = {}
            for b, d in zip(bio[fin], Dc[fin, j]):
                di = int(math.floor(d + 0.5)); want[int(b)] = min(want.get(int(b), di), di)
            rr = rows[(rows[:, 4] == r) & (rows[:, 2] != REACH)]
            got = {int(b): int(d) for b, d in rr[:, [2, 3]]}
            rho = reach[int(r)]
            for b in set(want) | set(got):
                w, gv = want.get(b), got.get(b)
                if (w is not None and w <= rho) or (gv is not None and gv <= rho):
                    st["rows_checked"] += 1; st["rows_mismatch"] += int(w != gv)
        st["rays_checked"] += 1; st["cells_checked"] += int(Cm.shape[0])
    return st


# ------------------------------------------------------------------ CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["plan", "run", "report", "verify", "order"])
    ap.add_argument("--alpha-pair", type=float, default=1e-6, help="order: failure chance for all pairwise sequences")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--threads", type=int, default=os.cpu_count() or 1)
    ap.add_argument("--seed0", type=int, default=10_000_000_000)
    ap.add_argument("--pilot-dir", default=None, help="default: out/certrun/pilot (surface) or out/certwalk_pilot_all (all layers)")
    ap.add_argument("--layers", choices=["surface", "all"], default="all", help="biome layers per cell (THEORY.md 8.9)")
    ap.add_argument("--pilot-seed0", type=int, default=8_000_000_000)
    ap.add_argument("--pilot-seeds", type=int, default=200)
    ap.add_argument("--radii", default="0,64,128")
    ap.add_argument("--rays", type=int, default=4)
    ap.add_argument("--target", default="0:0.05,64:0.10,128:0.10", help="radius:relative half width,...")
    ap.add_argument("--cap-mult", type=float, default=4.0)
    ap.add_argument("--uniform-radii", default="0")
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--alpha-rest", type=float, default=0.005)
    ap.add_argument("--target-biomes", default="auto", help="names, or auto = the 8 rarest in the pilot at each radius")
    ap.add_argument("--chunk", type=int, default=250)
    ap.add_argument("--uniform-L", type=int, default=1_000_000)
    ap.add_argument("--samples", type=int, default=3)
    ap.add_argument("--until", type=int, default=None, help="run: continue every radius to this many seeds (capped at n_max)")
    ap.add_argument("--extend-spawn", action="store_true", help="run --until N past n_max: reserve fresh seeds, spawn arm only (Proposition 27b)")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    pp = os.path.join(a.out, "plan.json")
    names = cr._names(); inv = {v: k for k, v in names.items()}
    if a.cmd == "plan":
        if os.path.exists(pp):
            sys.exit(f"{pp} exists: a plan is fixed once")
        radii = [int(x) for x in a.radii.split(",")]
        pdir = a.pilot_dir or os.path.join(ROOT, "out", "certrun" if a.layers == "surface" else "certwalk_pilot_all",
                                           "pilot" if a.layers == "surface" else "")
        pc = os.path.join(pdir, "chunk_00000.csv")
        if not os.path.exists(pc):                       # deterministic in (seeds, rays, radii, layers): regenerate
            os.makedirs(pdir, exist_ok=True)
            cr.discexact(a.pilot_seed0, a.pilot_seeds, sorted(set(radii)),
                         dict(rays=a.rays, rmax=20000, threads=a.threads, layers=a.layers), pc)
        P = cr.load_csv(pc)
        cr.check_integrity(P, a.pilot_seed0, a.pilot_seeds, a.rays, sorted(set(P[:, 4].tolist())))
        P = P[np.isin(P[:, 4], radii)]
        tgt = {int(k): float(v) for k, v in (x.split(":") for x in a.target.split(","))}
        plan = make_plan(P, a.pilot_seed0, a.pilot_seeds, a.rays, radii, names, None if a.target_biomes == "auto" else [inv[t] for t in a.target_biomes.split(",")],
                         tgt, a.alpha, a.alpha_rest, a.seed0, a.chunk, os.path.relpath(a.out, ROOT), a.cap_mult, a.uniform_L,
                         tuple(int(x) for x in a.uniform_radii.split(",") if x.strip()), a.layers)
        lp = os.path.join(ROOT, "out", "certrun", "ledger.json")
        ledger = json.load(open(lp)) if os.path.exists(lp) else []
        nmax = max(plan["n_max"].values())
        cr.check_fresh(a.seed0, nmax, ledger)
        ledger.append(dict(seed0=a.seed0, n=nmax, purpose=f"certwalk production {plan['hash'][:12]} (both arms)"))
        json.dump(plan, open(pp, "w"), indent=1)
        json.dump(ledger, open(lp, "w"), indent=1)
        print(json.dumps(dict(cap=plan["cap"], n_star=plan["n_star"], stopset=len(plan["biomes"]),
                              expected_cpu_hours=plan["expected_cpu_s"] / 3600), indent=1))
        return
    plan = json.load(open(pp))
    if plan.get("hash") != plan_hash(plan):
        sys.exit("plan.json was edited after planning: refusing")
    plan["threads"] = a.threads
    plan["out"] = os.path.join(ROOT, plan["out"])
    if a.cmd == "run":
        if a.extend_spawn:
            if a.until is None:
                sys.exit("--extend-spawn needs --until N")
            print(json.dumps(reserve_extension(plan, a.until, os.path.join(ROOT, "out", "certrun", "ledger.json"))))
        run(plan, until=a.until)
    elif a.cmd == "order":
        pair_order(plan, a.alpha_pair, log=print)
        print(open(os.path.join(plan["out"], "order.md")).read())
    elif a.cmd == "report":
        report(plan, names)
        print(open(os.path.join(plan["out"], "report.md")).read())
    else:
        rng = np.random.default_rng()
        print(json.dumps({arm: verify(plan, arm, a.samples, rng) for arm in ARMS if plan["arm_radii"][arm]}, indent=1))


if __name__ == "__main__":
    main()
