"""spawnratio.py: the spawn likelihood ratio rho_b(x) = P(D <= x | spawn) / P(D_u <= x | uniform start), THEORY.md 8.11."""
import json, math, os, sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import spawnratio as sr


def _rows(D, b, r=0):
    """D[seed, ray] (inf = not found) -> rows (seed, ray, biome, dist, mode) and the seed index of every row."""
    s, j = np.nonzero(np.isfinite(D))
    A = np.column_stack([s + 100, j, np.full(s.size, b), D[s, j].astype(np.int64), np.full(s.size, r)]).astype(np.int64)
    return A, s.astype(np.int64)


def test_counts_from_rows():
    D = np.array([[0, np.inf], [5, 7], [np.inf, np.inf], [3, 0]], float)
    A, si = _rows(D, b=7)
    A2, si2 = _rows(np.zeros((4, 2)), b=8)                      # another biome must not count
    A, si = np.concatenate([A, A2]), np.concatenate([si, si2])
    assert sr.counts(A, si, 4, 2, 7, 0, 0).tolist() == [1, 0, 0, 1]
    assert sr.counts(A, si, 4, 2, 7, 0, 5).tolist() == [1, 1, 0, 2]
    assert sr.counts(A, si, 4, 2, 7, 0, 100).tolist() == [1, 2, 0, 2]
    assert sr.counts(A, si, 4, 2, 7, 64, 100).tolist() == [0, 0, 0, 0]  # other radius


@pytest.mark.parametrize("p", [0.0005, 0.02, 0.3])
def test_interval_covers_the_true_probability(p):
    rng = np.random.default_rng(int(p * 1e6))
    alpha, reps, miss = 0.1, 40, 0
    for _ in range(reps):
        Y = (rng.random(20000) < p).astype(float)
        lo, hi = sr.prob_cs(Y, 1, alpha, prior_p=0.05)
        miss += not (lo <= p <= hi)
    assert miss <= 1                                          # expected misses <= 4 at alpha 0.1, usually 0


def test_ratio_interval_is_valid_and_has_power():
    rng = np.random.default_rng(5)
    n, ps, pu = 50000, 0.01, 0.004
    Ys, Yu = (rng.random(n) < ps).astype(float), (rng.random(n) < pu).astype(float)
    ls, us = sr.prob_cs(Ys, 1, 1e-6, 0.05); lu, uu = sr.prob_cs(Yu, 1, 1e-6, 0.05)
    lo, hi = sr.ratio_bounds(ls, us, lu, uu)
    assert lo <= ps / pu <= hi and lo > 1                     # certified "spawn favours" at 1e-6
    assert sr.ratio_bounds(0.1, 0.2, 0.0, 0.1) == (1.0, math.inf)


def _fake(monkeypatch, tmp_path, n=4000, J=1):
    rng = np.random.default_rng(1)
    arms = {}
    for arm, pa in (("spawn", {1: 0.6, 2: 0.0}), ("uniform", {1: 0.3, 2: 0.03})):
        parts, sis = [], []
        for b, p in pa.items():
            D = np.where(rng.random((n, J)) < p, 0.0, rng.exponential(300, (n, J)).round() + 1)
            A, si = _rows(D, b); parts.append(A); sis.append(si)
        arms[arm] = ({"hf": np.concatenate(parts)}, {"hf": np.concatenate(sis)}, [dict(k=0, n=n, radii=[0], seed0=0)])
    monkeypatch.setattr(sr.cw, "load_arm", lambda plan, arm: arms[arm])
    return dict(rays=J, cap=10000, biomes=[1, 2], names={"1": "plains", "2": "mushroom"}, radii=[0],
                arm_radii={"spawn": [0], "uniform": [0]}, out=str(tmp_path), hash="h" * 16)


def test_analyse_writes_json_and_markdown(monkeypatch, tmp_path):
    plan = _fake(monkeypatch, tmp_path)
    res = sr.analyse(plan, xs=[0, 128, 2048], alpha=1e-6, pilot=None)
    by = {(r["name"], r["x"]): r for r in res["rows"]}
    p0 = by[("plains", 0)]
    assert p0["lo"] > 1 and p0["verdict"] == "favours"         # 0.6 vs 0.3 with 4,000 seeds
    m0 = by[("mushroom", 0)]
    assert m0["spawn_hits"] == 0 and m0["hi"] < 1 and m0["verdict"] == "avoids"
    for r in res["rows"]:
        assert r["lo"] <= r["est"] <= r["hi"] or math.isnan(r["est"])
    assert res["alpha_each"] == pytest.approx(1e-6 / (2 * 2 * 3))
    js = json.load(open(os.path.join(tmp_path, "spawnratio.json")))
    assert js["plan_hash"] == "h" * 16 and len(js["rows"]) == 6
    md = open(os.path.join(tmp_path, "spawnratio.md")).read()
    assert "plains" in md and "1 in 1,000,000" in md and "—" not in md


def test_grid_beyond_the_cap_is_refused(monkeypatch, tmp_path):
    plan = _fake(monkeypatch, tmp_path)
    with pytest.raises(ValueError):
        sr.analyse(plan, xs=[0, 20000], alpha=1e-6, pilot=None)
