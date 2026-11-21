"""colsim --nested L: one pass records first hits for steps h, 2h, 4h, ... (grids are nested)."""
import csv, os, subprocess, tempfile
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLSIM = os.path.join(ROOT, "colsim")


def run(seeds=6, rays=2, rmax=3000, step=4, seed0=1, nested=None, nocol=True, threads=1):
    d = tempfile.mkdtemp()
    s, c = os.path.join(d, "s.csv"), os.path.join(d, "c.csv")
    cmd = [COLSIM, "--mc", "1.21", "--seeds", str(seeds), "--rays", str(rays), "--rmax", str(rmax),
           "--step", str(step), "--seed0", str(seed0), "--threads", str(threads),
           "--out-surface", s, "--out-column", c]
    if nocol:
        cmd.append("--no-column")
    if nested is not None:
        cmd += ["--nested", str(nested)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p, s


def rows(path):
    with open(path) as f:
        r = csv.DictReader(f)
        return r.fieldnames, [{k: int(v) if k != "angle" else v for k, v in row.items()} for row in r]


def key(r):
    return (r["seed"], r["ray"], r["biome"], r["dist"])


def test_header_has_level_only_in_nested_mode():
    p, s = run(nested=2)
    assert p.returncode == 0, p.stderr
    assert rows(s)[0] == ["seed", "ray", "angle", "biome", "dist", "level"]
    p, s = run(nested=None)
    assert rows(s)[0] == ["seed", "ray", "angle", "biome", "dist"]


def test_nested_level_equals_separate_run_at_coarser_step():
    p, s = run(nested=3, step=4, seeds=8, rays=3, rmax=4000)
    assert p.returncode == 0, p.stderr
    _, nest = rows(s)
    for m in range(3):
        pm, sm = run(nested=None, step=4 * 2 ** m, seeds=8, rays=3, rmax=4000)
        assert pm.returncode == 0
        _, sep = rows(sm)
        got = sorted(key(r) for r in nest if r["level"] == m)
        assert got == sorted(key(r) for r in sep), f"level {m} differs from step {4 * 2 ** m}"


def test_levels_monotone_finer_grid_never_later():
    p, s = run(nested=4, step=2, seeds=10, rays=3, rmax=5000)
    assert p.returncode == 0
    _, nest = rows(s)
    d = {}
    for r in nest:
        d[(r["seed"], r["ray"], r["biome"], r["level"])] = r["dist"]
    for (sd, ray, b, m), dist in d.items():
        if m + 1 < 4 and (sd, ray, b, m + 1) in d:
            assert d[(sd, ray, b, m + 1)] >= dist
        if m > 0:
            assert (sd, ray, b, m - 1) in d, "coarse grid saw a biome the finer grid missed"
            assert d[(sd, ray, b, m - 1)] <= dist


def test_levels_are_multiples_of_their_step():
    p, s = run(nested=3, step=8, seeds=5, rays=2, rmax=4000)
    _, nest = rows(s)
    assert all(r["dist"] % (8 * 2 ** r["level"]) == 0 for r in nest)


def test_nested_requires_no_column():
    p, _ = run(nested=2, nocol=False)
    assert p.returncode != 0 and "no-column" in p.stderr


@pytest.mark.parametrize("bad", [0, -1, 9])
def test_nested_level_count_validated(bad):
    p, _ = run(nested=bad)
    assert p.returncode != 0


def test_threads_do_not_change_nested_output():
    _, s1 = run(nested=3, seeds=9, threads=1)
    _, s2 = run(nested=3, seeds=9, threads=2)
    assert open(s1).read() == open(s2).read()


def test_chunks_concatenate_to_one_big_run():
    _, big = run(nested=3, seeds=8, seed0=500)
    _, a = run(nested=3, seeds=4, seed0=500)
    _, b = run(nested=3, seeds=4, seed0=504)
    kb = sorted(key(r) + (r["level"],) for r in rows(big)[1])
    kab = sorted(key(r) + (r["level"],) for r in rows(a)[1] + rows(b)[1])
    assert kb == kab


def test_every_ray_reports_its_start_biome_at_distance_zero_on_all_levels():
    _, s = run(nested=3, seeds=5, rays=2)
    _, nest = rows(s)
    z = {(r["seed"], r["ray"], r["level"]) for r in nest if r["dist"] == 0}
    seeds = {r["seed"] for r in nest}
    assert len(z) == len(seeds) * 2 * 3
