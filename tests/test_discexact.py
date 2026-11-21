"""discexact: exact cell-level capsule discovery. Geometry is checked against a brute-force numeric reference."""
import csv, math, os, subprocess, tempfile
import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, "discexact")


def run(args, check=True):
    p = subprocess.run([EXE] + [str(a) for a in args], capture_output=True, text=True)
    if check:
        assert p.returncode == 0, p.stderr
    return p


def run_out(seeds=4, rays=2, rmax=3000, radii="0,64", seed0=1, threads=1):
    d = tempfile.mkdtemp(); o = os.path.join(d, "o.csv")
    p = run(["--seeds", seeds, "--rays", rays, "--rmax", rmax, "--radii", radii, "--seed0", seed0,
             "--threads", threads, "--out", o], check=False)
    return p, o


def rows(o):
    with open(o) as f:
        return [{k: (float(v) if k == "angle" else int(v)) for k, v in r.items()} for r in csv.DictReader(f)]


def debug(seed0, i, ray, rmax, radii):
    p = run(["--seed0", seed0, "--rmax", rmax, "--radii", radii, "--rays", 3, "--debug", f"{i},{ray}"])
    meta, cells = None, []
    for line in p.stdout.splitlines():
        if line.startswith("#"):
            _, x, z, ang = line.split()
            meta = (int(x), int(z), float(ang))
        else:
            v = line.split(",")
            cells.append((int(v[0]), int(v[1]), int(v[2]), [float(a) for a in v[3:]]))
    return meta, cells


# ---------------------------------------------------------------- brute-force reference geometry
def dist_to_cell(px, pz, qx, qz):
    dx = max(4 * qx - 0.5 - px, 0, px - (4 * qx + 3.5)); dz = max(4 * qz - 0.5 - pz, 0, pz - (4 * qz + 3.5))
    return math.hypot(dx, dz)


def ref_D(meta, qx, qz, r, R):
    """Brute force: f(s) = dist(L(s), Q) - r is convex, so minimise by ternary search, then bisect for the first root."""
    px, pz, ang = meta
    ca, sa = math.cos(ang), math.sin(ang)
    rho = dist_to_cell(px, pz, qx, qz)
    if rho <= r:
        return rho
    f = lambda s: dist_to_cell(px + s * ca, pz + s * sa, qx, qz) - r
    lo, hi = 0.0, float(R)
    for _ in range(200):
        m1, m2 = lo + (hi - lo) / 3, hi - (hi - lo) / 3
        lo, hi = (lo, m2) if f(m1) < f(m2) else (m1, hi)
    smin = 0.5 * (lo + hi)
    if f(smin) > 1e-9:
        return None
    a, b = 0.0, smin
    for _ in range(100):
        mid = 0.5 * (a + b)
        a, b = (a, mid) if f(mid) <= 0 else (mid, b)
    return b + r


@pytest.mark.parametrize("i,ray", [(0, 0), (1, 1), (2, 2), (3, 0), (5, 1)])
def test_cell_D_matches_bruteforce_and_enumeration_is_complete(i, ray):
    R, radii = 400, "0,16,64"
    rl = [0, 16, 64]
    meta, cells = debug(11, i, ray, R, radii)
    got = {(qx, qz): ds for qx, qz, _, ds in cells}
    px, pz, ang = meta
    ca, sa = math.cos(ang), math.sin(ang)
    qx0, qx1 = int((px - R - 80) // 4), int((px + R + 80) // 4)
    qz0, qz1 = int((pz - R - 80) // 4), int((pz + R + 80) // 4)
    X, Z = np.meshgrid(np.arange(qx0, qx1 + 1), np.arange(qz0, qz1 + 1), indexing="ij")
    cx, cz = 4 * X + 1.5, 4 * Z + 1.5   # centre of the cell
    t = np.clip((cx - px) * ca + (cz - pz) * sa, 0, R)
    near = np.hypot(cx - (px + t * ca), cz - (pz + t * sa)) <= 64 + 4          # generous prefilter, exact test below
    checked = 0
    for qx, qz in zip(X[near], Z[near]):
        qx, qz = int(qx), int(qz)
        ref = [ref_D(meta, qx, qz, r, R) for r in rl]
        ref = [None if (d is None or d > R) else d for d in ref]
        if all(d is None for d in ref):
            assert (qx, qz) not in got or all(x < 0 for x in got[(qx, qz)]), (qx, qz)
            continue
        assert (qx, qz) in got, f"cell {(qx, qz)} missing"
        for d_ref, d_got in zip(ref, got[(qx, qz)]):
            if d_ref is None:
                assert d_got < 0, (qx, qz, d_got)
            else:
                assert d_got == pytest.approx(d_ref, abs=0.02), (qx, qz, d_ref, d_got)
        checked += 1
    assert checked > 50
    for (qx, qz), ds in got.items():              # nothing outside the prefilter may be reported
        if any(d >= 0 for d in ds):
            assert near[qx - qx0, qz - qz0]


def test_axis_aligned_rays_have_no_division_trouble():
    for i in range(0, 40):
        p = run(["--seed0", 3, "--rmax", 300, "--radii", "0,32", "--rays", 4, "--debug", f"{i},0"], check=False)
        assert p.returncode == 0 and "nan" not in p.stdout.lower() and "inf" not in p.stdout.lower()


def test_r0_is_cells_crossed_by_the_line():
    meta, cells = debug(5, 0, 1, 500, "0")
    px, pz, ang = meta
    ca, sa = math.cos(ang), math.sin(ang)
    crossed = {(int(math.floor((px + s * ca + 0.5) / 4)), int(math.floor((pz + s * sa + 0.5) / 4))) for s in np.arange(0, 500, 0.05)}
    got = {(qx, qz) for qx, qz, _, ds in cells if ds[0] >= 0}
    assert crossed <= got and len(got - crossed) <= 0.2 * len(got)   # grazing corner cells allowed


# ---------------------------------------------------------------- pipeline properties
def test_header_and_columns():
    p, o = run_out()
    assert p.returncode == 0, p.stderr
    assert next(csv.reader(open(o))) == ["seed", "ray", "angle", "biome", "dist", "mode", "level"]


def test_levels_nested_monotone():
    p, o = run_out(seeds=8, rays=3, rmax=4000, radii="0,64")
    d = {(r["seed"], r["ray"], r["biome"], r["mode"], r["level"]): r["dist"] for r in rows(o)}
    for (s, ra, b, m, lv), dist in d.items():
        if lv > 1:
            assert (s, ra, b, m, lv // 2) in d and d[(s, ra, b, m, lv // 2)] <= dist


def test_bigger_radius_never_later_and_spawn_biome_is_zero():
    p, o = run_out(seeds=8, rays=3, rmax=4000, radii="0,64,128")
    d = {(r["seed"], r["ray"], r["biome"], r["mode"], r["level"]): r["dist"] for r in rows(o)}
    for (s, ra, b, m, lv), dist in d.items():
        if m == 0:
            assert d[(s, ra, b, 64, lv)] <= dist and d[(s, ra, b, 128, lv)] <= d[(s, ra, b, 64, lv)]
    z = {(r["seed"], r["ray"], r["mode"]) for r in rows(o) if r["dist"] == 0 and r["level"] == 1}
    seeds = {r["seed"] for r in rows(o)}
    assert len(z) >= len(seeds) * 3 * 3 - 0


def test_levels_are_values_1_2_4():
    p, o = run_out()
    assert {r["level"] for r in rows(o)} == {1, 2, 4}


def test_threads_do_not_change_output():
    _, a = run_out(seeds=6, threads=1); _, b = run_out(seeds=6, threads=2)
    assert open(a).read() == open(b).read()


@pytest.mark.parametrize("radii", ["-1", "x", "", "64,,128"])
def test_bad_radii(radii):
    p, _ = run_out(radii=radii)
    assert p.returncode != 0


def test_needs_out():
    assert run(["--seeds", 2], check=False).returncode != 0


# ---------------------------------------------------------------- the cell model IS the block model
def ref_D_blocks(meta, qx, qz, r, R):
    """Pure block-level definition: min over the 16 unit blocks of the cell of D_block (block = [i-.5,i+.5]^2)."""
    px, pz, ang = meta
    ca, sa = math.cos(ang), math.sin(ang)

    def dblock(bx, bz, s):
        x, z = px + s * ca, pz + s * sa
        return math.hypot(max(bx - 0.5 - x, 0, x - bx - 0.5), max(bz - 0.5 - z, 0, z - bz - 0.5))

    best = None
    for bx in range(4 * qx, 4 * qx + 4):
        for bz in range(4 * qz, 4 * qz + 4):
            rho = dblock(bx, bz, 0.0)
            if rho <= r:
                d = rho
            else:
                lo, hi = 0.0, float(R)
                for _ in range(200):
                    m1, m2 = lo + (hi - lo) / 3, hi - (hi - lo) / 3
                    lo, hi = (lo, m2) if dblock(bx, bz, m1) < dblock(bx, bz, m2) else (m1, hi)
                sm = 0.5 * (lo + hi)
                if dblock(bx, bz, sm) - r > 1e-9:
                    continue
                a, b = 0.0, sm
                for _ in range(100):
                    mid = 0.5 * (a + b)
                    a, b = (a, mid) if dblock(bx, bz, mid) - r <= 0 else (mid, b)
                d = b + r
            best = d if best is None else min(best, d)
    return best


@pytest.mark.parametrize("r", [0, 16, 64])
def test_cell_model_equals_min_over_its_16_blocks(r):
    meta, cells = debug(11, 2, 1, 400, "0,16,64")
    idx = {0: 0, 16: 1, 64: 2}[r]
    import random
    random.seed(r)
    sample = random.sample([c for c in cells if c[3][idx] >= 0], 25)
    for qx, qz, _, ds in sample:
        d_blocks = ref_D_blocks(meta, qx, qz, r, 400)
        assert d_blocks is not None and ds[idx] == pytest.approx(d_blocks, abs=0.02)
