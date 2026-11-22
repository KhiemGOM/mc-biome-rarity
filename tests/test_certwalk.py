"""certwalk.py: E[D] from spawn, no window (THEORY.md section 8). Theorems first, then the code, then an end to end run."""
import json, math, os, subprocess

import numpy as np
import pytest

import certify as ct
import certrun as cr
import certwalk as cw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, "discexact")
J = 4


def mini_plan(C, T, alpha=0.05, n_star=400, rng=None):
    rng = rng or np.random.default_rng(0)
    pr = cw._sim_priors(T, C, J, rng, n=2000)
    return dict(rays=J, caps={"0": C}, alpha_each={"1@0": alpha / cw.SEQS}, n_star={"0": n_star}, priors={"1@0": pr})


def arm_stats(D, C):
    W = np.minimum(D, C).sum(1); K = (D > C).sum(1).astype(float)
    E, X = ct.stats(D, C / 2, C)
    return W, K, E, X


# ---------------------------------------------------------------- Theorem 18 (exact split, any cap)
@pytest.mark.parametrize("C", [500.0, 3000.0, 20000.0])
def test_split_is_exact_at_any_cap(C):
    rng = np.random.default_rng(1)
    D = np.concatenate([rng.uniform(0, 2000, 30000), 2000 + rng.pareto(3.0, 30000) * 4000])   # not exponential
    A, S = np.minimum(D, C).mean(), (D > C).mean()
    T = (D[D > C] - C).mean()
    assert A + S * T == pytest.approx(D.mean(), rel=1e-12)


# ---------------------------------------------------------------- Theorem 20: coverage
def test_ED_interval_covers_under_constant_hazard():
    """Exponential world (H_C true): E[D] = T inside [ED_lo, ED_hi] in >= 1 - alpha of worlds."""
    rng = np.random.default_rng(2)
    T, C, reps, bad = 30000.0, 90000.0, 150, 0
    plan = mini_plan(C, T, alpha=0.1)
    for _ in range(reps):
        q = cw.quantity_from(*arm_stats(rng.exponential(T, (400, J)), C), plan, 1, 0)
        bad += not (q["ED_lo"] <= T <= q["ED_hi"])
    assert bad / reps <= 0.1


def test_lower_bound_holds_without_any_tail_assumption():
    """Heavy, non exponential tail (H_C false): the A_lo bound still holds; the H_C interval may not."""
    rng = np.random.default_rng(3)
    C, reps, bad = 20000.0, 150, 0
    sample = lambda n: np.where(rng.random((n, J)) < 0.5, rng.uniform(0, 5000, (n, J)), 5000 + rng.pareto(1.5, (n, J)) * 20000)
    big = sample(400000)
    true_ED = 2500 * 0.5 + 0.5 * (5000 + 20000 / 0.5)        # uniform half + Pareto(1.5) mean 20000/(1.5-1)
    assert abs(big.mean() - true_ED) / true_ED < 0.05
    plan = mini_plan(C, 20000.0, alpha=0.1)
    for _ in range(reps):
        q = cw.quantity_from(*arm_stats(sample(400), C), plan, 1, 0)
        bad += not (q["ED_lower_no_assumption"] <= true_ED)
        assert q["A_lo"] <= q["ED_lo"]
    assert bad / reps <= 0.1


def test_capped_mean_and_tail_probability_cover():
    rng = np.random.default_rng(4)
    T, C, reps, badA, badS = 30000.0, 60000.0, 150, 0, 0
    A_true = T * (1 - math.exp(-C / T)); S_true = math.exp(-C / T)
    plan = mini_plan(C, T, alpha=0.1)
    for _ in range(reps):
        q = cw.quantity_from(*arm_stats(rng.exponential(T, (300, J)), C), plan, 1, 0)
        badA += not (q["A_lo"] <= A_true <= q["A_hi"]); badS += not (q["S_lo"] <= S_true <= q["S_hi"])
    assert badA / reps <= 0.1 and badS / reps <= 0.1


def test_spawn_bias_paired_interval_covers():
    """Spawn arm finds the biome sooner (mixture with a near find); paired capped difference must cover."""
    rng = np.random.default_rng(5)
    T, C, reps, bad, badfull = 30000.0, 90000.0, 150, 0, 0
    plan = mini_plan(C, T, alpha=0.1)
    p_near = 0.2
    dA = p_near * 500 - p_near * T * (1 - math.exp(-C / T))  # E[min(D_s,C)] - E[min(D_u,C)], approx (near ~ U(0,1000))
    for _ in range(reps):
        Du = rng.exponential(T, (400, J))
        Ds = np.where(rng.random((400, J)) < p_near, rng.uniform(0, 1000, (400, J)), Du)
        qs = cw.quantity_from(*arm_stats(Ds, C), plan, 1, 0)
        qu = cw.quantity_from(*arm_stats(Du, C), plan, 1, 0)
        b = cw.bias(qs, qu, plan, 1, 0, 400)
        bad += not (b["bias_A_lo"] <= dA <= b["bias_A_hi"])
        badfull += not (b["bias_lo"] <= -p_near * (T - 500) <= b["bias_hi"])
    assert bad / reps <= 0.1 and badfull / reps <= 0.1


def test_paired_bias_is_narrower_than_unpaired():
    rng = np.random.default_rng(6)
    T, C = 30000.0, 90000.0
    plan = mini_plan(C, T)
    Du = rng.exponential(T, (1500, J)); Ds = np.minimum(Du, rng.exponential(10 * T, (1500, J)))
    qs = cw.quantity_from(*arm_stats(Ds, C), plan, 1, 0); qu = cw.quantity_from(*arm_stats(Du, C), plan, 1, 0)
    b = cw.bias(qs, qu, plan, 1, 0, 1500)
    assert (b["bias_A_hi"] - b["bias_A_lo"]) < 0.5 * ((qs["A_hi"] - qs["A_lo"]) + (qu["A_hi"] - qu["A_lo"]))


# ---------------------------------------------------------------- code: walk_terms from sparse rows
def test_walk_terms_match_dense():
    rng = np.random.default_rng(7)
    n, C = 40, 10000.0
    D = rng.exponential(6000, (n, J)); D[rng.random((n, J)) < 0.2] = np.inf; D[0, 0] = C; D[1, 1] = C / 2
    rows, s0 = [], 9_500_000_000
    for i in range(n):
        for k in range(J):
            if D[i, k] <= C:
                rows.append((cr.signed(cr.seed_of(s0 + i)), k, 5, D[i, k], 0, 1))
    A = np.array(rows, dtype=np.int64); si = np.repeat(np.arange(n), [int((D[i] <= C).sum()) for i in range(n)])
    D_int = np.where(D <= C, np.floor(D), np.inf)                      # rows store integers
    W, K, E, X = cw.walk_terms(A, si, n, J, 5, 0, C)
    W2, K2, E2, X2 = arm_stats(D_int, C)
    assert np.allclose(W, W2) and np.array_equal(K, K2) and np.array_equal(E, E2) and np.allclose(X, X2)


def test_check_alpha_counts_seven_sequences():
    p = dict(alpha=0.05, biomes=[1, 2], radii=[0], alpha_each={"1@0": 0.05 / 14, "2@0": 0.05 / 14})
    cw.check_alpha(p)
    p["alpha_each"]["1@0"] = 0.05 / 7
    with pytest.raises(ValueError, match="alpha"):
        cw.check_alpha(p)


# ---------------------------------------------------------------- discexact --origin
@pytest.mark.skipif(not os.path.exists(EXE), reason="discexact not built")
def test_uniform_origin_is_deterministic_in_box_and_keeps_angles():
    run = lambda *o: subprocess.run([EXE, "--debug", "3,1", "--seed0", "77", "--rmax", "10", "--radii", "0", *o],
                                    capture_output=True, text=True, check=True).stdout.splitlines()[0].split()
    s, u1, u2 = run(), run("--origin", "uniform:1000000"), run("--origin", "uniform:1000000")
    assert u1 == u2 and s[3] == u1[3]                                 # same start twice, same angle as spawn arm
    assert max(abs(int(u1[1])), abs(int(u1[2]))) <= 1_000_000 and (u1[1], u1[2]) != (s[1], s[2])
    bad = subprocess.run([EXE, "--origin", "uniform:0", "--out", "/dev/null"], capture_output=True)
    assert bad.returncode == 2


@pytest.mark.skipif(not os.path.exists(EXE), reason="discexact not built")
def test_uniform_origin_spreads_over_the_box():
    xs = []
    for i in range(60):
        o = subprocess.run([EXE, "--debug", f"{i},0", "--seed0", "5", "--rmax", "1", "--radii", "0", "--origin", "uniform:1000"],
                           capture_output=True, text=True, check=True).stdout.splitlines()[0].split()
        xs.append(int(o[1]))
    assert min(xs) < -500 and max(xs) > 500


# ---------------------------------------------------------------- end to end
def tiny_plan(tmp_path):
    biomes = list(range(256))
    rng = np.random.default_rng(0)
    pr = cw._sim_priors(2000.0, 3000, 2, rng, n=500)
    plan = dict(seed0=9_200_000_000, rays=2, radii=[0, 64], caps={"0": 3000, "64": 3000}, chunk=2, alpha=0.05,
                alpha_rest=0.0, biomes=biomes, target_biomes=[1], target=0.001, uniform_L=1_000_000,
                alpha_each={cw.qkey(b, r): 0.05 / (cw.SEQS * 512) for b in biomes for r in (0, 64)},
                priors={cw.qkey(b, r): pr for b in biomes for r in (0, 64)}, n_star={"0": 4, "64": 4},
                n_max={"0": 4, "64": 2}, out=str(tmp_path), threads=2)
    return plan


@pytest.mark.skipif(not os.path.exists(EXE), reason="discexact not built")
def test_end_to_end_two_arms(tmp_path):
    plan = tiny_plan(tmp_path)
    cw.run(plan, log=lambda *a: None)
    for r, n in ((0, 4), (64, 2)):
        for arm in cw.ARMS:
            man = cr.load_manifest(cw.group_plan(plan, r, arm))
            assert sum(c["n"] for c in man) == n
    cert = cw.report(plan)
    seeds = {x["radius"]: x["seeds"] for x in cert["results"]}
    assert seeds == {0: 4, 64: 2}
    for x in cert["results"]:
        assert x["A_lo"] <= x["A"] <= x["A_hi"] and x["ED_lower_no_assumption"] <= x["ED"]
        assert x["bias_A_lo"] <= x["bias_A"] <= x["bias_A_hi"]
    v = cr.verify(cw.group_plan(plan, 0, "uniform"), samples=2, rng=np.random.default_rng(0))
    assert v["missing_cells"] == 0 and v["rows_mismatch"] == 0 and v["max_abs_D_err"] < 1e-4
    cw.run(plan, log=lambda *a: None)                                  # resumable: nothing new
    assert sum(c["n"] for c in cr.load_manifest(cw.group_plan(plan, 0, "spawn"))) == 4


def test_ties_where_ranges_overlap():
    R = lambda n, e, lo, hi: dict(name=n, ED=e, ED_lo=lo, ED_hi=hi)
    g = cw.tie_groups([R("a", 100, 95, 105), R("b", 80, 70, 96), R("c", 50, 45, 55), R("d", 30, 28, 32)])
    assert [[x["name"] for x in grp] for grp in g] == [["a", "b"], ["c"], ["d"]]
