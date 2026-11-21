"""certify.py: two-phase estimator, SE, certificate, planner. Synthetic data with known truth."""
import math
import numpy as np
import pytest

import certify as ct

R0, R = 4000.0, 20000.0


# ---------------------------------------------------------------- synthetic worlds
def exp_world(n, rays, M, rng, frailty=4.0):
    """First hit ~ Exp(mean M / g_i), g_i ~ Gamma(frailty, 1/frailty) shared by the rays of a seed."""
    g = rng.gamma(frailty, 1.0 / frailty, size=(n, 1))
    return rng.exponential(M, size=(n, rays)) / g


def patch_world(n, rays, rng, levels=(1, 2, 4, 8, 16, 32), lam0=1 / 40000.0, mean_chord=14.0, frailty=4.0):
    """Poisson patches (rate lam0 * frailty_i) with exponential chord lengths; grid hit = first multiple of h
    inside a patch. Grids are nested, so D_h <= D_2h per ray. Returns {h: D array (n, rays)}."""
    g = rng.gamma(frailty, 1.0 / frailty, size=(n, 1)) * np.ones((1, rays))
    pos = np.zeros((n, rays))
    out = {h: np.full((n, rays), np.inf) for h in levels}
    alive = np.ones((n, rays), bool)
    for _ in range(400):
        if not alive.any():
            break
        a = pos + rng.exponential(1.0 / (lam0 * g))
        ch = rng.exponential(mean_chord, size=(n, rays))
        b = a + ch
        alive &= a <= R
        for h in levels:
            first = np.ceil(a / h) * h
            hit = alive & (first <= b) & ~np.isfinite(out[h])
            out[h][hit] = first[hit]
        pos = b
        alive &= pos <= R
        # a ray can stop once every level has hit
        alive &= ~np.all([np.isfinite(out[h]) for h in levels], axis=0)
    return out


def terms_from(main, calib, lo=8, hi=16):
    return ct.build_terms(main, calib, R0, R, lo=lo, hi=hi)


# ---------------------------------------------------------------- basics
def test_stats_counts_events_and_exposure():
    D = np.array([[100.0, 5000.0, 30000.0, np.inf], [4000.0, 20000.0, 19999.0, 3999.0]])
    E, X = ct.stats(D, R0, R)
    assert E.tolist() == [1, 3]
    assert X.tolist() == [1000 + 16000 + 16000, 0 + 16000 + 15999]


def test_ratio_estimator_recovers_exponential_mean():
    rng = np.random.default_rng(1)
    M = 50000.0
    D = rng.exponential(M, size=(60000, 4))
    E, X = ct.stats(D, R0, R)
    est, se = ct.combo([ct.Term(1.0, E, X)])[:2]
    assert abs(est - M) < 4 * se
    assert se / M == pytest.approx(1 / math.sqrt(E.sum()), rel=0.05)   # exponential: rel SE = 1/sqrt(events)


def test_delta_se_matches_cluster_bootstrap():
    rng = np.random.default_rng(2)
    D = exp_world(4000, 4, 40000.0, rng)
    E, X = ct.stats(D, R0, R)
    t = [ct.Term(1.0, E, X)]
    se_d = ct.combo(t)[1]
    se_b = ct.boot_se(t, 800, np.random.default_rng(3))
    assert abs(se_b / se_d - 1) < 0.10


def test_ci_coverage_with_seed_frailty():
    rng = np.random.default_rng(4)
    big = exp_world(150000, 4, 40000.0, np.random.default_rng(5))
    Eb, Xb = ct.stats(big, R0, R)
    truth = ct.combo([ct.Term(1.0, Eb, Xb)])[0]
    hit, K = 0, 300
    for _ in range(K):
        E, X = ct.stats(exp_world(400, 4, 40000.0, rng), R0, R)
        est, se = ct.combo([ct.Term(1.0, E, X)])[:2]
        hit += abs(est - truth) <= 1.96 * se
    assert 0.91 <= hit / K <= 0.99


# ---------------------------------------------------------------- two-phase estimator
@pytest.fixture(scope="module")
def truth_and_bias():
    big = patch_world(120000, 4, np.random.default_rng(10))
    t1 = ct.combo([ct.Term(1.0, *ct.stats(big[1], R0, R))])[0]
    t8 = ct.combo([ct.Term(1.0, *ct.stats(big[8], R0, R))])[0]
    return t1, t8


def test_synthetic_world_has_real_step_bias(truth_and_bias):
    t1, t8 = truth_and_bias
    assert t8 / t1 - 1 > 0.01, "synthetic world must have a bias worth correcting"


def test_nested_synthetic_levels_are_monotone():
    w = patch_world(300, 4, np.random.default_rng(11))
    hs = sorted(w)
    for a, b in zip(hs, hs[1:]):
        assert np.all(w[a] <= w[b])


def test_two_phase_unbiased_and_se_matches_replication_sd(truth_and_bias):
    t1, t8 = truth_and_bias
    rng = np.random.default_rng(12)
    ests, ses, raw8 = [], [], []
    for _ in range(120):
        full = patch_world(1500, 4, rng)
        nc = 300
        main = {h: full[h] for h in (8, 16, 32)}
        calib = {h: full[h][:nc] for h in full}
        est, se = ct.combo(terms_from(main, calib))[:2]
        ests.append(est); ses.append(se)
        raw8.append(ct.combo([ct.Term(1.0, *ct.stats(full[8], R0, R))])[0])
    ests = np.array(ests)
    sd = ests.std(ddof=1)
    assert abs(ests.mean() - t1) < 3.5 * sd / math.sqrt(len(ests)) + 0.002 * t1
    assert abs(np.mean(ses) / sd - 1) < 0.20
    assert abs(np.mean(raw8) / t1 - 1) > 0.01


def test_two_phase_coverage(truth_and_bias):
    t1, _ = truth_and_bias
    rng = np.random.default_rng(13)
    hit, K = 0, 200
    for _ in range(K):
        full = patch_world(1200, 4, rng)
        nc = 300
        est, se = ct.combo(terms_from({h: full[h] for h in (8, 16, 32)}, {h: full[h][:nc] for h in full}))[:2]
        hit += abs(est - t1) <= 1.96 * se
    assert 0.90 <= hit / K <= 0.99


def test_two_phase_se_agrees_with_bootstrap():
    full = patch_world(1500, 4, np.random.default_rng(14))
    t = terms_from({h: full[h] for h in (8, 16, 32)}, {h: full[h][:300] for h in full})
    se_d = ct.combo(t)[1]
    se_b = ct.boot_se(t, 600, np.random.default_rng(15))
    assert abs(se_b / se_d - 1) < 0.15


def test_calibration_must_be_a_prefix_subset_of_main():
    full = patch_world(100, 4, np.random.default_rng(16))
    main = {h: full[h][:50] for h in (8, 16)}
    calib = {h: full[h] for h in full}          # longer than main
    with pytest.raises(ValueError):
        terms_from(main, calib)


def test_missing_level_raises():
    full = patch_world(100, 4, np.random.default_rng(17))
    with pytest.raises(KeyError):
        terms_from({8: full[8]}, {h: full[h] for h in full})


def test_rows_must_have_same_ray_count():
    a = np.zeros((10, 4)); b = np.zeros((10, 3))
    with pytest.raises(ValueError):
        ct.build_terms({8: a, 16: a}, {1: b, 8: b, 16: b}, R0, R)


# ---------------------------------------------------------------- certificate
def test_certificate_uses_corrected_center_and_flags_threshold():
    rng = np.random.default_rng(18)
    full = patch_world(2000, 4, rng)
    t = terms_from({h: full[h] for h in (8, 16, 32)}, {h: full[h][:400] for h in full})
    c = ct.certificate(t, target=0.5, n_boot=300, rng=np.random.default_rng(19))
    assert c["rel_half"] == pytest.approx(1.96 * c["se"] / c["est"])
    assert c["certified"] is True
    c2 = ct.certificate(t, target=1e-6, n_boot=300, rng=np.random.default_rng(19))
    assert c2["certified"] is False
    assert c["se"] == max(c["se_delta"], c["se_boot"])


def test_certificate_with_zero_events_is_uncertified_not_nan():
    D = {h: np.full((200, 4), np.inf) for h in (1, 2, 4, 8, 16, 32)}
    t = terms_from({h: D[h] for h in (8, 16, 32)}, {h: D[h][:50] for h in D})
    c = ct.certificate(t, target=0.02, n_boot=50, rng=np.random.default_rng(0))
    assert c["certified"] is False and c["events"] == 0
    assert not any(isinstance(v, float) and math.isnan(v) for v in c.values())


def test_certificate_with_few_events_is_uncertified():
    rng = np.random.default_rng(20)
    D = np.full((200, 4), np.inf); D[:3, 0] = 9000.0
    full = {h: D for h in (1, 2, 4, 8, 16, 32)}
    t = terms_from({h: full[h] for h in (8, 16, 32)}, {h: full[h][:50] for h in full})
    c = ct.certificate(t, target=0.5, n_boot=100, rng=rng)
    assert c["events"] == 3 and c["certified"] is False


# ---------------------------------------------------------------- planner
def test_planner_meets_target_on_fresh_data():
    rng = np.random.default_rng(21)
    pilot = patch_world(1500, 4, rng)
    tp = terms_from({h: pilot[h] for h in (8, 16, 32)}, {h: pilot[h] for h in pilot})
    target = 0.08
    plan = ct.plan(tp, target, cost_ratio=8.0)
    assert plan["n_calib"] <= plan["n_seeds"]
    assert plan["proj_rel_half"] <= target * 1.001
    n, nc = plan["n_seeds"], plan["n_calib"]
    got = []
    for _ in range(6):
        fresh = patch_world(n, 4, rng)
        t = terms_from({h: fresh[h] for h in (8, 16, 32)}, {h: fresh[h][:nc] for h in fresh})
        got.append(ct.certificate(t, target, n_boot=100, rng=rng)["rel_half"])
    assert np.mean(got) <= target * 1.25


def test_planner_projection_matches_certificate_at_pilot_size():
    pilot = patch_world(2500, 4, np.random.default_rng(22))
    tp = terms_from({h: pilot[h] for h in (8, 16, 32)}, {h: pilot[h] for h in pilot})
    est, se = ct.combo(tp)[:2]
    proj = ct.projected_rel_half(tp, 2500, 2500)
    assert proj == pytest.approx(1.96 * se / est, rel=0.05)


# ---------------------------------------------------------------- independent checks
def test_fold_check_accepts_correct_se_and_rejects_wrong_se():
    rng = np.random.default_rng(23)
    D = exp_world(8000, 4, 40000.0, rng)
    E, X = ct.stats(D, R0, R)
    t = [ct.Term(1.0, E, X)]
    ok = ct.fold_check(t, 8)
    assert ok["p"] > 0.01
    assert ok["chi2"] == pytest.approx(sum(z * z for z in ok["z"]), rel=1e-9)
    # fake: SE claimed half of the true one
    bad = ct.fold_check(t, 8, se_scale=0.5)
    assert bad["p"] < 0.05


def test_hazard_bins_flat_for_exponential():
    rng = np.random.default_rng(24)
    D = rng.exponential(30000.0, size=(40000, 4))
    h = ct.bin_hazards(D, R0, R, bins=4)
    rates = np.array([b["rate"] for b in h])
    ses = np.array([b["se"] for b in h])
    assert np.all(np.abs(rates - 1 / 30000.0) < 4 * ses)
    assert h[0]["events"] > 0


def test_hazard_bins_detect_changing_hazard():
    rng = np.random.default_rng(25)
    D = 25000.0 * rng.weibull(2.0, size=(40000, 4))          # hazard rises linearly with distance
    h = ct.bin_hazards(D, R0, R, bins=4)
    assert h[3]["rate"] > h[0]["rate"] + 4 * math.hypot(h[3]["se"], h[0]["se"])


# ---------------------------------------------------------------- stride variant
def test_stride_two_phase_is_consistent_for_exact_not_for_sparse():
    rng = np.random.default_rng(31)
    big = patch_world(120000, 4, np.random.default_rng(32))
    t1 = ct.combo([ct.Term(1.0, *ct.stats(big[1], R0, R))])[0]
    tk = ct.combo([ct.Term(1.0, *ct.stats(big[16], R0, R))])[0]
    assert tk / t1 - 1 > 0.02
    ests, covered = [], 0
    for _ in range(60):
        w = patch_world(1500, 4, rng)
        nc = 300
        t = ct.build_terms_stride(w[16], {1: w[1][:nc], 16: w[16][:nc]}, R0, R, 16)
        est, se = ct.combo(t)[:2]
        ests.append(est); covered += abs(est - t1) <= 1.96 * se
    ests = np.array(ests)
    assert abs(ests.mean() - t1) < 3.5 * ests.std(ddof=1) / math.sqrt(len(ests)) + 0.002 * t1   # unbiased for the exact value
    assert tk / t1 - 1 > 0.02                                  # while the sparse level alone is biased
    assert covered / 60 > 0.88


def test_stride_builder_rejects_wrong_prefix():
    w = patch_world(200, 4, np.random.default_rng(33))
    with pytest.raises(ValueError):
        ct.build_terms_stride(w[16], {1: w[1][:50], 16: w[16][50:100]}, R0, R, 16)
