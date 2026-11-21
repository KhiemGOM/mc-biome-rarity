"""Estimators for biome rarity from raysim output.

Conventions: D is the first-hit distance, np.inf when never seen within the
cap R. Because the cap R is the same for every ray, the data are
administratively right-censored at R, so the Kaplan-Meier estimate equals the
empirical survival function.
"""
import csv
import math
from collections import defaultdict

import numpy as np


# ------------------------------------------------------------------ basics
def restricted_mean(d, R):
    """E[min(D, R)] = integral_0^R S(r) dr."""
    d = np.asarray(d, float)
    return float(np.minimum(d, R).mean())


def survival(d, grid):
    """Empirical S(r) = P(D > r) on a grid."""
    d = np.sort(np.asarray(d, float).ravel())
    n = d.size
    return 1.0 - np.searchsorted(d, np.asarray(grid, float), side="right") / n


def kaplan_meier(d, R, grid):
    """Product-limit estimate with censoring at R (kept explicit for the test)."""
    d = np.asarray(d, float).ravel()
    ev = np.sort(d[np.isfinite(d) & (d <= R)])
    n = d.size
    times = np.unique(ev)
    s, S = 1.0, []
    surv_at = {}
    at_risk = n
    j = 0
    for t in times:
        k = 0
        while j < ev.size and ev[j] == t:
            k += 1
            j += 1
        s *= 1.0 - k / at_risk
        at_risk -= k
        surv_at[t] = s
    ts = np.array(sorted(surv_at))
    vals = np.array([surv_at[t] for t in ts])
    out = []
    for r in np.asarray(grid, float):
        i = np.searchsorted(ts, r, side="right") - 1
        out.append(1.0 if i < 0 else vals[i])
    return np.array(out)


def median(d, R):
    """Smallest x with F(x) >= 0.5; inf if the median is censored."""
    d = np.sort(np.asarray(d, float).ravel())
    k = math.ceil(0.5 * d.size) - 1
    v = d[k]
    return float(v) if v <= R else math.inf


def hoeffding_n(R, eps, delta):
    """Seeds needed so |mean - mu| < eps w.p. >= 1-delta for X in [0, R]."""
    return math.ceil(R * R * math.log(2 / delta) / (2 * eps * eps))


def dkw_eps(N, delta):
    """Uniform band half-width for the empirical CDF (DKW)."""
    return math.sqrt(math.log(2 / delta) / (2 * N))


def hazard(d, R, edges):
    """Piecewise-constant hazard (MLE): events / exposure per bin."""
    d = np.asarray(d, float).ravel()
    edges = np.asarray(edges, float)
    mids, haz = [], []
    for a, b in zip(edges[:-1], edges[1:]):
        at_risk = d >= a
        events = np.sum(at_risk & (d < b))
        exposure = np.sum(np.minimum(d[at_risk], b) - a)
        mids.append(0.5 * (a + b))
        haz.append(events / exposure if exposure > 0 else np.nan)
    return np.array(mids), np.array(haz)


# ----------------------------------------------------------- uncertainty
def _seed_means(d, R):
    d = np.asarray(d, float)
    return np.minimum(d, R).mean(axis=1)


def bootstrap_restricted_mean(d, R, n_boot=2000, rng=None, alpha=0.05):
    """Cluster bootstrap over seeds (rows). Rays in a seed are not independent."""
    rng = rng or np.random.default_rng()
    m = _seed_means(d, R)
    N = m.size
    idx = rng.integers(0, N, (n_boot, N))
    boots = m[idx].mean(axis=1)
    return (float(np.quantile(boots, alpha / 2)),
            float(np.quantile(boots, 1 - alpha / 2)))


def bootstrap_median(d, R, n_boot=1000, rng=None, alpha=0.05):
    rng = rng or np.random.default_rng()
    d = np.asarray(d, float)
    N = d.shape[0]
    meds = []
    for _ in range(n_boot):
        s = d[rng.integers(0, N, N)]
        meds.append(median(s, R))
    meds = np.array(meds)
    return (float(np.quantile(meds, alpha / 2)),
            float(np.quantile(meds, 1 - alpha / 2)))


def variance_components(x):
    """One-way random-effects ANOVA. x is seeds x rays. Returns (var_seed, var_ray)."""
    x = np.asarray(x, float)
    N, K = x.shape
    msw = x.var(axis=1, ddof=1).mean()
    msb = K * x.mean(axis=1).var(ddof=1)
    return max(0.0, (msb - msw) / K), float(msw)


def k_star(c0, c1, var_ray, var_seed):
    """Best rays per seed for a fixed budget (never below 1)."""
    if var_seed <= 0:
        return math.inf
    return max(1.0, math.sqrt(c0 * var_ray / (c1 * var_seed)))


# ------------------------------------------------------------- far field
def far_mean_free_path(samples_in, entries, samples_total, step):
    """Mean gap between encounters, l = c(1-p)/p = step * outside_samples / entries."""
    if samples_in <= 0 or entries <= 0:
        return math.inf
    return step * (samples_total - samples_in) / entries


# --------------------------------------------------------------- loading
def load_first(path, n_seeds, rays):
    """Return {biome: array (n_seeds, rays)} of first-hit distances (inf = unseen)."""
    seed_index = {}
    data = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            s = int(r["seed"])
            si = seed_index.setdefault(s, len(seed_index))
            b = int(r["biome"])
            if b not in data:
                data[b] = np.full((n_seeds, rays), np.inf)
            data[b][si, int(r["ray"])] = int(r["dist"])
    return data


def load_far(path):
    """Return {biome: (samples_in, entries, samples_total)} summed over rays."""
    agg = defaultdict(lambda: [0, 0, 0])
    totals = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            b = int(r["biome"])
            agg[b][0] += int(r["samples_in"])
            agg[b][1] += int(r["entries"])
            totals[(r["seed"], r["ray"])] = int(r["samples_total"])
    grand = sum(totals.values())
    return {b: (v[0], v[1], grand) for b, v in agg.items()}
