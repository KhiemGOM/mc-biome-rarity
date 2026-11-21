import csv, os, subprocess, tempfile
from collections import defaultdict
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLSIM = os.path.join(ROOT, "colsim")
NAMES = {int(a): b for a, b in (l.strip().split(",", 1) for l in open(os.path.join(ROOT, "out/names.csv")))}
INV = {v: k for k, v in NAMES.items()}


def probe(seed, qx, qz):
    p = subprocess.run([COLSIM, "--probe", str(seed), str(qx), str(qz)], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    rows = []
    for line in p.stdout.strip().splitlines():
        if line.startswith("#"):
            continue
        qy, d, br, bg, surf = line.split(",")
        rows.append(dict(qy=int(qy), depth=int(d), recon=int(br), game=int(bg), surf=int(surf)))
    return rows


def run(seeds=3, rays=2, rmax=2000, step=32, seed0=1, check=True, mc="1.21"):
    d = tempfile.mkdtemp()
    s, c = os.path.join(d, "s.csv"), os.path.join(d, "c.csv")
    p = subprocess.run([COLSIM, "--mc", mc, "--seeds", str(seeds), "--rays", str(rays), "--rmax", str(rmax),
                        "--step", str(step), "--seed0", str(seed0), "--out-surface", s, "--out-column", c],
                       capture_output=True, text=True)
    if check:
        assert p.returncode == 0, p.stderr
    return p, s, c


def read(path):
    with open(path) as f:
        return [dict(seed=int(r["seed"]), ray=int(r["ray"]), biome=int(r["biome"]), dist=int(r["dist"]))
                for r in csv.DictReader(f)]


PTS = [(1, 0, 0), (1, 500, -300), (42, -1200, 800), (42, 3000, 3000), (7, -50, 9000), (99, 2500, -4000)]


# ------------------------------------------------------------ happy path
def test_probe_has_96_layers_covering_world_height():
    r = probe(*PTS[0])
    assert [x["qy"] for x in r] == list(range(-16, 80))  # y = -64 .. 319


def test_reconstruction_matches_game_lookup():
    tot = bad = 0
    for pt in PTS:
        for x in probe(*pt):
            tot += 1
            bad += x["recon"] != x["game"]
    assert tot == 96 * len(PTS)
    assert bad / tot <= 0.001, f"{bad}/{tot} layers differ"


def test_depth_strictly_decreasing_about_312_per_layer():
    for pt in PTS:
        r = probe(*pt)
        for a, b in zip(r, r[1:]):
            assert 300 <= a["depth"] - b["depth"] <= 325


# ------------------------------------------------------------ failure modes
def test_surface_layer_is_where_depth_is_about_zero():
    for pt in PTS:
        r = probe(*pt)
        qs = r[0]["surf"]
        row = next(x for x in r if x["qy"] == qs)
        if -16 < qs < 79:
            assert abs(row["depth"]) <= 10000 / 64 + 1
        else:
            assert qs in (-16, 79)


def test_cave_biomes_sit_near_their_depth_bands():
    """Lookup is nearest-neighbour, so bands blur a little beyond Mojang's [0.2, 0.9] / [1.1]."""
    import random
    random.seed(1)
    seen = defaultdict(list)
    for seed in range(1, 31):
        for _ in range(6):
            for x in probe(seed, random.randint(-3000, 3000), random.randint(-3000, 3000)):
                n = NAMES.get(x["game"])
                if n in ("lush_caves", "dripstone_caves", "deep_dark"):
                    seen[n].append(x["depth"] / 1e4)
    assert all(len(seen[n]) > 50 for n in ("lush_caves", "dripstone_caves", "deep_dark")), "test would be vacuous"
    for n in ("lush_caves", "dripstone_caves"):
        assert 0.05 <= min(seen[n]) and max(seen[n]) <= 1.0, (n, min(seen[n]), max(seen[n]))
    assert min(seen["deep_dark"]) > 1.0


def test_outputs_wellformed_and_surface_subset_of_column():
    _, s, c = run(seeds=6, rays=3, rmax=6000)
    surf = {(r["seed"], r["ray"], r["biome"]): r["dist"] for r in read(s)}
    col = {(r["seed"], r["ray"], r["biome"]): r["dist"] for r in read(c)}
    assert surf and col
    for k, d in surf.items():
        assert k in col and col[k] <= d
    assert all(r["dist"] % 32 == 0 for r in read(c))


def test_spawn_biome_at_zero_exactly_one_surface_biome_per_ray():
    _, s, _ = run(seeds=4, rays=3)
    per = defaultdict(int)
    for r in read(s):
        if r["dist"] == 0:
            per[(r["seed"], r["ray"])] += 1
    assert len(per) == 12 and all(v == 1 for v in per.values())


def test_rmax_zero_and_determinism():
    _, s, c = run(seeds=3, rays=2, rmax=0)
    assert all(r["dist"] == 0 for r in read(s))
    _, s1, c1 = run(seed0=5)
    _, s2, c2 = run(seed0=5)
    assert open(s1).read() == open(s2).read() and open(c1).read() == open(c2).read()


@pytest.mark.parametrize("bad", [dict(rays=0), dict(step=0), dict(rmax=-1), dict(seeds=0), dict(mc="9.99")])
def test_bad_arguments_fail_nonzero(bad):
    p, _, _ = run(check=False, **bad)
    assert p.returncode != 0


# ------------------------------------------------ surface-only fast mode
def run_flag(extra, **kw):
    d = tempfile.mkdtemp()
    s, c = os.path.join(d, "s.csv"), os.path.join(d, "c.csv")
    a = dict(seeds=5, rays=3, rmax=5000, step=32, seed0=3)
    a.update(kw)
    p = subprocess.run([COLSIM, "--seeds", str(a["seeds"]), "--rays", str(a["rays"]), "--rmax", str(a["rmax"]),
                        "--step", str(a["step"]), "--seed0", str(a["seed0"]), "--out-surface", s, "--out-column", c, *extra],
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return s, c


def test_no_column_gives_identical_surface_output():
    s1, c1 = run_flag([])
    s2, c2 = run_flag(["--no-column"])
    assert open(s1).read() == open(s2).read()
    assert open(c2).read().strip().splitlines() == ["seed,ray,angle,biome,dist"]
    assert len(open(c1).read().splitlines()) > 1


def test_grid_nesting_coarser_step_never_earlier():
    """h=8 grid is a subset of the h=4 grid, so first hits can only get later, never earlier."""
    s4, _ = run_flag(["--no-column"], step=4, seeds=8, rmax=6000)
    s8, _ = run_flag(["--no-column"], step=8, seeds=8, rmax=6000)
    a = {(r["seed"], r["ray"], r["biome"]): r["dist"] for r in read(s4)}
    b = {(r["seed"], r["ray"], r["biome"]): r["dist"] for r in read(s8)}
    assert b
    for k, d in b.items():
        assert k in a and a[k] <= d
