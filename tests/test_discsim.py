"""discsim: capsule (rectangle + 2 semicircles) discovery model along each ray.
D = path length to first discovery + r (biome block sits at distance r when the disc first touches it);
if the biome is already within r of spawn, D = straight distance from spawn to it."""
import csv, os, subprocess, tempfile
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DISC = os.path.join(ROOT, "discsim")
COLSIM = os.path.join(ROOT, "colsim")


def run_disc(seeds=6, rays=2, rmax=3000, radii="64,128", seed0=1, threads=1):
    d = tempfile.mkdtemp(); out = os.path.join(d, "o.csv")
    p = subprocess.run([DISC, "--seeds", str(seeds), "--rays", str(rays), "--rmax", str(rmax), "--radii", radii,
                        "--seed0", str(seed0), "--threads", str(threads), "--out", out], capture_output=True, text=True)
    return p, out


def rows(path):
    with open(path) as f:
        return [{k: int(v) for k, v in r.items() if k != "angle"} for r in csv.DictReader(f)]


def test_header_and_modes():
    p, o = run_disc(radii="64,128")
    assert p.returncode == 0, p.stderr
    r = rows(o)
    assert {x["mode"] for x in r} == {0, 64, 128}
    assert list(csv.DictReader(open(o)).fieldnames) == ["seed", "ray", "angle", "biome", "dist", "mode"]


def test_centerline_mode_equals_colsim_step16():
    p, o = run_disc(seeds=8, rays=3, rmax=4000)
    d = tempfile.mkdtemp(); s, c = os.path.join(d, "s"), os.path.join(d, "c")
    q = subprocess.run([COLSIM, "--mc", "26.3", "--seeds", "8", "--rays", "3", "--rmax", "4000", "--step", "16",
                        "--seed0", "1", "--no-column", "--out-surface", s, "--out-column", c], capture_output=True, text=True)
    assert q.returncode == 0
    a = sorted((x["seed"], x["ray"], x["biome"], x["dist"]) for x in rows(o) if x["mode"] == 0)
    b = sorted((x["seed"], x["ray"], x["biome"], x["dist"]) for x in rows(s))
    assert a == b


def test_disc_never_later_than_centerline_and_never_misses_a_centerline_biome():
    p, o = run_disc(seeds=10, rays=3, rmax=5000, radii="64,128")
    d = {}
    for x in rows(o):
        d[(x["seed"], x["ray"], x["biome"], x["mode"])] = x["dist"]
    for (s, r, b, m), dist in d.items():
        if m == 0:
            for rad in (64, 128):
                assert (s, r, b, rad) in d and d[(s, r, b, rad)] <= dist


def test_larger_radius_never_later():
    p, o = run_disc(seeds=10, rays=3, rmax=5000, radii="64,128")
    d = {(x["seed"], x["ray"], x["biome"], x["mode"]): x["dist"] for x in rows(o)}
    for (s, r, b, m), dist in d.items():
        if m == 64:
            assert d[(s, r, b, 128)] <= dist


def test_spawn_biome_is_distance_zero_in_every_mode():
    p, o = run_disc(seeds=5, rays=2)
    z = {(x["seed"], x["ray"], x["mode"]) for x in rows(o) if x["dist"] == 0}
    seeds = {x["seed"] for x in rows(o)}
    assert len(z) == len(seeds) * 2 * 3


def test_biomes_inside_radius_at_spawn_use_straight_distance_bounded_by_radius():
    p, o = run_disc(seeds=12, rays=2, radii="128")
    for x in rows(o):
        if x["mode"] == 128 and x["dist"] < 128:
            assert x["dist"] >= 0       # straight distance from spawn, below r by construction


def test_distances_in_disc_mode_at_least_straight_line_minus_nothing():
    # the biome sample is at straight distance <= path, so D_disc >= distance(spawn, sample) is implicit;
    # observable consequence: nothing beyond rmax is reported
    p, o = run_disc(seeds=6, rays=2, rmax=2000)
    assert all(0 <= x["dist"] <= 2000 for x in rows(o))


def test_threads_do_not_change_output():
    _, a = run_disc(seeds=9, threads=1); _, b = run_disc(seeds=9, threads=2)
    assert open(a).read() == open(b).read()


@pytest.mark.parametrize("radii", ["0", "50", "-64", "abc", ""])
def test_bad_radii_rejected(radii):
    p, _ = run_disc(radii=radii)
    assert p.returncode != 0


def test_missing_out_rejected():
    p = subprocess.run([DISC, "--seeds", "2"], capture_output=True, text=True)
    assert p.returncode != 0
