"""Tests for the raysim CLI. Written before the implementation.

Happy-path tests come first, then the failure modes listed in PLAN.md.
"""
import csv
import ctypes
import math
import os
import subprocess
import tempfile
from collections import defaultdict

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAYSIM = os.path.join(ROOT, "raysim")
LIB = os.path.join(os.environ.get("CUBIOMES", "/home/claude/cubiomes"), "libcubiomes.so")
MC_1_21 = 28
MASK = (1 << 64) - 1


def run(seeds=3, rays=2, rmax=2000, step=16, seed0=1, far_from=1000,
        mc="1.21", extra=(), check=True):
    d = tempfile.mkdtemp()
    first = os.path.join(d, "first.csv")
    far = os.path.join(d, "far.csv")
    cmd = [RAYSIM, "--mc", mc, "--seeds", str(seeds), "--rays", str(rays),
           "--rmax", str(rmax), "--step", str(step), "--seed0", str(seed0),
           "--far-from", str(far_from), "--out-first", first,
           "--out-far", far, *extra]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if check:
        assert p.returncode == 0, p.stderr
    return p, first, far


def read_first(path):
    with open(path) as f:
        return [dict(seed=int(r["seed"]), ray=int(r["ray"]),
                     angle=float(r["angle"]), biome=int(r["biome"]),
                     dist=int(r["dist"])) for r in csv.DictReader(f)]


def read_far(path):
    with open(path) as f:
        return [dict(seed=int(r["seed"]), ray=int(r["ray"]),
                     biome=int(r["biome"]), samples_in=int(r["samples_in"]),
                     entries=int(r["entries"]),
                     samples_total=int(r["samples_total"]))
                for r in csv.DictReader(f)]


# ---------------------------------------------------------------- happy path
def test_runs_and_outputs_wellformed():
    p, first, far = run()
    rows = read_first(first)
    assert rows, "no first-hit rows"
    for r in rows:
        assert 0 <= r["dist"] <= 2000
        assert r["dist"] % 16 == 0
        assert 0 <= r["biome"] < 256
    assert {r["seed"] for r in rows}.__len__() == 3
    assert {r["ray"] for r in rows} == {0, 1}


def test_spawn_biome_at_distance_zero_shared_by_rays():
    _, first, _ = run(seeds=4, rays=4)
    rows = read_first(first)
    zero = defaultdict(set)
    per_ray = defaultdict(int)
    for r in rows:
        if r["dist"] == 0:
            zero[r["seed"]].add(r["biome"])
            per_ray[(r["seed"], r["ray"])] += 1
    assert len(zero) == 4
    for s, biomes in zero.items():
        assert len(biomes) == 1, "rays of one seed disagree on spawn biome"
    assert all(v == 1 for v in per_ray.values()), "exactly one biome at r=0"
    assert len(per_ray) == 16


def test_each_biome_listed_once_per_ray_with_first_distance():
    _, first, _ = run(seeds=3, rays=3, rmax=4000)
    seen = set()
    for r in read_first(first):
        key = (r["seed"], r["ray"], r["biome"])
        assert key not in seen, "biome repeated within a ray"
        seen.add(key)


def test_angles_evenly_spaced_within_seed():
    K = 6
    _, first, _ = run(seeds=3, rays=K)
    ang = defaultdict(dict)
    for r in read_first(first):
        ang[r["seed"]][r["ray"]] = r["angle"]
    for s, d in ang.items():
        assert len(d) == K
        for k in range(K):
            gap = (d[(k + 1) % K] - d[k]) % (2 * math.pi)
            assert gap == pytest.approx(2 * math.pi / K, abs=1e-9)


def test_far_csv_wellformed_and_consistent():
    _, _, far = run(seeds=3, rays=2, rmax=3000, step=16, far_from=1000)
    rows = read_far(far)
    assert rows
    # samples from r0 to R inclusive: r = 1008..2992 step 16 plus 3000? steps are multiples of 16
    expected_total = len([r for r in range(0, 3001, 16) if r >= 1000])
    by_ray = defaultdict(int)
    for r in rows:
        assert r["samples_total"] == expected_total
        assert 0 < r["samples_in"] <= r["samples_total"]
        assert r["entries"] <= r["samples_in"]
        by_ray[(r["seed"], r["ray"])] += r["samples_in"]
    for k, v in by_ray.items():
        assert v == expected_total, "every far sample belongs to exactly one biome"


# ------------------------------------------------------------ failure modes
def test_deterministic_and_seed0_matters():
    _, f1, g1 = run(seed0=7)
    _, f2, g2 = run(seed0=7)
    _, f3, g3 = run(seed0=8)
    assert open(f1).read() == open(f2).read()
    assert open(g1).read() == open(g2).read()
    assert open(f1).read() != open(f3).read()


def test_rmax_zero_records_only_spawn_biome_censoring_not_R():
    _, first, _ = run(seeds=3, rays=2, rmax=0, far_from=0)
    rows = read_first(first)
    assert len(rows) == 3 * 2
    assert all(r["dist"] == 0 for r in rows)


def test_refinement_never_later_than_coarse():
    """h=4 grid contains the h=16 grid, so first hits can only move earlier."""
    _, f16, _ = run(seeds=12, rays=4, rmax=6000, step=16, seed0=11)
    _, f4, _ = run(seeds=12, rays=4, rmax=6000, step=4, seed0=11)
    a = {(r["seed"], r["ray"], r["biome"]): r["dist"] for r in read_first(f16)}
    b = {(r["seed"], r["ray"], r["biome"]): r["dist"] for r in read_first(f4)}
    # every biome found coarsely is found finely, no later
    for k, d in a.items():
        assert k in b and b[k] <= d
    # diagnostic: how many biome-hits does the coarse step miss entirely?
    missed = sum(1 for k in b if k not in a)
    print(f"coarse step missed {missed} of {len(b)} (seed,ray,biome) hits")


def test_matches_independent_python_ctypes_oracle():
    seeds, rays, R, h, seed0 = 2, 3, 3000, 16, 5
    _, first, _ = run(seeds=seeds, rays=rays, rmax=R, step=h, seed0=seed0)
    rows = read_first(first)
    lib = ctypes.CDLL(LIB)

    class Pos(ctypes.Structure):
        _fields_ = [("x", ctypes.c_int), ("z", ctypes.c_int)]

    lib.estimateSpawn.restype = Pos
    lib.estimateSpawn.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    lib.setupGenerator.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_uint32]
    lib.applySeed.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_uint64]
    lib.getBiomeAt.argtypes = [ctypes.c_void_p] + [ctypes.c_int] * 4
    lib.getBiomeAt.restype = ctypes.c_int
    g = ctypes.create_string_buffer(1 << 20)
    lib.setupGenerator(g, MC_1_21, 0)

    got = defaultdict(dict)
    angle = {}
    for r in rows:
        got[(r["seed"], r["ray"])][r["biome"]] = r["dist"]
        angle[(r["seed"], r["ray"])] = r["angle"]
    assert len(got) == seeds * rays
    for (seed, ray), exp in got.items():
        lib.applySeed(g, 0, seed & MASK)
        sp = lib.estimateSpawn(g, None)
        t = angle[(seed, ray)]
        mine = {}
        for r in range(0, R + 1, h):
            x = sp.x + math.floor(r * math.cos(t) + 0.5)
            z = sp.z + math.floor(r * math.sin(t) + 0.5)
            b = lib.getBiomeAt(g, 4, x >> 2, 15, z >> 2)
            mine.setdefault(b, r)
        assert mine == exp


@pytest.mark.parametrize("bad", [
    dict(rays=0), dict(step=0), dict(step=-4), dict(rmax=-1), dict(seeds=0),
    dict(mc="9.99"),
])
def test_bad_arguments_fail_nonzero(bad):
    p, _, _ = run(check=False, **bad)
    assert p.returncode != 0
