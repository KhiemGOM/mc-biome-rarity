"""Certified exact Monte Carlo sampler (THEORY.md sections 6 and 7).

  python3 certrun.py plan   [--pilot-seeds 200] [--target 0.05] [--threads T]   # fixes alpha split, bets, budget
  python3 certrun.py run    [--threads T]     # sequential, resumable; stops as soon as every target is met
  python3 certrun.py report                   # certificate.json + report.md
  python3 certrun.py verify [--samples 5]     # independent re-derivation of the geometry on production rays

What makes it certified (each point is a hypothesis of Theorem 17):
  - exact model only: level 1 rows of discexact (every cell); r = 0 is the exact centerline;
  - every (biome, radius) gets a betting confidence sequence at its own level alpha_q with sum alpha_q = alpha,
    fixed in the plan from a pilot on DIFFERENT seeds; a confidence sequence covers at every N at once, so the
    data-dependent stopping rule (stop a radius when its targets are met) keeps the guarantee;
  - production seeds are fresh (ledger), the plan is hash-locked, and the report refuses data that are not
    exactly the planned seed prefix or that miss a spawn row.
"""
import argparse, hashlib, json, math, os, subprocess, sys

import numpy as np

import certify as ct
import theory as th

ROOT = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.join(ROOT, "discexact")
OUT = os.path.join(ROOT, "out", "certrun")
MASK = (1 << 64) - 1
# seed index ranges already used by earlier runs (seed index i means world seed splitmix64(i))
HISTORICAL = [dict(seed0=5_000_000_000, n=1_500, purpose="centerline certification pilot (cert_pipeline.py)"),
              dict(seed0=7_000_000_000, n=40_000, purpose="certified centerline run and the 600 seed exact pilot")]
RARE = ["mushroom_fields", "pale_garden", "windswept_gravelly_hills", "stony_peaks", "ice_spikes", "eroded_badlands"]


# ------------------------------------------------------------------ seeds
def seed_of(i):
    """World seed for seed index i: splitmix64 exactly as in discexact.c / colsim.c."""
    z = (i + 0x9E3779B97F4A7C15) & MASK
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
    return z ^ (z >> 31)


def signed(u):
    """The seed as discexact prints it: (long long)(int64_t)seed."""
    return u - (1 << 64) if u >= 1 << 63 else u


def check_fresh(seed0, n, ledger):
    """Refuse a seed index range [seed0, seed0 + n) that overlaps a used one (independence of pilot and production)."""
    for u in HISTORICAL + list(ledger):
        if seed0 < u["seed0"] + u["n"] and u["seed0"] < seed0 + n:
            raise ValueError(f"seed range [{seed0}, {seed0 + n}) overlaps [{u['seed0']}, {u['seed0'] + u['n']}) "
                             f"used for: {u['purpose']}")


# ------------------------------------------------------------------ data
COLS = ["seed", "ray", "biome", "dist", "mode", "level"]


def load_csv(path):
    """Level 1 (exact) rows as an int64 array with columns COLS."""
    import pandas as pd
    df = pd.read_csv(path, usecols=COLS, dtype={c: np.int64 for c in COLS})
    df = df[df["level"] == 1]
    return df[COLS].to_numpy(np.int64)


def check_integrity(A, seed0, n, rays, radii):
    """The rows must be exactly the planned seeds, rays and radii, and every (seed, ray, radius) must carry the
    spawn cell's row (D = 0: the spawn cell is always visible). Raises ValueError otherwise."""
    A = A[A[:, 5] == 1]
    want = np.array([signed(seed_of(seed0 + i)) for i in range(n)], dtype=np.int64)
    got = np.unique(A[:, 0])
    if got.size != want.size or not np.array_equal(got, np.sort(want)):
        raise ValueError(f"seed set differs from the plan: {got.size} distinct seeds, {want.size} planned "
                         f"({np.setdiff1d(want, got).size} missing, {np.setdiff1d(got, want).size} unexpected)")
    if A[:, 1].min() < 0 or A[:, 1].max() >= rays:
        raise ValueError("ray index outside the plan")
    bad = np.setdiff1d(np.unique(A[:, 4]), np.asarray(radii, np.int64))
    if bad.size:
        raise ValueError(f"radius {bad.tolist()} is not in the plan")
    key = np.unique(A[:, [0, 1, 2, 4]], axis=0)
    if key.shape[0] != A.shape[0]:
        raise ValueError("duplicate (seed, ray, biome, radius) rows")
    sp = A[A[:, 3] == 0][:, [0, 1, 4]]
    have = np.unique(sp, axis=0).shape[0]
    if have != n * rays * len(radii):
        raise ValueError(f"spawn rows: {have} of {n * rays * len(radii)} (seed, ray, radius) present: data truncated")


def per_seed_EX(si, d, n, rays, R0, R):
    """Per seed (E_i, X_i) from the rows that exist (one per found ray); a missing ray means D = inf (x = R - R0)."""
    d = np.asarray(d, float)
    e = ((d >= R0) & (d <= R)).astype(float)
    x = np.where(d >= R0, np.minimum(d, R) - R0, 0.0)
    E = np.bincount(si, weights=e, minlength=n)
    X = rays * (R - R0) - np.bincount(si, weights=(R - R0) - x, minlength=n)
    return E, X


# ------------------------------------------------------------------ measured cost constants (THEORY.md 7.1)
SEC_PER_CELL = 3.26e-6                    # biome lookup, 98% of the run time (profiled on a 2.1 GHz Xeon core)
def cells_per_ray(rmax_radius, R=20000.0):
    return (5573 + 2510 * rmax_radius) * R / 20000.0
def sec_per_ray(rmax_radius, R=20000.0):
    return SEC_PER_CELL * cells_per_ray(rmax_radius, R)


def qkey(b, r):
    return f"{int(b)}@{int(r)}"


# ------------------------------------------------------------------ intervals and ordering
def stream_cs(E, X, include, plan, b, r):
    pm, pvp, pvm = plan["priors"][qkey(b, r)]
    return th.BettingCS(E, X, plan["rays"], plan["R0"], plan["R"], plan["alpha_q"][qkey(b, r)],
                        plan["n_star"][str(r)], pm, pvp, pvm, include=include).interval()


def certified_order(res):
    """Pairs (a, b) meaning M_a > M_b is certified: the simultaneous intervals are disjoint."""
    return [(a, b) for a in res for b in res if a != b and res[a]["lo"] > res[b]["hi"]]


# ------------------------------------------------------------------ planning
def _calibrate(E, X, rays, R0, R, prior, n_ref, rng):
    """kappa = (betting half width) / (leading term sqrt(2 ln(2/a) V / N) / (Ebar m)) on a bootstrap world."""
    a = 1e-4
    b = rng.integers(0, len(E), n_ref)
    lo, hi = th.BettingCS(E[b], X[b], rays, R0, R, a, n_ref, *prior).interval()
    m = X.sum() / E.sum(); V = float((X - m * E).var(ddof=1))
    lead = math.sqrt(2 * math.log(2 / a) * V / n_ref) / (E.mean() * m)
    return ((hi - lo) / 2 / (X[b].sum() / E[b].sum())) / lead, 2 * V / (E.mean() * m) ** 2


def optimise(A, groups, radii, rays, alpha_t, R):
    """Minimise rays * sum_r cost_r * (N_r - N_next larger radius) over nested N_r, subject to
    sum_q 2 exp(-N_g(q) / A_q) <= alpha_t, where A_q = 2 kappa^2 V / (t Ebar m)^2 (THEORY.md 7.2)."""
    rs = sorted(radii, reverse=True)
    c = [sec_per_ray(r, R) for r in rs]
    grid = np.unique(np.geomspace(500, 400000, 90).astype(int))
    best = None
    def need(r, N):
        return sum(2 * math.exp(-N / A[q]) for q in groups.get(r, []))
    import itertools
    for Ns in itertools.product(grid, repeat=len(rs)):
        Ns = np.maximum.accumulate(np.array(Ns))           # smaller radii see at least the seeds of larger ones
        tot = sum(need(r, N) for r, N in zip(rs, Ns))
        if tot > alpha_t:
            continue
        inc = np.diff(np.concatenate([[0], Ns]))
        cost = rays * sum(ci * ni for ci, ni in zip(c, inc))
        if best is None or cost < best[0]:
            best = (cost, dict(zip(rs, Ns.tolist())))
    if best is None:
        raise ValueError("no seed counts on the grid meet the targets")
    return best


def make_plan(P, pilot_seed0, n_pilot, rays, radii, biomes, targets, target, alpha, alpha_rest, seed0, chunk, out, rng):
    R0, R = 4000.0, 20000.0
    idx = {signed(seed_of(pilot_seed0 + i)): i for i in range(n_pilot)}
    si = np.fromiter((idx[s] for s in P[:, 0]), np.int64, P.shape[0])
    priors, A, groups = {}, {}, {}
    for r in radii:
        for b in biomes:
            m = (P[:, 2] == b) & (P[:, 4] == r)
            E, X = per_seed_EX(si[m], P[m, 3], n_pilot, rays, R0, R)
            if E.sum() >= 5:
                priors[qkey(b, r)] = list(th.BettingCS.pilot_priors(E, X, rays, R0, R))
            else:                                         # too rare in the pilot: any constant prior is valid
                priors[qkey(b, r)] = [float(X.sum() / max(E.sum(), 0.5)), 0.25, 0.25]
            if b in targets:
                kappa, a = _calibrate(E, X, rays, R0, R, priors[qkey(b, r)], 20000, rng)
                A[qkey(b, r)] = kappa ** 2 * a / target ** 2
                groups.setdefault(r, []).append(qkey(b, r))
    alpha_t = alpha - alpha_rest
    cost, Nr = optimise(A, groups, radii, rays, alpha_t, R)
    aq = {q: 2 * math.exp(-Nr[int(q.split("@")[1])] / A[q]) for q in A}
    scale = alpha_t / sum(aq.values())                  # hand any slack back to the targets (sum stays alpha_t)
    aq = {q: v * scale for q, v in aq.items()}
    rest = [qkey(b, r) for r in radii for b in biomes if qkey(b, r) not in aq]
    for q in rest:
        aq[q] = alpha_rest / len(rest)
    plan = dict(seed0=seed0, rays=rays, radii=list(radii), rmax=int(R), R0=R0, R=R, chunk=chunk, alpha=alpha,
                alpha_rest=alpha_rest, biomes=list(biomes), target_biomes=list(targets), target=target, alpha_q=aq,
                priors=priors, n_star={str(r): int(n) for r, n in Nr.items()},
                n_max={str(r): int(2 * n) for r, n in Nr.items()}, expected_cpu_s=cost,
                pilot=dict(seed0=pilot_seed0, n=n_pilot), out=out)
    plan["hash"] = plan_hash(plan)
    return plan


# ------------------------------------------------------------------ running discexact
def chunk_path(plan, k):
    return os.path.join(plan["out"], f"chunk_{k:05d}.csv")


def manifest_path(plan):
    return os.path.join(plan["out"], "manifest.json")


def discexact(seed0, n, radii, plan, out):
    cmd = [EXE, "--seeds", n, "--rays", plan["rays"], "--rmax", plan["rmax"], "--radii", ",".join(map(str, radii)),
           "--seed0", seed0, "--threads", plan.get("threads", 1), "--out", out]
    subprocess.run([str(a) for a in cmd], check=True)


def load_manifest(plan):
    p = manifest_path(plan)
    return json.load(open(p)) if os.path.exists(p) else []


def load_all(plan):
    """All chunks in order, each integrity checked against its own radii. Returns (A, si, man)."""
    man = load_manifest(plan)
    if not man:
        raise ValueError("no chunk in the manifest: nothing has been simulated")
    parts, n = [], 0
    for k, c in enumerate(man):
        if c["k"] != k or c["seed0"] != plan["seed0"] + n:
            raise ValueError(f"chunk {k}: not the next seed block of the plan")
        p = chunk_path(plan, k)
        if not os.path.exists(p):
            raise ValueError(f"chunk {k} missing ({p})")
        Ak = load_csv(p)
        check_integrity(Ak, c["seed0"], c["n"], plan["rays"], c["radii"])
        parts.append(Ak); n += c["n"]
    A = np.concatenate(parts)
    idx = {signed(seed_of(plan["seed0"] + i)): i for i in range(n)}
    si = np.fromiter((idx[s] for s in A[:, 0]), np.int64, A.shape[0])
    return A, si, man


def stream_data(A, si, man, plan, b, r):
    n = sum(c["n"] for c in man)
    include = np.zeros(n, bool); i = 0
    for c in man:
        include[i:i + c["n"]] = r in c["radii"]; i += c["n"]
    m = (A[:, 2] == b) & (A[:, 4] == r)
    E, X = per_seed_EX(si[m], A[m, 3], n, plan["rays"], plan["R0"], plan["R"])
    return E * include, X * include, include


def next_radii(plan, A, si, man):
    """The stopping rule, a function of earlier chunks only (predictable): a radius stays active while it is
    below its cap and one of its targets is wider than the target; every radius up to the largest active one is
    computed (free: the cells are a subset)."""
    active = []
    for r in plan["radii"]:
        done = sum(c["n"] for c in man if r in c["radii"])
        if done >= plan["n_max"][str(r)]:
            continue
        if not man:
            active.append(r); continue
        for b in plan["target_biomes"]:
            E, X, inc = stream_data(A, si, man, plan, b, r)
            lo, hi = stream_cs(E, X, inc, plan, b, r)
            est = X.sum() / E.sum() if E.sum() > 0 else math.inf
            if not (math.isfinite(hi) and (hi - lo) / 2 / est <= plan["target"]):
                active.append(r); break
    if not active:
        return []
    return [r for r in plan["radii"] if r <= max(active)]


def run(plan, log=print):
    os.makedirs(plan["out"], exist_ok=True)
    man = load_manifest(plan)
    A = si = None
    while True:
        if man:
            A, si, man = load_all(plan)
        radii = next_radii(plan, A, si, man)
        if not radii:
            log("all targets met (or caps reached): stopping"); return man
        k = len(man); s0 = plan["seed0"] + sum(c["n"] for c in man)
        p = chunk_path(plan, k)
        discexact(s0, plan["chunk"], radii, plan, p)
        check_integrity(load_csv(p), s0, plan["chunk"], plan["rays"], radii)
        man.append(dict(k=k, seed0=s0, n=plan["chunk"], radii=radii))
        json.dump(man, open(manifest_path(plan) + ".tmp", "w"), indent=1); os.replace(manifest_path(plan) + ".tmp", manifest_path(plan))
        log(f"chunk {k} done: seeds {s0}..{s0 + plan['chunk'] - 1}, radii {radii}")


# ------------------------------------------------------------------ report
def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def plan_hash(plan):
    keys = ["seed0", "rays", "radii", "rmax", "R0", "R", "chunk", "alpha", "alpha_rest", "biomes", "target_biomes",
            "target", "alpha_q", "priors", "n_star", "n_max"]
    return hashlib.sha256(json.dumps({k: plan[k] for k in keys}, sort_keys=True).encode()).hexdigest()


def report(plan, names=None):
    if plan["rmax"] != plan["R"]:
        raise ValueError("rmax must equal R (censoring, THEORY.md section 4 row 11)")
    total = sum(plan["alpha_q"].values())
    if total > plan["alpha"] * (1 + 1e-9) or len(plan["alpha_q"]) != len(plan["biomes"]) * len(plan["radii"]):
        raise ValueError("alpha_q must cover every (biome, radius) and sum to at most alpha")
    A, si, man = load_all(plan)
    names = names or {}
    results, by_radius = [], {}
    for r in plan["radii"]:
        for b in plan["biomes"]:
            E, X, inc = stream_data(A, si, man, plan, b, r)
            lo, hi = stream_cs(E, X, inc, plan, b, r)
            ev = int(E.sum()); est = X.sum() / E.sum() if ev > 0 else math.inf
            row = dict(biome=int(b), name=names.get(int(b), str(b)), radius=int(r), seeds=int(inc.sum()), events=ev,
                       est=est, lo=lo, hi=hi, alpha_q=plan["alpha_q"][qkey(b, r)],
                       rel_half=(hi - lo) / 2 / est if ev > 0 and math.isfinite(hi) else math.inf)
            if int(b) in plan["target_biomes"]:
                row["target_met"] = bool(row["rel_half"] <= plan["target"])
                D = np.full((len(inc), plan["rays"]), np.inf)
                m = (A[:, 2] == b) & (A[:, 4] == r)
                D[si[m], A[m, 1]] = A[m, 3]
                row["hazard_bins"] = ct.bin_hazards(D[inc], plan["R0"], plan["R"], bins=4)
            results.append(row)
            if ev > 0:
                by_radius.setdefault(int(r), {})[row["name"]] = row
    order = {r: certified_order(res) for r, res in by_radius.items()}
    cpu = sum(c["n"] * plan["rays"] * sec_per_ray(max(c["radii"]), plan["R"]) for c in man)
    cert = dict(plan_hash=plan_hash(plan), seeds_simulated=sum(c["n"] for c in man), K=len(results),
                alpha=plan["alpha"], est_cpu_s=cpu,
                statement=f"Under A1 and A2 (THEORY.md 3.1), with probability >= {1 - plan['alpha']:.3f} every one of the "
                          f"{len(results)} intervals contains its M simultaneously (Theorem 17), hence every listed order too.",
                discexact_sha256=_sha(EXE) if os.path.exists(EXE) else None, git=_git(), results=results,
                certified_order={str(r): v for r, v in order.items()})
    with open(os.path.join(plan["out"], "certificate.json"), "w") as f:
        json.dump(cert, f, indent=1, default=float)
    with open(os.path.join(plan["out"], "report.md"), "w") as f:
        f.write(_markdown(cert, plan))
    return cert


def _git():
    try:
        return subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    except OSError:
        return None


def _markdown(cert, plan):
    out = ["# Certified exact run\n", cert["statement"] + "\n",
           f"{cert['seeds_simulated']} seeds x {plan['rays']} rays from index {plan['seed0']}; about "
           f"{cert['est_cpu_s'] / 3600:.1f} CPU hours. Plan hash `{cert['plan_hash'][:16]}`, code `{(cert['git'] or '')[:10]}`.\n"]
    for r in plan["radii"]:
        rows = sorted([x for x in cert["results"] if x["radius"] == r and x["events"] > 0], key=lambda x: -x["est"])[:15]
        out.append(f"\n## r = {r} (rarest 15)\n\n| biome | M | certified interval | rel half | seeds | events |\n|---|---|---|---|---|---|")
        for x in rows:
            hi = f"{x['hi']:,.0f}" if math.isfinite(x["hi"]) else "inf"
            out.append(f"| {x['name']} | {x['est']:,.0f} | [{x['lo']:,.0f}, {hi}] | {100 * x['rel_half']:.1f}% | {x['seeds']} | {x['events']} |")
        top = {x["name"] for x in rows[:6]}
        pairs = [p for p in cert["certified_order"].get(str(r), []) if p[0] in top and p[1] in top]
        out.append("\nCertified orders among the top 6: " + (", ".join(f"{a} > {b}" for a, b in pairs) or "none") + "\n")
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------ independent geometry check
def _candidates(px, pz, ang, rr, rmax):
    """Superset of the cells within rr of the segment, derived independently of scan_ray (THEORY.md 6.4)."""
    ux, uz = math.cos(ang), math.sin(ang)
    ex = px + rmax * ux
    qa, qb = math.floor((min(px, ex) - rr - 8) / 4), math.floor((max(px, ex) + rr + 8) / 4)
    QX, QZ = [], []
    for qx in range(qa, qb + 1):
        x0, x1 = 4 * qx - 0.5 - rr, 4 * qx + 3.5 + rr       # nearest segment point has x within rr of the strip
        if abs(ux) < 1e-12:
            if not (x0 <= px <= x1):
                continue
            s0, s1 = 0.0, float(rmax)
        else:
            t0, t1 = sorted(((x0 - px) / ux, (x1 - px) / ux))
            s0, s1 = max(t0, 0.0), min(t1, float(rmax))
            if s0 > s1:
                continue
        za, zb = sorted((pz + s0 * uz, pz + s1 * uz))
        qza, qzb = math.floor((za - rr + 0.5) / 4) - 1, math.floor((zb + rr + 0.5) / 4) + 1
        QZ.append(np.arange(qza, qzb + 1)); QX.append(np.full(qzb - qza + 1, qx))
    return np.concatenate(QX), np.concatenate(QZ)


def verify(plan, samples=5, rng=None):
    """For random production (seed, ray): rerun discexact --debug, recompute every cell's D with theory.cell_D,
    check no cell is missing from the C enumeration, and that the per biome minima equal the production rows."""
    rng = rng or np.random.default_rng()
    A, _, man = load_all(plan)
    J, rmax = plan["rays"], plan["rmax"]
    n_total = sum(c["n"] for c in man)
    stats = dict(rays_checked=0, cells_checked=0, max_abs_D_err=0.0, missing_cells=0, rows_mismatch=0)
    for _ in range(samples):
        i, k = int(rng.integers(n_total)), int(rng.integers(J))
        radii = next(c["radii"] for c in man if c["seed0"] <= plan["seed0"] + i < c["seed0"] + c["n"])
        p = subprocess.run([EXE, "--seed0", str(plan["seed0"]), "--rays", str(J), "--rmax", str(rmax),
                            "--radii", ",".join(map(str, radii)), "--debug", f"{i},{k}"],
                           capture_output=True, text=True, check=True)
        lines = p.stdout.splitlines()
        _, sx, sz, sang = lines[0].split()
        px, pz, ang = float(sx), float(sz), float(sang)
        C = np.array([[float(v) for v in l.split(",")] for l in lines[1:]])
        qx, qz, bio, Dc = C[:, 0].astype(int), C[:, 1].astype(int), C[:, 2].astype(int), C[:, 3:]
        for j, r in enumerate(radii):
            Dp = th.cell_D(px, pz, ang, qx, qz, float(r), cap=float(rmax))
            fin = Dc[:, j] >= 0
            if (np.isfinite(Dp) != fin).any():
                stats["max_abs_D_err"] = math.inf
            else:
                stats["max_abs_D_err"] = max(stats["max_abs_D_err"], float(np.max(np.abs(Dp[fin] - Dc[fin, j]), initial=0)))
        cx, cz = _candidates(px, pz, ang, float(max(radii)), rmax)
        anyf = np.zeros(cx.size, bool)
        for r in radii:
            anyf |= np.isfinite(th.cell_D(px, pz, ang, cx, cz, float(r), cap=float(rmax)))
        have = set(zip(qx.tolist(), qz.tolist()))
        stats["missing_cells"] += sum((a, b) not in have for a, b in zip(cx[anyf].tolist(), cz[anyf].tolist()))
        s = signed(seed_of(plan["seed0"] + i))
        rows = A[(A[:, 0] == s) & (A[:, 1] == k) & (A[:, 5] == 1)]
        for j, r in enumerate(radii):
            fin = Dc[:, j] >= 0
            want = {}
            for b, d in zip(bio[fin], Dc[fin, j]):
                di = int(math.floor(d + 0.5))
                want[b] = min(want.get(b, di), di)
            got = {int(b): int(d) for b, d in rows[rows[:, 4] == r][:, [2, 3]]}
            stats["rows_mismatch"] += sum(want.get(b) != got.get(b) for b in set(want) | set(got))
        stats["rays_checked"] += 1; stats["cells_checked"] += int(C.shape[0])
    return stats


# ------------------------------------------------------------------ CLI
def _names():
    p = os.path.join(ROOT, "out", "names.csv")
    return {int(a): b for a, b in (l.strip().split(",", 1) for l in open(p))} if os.path.exists(p) else {}


def _ledger(out):
    p = os.path.join(out, "ledger.json")
    return json.load(open(p)) if os.path.exists(p) else []


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["plan", "run", "report", "verify"])
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--threads", type=int, default=os.cpu_count() or 1)
    ap.add_argument("--seed0", type=int, default=9_000_000_000)
    ap.add_argument("--pilot-seed0", type=int, default=8_000_000_000)
    ap.add_argument("--pilot-seeds", type=int, default=200)
    ap.add_argument("--radii", default="0,64,128")
    ap.add_argument("--rays", type=int, default=4)
    ap.add_argument("--target", type=float, default=0.05, help="relative half width wanted for the target biomes")
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--alpha-rest", type=float, default=0.005, help="share of alpha for the non-target quantities")
    ap.add_argument("--target-biomes", default=",".join(RARE))
    ap.add_argument("--chunk", type=int, default=500)
    ap.add_argument("--samples", type=int, default=5)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    pp = os.path.join(a.out, "plan.json")
    names = _names(); inv = {v: k for k, v in names.items()}
    if a.cmd == "plan":
        if os.path.exists(pp):
            sys.exit(f"{pp} exists: a plan is fixed once (delete it only if no production chunk has been run)")
        ledger = _ledger(a.out)
        pilot_entry = [u for u in ledger if u["seed0"] == a.pilot_seed0 and u["n"] == a.pilot_seeds]
        if not pilot_entry:
            check_fresh(a.pilot_seed0, a.pilot_seeds, ledger)
            ledger.append(dict(seed0=a.pilot_seed0, n=a.pilot_seeds, purpose="certrun pilot"))
        radii = [int(x) for x in a.radii.split(",")]
        pilot = dict(seed0=a.pilot_seed0, rays=a.rays, rmax=20000, threads=a.threads, out=os.path.join(a.out, "pilot"))
        os.makedirs(pilot["out"], exist_ok=True)
        pc = os.path.join(pilot["out"], "chunk_00000.csv")
        if not os.path.exists(pc):
            discexact(a.pilot_seed0, a.pilot_seeds, radii, pilot, pc)
        P = load_csv(pc)
        check_integrity(P, a.pilot_seed0, a.pilot_seeds, a.rays, radii)
        biomes = sorted(names) if names else sorted(set(P[:, 2].tolist()))
        targets = [inv[t] for t in a.target_biomes.split(",")]
        plan = make_plan(P, a.pilot_seed0, a.pilot_seeds, a.rays, radii, biomes, targets, a.target, a.alpha,
                         a.alpha_rest, a.seed0, a.chunk, os.path.relpath(a.out, ROOT), np.random.default_rng(0))
        nmax = max(plan["n_max"].values())
        check_fresh(a.seed0, nmax, [u for u in ledger if not u["purpose"].startswith("certrun production")])
        ledger = [u for u in ledger if not u["purpose"].startswith("certrun production")]
        ledger.append(dict(seed0=a.seed0, n=nmax, purpose=f"certrun production {plan['hash'][:12]} (at most n_max)"))
        json.dump(plan, open(pp, "w"), indent=1)          # commit plan.json and ledger.json before running production
        json.dump(ledger, open(os.path.join(a.out, "ledger.json"), "w"), indent=1)
        print(json.dumps(dict(n_star=plan["n_star"], expected_cpu_hours=plan["expected_cpu_s"] / 3600), indent=1))
        return
    plan = json.load(open(pp))
    if plan.get("hash") != plan_hash(plan):
        sys.exit("plan.json was edited after planning: refusing")
    plan["threads"] = a.threads
    plan["out"] = os.path.join(ROOT, plan["out"])          # stored relative to the repo so the plan travels
    if a.cmd == "run":
        run(plan)
    elif a.cmd == "report":
        report(plan, names)
        print(open(os.path.join(plan["out"], "report.md")).read())
    else:
        print(json.dumps(verify(plan, a.samples), indent=1))


if __name__ == "__main__":
    main()
