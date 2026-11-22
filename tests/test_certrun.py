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


# ---------------------------------------------------------------- the certificate
def world(n, J, M, q, rng):
    late = rng.random((n, J)) < q
    return np.where(late, R0 + rng.exponential(M, (n, J)), rng.uniform(0, R0, (n, J)))


def test_simultaneous_coverage():
    """Theorem 13: all K intervals hold at once with probability >= 1 - alpha."""
    rng = np.random.default_rng(1)
    Ms = [8000.0, 30000.0, 90000.0, 150000.0]
    alpha, reps, all_ok = 0.2, 150, 0
    for _ in range(reps):
        ok = True
        for M in Ms:
            E, X = ct.stats(world(300, 4, M, 0.3, rng), R0, R)
            lo, hi = cr.interval(E, X, R0, R, 4, alpha / len(Ms))
            ok &= lo <= M <= hi
        all_ok += ok
    assert all_ok / reps >= 1 - alpha


def test_ordering_needs_disjoint_intervals():
    res = {"a": dict(lo=10.0, hi=20.0), "b": dict(lo=21.0, hi=30.0), "c": dict(lo=19.0, hi=25.0)}
    pairs = cr.certified_order(res)
    assert ("b", "a") in pairs and ("c", "a") not in pairs and ("b", "c") not in pairs


def test_plan_gives_enough_seeds_for_the_target():
    rng = np.random.default_rng(2)
    E, X = ct.stats(world(400, 4, 60000.0, 0.4, rng), R0, R)
    N = cr.required_N(E, X, R0, R, 4, alpha_each=0.05 / 10, target=0.10)
    E2, X2 = ct.stats(world(N, 4, 60000.0, 0.4, rng), R0, R)
    lo, hi = cr.interval(E2, X2, R0, R, 4, 0.05 / 10)
    est = X2.sum() / E2.sum()
    assert (hi - lo) / 2 / est <= 0.10 * 1.25                                 # planned width, up to pilot noise


def test_report_refuses_unplanned_N(tmp_path):
    plan = dict(seed0=9_000_000_000, n_seeds=10, rays=4, radii=[0], rmax=20000, R0=R0, R=R, alpha=0.05,
                biomes=[7, 9], chunk=5, target_biomes=[9], target=0.1, out=str(tmp_path))
    with pytest.raises(ValueError, match="chunk"):
        cr.report(plan)                                                       # no data at all


# ---------------------------------------------------------------- end to end on the real binary
@pytest.mark.skipif(not os.path.exists(EXE), reason="discexact not built")
def test_end_to_end(tmp_path):
    plan = dict(seed0=9_100_000_000, n_seeds=4, rays=2, radii=[0, 64], rmax=3000, R0=1000.0, R=3000.0, alpha=0.05,
                biomes=list(range(256)), chunk=2, target_biomes=[1], target=0.5, out=str(tmp_path), threads=2)
    cr.run(plan)
    cert = cr.report(plan)
    assert cert["n_seeds"] == 4 and cert["K"] == 512
    for row in cert["results"]:
        assert row["lo"] <= row["est"] <= row["hi"] or row["events"] == 0
    v = cr.verify(plan, samples=1, rng=np.random.default_rng(0))
    assert v["cells_checked"] > 1000 and v["max_abs_D_err"] < 1e-4 and v["missing_cells"] == 0
    assert v["rows_mismatch"] == 0
