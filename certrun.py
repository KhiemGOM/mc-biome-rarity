"""Certified exact Monte Carlo sampler (THEORY.md section 6).

  python3 certrun.py plan   [--pilot-seeds 200] [--seed0 9000000000] [--radii 0,64,128] [--target 0.05] [--threads T]
  python3 certrun.py run    [--threads T]          # resumable; chunks of plan["chunk"] seeds
  python3 certrun.py report                       # certificate.json + report.md
  python3 certrun.py verify [--samples 5]         # independent re-derivation of the geometry on production rays

What makes it certified (each point is a hypothesis of Theorem 13):
  - exact model only: level 1 rows of discexact (every cell), r = 0 is the exact centerline (no step walk, no stride);
  - N is fixed by the plan from a pilot on DIFFERENT seeds, before any production seed is simulated (no optional stopping);
  - production seeds are fresh: the plan refuses any range that overlaps the ledger or the historical runs;
  - the report refuses data that are not exactly the planned seeds, or any (seed, ray, radius) without its spawn row;
  - every (biome, radius) gets an empirical-Bernstein interval at level alpha / K (K = biomes x radii), so all K hold
    at once with probability >= 1 - alpha for the planned N, under assumptions A1 and A2 only.
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


# ------------------------------------------------------------------ intervals, planning, ordering
def interval(E, X, R0, R, rays, alpha_each):
    return th.eb_ratio_ci(E, X, R0, R, rays, alpha=alpha_each)


def rel_half(E, X, R0, R, rays, alpha_each, N):
    """Predicted relative half width of the EB interval at N seeds from pilot moments (THEORY.md 6.3)."""
    m = X.sum() / E.sum()
    V = float((X - m * E).var(ddof=1)); L = math.log(4.0 / alpha_each)
    half = (math.sqrt(2 * V * L / N) + 7 * rays * (R - R0 + m) * L / (3 * (N - 1))) / E.mean()
    return half / m


def required_N(E, X, R0, R, rays, alpha_each, target, margin=1.10):
    if E.sum() <= 0:
        raise ValueError("no pilot events: cannot plan")
    hi = 2
    while rel_half(E, X, R0, R, rays, alpha_each, hi) > target:
        hi *= 2
    lo = hi // 2
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (mid, hi) if rel_half(E, X, R0, R, rays, alpha_each, mid) > target else (lo, mid)
    return int(math.ceil(hi * margin))


def certified_order(res):
    """Pairs (a, b) meaning M_a > M_b is certified: the simultaneous intervals are disjoint."""
    return [(a, b) for a in res for b in res if a != b and res[a]["lo"] > res[b]["hi"]]


# ------------------------------------------------------------------ running discexact
def chunks(plan):
    c, n = plan["chunk"], plan["n_seeds"]
    return [(k, plan["seed0"] + k * c, min(c, n - k * c)) for k in range((n + c - 1) // c)]


def chunk_path(plan, k):
    return os.path.join(plan["out"], f"chunk_{k:05d}.csv")


def discexact(seed0, n, plan, out):
    cmd = [EXE, "--seeds", n, "--rays", plan["rays"], "--rmax", plan["rmax"], "--radii", ",".join(map(str, plan["radii"])),
           "--seed0", seed0, "--threads", plan.get("threads", 1), "--out", out]
    subprocess.run([str(a) for a in cmd], check=True)


def run(plan, log=print):
    for k, s0, n in chunks(plan):
        p = chunk_path(plan, k)
        if os.path.exists(p):
            try:
                check_integrity(load_csv(p), s0, n, plan["rays"], plan["radii"]); continue
            except ValueError as e:
                log(f"chunk {k}: {e}; recomputing")
        discexact(s0, n, plan, p)
        check_integrity(load_csv(p), s0, n, plan["rays"], plan["radii"])
        log(f"chunk {k} done ({s0}..{s0 + n - 1})")


# ------------------------------------------------------------------ report
def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def plan_hash(plan):
    keys = ["seed0", "n_seeds", "rays", "radii", "rmax", "R0", "R", "alpha", "biomes", "target", "target_biomes", "chunk"]
    return hashlib.sha256(json.dumps({k: plan[k] for k in keys}, sort_keys=True).encode()).hexdigest()


def load_all(plan):
    parts = []
    for k, s0, n in chunks(plan):
        p = chunk_path(plan, k)
        if not os.path.exists(p):
            raise ValueError(f"chunk {k} missing ({p}): the planned N has not been simulated")
        parts.append(load_csv(p))
    A = np.concatenate(parts)
    check_integrity(A, plan["seed0"], plan["n_seeds"], plan["rays"], plan["radii"])
    return A


def report(plan, names=None):
    A = load_all(plan)
    n, J, R0, R = plan["n_seeds"], plan["rays"], float(plan["R0"]), float(plan["R"])
    if plan["rmax"] != R:
        raise ValueError("rmax must equal R (censoring, THEORY.md section 4 row 11)")
    idx = {signed(seed_of(plan["seed0"] + i)): i for i in range(n)}
    si_all = np.fromiter((idx[s] for s in A[:, 0]), np.int64, A.shape[0])
    K = len(plan["biomes"]) * len(plan["radii"])
    a_each = plan["alpha"] / K
    names = names or {}
    results, by_radius = [], {}
    for r in plan["radii"]:
        for b in plan["biomes"]:
            m = (A[:, 2] == b) & (A[:, 4] == r)
            E, X = per_seed_EX(si_all[m], A[m, 3], n, J, R0, R)
            lo, hi = interval(E, X, R0, R, J, a_each)
            ev = int(E.sum())
            est, se = (ct.combo([ct.Term(1.0, E, X)])[:2]) if ev > 0 else (math.inf, math.inf)
            row = dict(biome=int(b), name=names.get(int(b), str(b)), radius=int(r), events=ev, est=est, lo=lo, hi=hi,
                       rel_half=(hi - lo) / 2 / est if ev > 0 and math.isfinite(hi) else math.inf,
                       delta_lo=est - 1.96 * se, delta_hi=est + 1.96 * se)
            if int(b) in plan["target_biomes"]:
                row["target_met"] = bool(row["rel_half"] <= plan["target"])
                D = np.full((n, J), np.inf); D[si_all[m], A[m, 1]] = A[m, 3]
                row["hazard_bins"] = ct.bin_hazards(D, R0, R, bins=4)
            results.append(row)
            if ev > 0:
                by_radius.setdefault(int(r), {})[row["name"]] = row
    order = {r: certified_order(res) for r, res in by_radius.items()}
    cert = dict(plan_hash=plan_hash(plan), n_seeds=n, K=K, alpha=plan["alpha"], alpha_each=a_each,
                statement=f"Under A1 and A2 (THEORY.md 3.1), with probability >= {1 - plan['alpha']:.3f} every one of the "
                          f"{K} intervals contains its M simultaneously (Theorem 13), hence every listed order too.",
                discexact_sha256=_sha(EXE) if os.path.exists(EXE) else None, git=_git(), results=results,
                certified_order={str(r): v for r, v in order.items()})
    os.makedirs(plan["out"], exist_ok=True)
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
    out = [f"# Certified exact run\n", cert["statement"] + "\n",
           f"Seeds: index {plan['seed0']} .. {plan['seed0'] + plan['n_seeds'] - 1} ({plan['n_seeds']} seeds x {plan['rays']} rays). "
           f"Plan hash `{cert['plan_hash'][:16]}`, code `{(cert['git'] or '')[:10]}`.\n"]
    for r in plan["radii"]:
        rows = sorted([x for x in cert["results"] if x["radius"] == r and x["events"] > 0], key=lambda x: -x["est"])[:15]
        out.append(f"\n## r = {r} (rarest 15)\n\n| biome | M | certified interval | rel half | events |\n|---|---|---|---|---|")
        for x in rows:
            hi = f"{x['hi']:,.0f}" if math.isfinite(x["hi"]) else "inf"
            out.append(f"| {x['name']} | {x['est']:,.0f} | [{x['lo']:,.0f}, {hi}] | {100 * x['rel_half']:.1f}% | {x['events']} |")
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


def verify(plan, samples=5, rng=None, A=None):
    """For random production (seed, ray): rerun discexact --debug, recompute every cell's D with theory.cell_D,
    check no cell is missing from the C enumeration, and that the per biome minima equal the production rows."""
    rng = rng or np.random.default_rng()
    A = load_all(plan) if A is None else A
    J, rmax, radii = plan["rays"], plan["rmax"], plan["radii"]
    stats = dict(rays_checked=0, cells_checked=0, max_abs_D_err=0.0, missing_cells=0, rows_mismatch=0)
    for _ in range(samples):
        i, k = int(rng.integers(plan["n_seeds"])), int(rng.integers(J))
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
    ap.add_argument("--target-biomes", default=",".join(RARE))
    ap.add_argument("--chunk", type=int, default=500)
    ap.add_argument("--max-seeds", type=int, default=0, help="cap N (then the target may not be met; coverage still holds)")
    ap.add_argument("--samples", type=int, default=5)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    pp = os.path.join(a.out, "plan.json")
    names = _names(); inv = {v: k for k, v in names.items()}
    if a.cmd == "plan":
        if os.path.exists(pp):
            sys.exit(f"{pp} exists: a plan is fixed once (delete it only if no production chunk has been run)")
        ledger = _ledger(a.out)
        check_fresh(a.pilot_seed0, a.pilot_seeds, ledger)
        radii = [int(x) for x in a.radii.split(",")]
        pilot = dict(seed0=a.pilot_seed0, n_seeds=a.pilot_seeds, rays=a.rays, radii=radii, rmax=20000,
                     threads=a.threads, chunk=a.pilot_seeds, out=os.path.join(a.out, "pilot"))
        os.makedirs(pilot["out"], exist_ok=True)
        run(pilot)
        P = load_all(pilot)
        biomes = sorted(names) if names else sorted(set(P[:, 2].tolist()))
        targets = [inv[t] for t in a.target_biomes.split(",")]
        K = len(biomes) * len(radii)
        idx = {signed(seed_of(a.pilot_seed0 + i)): i for i in range(a.pilot_seeds)}
        si = np.fromiter((idx[s] for s in P[:, 0]), np.int64, P.shape[0])
        need = {}
        for r in radii:
            for b in targets:
                m = (P[:, 2] == b) & (P[:, 4] == r)
                E, X = per_seed_EX(si[m], P[m, 3], a.pilot_seeds, a.rays, 4000.0, 20000.0)
                need[f"{names.get(b, b)}@r{r}"] = required_N(E, X, 4000.0, 20000.0, a.rays, a.alpha / K, a.target)
        N = max(need.values())
        if a.max_seeds:
            N = min(N, a.max_seeds)
        check_fresh(a.seed0, N, ledger + [dict(seed0=a.pilot_seed0, n=a.pilot_seeds, purpose="this plan's pilot")])
        plan = dict(seed0=a.seed0, n_seeds=N, rays=a.rays, radii=radii, rmax=20000, R0=4000.0, R=20000.0, alpha=a.alpha,
                    biomes=biomes, chunk=a.chunk, target_biomes=targets, target=a.target, out=os.path.relpath(a.out, ROOT),
                    pilot=dict(seed0=a.pilot_seed0, n=a.pilot_seeds, required=need))
        plan["hash"] = plan_hash(plan)
        json.dump(plan, open(pp, "w"), indent=1)          # commit plan.json and ledger.json before running production
        ledger += [dict(seed0=a.pilot_seed0, n=a.pilot_seeds, purpose="certrun pilot"),
                   dict(seed0=a.seed0, n=N, purpose=f"certrun production {plan['hash'][:12]}")]
        json.dump(ledger, open(os.path.join(a.out, "ledger.json"), "w"), indent=1)
        print(json.dumps(need, indent=1)); print(f"N = {N} seeds x {a.rays} rays, K = {K}, alpha/K = {a.alpha / K:.2e}")
        return
    plan = json.load(open(pp))
    if plan.get("hash") != plan_hash(plan):
        sys.exit("plan.json was edited after planning: refusing")
    plan["threads"] = a.threads
    plan["out"] = os.path.join(ROOT, plan["out"])          # stored relative to the repo so the plan travels
    if a.cmd == "run":
        run(plan)
    elif a.cmd == "report":
        cert = report(plan, names)
        print(open(os.path.join(plan["out"], "report.md")).read())
    else:
        print(json.dumps(verify(plan, a.samples), indent=1))


if __name__ == "__main__":
    main()
