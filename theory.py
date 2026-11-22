"""Reference implementations used by THEORY.md and tests/test_theory.py.

Nothing here is used by the production pipeline. These are independent (pure numpy) versions of the objects the
theory talks about, so the theorems can be checked numerically on synthetic worlds with known truth:
  - window_M          : the estimand as a functional of a survival curve (THEORY.md section 1.4)
  - cell_D / set_D    : the discovery functional D(A, r) for a union of 4x4 cells (section 1.2)
  - covering_radius   : an upper bound on the one-sided Hausdorff distance h(P_b, S_k(b)) (Theorem 3)
  - step_walk_D       : the colsim step-h walk (rounded points every h blocks), for Proposition 11
  - eb_ratio_ci       : finite-sample confidence interval for M by empirical-Bernstein inversion (Theorem 9)
"""
import math

import numpy as np


# ------------------------------------------------------------------ estimand as a functional
def window_M(t, S, R0, R):
    """M = int_{R0}^{R} S(t) dt / (S(R0-) - S(R)) on a grid t (ascending, t[0] = R0, t[-1] = R), S = P(D > t).
    S[0] is read as S(R0-) (no atom exactly at R0)."""
    t = np.asarray(t, float); S = np.asarray(S, float)
    num = float(np.sum(0.5 * (S[1:] + S[:-1]) * np.diff(t)))
    den = float(S[0] - S[-1])
    return num / den if den > 0 else math.inf


def ratio_M(D, R0, R):
    """Plain ratio estimator sum X / sum E over all entries of D."""
    D = np.asarray(D, float)
    E = ((D >= R0) & (D <= R)).sum()
    X = np.where(D >= R0, np.minimum(D, R) - R0, 0.0).sum()
    return X / E if E > 0 else math.inf


# ------------------------------------------------------------------ geometry (independent of discexact.c)
def cell_box(qx, qz):
    qx = np.asarray(qx, float); qz = np.asarray(qz, float)
    return 4 * qx - 0.5, 4 * qx + 3.5, 4 * qz - 0.5, 4 * qz + 3.5


def rect_dist(px, pz, x0, x1, z0, z1):
    dx = np.maximum(np.maximum(x0 - px, 0.0), px - x1)
    dz = np.maximum(np.maximum(z0 - pz, 0.0), pz - z1)
    return np.hypot(dx, dz)


def _slab(px, pz, ux, uz, xa, xb, za, zb):
    lo = np.full(np.shape(xa), -np.inf); hi = np.full(np.shape(xa), np.inf); ok = np.ones(np.shape(xa), bool)
    for p, u, a, b in ((px, ux, xa, xb), (pz, uz, za, zb)):
        if abs(u) < 1e-12:
            ok &= (p >= a) & (p <= b)
        else:
            t1, t2 = (a - p) / u, (b - p) / u
            lo = np.maximum(lo, np.minimum(t1, t2)); hi = np.minimum(hi, np.maximum(t1, t2))
    ok &= lo <= hi
    return np.where(ok, lo, np.inf), np.where(ok, hi, -np.inf)


def _disc(px, pz, ux, uz, cx, cz, r):
    dx, dz = px - cx, pz - cz
    b = dx * ux + dz * uz
    disc = b * b - (dx * dx + dz * dz - r * r)
    q = np.sqrt(np.maximum(disc, 0.0))
    ok = disc >= 0
    return np.where(ok, -b - q, np.inf), np.where(ok, -b + q, -np.inf)


def cell_D(px, pz, ang, qx, qz, r, cap=np.inf):
    """D_c for every cell (qx, qz): rho if rho <= r, else (first s >= 0 with dist(L(s), Q_c) <= r) + r; inf if > cap."""
    ux, uz = math.cos(ang), math.sin(ang)
    x0, x1, z0, z1 = cell_box(qx, qz)
    rho = rect_dist(px, pz, x0, x1, z0, z1)
    pieces = [_slab(px, pz, ux, uz, x0 - r, x1 + r, z0, z1), _slab(px, pz, ux, uz, x0, x1, z0 - r, z1 + r)]
    if r > 0:
        pieces += [_disc(px, pz, ux, uz, cx, cz, r) for cx in (x0, x1) for cz in (z0, z1)]
    lo = np.min([p[0] for p in pieces], axis=0); hi = np.max([p[1] for p in pieces], axis=0)
    s = np.maximum(lo, 0.0)
    D = np.where(hi >= 0, s + r, np.inf)
    D = np.where(rho <= r, rho, D)
    return np.where(D <= cap, D, np.inf)


def set_D(px, pz, ang, qx, qz, r, cap=np.inf):
    """D(A, r) for A = union of the given cells (min over cells, Lemma 3)."""
    if len(qx) == 0:
        return math.inf
    return float(np.min(cell_D(px, pz, ang, qx, qz, r, cap)))


def covering_radius(qx, qz, sx, sz):
    """Upper bound on h(P, S) = sup_{x in P} dist(x, S) for P = union of cells (qx, qz), S = union of cells (sx, sz).
    For each cell of P: min over S-cells of the max over the 4 vertices of the distance to that S-cell (the distance
    to one convex S-cell is convex, so its max over a square is at a vertex). inf if S is empty."""
    if len(sx) == 0:
        return math.inf
    x0, x1, z0, z1 = cell_box(qx, qz)
    a0, a1, b0, b1 = (v[None, :] for v in cell_box(sx, sz))
    worst = np.zeros((len(qx), len(sx)))
    for vx in (x0, x1):
        for vz in (z0, z1):
            worst = np.maximum(worst, rect_dist(vx[:, None], vz[:, None], a0, a1, b0, b1))
    return float(worst.min(axis=1).max())


def step_walk_D(px, pz, ang, is_b, h=1, rmax=20000):
    """colsim walk: block = round(L(s)) at s = 0, h, 2h, ...; cell = floor(block / 4). is_b(qx, qz) -> bool array."""
    s = np.arange(0, rmax + 1, h, dtype=float)
    bx = px + np.floor(s * math.cos(ang) + 0.5); bz = pz + np.floor(s * math.sin(ang) + 0.5)
    hit = is_b(np.floor(bx / 4).astype(int), np.floor(bz / 4).astype(int))
    return float(s[np.argmax(hit)]) if hit.any() else math.inf


# ------------------------------------------------------------------ finite-sample confidence interval
def eb_ratio_ci(E, X, R0, R, rays, alpha=0.05, iters=200):
    """Confidence set for M = E[X_i] / E[E_i] with coverage >= 1 - alpha for every N (iid seeds), by inverting the
    empirical-Bernstein bound (Maurer and Pontil 2009, Thm 4) for Z_i(m) = X_i - m E_i, each side at level alpha/2.
    Accept m iff h(m) = bound(m) - |mean Z(m)| >= 0. h is convex on [0, M_hat] and on [M_hat, inf) (THEORY.md,
    Theorem 9), so each side's accepted set is an interval found exactly by bisection. Returns (lo, hi); hi may be inf."""
    E = np.asarray(E, float); X = np.asarray(X, float); N = len(E)
    if E.sum() <= 0 or N < 2:
        return 0.0, math.inf
    est = X.sum() / E.sum()
    L = math.log(2.0 / (alpha / 2.0))

    def h(m):
        Z = X - m * E
        return math.sqrt(2 * Z.var(ddof=1) * L / N) + 7 * rays * (R - R0 + m) * L / (3 * (N - 1)) - abs(Z.mean())

    def root(a, b):                       # h(a) >= 0 > h(b) or the reverse; returns the crossing point
        ha = h(a) >= 0
        for _ in range(iters):
            c = 0.5 * (a + b)
            if (h(c) >= 0) == ha:
                a = c
            else:
                b = c
        return a if ha else b

    lo = 0.0 if h(0.0) >= 0 else root(est, 0.0)          # h(0) < 0 < h(est): accepted part of [0, est] is [lo, est]
    slope_inf = math.sqrt(2 * L / N) * E.std(ddof=1) + 7 * rays * L / (3 * (N - 1)) - E.mean()
    if slope_inf >= 0:
        return lo, math.inf                               # too few events: the set is unbounded above
    top = 2 * est
    while h(top) >= 0:
        top *= 2
    return lo, root(est, top)
