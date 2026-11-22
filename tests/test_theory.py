"""Numerical checks of the theorems in THEORY.md on synthetic worlds with known truth (no Cubiomes needed)."""
import math

import numpy as np
import pytest

import certify as ct
import theory as th

R0, R = 4000.0, 20000.0


# ---------------------------------------------------------------- section 1.4: the estimand as a functional
@pytest.mark.parametrize("lam", [1 / 3000, 1 / 20000, 1 / 150000])
def test_constant_hazard_gives_inverse_rate(lam):
    """Lemma 1: if the hazard is constant on [R0, R], M = 1 / lambda exactly, whatever happens before R0."""
    t = np.linspace(R0, R, 200001)
    S = 0.37 * np.exp(-lam * (t - R0))           # 63% of rays found it before R0: irrelevant
    assert th.window_M(t, S, R0, R) == pytest.approx(1 / lam, rel=1e-6)


def test_functional_is_monotone_in_conditional_survival():
    """Lemma 2: G' >= G pointwise on the window (conditional on reaching R0) implies M(G') >= M(G)."""
    rng = np.random.default_rng(1)
    t = np.linspace(R0, R, 4001)
    for _ in range(200):
        h = rng.gamma(1.0, 1 / 20000.0, size=t.size)              # arbitrary non-constant hazard
        G = np.exp(-np.concatenate([[0], np.cumsum(h[1:] * np.diff(t))]))
        theta = rng.uniform(0.3, 1.0, size=t.size)                # sparse hazard = theta * exact hazard
        Gk = np.exp(-np.concatenate([[0], np.cumsum(theta[1:] * h[1:] * np.diff(t))]))
        assert th.window_M(t, Gk, R0, R) >= th.window_M(t, G, R0, R) - 1e-9


# ---------------------------------------------------------------- Theorem 2: the sign of the sparse bias
def test_pointwise_later_does_not_imply_larger_M():
    """Counterexample: D_k >= D on every ray, yet M_k < M (left truncation at R0 lets a new event in)."""
    D = np.array([[1000.0], [np.inf], [10000.0]])
    Dk = np.array([[4001.0], [np.inf], [10000.0]])
    assert (Dk >= D).all()
    M, Mk = th.ratio_M(D, R0, R), th.ratio_M(Dk, R0, R)
    assert Mk < M                                            # 11000.5 < 22000


def test_lower_bound_on_sparse_bias():
    """Theorem 2(c): M_k - M >= -M * P(D < R0 <= D_k <= R) / P(R0 <= D_k <= R), for any coupling with D_k >= D."""
    rng = np.random.default_rng(2)
    for _ in range(300):
        D = rng.exponential(rng.uniform(2000, 40000), size=500)
        Dk = D + rng.exponential(rng.uniform(1, 3000), size=500) * (rng.random(500) < rng.uniform(0, 1))
        M, Mk = th.ratio_M(D, R0, R), th.ratio_M(Dk, R0, R)
        p_in = np.mean((D < R0) & (Dk >= R0) & (Dk <= R))
        Bk = np.mean((Dk >= R0) & (Dk <= R))
        assert Mk - M >= -M * p_in / Bk - 1e-9


# ---------------------------------------------------------------- Lemma 3 / geometry
def test_python_cell_D_matches_bruteforce():
    """cell_D (closed form) against convex minimisation + bisection on dist(L(s), Q) - r."""
    rng = np.random.default_rng(3)
    for _ in range(400):
        px, pz, ang = rng.uniform(-20, 20), rng.uniform(-20, 20), rng.uniform(0, 2 * math.pi)
        qx, qz = rng.integers(-15, 15), rng.integers(-15, 15)
        r = float(rng.choice([0.0, 3.0, 17.5, 64.0]))
        got = th.cell_D(px, pz, ang, np.array([qx]), np.array([qz]), r, cap=500.0)[0]
        x0, x1, z0, z1 = th.cell_box(qx, qz)
        f = lambda s: th.rect_dist(px + s * math.cos(ang), pz + s * math.sin(ang), x0, x1, z0, z1) - r
        rho = f(0.0) + r
        if rho <= r:
            assert got == pytest.approx(rho, abs=1e-9); continue
        lo, hi = 0.0, 500.0
        for _ in range(200):
            a, b = lo + (hi - lo) / 3, hi - (hi - lo) / 3
            lo, hi = (lo, b) if f(a) < f(b) else (a, hi)
        smin = 0.5 * (lo + hi)
        if f(smin) > 1e-9 or smin + r > 500:
            assert got == math.inf; continue
        a, b = 0.0, smin
        for _ in range(200):
            m = 0.5 * (a + b)
            a, b = (m, b) if f(m) > 0 else (a, m)
        assert got == pytest.approx(b + r, abs=1e-6)


# ---------------------------------------------------------------- Theorem 3: sandwich under the covering assumption
def disc_world(rng, n_disc=25, rlo=28, rhi=48, half=100):
    """Biome b = cells whose centre lies in one of n_disc discs (fully inside the region)."""
    q = np.arange(-half, half)
    QX, QZ = np.meshgrid(q, q, indexing="ij")
    cx, cz = 4 * QX + 1.5, 4 * QZ + 1.5
    inb = np.zeros(QX.shape, bool)
    for _ in range(n_disc):
        rad = rng.uniform(rlo, rhi)
        x, z = rng.uniform(-4 * half + rad + 8, 4 * half - rad - 8, size=2)
        inb |= (cx - x) ** 2 + (cz - z) ** 2 <= rad ** 2
    return QX[inb], QZ[inb]


@pytest.mark.parametrize("k", [2, 4])
def test_sandwich_under_covering(k):
    """D_r <= D_r^k <= D_{r - Delta} + Delta for r >= Delta, Delta = covering radius of the sampled cells."""
    rng = np.random.default_rng(10 + k)
    bx, bz = disc_world(rng)
    s = (bx % k == 0) & (bz % k == 0)
    Delta = th.covering_radius(bx, bz, bx[s], bz[s])
    assert Delta < 6 * k + 8                                # fat patches: finite and small
    for r in (math.ceil(Delta), 64.0, 96.0):
        for _ in range(60):
            px, pz, ang = rng.uniform(-40, 40), rng.uniform(-40, 40), rng.uniform(0, 2 * math.pi)
            D = th.set_D(px, pz, ang, bx, bz, r, cap=250)
            Dk = th.set_D(px, pz, ang, bx[s], bz[s], r, cap=250)
            Dlo = th.set_D(px, pz, ang, bx, bz, r - Delta, cap=250)
            assert Dk >= D - 1e-9                            # Theorem 1
            if Dlo + Delta <= 250:
                assert Dk <= Dlo + Delta + 1e-6              # Theorem 3


def test_sandwich_fails_without_covering():
    """A patch with no sampled cell is never found by the sparse level: no bound in terms of D exists."""
    bx, bz = np.array([1, 1, 2, 2]), np.array([1, 2, 1, 2])          # one 8x8-block patch, no cell with q % 4 == 0
    s = (bx % 4 == 0) & (bz % 4 == 0)
    assert th.covering_radius(bx, bz, bx[s], bz[s]) == math.inf
    assert th.set_D(0.0, 6.0, 0.0, bx, bz, 64.0) < 64
    assert th.set_D(0.0, 6.0, 0.0, bx[s], bz[s], 64.0) == math.inf


# ---------------------------------------------------------------- Proposition 11: colsim step-1 walk vs exact centerline
def test_step1_walk_is_within_one_block_when_chords_are_long():
    """D_0 <= D_step1, and D_step1 < D_0 + 1 whenever the line's first run inside P_b is at least 1 block long."""
    rng = np.random.default_rng(5)
    bx, bz = disc_world(rng, rlo=20, rhi=40)
    key = set(zip(bx.tolist(), bz.tolist()))
    is_b = lambda qx, qz: np.fromiter(((a, b) in key for a, b in zip(qx, qz)), bool, len(qx))
    checked = 0
    for _ in range(150):
        px, pz, ang = float(rng.integers(-40, 40)), float(rng.integers(-40, 40)), rng.uniform(0, 2 * math.pi)
        D0 = th.set_D(px, pz, ang, bx, bz, 0.0, cap=300)
        D1 = th.step_walk_D(px, pz, ang, is_b, h=1, rmax=300)
        assert D1 >= D0 - 1e-9
        if math.isfinite(D0) and D0 > 0:
            e = np.linspace(1e-6, 1.0, 60)                   # points L(D0 + e); cell q covers [4q - 0.5, 4q + 3.5]
            cqx = np.floor((px + (D0 + e) * math.cos(ang) + 0.5) / 4).astype(int)
            cqz = np.floor((pz + (D0 + e) * math.sin(ang) + 0.5) / 4).astype(int)
            if is_b(cqx, cqz).all():                         # first run inside P_b is at least 1 block long
                assert D1 < D0 + 1 + 1e-9; checked += 1
    assert checked > 20


# ---------------------------------------------------------------- Theorems 6-8: the exact estimator
def window_world(n, rays, M, q, rng, reps=None):
    """Ray first hit: with prob 1-q before R0 (uniform), else R0 + Exp(mean M). True window M is exactly M."""
    shape = (n, rays) if reps is None else (reps, n, rays)
    late = rng.random(shape) < q
    return np.where(late, R0 + rng.exponential(M, shape), rng.uniform(0, R0, shape))


def per_seed(D):
    E = ((D >= R0) & (D <= R)).sum(-1).astype(float)
    X = np.where(D >= R0, np.minimum(D, R) - R0, 0.0).sum(-1)
    return E, X


def test_consistency():
    rng = np.random.default_rng(6)
    E, X = per_seed(window_world(400_000, 4, 30000.0, 0.3, rng))
    assert X.sum() / E.sum() == pytest.approx(30000.0, rel=0.01)


def test_finite_sample_bias_matches_leading_term():
    """Theorem 7: E[M_hat] - M = (M Var(E) - Cov(X, E)) / (N mu^2) + O(N^-3/2)."""
    rng = np.random.default_rng(7)
    M, q, N, reps = 20000.0, 0.5, 60, 60000
    E, X = per_seed(window_world(N, 4, M, q, rng, reps=reps))
    est = X.sum(1) / E.sum(1)
    Eb, Xb = per_seed(window_world(2_000_000, 4, M, q, rng))
    mu = Eb.mean()
    pred = (M * Eb.var() - np.cov(Xb, Eb)[0, 1]) / (N * mu ** 2)
    obs = est.mean() - M
    se = est.std() / math.sqrt(reps)
    assert pred > 4 * se                                     # the effect is visible at this N
    assert abs(obs - pred) < 4 * se + 0.25 * abs(pred)       # remainder is higher order


def test_delta_ci_coverage():
    """Theorem 8: the combo() interval covers M at about 95% once events are plentiful."""
    rng = np.random.default_rng(8)
    M, hits, reps = 30000.0, 0, 1500
    for _ in range(reps):
        E, X = per_seed(window_world(800, 4, M, 0.3, rng))
        est, se, _ = ct.combo([ct.Term(1.0, E, X)])
        hits += abs(est - M) <= 1.96 * se
    assert 0.93 <= hits / reps <= 0.97


def test_empirical_bernstein_ci_has_finite_sample_coverage():
    """Theorem 9: coverage >= 95% even at small N, and about 1.5-2x the delta-method width at large N."""
    rng = np.random.default_rng(9)
    M, hits, reps = 30000.0, 0, 400
    for _ in range(reps):
        E, X = per_seed(window_world(60, 4, M, 0.3, rng))
        lo, hi = th.eb_ratio_ci(E, X, R0, R, rays=4)
        hits += lo <= M <= hi
    assert hits / reps >= 0.95
    E, X = per_seed(window_world(40000, 4, M, 0.3, rng))
    lo, hi = th.eb_ratio_ci(E, X, R0, R, rays=4)
    est, se, _ = ct.combo([ct.Term(1.0, E, X)])
    assert 1.2 < (hi - lo) / (2 * 1.96 * se) < 2.5


# ---------------------------------------------------------------- Proposition 12: integer rounding of D
def test_rounding_changes_M_by_at_most_the_bound():
    rng = np.random.default_rng(11)
    for _ in range(100):
        D = rng.exponential(rng.uniform(3000, 60000), size=4000)
        Dr = np.floor(D + 0.5)
        M, Mr = th.ratio_M(D, R0, R), th.ratio_M(Dr, R0, R)
        Br = np.mean((Dr >= R0) & (Dr <= R))
        a = 0.5 * np.mean(D >= R0 - 0.5)                     # X is 1-Lipschitz and flat outside [R0, R]
        e = np.mean((np.abs(D - R0) <= 0.5) | (np.abs(D - R) <= 0.5))   # E can flip only here
        bound = (a + M * e) / Br
        assert abs(Mr - M) <= bound + 1e-9
