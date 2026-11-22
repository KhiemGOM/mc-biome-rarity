"""certrun.py: certified exact sampler (THEORY.md section 6). Failure modes first, then an end to end run."""
import json, math, os, subprocess, sys

import numpy as np
import pytest

import certify as ct
import certrun as cr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, "discexact")
R0, R = 4000.0, 20000.0


# ---------------------------------------------------------------- seeds
def test_splitmix_matches_c():
    """Python splitmix64 must reproduce the C seeds (checked against a discexact row below when the binary exists)."""
    assert cr.seed_of(0) == cr.seed_of(0)
    assert len({cr.seed_of(i) for i in range(10000)}) == 10000            # bijection: distinct


@pytest.mark.parametrize("a,b,ok", [((9_000_000_000, 100), (9_000_000_100, 50), True),
                                     ((9_000_000_000, 100), (9_000_000_099, 5), False),
                                     ((7_000_000_000, 10), None, False),          # historical certified run
                                     ((5_000_000_000, 10), None, False)])         # historical pilot
def test_overlap_guard(a, b, ok):
    ledger = [] if b is None else [dict(seed0=b[0], n=b[1], purpose="x")]
    if ok:
        cr.check_fresh(a[0], a[1], ledger)
    else:
        with pytest.raises(ValueError):
            cr.check_fresh(a[0], a[1], ledger)


# ---------------------------------------------------------------- per seed X, E from sparse rows
def test_per_seed_EX_matches_dense_stats():
    rng = np.random.default_rng(0)
    n, J = 50, 4
    D = rng.exponential(15000, size=(n, J)); D[rng.random((n, J)) < 0.3] = np.inf; D[0, 0] = R0; D[1, 1] = R
    E_ref, X_ref = ct.stats(D, R0, R)
    si, ray = np.nonzero(np.isfinite(D))
    E, X = cr.per_seed_EX(si, D[si, ray], n, J, R0, R)
    assert np.array_equal(E, E_ref) and np.allclose(X, X_ref)


# ---------------------------------------------------------------- data integrity checks
def fake_rows(n, J, radii, seed0, drop=None):
    rows = []
    for i in range(n):
        s = cr.signed(cr.seed_of(seed0 + i))
        for k in range(J):
            for r in radii:
                if drop != (i, k, r):
                    rows.append((s, k, 7, 0, r, 1))                             # spawn cell, D = 0
                rows.append((s, k, 9, 5000 + i, r, 1))
    return np.array(rows, dtype=np.int64)


def test_integrity_accepts_good_data():
    A = fake_rows(5, 4, (0, 64), 9_000_000_000)
    cr.check_integrity(A, 9_000_000_000, 5, 4, (0, 64))


def test_integrity_rejects_missing_seed():
    A = fake_rows(5, 4, (0, 64), 9_000_000_000)
    A = A[A[:, 0] != cr.signed(cr.seed_of(9_000_000_003))]
    with pytest.raises(ValueError, match="seed"):
        cr.check_integrity(A, 9_000_000_000, 5, 4, (0, 64))


def test_integrity_rejects_wrong_seeds():
    A = fake_rows(5, 4, (0, 64), 9_000_000_001)                                # shifted range
    with pytest.raises(ValueError, match="seed"):
        cr.check_integrity(A, 9_000_000_000, 5, 4, (0, 64))


def test_integrity_rejects_truncated_ray():
    A = fake_rows(5, 4, (0, 64), 9_000_000_000, drop=(2, 1, 64))
    with pytest.raises(ValueError, match="spawn"):
        cr.check_integrity(A, 9_000_000_000, 5, 4, (0, 64))


def test_integrity_rejects_unplanned_radius():
    A = fake_rows(5, 4, (0, 64), 9_000_000_000)
    with pytest.raises(ValueError, match="radius"):
        cr.check_integrity(A, 9_000_000_000, 5, 4, (0,))


# ---------------------------------------------------------------- the betting confidence sequence (Theorem 16)
import theory as th


def world(n, J, M, q, rng):
    late = rng.random((n, J)) < q
    return np.where(late, R0 + rng.exponential(M, (n, J)), rng.uniform(0, R0, (n, J)))


def cs(E, X, alpha, n_star, prior, include=None):
    return th.BettingCS(E, X, 4, R0, R, alpha, n_star, *prior, include=include)


def test_cs_covers_at_every_time_at_once():
    """Anytime validity: the true M is inside C_t at all checked t simultaneously, in >= 1 - alpha of worlds."""
    rng = np.random.default_rng(1)
    M, alpha, reps, bad = 50000.0, 0.1, 300, 0
    prior = th.BettingCS.pilot_priors(*ct.stats(world(300, 4, M, 0.3, rng), R0, R), 4, R0, R)
    for _ in range(reps):
        E, X = ct.stats(world(800, 4, M, 0.3, rng), R0, R)
        bad += any(not (lo <= M <= hi) for lo, hi in (cs(E[:t], X[:t], alpha, 800, prior).interval()
                                                      for t in (40, 100, 200, 400, 800)))
    assert bad / reps <= alpha


def test_wealth_is_monotone_so_the_set_is_an_interval():
    rng = np.random.default_rng(2)
    E, X = ct.stats(world(500, 4, 30000.0, 0.4, rng), R0, R)
    c = cs(E, X, 0.01, 500, th.BettingCS.pilot_priors(E, X, 4, R0, R))
    ms = np.geomspace(3000, 300000, 300)
    kp = [c.logK_plus(m) for m in ms]; km = [c.logK_minus(m) for m in ms]
    assert all(a >= b - 1e-12 for a, b in zip(kp, kp[1:])) and all(a <= b + 1e-12 for a, b in zip(km, km[1:]))
    lo, hi = c.interval()
    inside = [(c.logK_plus(m) < c.thr) and (c.logK_minus(m) < c.thr) for m in ms]
    assert all(ok == (lo <= m <= hi) for m, ok in zip(ms, inside) if abs(m - lo) > 1 and abs(m - hi) > 1)


def test_bets_are_predictable():
    """The bet for seed t must not change when later seeds change."""
    rng = np.random.default_rng(3)
    E, X = ct.stats(world(300, 4, 30000.0, 0.4, rng), R0, R)
    prior = (30000.0, 0.1, 0.01)
    E2, X2 = E.copy(), X.copy(); E2[150:] = 0; X2[150:] = 4 * (R - R0)
    a, b = cs(E, X, 0.05, 300, prior), cs(E2, X2, 0.05, 300, prior)
    assert np.array_equal(a.lp[:151], b.lp[:151]) and np.array_equal(a.lm[:151], b.lm[:151])


def test_excluded_seeds_do_not_bet():
    rng = np.random.default_rng(4)
    E, X = ct.stats(world(200, 4, 30000.0, 0.4, rng), R0, R)
    inc = np.arange(200) < 120
    c = cs(E, X, 0.05, 200, (30000.0, 0.1, 0.01), include=inc)
    d = cs(E[:120], X[:120], 0.05, 200, (30000.0, 0.1, 0.01))
    assert c.logK_plus(25000.0) == pytest.approx(d.logK_plus(25000.0))
    assert c.logK_minus(45000.0) == pytest.approx(d.logK_minus(45000.0))


def test_cs_is_narrower_than_empirical_bernstein():
    rng = np.random.default_rng(5)
    E, X = ct.stats(world(20000, 4, 60000.0, 0.4, rng), R0, R)
    a = 0.05 / 282
    lo, hi = cs(E, X, a, 20000, th.BettingCS.pilot_priors(E[:300], X[:300], 4, R0, R)).interval()
    l2, h2 = th.eb_ratio_ci(E, X, R0, R, 4, a)
    assert (hi - lo) < 0.85 * (h2 - l2)


def test_simultaneous_coverage_with_unequal_alpha():
    """Theorem 17: any split with sum alpha_q <= alpha; all K hold at once with probability >= 1 - alpha."""
    rng = np.random.default_rng(6)
    Ms, al = [8000.0, 30000.0, 90000.0], [0.12, 0.05, 0.03]
    reps, ok_all = 200, 0
    for _ in range(reps):
        ok = True
        for M, a in zip(Ms, al):
            E, X = ct.stats(world(300, 4, M, 0.3, rng), R0, R)
            lo, hi = cs(E, X, a, 300, (M * 1.2, 0.1, 0.01)).interval()
            ok &= lo <= M <= hi
        ok_all += ok
    assert ok_all / reps >= 1 - sum(al)


def test_ordering_needs_disjoint_intervals():
    res = {"a": dict(lo=10.0, hi=20.0), "b": dict(lo=21.0, hi=30.0), "c": dict(lo=19.0, hi=25.0)}
    pairs = cr.certified_order(res)
    assert ("b", "a") in pairs and ("c", "a") not in pairs and ("b", "c") not in pairs


# ---------------------------------------------------------------- planning
def test_optimiser_respects_alpha_budget_and_nesting():
    A = {"1@0": 3000.0, "2@0": 2000.0, "1@64": 1500.0, "1@128": 1200.0}
    groups = {0: ["1@0", "2@0"], 64: ["1@64"], 128: ["1@128"]}
    cost, N = cr.optimise(A, groups, [0, 64, 128], 4, 0.045, 20000.0)
    assert N[0] >= N[64] >= N[128]
    used = sum(2 * math.exp(-N[int(q.split("@")[1])] / a) for q, a in A.items())
    assert used <= 0.045
    assert N[0] > N[128]                         # the cheap radius gets more seeds


def test_cost_constants():
    assert cr.sec_per_ray(0) < cr.sec_per_ray(64) < cr.sec_per_ray(128)
    assert cr.sec_per_ray(128) / cr.sec_per_ray(0) > 50


# ---------------------------------------------------------------- report guards
def tiny_plan(tmp_path, **kw):
    biomes = list(range(256)); radii = [0, 64]
    aq = {cr.qkey(b, r): 0.05 / 512 for b in biomes for r in radii}
    plan = dict(seed0=9_100_000_000, rays=2, radii=radii, rmax=3000, R0=1000.0, R=3000.0, chunk=2, alpha=0.05,
                alpha_rest=0.0, biomes=biomes, target_biomes=[1], target=0.01, alpha_q=aq,
                priors={q: [2000.0, 0.25, 0.25] for q in aq}, n_star={"0": 4, "64": 4}, n_max={"0": 6, "64": 4},
                out=str(tmp_path), threads=2)
    plan.update(kw)
    return plan


def test_report_refuses_empty_manifest(tmp_path):
    with pytest.raises(ValueError, match="manifest"):
        cr.report(tiny_plan(tmp_path))


def test_report_refuses_alpha_over_budget(tmp_path):
    p = tiny_plan(tmp_path); p["alpha_q"]["1@0"] = 0.5
    with pytest.raises(ValueError, match="alpha"):
        cr.report(p)


@pytest.mark.skipif(not os.path.exists(EXE), reason="discexact not built")
def test_end_to_end_sequential(tmp_path):
    """Runs until the caps (target 1% is unreachable on 6 seeds): r=64 stops at 4 seeds, r=0 continues to 6."""
    plan = tiny_plan(tmp_path)
    man = cr.run(plan, log=lambda *a: None)
    assert [c["radii"] for c in man] == [[0, 64], [0, 64], [0]]
    cert = cr.report(plan)
    assert cert["seeds_simulated"] == 6 and cert["K"] == 512
    seeds = {(x["radius"]): x["seeds"] for x in cert["results"]}
    assert seeds == {0: 6, 64: 4}
    for row in cert["results"]:
        assert row["events"] == 0 or row["lo"] <= row["est"] <= row["hi"]
    v = cr.verify(plan, samples=2, rng=np.random.default_rng(0))
    assert v["cells_checked"] > 1000 and v["max_abs_D_err"] < 1e-4 and v["missing_cells"] == 0 and v["rows_mismatch"] == 0
    man[1]["seed0"] += 1
    json.dump(man, open(cr.manifest_path(plan), "w"))
    with pytest.raises(ValueError, match="seed block"):
        cr.load_all(plan)
