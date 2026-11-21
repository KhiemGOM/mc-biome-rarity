"""Certified estimate of the mean walk M_b with a computed total error.

Estimator (two-phase): M_hat = rich(all) + [ M_1(calib) - rich(calib) ],  rich = 2 M_lo - M_hi (hi = 2 lo).
  - all    : N seeds simulated at grid steps lo, 2lo, ... (nested, one pass)
  - calib  : the first n_c of the same seeds also simulated at step 1 (the exact estimand)
The correction term measures the residual grid bias on the calibration seeds instead of assuming it is zero.
Every M_k is a ratio sum(X)/sum(E) over seeds, so M_hat is a linear combination of ratio estimators and
its variance follows from seed-cluster influence functions (delta method). A seed-cluster bootstrap
re-derives the same variance independently. epsilon = 1.96 * max(SE_delta, SE_boot) / M_hat.
"""
import math
from collections import namedtuple

import numpy as np

Term = namedtuple("Term", "coef E X name", defaults=("",))
MIN_EVENTS = 30            # below this the CLT is not credible: never certify


# ------------------------------------------------------------------ per-seed statistics
def stats(D, R0, R):
    """D: (n_seeds, rays) first-hit distances (inf = never). Returns per-seed (E, X)."""
    D = np.asarray(D, float)
    at_risk = D >= R0
    E = ((D >= R0) & (D <= R)).sum(1).astype(float)
    X = np.where(at_risk, np.minimum(D, R) - R0, 0.0).sum(1)
    return E, X


def _sums(t):
    return float(t.E.sum()), float(t.X.sum())


# ------------------------------------------------------------------ estimator and delta-method SE
def combo(terms):
    """Return (estimate, se_delta, z) for sum_k coef_k * sum(X_k)/sum(E_k).
    Terms may cover a prefix of the seeds (the calibration subset)."""
    N = max(len(t.E) for t in terms)
    est = 0.0
    z = np.zeros(N)
    for t in terms:
        se_, sx_ = _sums(t)
        if se_ <= 0:
            return 0.0, math.inf, z
        m = sx_ / se_
        est += t.coef * m
        z[: len(t.E)] += t.coef * (t.X - m * t.E) / se_
    var = float((z * z).sum()) * N / max(N - 1, 1)
    return est, math.sqrt(var), z


def boot_se(terms, n_boot, rng, chunk=40):
    """Seed-cluster bootstrap SE of the same estimator (a prefix term keeps the resampled seeds that fall in it)."""
    N = max(len(t.E) for t in terms)
    ests = []
    left = n_boot
    while left > 0:
        b = min(chunk, left)
        W = rng.multinomial(N, np.full(N, 1.0 / N), size=b).astype(float)   # (b, N) resample counts
        tot = np.zeros(b)
        for t in terms:
            n = len(t.E)
            w = W[:, :n]
            se_ = w @ t.E
            sx_ = w @ t.X
            with np.errstate(divide="ignore", invalid="ignore"):
                tot += t.coef * np.where(se_ > 0, sx_ / se_, np.nan)
        ests.append(tot)
        left -= b
    e = np.concatenate(ests)
    e = e[np.isfinite(e)]
    return float(e.std(ddof=1)) if e.size > 1 else math.inf


# ------------------------------------------------------------------ building the two-phase terms
def build_terms(main, calib, R0, R, lo=8, hi=16):
    """main: {step: D (N, rays)}, calib: {step: D (n_c, rays)} (first n_c seeds of main, also at step 1)."""
    if hi != 2 * lo:
        raise ValueError("Richardson needs hi == 2 * lo")
    for lvl in (lo, hi):
        if lvl not in main:
            raise KeyError(f"main run lacks step {lvl}")
    for lvl in (1, lo, hi):
        if lvl not in calib:
            raise KeyError(f"calibration run lacks step {lvl}")
    N, rays = main[lo].shape
    n_c, rays_c = calib[1].shape
    if rays != rays_c or main[hi].shape != (N, rays) or calib[lo].shape != (n_c, rays) or calib[hi].shape != (n_c, rays):
        raise ValueError("ray counts or row counts disagree between levels")
    if n_c > N:
        raise ValueError("calibration seeds must be a prefix subset of the main seeds")
    for lvl in (lo, hi):
        if not np.array_equal(calib[lvl], main[lvl][:n_c]):
            raise ValueError(f"calibration seeds are not the first {n_c} main seeds (step {lvl} differs)")
    s = {}
    for name, D in (("main_lo", main[lo]), ("main_hi", main[hi]), ("cal_1", calib[1]),
                    ("cal_lo", calib[lo]), ("cal_hi", calib[hi])):
        s[name] = stats(D, R0, R)
    return [Term(2.0, *s["main_lo"], "main_lo"), Term(-1.0, *s["main_hi"], "main_hi"),
            Term(1.0, *s["cal_1"], "cal_1"), Term(-2.0, *s["cal_lo"], "cal_lo"), Term(1.0, *s["cal_hi"], "cal_hi")]


# ------------------------------------------------------------------ certificate
def certificate(terms, target, n_boot=1000, rng=None):
    """Relative 95% half-width of the corrected estimate and whether it meets `target`."""
    rng = rng or np.random.default_rng(0)
    est, se_d, _ = combo(terms)
    events = int(round(terms[0].E.sum()))
    if events == 0 or not math.isfinite(se_d) or est <= 0:
        return dict(est=0.0, se_delta=math.inf, se_boot=math.inf, se=math.inf, half=math.inf,
                    rel_half=math.inf, certified=False, events=events, target=target)
    se_b = boot_se(terms, n_boot, rng)
    se = max(se_d, se_b)
    rel = 1.96 * se / est
    return dict(est=est, se_delta=se_d, se_boot=se_b, se=se, half=1.96 * se, rel_half=rel,
                certified=bool(rel <= target and events >= MIN_EVENTS), events=events, target=target)


# ------------------------------------------------------------------ planning (pilot -> N, n_c)
def _infl(t):
    se_, sx_ = _sums(t)
    m = sx_ / se_
    return (t.X - m * t.E) / (se_ / len(t.E))        # M_hat - M ~ mean of this


def _components(terms):
    by = {t.name: t for t in terms}
    for k in ("main_lo", "main_hi", "cal_1", "cal_lo", "cal_hi"):
        if k not in by:
            raise ValueError("planner needs terms from build_terms")
    if len(by["cal_1"].E) != len(by["main_lo"].E):
        raise ValueError("pilot must have the calibration run on every pilot seed")
    u = 2 * _infl(by["main_lo"]) - _infl(by["main_hi"])
    v = _infl(by["cal_1"]) - 2 * _infl(by["cal_lo"]) + _infl(by["cal_hi"])
    return u, v


def _var_parts(terms):
    u, v = _components(terms)
    a = float(u.var(ddof=1))
    b = float(v.var(ddof=1))
    c = float(np.cov(u, v)[0, 1])
    return a, b, c


def projected_rel_half(terms, N, n_c):
    a, b, c = _var_parts(terms)
    est = combo(terms)[0]
    var = (a + 2 * c) / N + b / n_c
    return 1.96 * math.sqrt(max(var, 0.0)) / est


def plan(terms, target, cost_ratio=8.0, margin=1.10, n_calib_grid=None):
    """Smallest cost N + cost_ratio * n_c meeting the target (pilot variance parts scaled to the new sizes)."""
    a, b, c = _var_parts(terms)
    est = combo(terms)[0]
    vt = (target * est / 1.96) ** 2
    best = None
    for n_c in (n_calib_grid or np.unique(np.geomspace(50, 200000, 120).astype(int))):
        room = vt - b / n_c
        if room <= 0:
            continue
        N = max((a + 2 * c) / room, n_c) * margin
        cost = N + cost_ratio * n_c
        if best is None or cost < best[0]:
            best = (cost, N, n_c)
    if best is None:
        raise ValueError("target unreachable: calibration variance floor is above the target")
    _, N, n_c = best
    N, n_c = int(math.ceil(N)), int(min(math.ceil(n_c), math.ceil(N)))
    while projected_rel_half(terms, N, n_c) > target:
        N = int(N * 1.02) + 1
    return dict(n_seeds=N, n_calib=n_c, proj_rel_half=projected_rel_half(terms, N, n_c),
                var_parts=dict(a=a, b=b, c=c))


# ------------------------------------------------------------------ independent consistency checks
def fold_check(terms, K=8, se_scale=1.0):
    """Split seeds i % K into K folds, estimate in each, chi-square the spread against the reported SE."""
    from scipy.stats import chi2 as _chi2
    est, se, _ = combo(terms)
    ests = []
    for f in range(K):
        sub = []
        for t in terms:
            idx = np.arange(len(t.E))
            m = (idx % K) == f
            sub.append(Term(t.coef, t.E[m], t.X[m], t.name))
        ests.append(combo(sub)[0])
    z = [(e - est) / (se * math.sqrt(K) * se_scale) for e in ests]
    c2 = float(sum(x * x for x in z))
    return dict(z=z, chi2=c2, dof=K - 1, p=float(_chi2.sf(c2, K - 1)), ests=ests)


def bin_hazards(D, R0, R, bins=4):
    """Piecewise-constant hazard (events per block of exposure) in equal bins of [R0, R]."""
    D = np.asarray(D, float).ravel()
    edges = np.linspace(R0, R, bins + 1)
    out = []
    for i in range(bins):
        lo, hi = edges[i], edges[i + 1]
        last = i == bins - 1
        ev = int(((D >= lo) & ((D <= hi) if last else (D < hi))).sum())
        expo = float(np.clip(np.minimum(D, hi) - lo, 0, None).sum())
        rate = ev / expo if expo > 0 else 0.0
        se = rate / math.sqrt(ev) if ev > 0 else (1.0 / expo if expo > 0 else math.inf)
        out.append(dict(lo=lo, hi=hi, events=ev, exposure=expo, rate=rate, se=se))
    return out


# ------------------------------------------------------------------ loading nested csv
def load_nested(path, n_seeds, rays, levels):
    """{biome: {step_index: D array (n_seeds, rays)}} from a --nested csv. Seeds are indexed by first appearance."""
    import pandas as pd
    df = pd.read_csv(path, dtype={"seed": np.int64, "ray": np.int32, "biome": np.int32,
                                  "dist": np.int64, "level": np.int8}, usecols=["seed", "ray", "biome", "dist", "level"])
    seeds = df["seed"].to_numpy()
    _, first = np.unique(seeds, return_index=True)
    order = seeds[np.sort(first)]
    if len(order) != n_seeds:
        raise ValueError(f"expected {n_seeds} seeds, found {len(order)}")
    idx = {int(s): i for i, s in enumerate(order)}
    si = np.fromiter((idx[int(s)] for s in seeds), dtype=np.int64, count=len(seeds)) if len(seeds) < 2_000_000 else \
        pd.Series(seeds).map(idx).to_numpy()
    out = {}
    for b in np.unique(df["biome"].to_numpy()):
        mb = (df["biome"].to_numpy() == b)
        out[int(b)] = {}
        for m in range(levels):
            mm = mb & (df["level"].to_numpy() == m)
            A = np.full((n_seeds, rays), np.inf)
            A[si[mm], df["ray"].to_numpy()[mm]] = df["dist"].to_numpy()[mm]
            out[int(b)][m] = A
    return out


# ------------------------------------------------------------------ stride variant (sparse cells + exact subsample)
def build_terms_stride(main_k, calib, R0, R, k):
    """M_hat = M_k(all) + [ M_1(cal) - M_k(cal) ]; main_k: D (N, rays) at stride k, calib: {1: D, k: D} on the first n_c seeds."""
    if 1 not in calib or k not in calib:
        raise KeyError("calibration needs stride 1 and stride k")
    N, rays = main_k.shape
    n_c = calib[1].shape[0]
    if calib[1].shape != calib[k].shape or calib[1].shape[1] != rays:
        raise ValueError("ray counts or row counts disagree between levels")
    if n_c > N:
        raise ValueError("calibration seeds must be a prefix subset of the main seeds")
    if not np.array_equal(calib[k], main_k[:n_c]):
        raise ValueError("calibration seeds are not the first n_c main seeds")
    return [Term(1.0, *stats(main_k, R0, R), "main_lo"), Term(1.0, *stats(calib[1], R0, R), "cal_1"),
            Term(-1.0, *stats(calib[k], R0, R), "cal_lo")]
