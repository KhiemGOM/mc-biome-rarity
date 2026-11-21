"""Tests for the estimator module rarity.py. Written before the implementation."""
import math

import numpy as np
import pytest

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rarity as ry


# ---------------------------------------------------------------- happy path
def test_restricted_mean_matches_closed_form_exponential():
    rng = np.random.default_rng(0)
    lam, R, N = 1 / 3000.0, 8000.0, 200_000
    d = rng.exponential(1 / lam, N)
    d[d > R] = np.inf  # censored at cap
    est = ry.restricted_mean(d, R)
    truth = (1 - math.exp(-lam * R)) / lam
    assert est == pytest.approx(truth, rel=0.01)


def test_empirical_survival_equals_kaplan_meier_with_fixed_cap():
    rng = np.random.default_rng(1)
    R = 5000.0
    d = rng.exponential(2500, 3000)
    d[d > R] = np.inf
    grid = np.linspace(0, R, 41)
    s = ry.survival(d, grid)
    km = ry.kaplan_meier(d, R, grid)
    assert np.allclose(s, km)
    assert s[0] == 1.0 and np.all(np.diff(s) <= 1e-12)


def test_median_found_and_censored_cases():
    d = np.array([100.0, 200.0, 300.0, np.inf, np.inf])
    assert ry.median(d, 1000.0) == 300.0
    d2 = np.array([100.0, np.inf, np.inf, np.inf])
    assert math.isinf(ry.median(d2, 1000.0))


def test_sample_size_formulas():
    n = ry.hoeffding_n(R=20000, eps=100, delta=0.05)
    assert n == math.ceil(20000**2 * math.log(2 / 0.05) / (2 * 100**2))
    assert 73000 < n < 75000
    e = ry.dkw_eps(N=2000, delta=0.05)
    assert e == pytest.approx(math.sqrt(math.log(2 / 0.05) / (2 * 2000)))


def test_hazard_of_exponential_is_flat():
    rng = np.random.default_rng(2)
    lam = 1 / 4000.0
    d = rng.exponential(1 / lam, 400_000)
    R = 12000.0
    d[d > R] = np.inf
    edges = np.linspace(0, R, 7)
    mid, h = ry.hazard(d, R, edges)
    assert np.allclose(h, lam, rtol=0.1)


# ------------------------------------------------------------ failure modes
def test_cluster_bootstrap_ci_covers_truth():
    rng = np.random.default_rng(3)
    lam, R = 1 / 3000.0, 8000.0
    truth = (1 - math.exp(-lam * R)) / lam
    cover, trials = 0, 60
    for t in range(trials):
        d = rng.exponential(1 / lam, (150, 4))
        d[d > R] = np.inf
        lo, hi = ry.bootstrap_restricted_mean(d, R, n_boot=300, rng=rng)
        cover += lo <= truth <= hi
    assert cover / trials >= 0.85  # nominal 95%, allow slack at 60 trials


def test_all_censored_biome_gives_cap_mean_and_inf_median():
    d = np.full((50, 4), np.inf)
    assert ry.restricted_mean(d, 9000.0) == 9000.0
    assert math.isinf(ry.median(d, 9000.0))


def test_variance_components_recovered():
    rng = np.random.default_rng(4)
    N, K = 4000, 8
    s_seed, s_ray = 3.0, 5.0
    mu = rng.normal(0, s_seed, (N, 1))
    x = 100 + mu + rng.normal(0, s_ray, (N, K))
    vb, vw = ry.variance_components(x)
    assert vb == pytest.approx(s_seed**2, rel=0.12)
    assert vw == pytest.approx(s_ray**2, rel=0.05)


def test_k_star_formula_and_floor_at_one():
    assert ry.k_star(c0=100.0, c1=1.0, var_ray=4.0, var_seed=1.0) == pytest.approx(
        math.sqrt(100 * 4 / 1))
    assert ry.k_star(c0=0.01, c1=1.0, var_ray=1.0, var_seed=10.0) == 1.0


def test_far_field_mean_free_path_on_synthetic_renewal_line():
    rng = np.random.default_rng(5)
    h = 16
    chord_mean, gap_mean = 400.0, 3600.0
    n = 4_000_000
    inside = np.zeros(n, bool)
    i, state = 0, False
    while i < n:
        L = int(max(1, rng.exponential((chord_mean if state else gap_mean) / h)))
        inside[i:i + L] = state
        i += L
        state = not state
    entries = int(np.sum(inside[1:] & ~inside[:-1]))
    p = inside.mean()
    ell = ry.far_mean_free_path(samples_in=int(inside.sum()), entries=entries,
                                samples_total=n, step=h)
    # alternating renewal: gap between encounters ~ chord*(1-p)/p = gap_mean
    assert ell == pytest.approx(gap_mean, rel=0.08)


def test_far_field_handles_zero_entries():
    assert math.isinf(ry.far_mean_free_path(0, 0, 1000, 16))
