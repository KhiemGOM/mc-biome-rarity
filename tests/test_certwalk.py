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


# ---------------------------------------------------------------- early stop (Proposition 22)
import theory as th


def test_lemma_cell_D_at_least_centre_projection_minus_2sqrt2():
    rng = np.random.default_rng(8)
    for _ in range(40):
        px, pz, ang, r = rng.uniform(-50, 50), rng.uniform(-50, 50), rng.uniform(0, 2 * math.pi), float(rng.choice([0, 64, 128]))
        qx, qz = rng.integers(-300, 300, 4000), rng.integers(-300, 300, 4000)
        D = th.cell_D(px, pz, ang, qx, qz, r, cap=1e9)
        tc = (4 * qx + 1.5 - px) * math.cos(ang) + (4 * qz + 1.5 - pz) * math.sin(ang)
        ok = np.isfinite(D)
        assert np.all(D[ok] >= tc[ok] - 2 * math.sqrt(2) - 1e-9)


@pytest.mark.skipif(not os.path.exists(EXE), reason="discexact not built")
def test_early_stop_rows_equal_full_scan_within_reach(tmp_path):
    f, g = str(tmp_path / "f.csv"), str(tmp_path / "g.csv")
    base = [EXE, "--seeds", "6", "--rays", "2", "--rmax", "12000", "--radii", "0,64", "--seed0", "4242", "--threads", "2"]
    subprocess.run(base + ["--out", f], check=True)
    subprocess.run(base + ["--out", g, "--stopset", "1,4,5,7,21,35"], check=True)
    F = cr.load_csv(f); G = cr.load_csv(g)
    reach = {(a, b, c): d for a, b, d, c in G[G[:, 2] == cw.REACH][:, [0, 1, 3, 4]].tolist()}
    assert len(reach) == 6 * 2 * 2
    full = {(a, b, c, e): d for a, b, c, d, e in F[:, :5].tolist()}
    seg = {(a, b, c, e): d for a, b, c, d, e in G[G[:, 2] != cw.REACH][:, :5].tolist()}
    checked = 0
    for key in set(full) | set(seg):
        rho = reach[(key[0], key[1], key[3])]
        if full.get(key, 1e18) <= rho or seg.get(key, 1e18) <= rho:
            assert full.get(key) == seg.get(key); checked += 1
    assert checked > 50
    cw.check_reach(G, 6, 2, [0, 64], [1, 4, 5, 7, 21, 35], 12000)


def test_check_reach_rejects_a_ray_that_stopped_without_its_biomes():
    s = 123
    rows = [(s, 0, cw.REACH, 5000, 0, 1), (s, 0, 1, 100, 0, 1), (s, 0, 4, 4000, 0, 1)]
    A = np.array(rows, dtype=np.int64)
    cw.check_reach(A, 1, 1, [0], [1, 4], 20000)
    with pytest.raises(ValueError, match="stopped early"):
        cw.check_reach(A, 1, 1, [0], [1, 4, 5], 20000)
    with pytest.raises(ValueError, match="reach rows"):
        cw.check_reach(A[1:], 1, 1, [0], [1, 4], 20000)


# ---------------------------------------------------------------- end to end
def tiny_plan(tmp_path):
    biomes = [1, 4, 5, 7, 21, 35]
    rng = np.random.default_rng(0)
    pr = cw._sim_priors(2000.0, 6000, 2, rng, n=500)
    radii = [0, 64]
    plan = dict(seed0=9_200_000_000, rays=2, radii=radii, cap=6000, caps={"0": 6000, "64": 6000}, chunk=2, alpha=0.05,
                alpha_rest=0.0, biomes=biomes, target_biomes=[1], target={"0": 0.001, "64": 0.001}, uniform_L=1_000_000,
                alpha_each={cw.qkey(b, r): 0.05 / (cw.SEQS * 12) for b in biomes for r in radii},
                priors={cw.qkey(b, r): pr for b in biomes for r in radii}, n_star={"0": 4, "64": 4},
                n_max={"0": 6, "64": 2}, arm_radii={"spawn": radii, "uniform": [0]}, out=str(tmp_path), threads=2)
    return plan


@pytest.mark.skipif(not os.path.exists(EXE), reason="discexact not built")
def test_end_to_end_one_pass_two_arms(tmp_path):
    plan = tiny_plan(tmp_path)
    cw.run(plan, log=lambda *a: None)
    ms = cr.load_manifest(cw.arm_plan(plan, "spawn")); mu = cr.load_manifest(cw.arm_plan(plan, "uniform"))
    assert [c["radii"] for c in ms] == [[0, 64], [0], [0]] and [c["radii"] for c in mu] == [[0], [0], [0]]
    cert = cw.report(plan)
    seeds = {(x["radius"]): x["seeds"] for x in cert["results"]}
    assert seeds == {0: 6, 64: 2}
    for x in cert["results"]:
        assert x["A_lo"] <= x["A"] <= x["A_hi"] and x["ED_lower_no_assumption"] <= x["ED"]
        if x["radius"] == 0:
            assert x["bias_A_lo"] <= x["bias_A"] <= x["bias_A_hi"]
        else:
            assert "uniform" not in x
    for arm in cw.ARMS:
        v = cw.verify(plan, arm, samples=2, rng=np.random.default_rng(0))
        assert v["rows_mismatch"] == 0 and v["rows_checked"] > 5 and v["max_abs_D_err"] < 1e-4
    cw.run(plan, log=lambda *a: None)                                  # resumable: nothing new
    assert len(cr.load_manifest(cw.arm_plan(plan, "spawn"))) == 3


def test_ties_where_ranges_overlap():
    R = lambda n, e, lo, hi: dict(name=n, ED=e, ED_lo=lo, ED_hi=hi)
    g = cw.tie_groups([R("a", 100, 95, 105), R("b", 80, 70, 96), R("c", 50, 45, 55), R("d", 30, 28, 32)])
    assert [[x["name"] for x in grp] for grp in g] == [["a", "b"], ["c"], ["d"]]


def test_common_biome_gets_a_finite_interval_with_its_own_cap():
    """Global cap 540k: a biome with E[D] = 1000 never reaches [C/2, C], so T is unbounded. Its own cap fixes that."""
    rng = np.random.default_rng(9)
    T = 1000.0
    pr = cw._sim_priors(T, 540000, J, rng, n=2000)
    plan = dict(rays=J, cap=540000, caps={"0": 540000}, cap_mult=4.0, alpha_each={"1@0": 1e-8}, n_star={"0": 3000},
                priors={"1@0": pr}, hash="t")
    assert cw.cap_of(plan, 1, 0) == 4000
    bad = 0
    for _ in range(40):
        D = rng.exponential(T, (3000, J))
        q = cw.quantity_from(*arm_stats(D, 4000.0), plan, 1, 0)
        assert math.isfinite(q["ED_hi"]) and q["rel_half"] < 0.1
        bad += not (q["ED_lo"] <= T <= q["ED_hi"])
    assert bad == 0


def test_until_keeps_a_met_radius_running_up_to_n_max(monkeypatch):
    """until overrides a met target (any stopping time is valid, Theorem 20) but never passes n_max."""
    plan = dict(radii=[0, 64], n_max={"0": 10, "64": 4}, chunk=2, target_biomes=[1], target={"0": 0.1, "64": 0.1})
    monkeypatch.setattr(cw, "stats_at", lambda *a: (dict(rel_half=0.01), None, None))     # every target met
    man = [dict(radii=[0, 64], n=2), dict(radii=[0, 64], n=2)]
    monkeypatch.setattr(cw, "n_of", lambda m, r: sum(c["n"] for c in m if r in c["radii"]))
    data = {"spawn": (None, None, man)}
    assert cw.active_radii(plan, data) == []
    assert cw.active_radii(plan, data, until=8) == [0]                 # 64 is at its n_max of 4
    assert cw.active_radii(plan, data, until=4) == []                  # both already at 4 seeds


@pytest.mark.skipif(not os.path.exists(EXE), reason="discexact not built")
def test_pair_order_contains_estimates_and_rank_ranges(tmp_path):
    plan = tiny_plan(tmp_path)
    cw.run(plan, log=lambda *a: None)
    o = cw.pair_order(plan, 1e-3)
    nb = len(plan["biomes"])
    for r, v in o["radii"].items():
        assert len(v["pairs"]) == nb * (nb - 1) // 2
        for p in v["pairs"]:
            assert p["lo"] <= p["diff"] <= p["hi"] and p["dA_lo"] <= p["dA_hi"]
        for pos, x in enumerate(v["ranks"], 1):
            assert x["rank_lo"] <= pos <= x["rank_hi"]
    assert os.path.exists(os.path.join(plan["out"], "order.md"))


def test_paired_interval_covers_the_true_difference():
    """Coverage of the pair sequence on a synthetic world with known means (exponential, independent per biome)."""
    rng = np.random.default_rng(5)
    Ta, Tb, C, J, n, a = 3000.0, 2500.0, 12000, 1, 600, 0.05
    true = (Ta * (1 - np.exp(-C / Ta))) - (Tb * (1 - np.exp(-C / Tb)))       # E[min(D, C)] difference
    pr = cw._pair_prior(Ta, C, Tb, C, J, 1)
    miss = 0
    for t in range(60):
        Wa = np.minimum(rng.exponential(Ta, n), C); Wb = np.minimum(rng.exponential(Tb, n), C)
        lo, hi = cw.th.BettingCS(np.full(n, float(J)), Wa - Wb + J * C, J, 0.0, 2.0 * C, a, n, *pr).interval()
        miss += not (lo - C <= true <= hi - C)
    assert miss <= 3


def test_extension_reserves_fresh_seeds_and_lifts_the_spawn_limit(tmp_path):
    """Proposition 27b: past n_max only after the new seed range is checked fresh and written to the ledger."""
    plan = dict(seed0=12_000_000_000, n_max={"0": 100}, out=str(tmp_path), radii=[0], rays=1, uniform_L=1, cap=1,
                caps={}, chunk=1, alpha=1, alpha_rest=0, biomes=[], target_biomes=[], target={}, alpha_each={},
                priors={}, n_star={}, arm_radii={"spawn": [0], "uniform": [0]})
    lp = str(tmp_path / "ledger.json")
    json.dump([dict(seed0=12_000_000_000, n=100, purpose="this plan"), dict(seed0=12_000_000_500, n=10, purpose="other")],
              open(lp, "w"))
    assert cw.limit_of(plan, 0) == 100
    with pytest.raises(ValueError):
        cw.reserve_extension(plan, 600, lp)                     # would overlap the other run's seeds
    assert cw.extension(plan) is None and len(json.load(open(lp))) == 2
    ext = cw.reserve_extension(plan, 400, lp)
    assert ext["ranges"] == [[12_000_000_100, 12_000_000_400]] and len(json.load(open(lp))) == 3
    assert cw.limit_of(plan, 0) == 400 and cw.limit_of(plan, 0, "uniform") == 100
    cw.reserve_extension(plan, 300, lp)                         # smaller: nothing new
    assert len(json.load(open(lp))) == 3


@pytest.mark.skipif(not os.path.exists(EXE), reason="discexact not built")
def test_spawn_only_extension_end_to_end(tmp_path):
    """The uniform arm stops at n_max; report gives spawn quantities on all seeds and the bias on the shared ones."""
    plan = tiny_plan(tmp_path)
    cw.run(plan, log=lambda *a: None)
    lp = str(tmp_path / "ledger.json")
    cw.reserve_extension(plan, 10, lp)
    cw.run(plan, log=lambda *a: None, until=10)
    ms = cr.load_manifest(cw.arm_plan(plan, "spawn")); mu = cr.load_manifest(cw.arm_plan(plan, "uniform"))
    assert sum(c["n"] for c in ms if 0 in c["radii"]) == 10 and sum(c["n"] for c in mu) == 6
    cert = cw.report(plan)
    r0 = [x for x in cert["results"] if x["radius"] == 0]
    assert all(x["seeds"] == 10 and x["uniform"]["seeds"] == 6 for x in r0)
    for x in r0:
        assert x["bias_A_lo"] <= x["bias_A"] <= x["bias_A_hi"]
    assert "(6 random start, bias on those)" in open(os.path.join(plan["out"], "report.md")).read()


def test_until_fast_path_matches_active_radii(monkeypatch):
    """run's count-only shortcut picks exactly what active_radii picks while every radius is below until."""
    plan = dict(radii=[0, 64], n_max={"0": 10, "64": 4}, chunk=2, target_biomes=[1], target={"0": 0.1, "64": 0.1})
    monkeypatch.setattr(cw, "stats_at", lambda *a: (dict(rel_half=0.01), None, None))
    for man in ([dict(radii=[0, 64], n=2)], [dict(radii=[0, 64], n=2), dict(radii=[0, 64], n=2)]):
        until = 8
        fast = [r for r in man[-1]["radii"] if cw.n_of(man, r) < cw.limit_of(plan, r)]
        assert fast == cw.active_radii(plan, {"spawn": (None, None, man)}, until)


# ---------------------------------------------------------------- biome ties (THEORY.md 0.1, Lemma 30)
def test_tview_replaces_only_the_differing_rows():
    # cols seed, ray, biome, dist, radius, level
    A = np.array([[5, 0, 3, 100, 0, 1], [5, 0, 4, 200, 0, 1], [5, 0, cw.REACH, 900, 0, 1],
                  [5, 0, 3 + cw.TIE_ANY, 80, 0, 1], [5, 0, 4 + cw.TIE_STRICT, 250, 0, 1],
                  [5, 0, 3 + cw.TIE_STRICT, -1, 0, 1], [6, 0, 3, 50, 0, 1], [6, 0, 7 + cw.TIE_ANY, 40, 0, 1]])
    key = lambda X: sorted(map(tuple, X[:, [0, 2, 3]].tolist()))
    assert key(cw.tview(A, "hf")) == [(5, 3, 100), (5, 4, 200), (5, cw.REACH, 900), (6, 3, 50)]
    assert key(cw.tview(A, "any")) == [(5, 3, 80), (5, 4, 200), (5, cw.REACH, 900), (6, 3, 50), (6, 7, 40)]
    assert key(cw.tview(A, "strict")) == [(5, 4, 250), (5, cw.REACH, 900), (6, 3, 50)]
    assert cw.never_strict(A) == 1


def test_seqs_double_with_ties():
    assert cw.seqs({}) == cw.SEQS and cw.seqs({"ties": True}) == 2 * cw.SEQS


@pytest.mark.skipif(not os.path.exists(EXE), reason="discexact not built")
def test_end_to_end_with_tie_rows_brackets_the_hint_free_estimate(tmp_path):
    plan = tiny_plan(tmp_path)
    plan["ties"] = True
    plan["alpha_each"] = {k: v / 2 for k, v in plan["alpha_each"].items()}
    cw.check_alpha(plan)
    cw.run(plan, log=lambda *a: None)
    V, S, man = cw.load_arm(plan, "spawn")
    assert set(V) == set(cw.VIEWS)
    cert = cw.report(plan)
    for x in cert["results"]:
        assert x["ED_lo"] <= x["ED_any"] + 1e-9 and x["ED_strict"] <= x["ED_hi"] + 1e-9
        assert x["A_any"] <= x["A"] + 1e-9 <= x["A_strict"] + 2e-9
        if x["radius"] == 0:
            assert x["bias_lo"] <= x["bias_hi"]
    o = cw.pair_order(plan, 1e-3)
    for r, v in o["radii"].items():
        for p in v["pairs"]:
            assert p["lo"] <= p["diff"] <= p["hi"]
    for arm in cw.ARMS:
        assert cw.verify(plan, arm, samples=1, rng=np.random.default_rng(1))["rows_mismatch"] == 0


@pytest.mark.skipif(not os.path.exists(EXE), reason="discexact not built")
def test_fixed_plan_runs_exactly_n_max_even_when_targets_are_met(tmp_path):
    plan = tiny_plan(tmp_path)
    plan["target"] = {"0": 1e9, "64": 1e9}            # met at once: an adaptive plan would stop after one chunk
    cw.fix_n(plan, {0: 6, 64: 4})
    cw.run(plan, log=lambda *a: None)
    ms = cr.load_manifest(cw.arm_plan(plan, "spawn"))
    assert cw.n_of(ms, 0) == 6 and cw.n_of(ms, 64) == 4
