"""discexact --layers all: the biome set of a cell over all 96 quart layers (world y = -64..319), THEORY.md 8.9.

1. --column-check: the fast class split (Proposition 26) equals the brute force (Cubiomes sampleBiomeNoise at every
   layer + hint-free climateToBiome) on random cells, far and near spawn;
2. the 1.21 tree satisfies the finite facts Proposition 26 uses (nested boxes, few depth classes, paired classes);
3. fast build vs -DDISCEXACT_REFERENCE (brute force column): byte-identical CSV, early stop on, several threads;
4. the column is a superset of the surface: every surface row has a column row no later;
5. cave biomes (lush caves, dripstone caves, deep dark) appear; thread count does not change output.
"""
import csv, io, os, subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUBI = os.environ.get("CUBIOMES", os.path.expanduser("~/cubiomes"))
LIB = os.path.join(CUBI, "libcubiomes.a")
pytestmark = pytest.mark.skipif(not os.path.exists(LIB), reason="needs a built Cubiomes (./build.sh)")
FLAGS = ["-O3", "-fwrapv", f"-I{CUBI}"]
CAVES = {174, 175, 183}          # dripstone_caves, lush_caves, deep_dark


def _cc(out, src, *extra):
    subprocess.run(["gcc", *FLAGS, *extra, "-o", out, src, LIB, "-lm", "-pthread"], check=True, cwd=ROOT)
    return out


@pytest.fixture(scope="module")
def bins(tmp_path_factory):
    d = tmp_path_factory.mktemp("col")
    return dict(fast=_cc(str(d / "dx_fast"), "discexact.c"),
                ref=_cc(str(d / "dx_ref"), "discexact.c", "-DDISCEXACT_REFERENCE"), dir=d)


def test_column_check_brute_force(bins):
    p = subprocess.run([bins["fast"], "--seeds", "24", "--seed0", "31337", "--column-check", "4000"],
                       capture_output=True, text=True, timeout=900)
    tot, bad = map(int, p.stdout.split())
    assert tot == 96000 and bad == 0 and p.returncode == 0


TREE_C = r'''
#include <stdio.h>
#include <stdint.h>
#include "tables/btree21wd.h"
static const uint64_t *N = btree21wd_nodes; static int LEN = sizeof(btree21wd_nodes) / 8;
static long bad = 0, leaves = 0;
static void box(int i, int lo[6], int hi[6]) { for (int d = 0; d < 6; d++) { int p = (N[i] >> 8 * d) & 0xFF;
    lo[d] = btree21wd_param[p][0]; hi[d] = btree21wd_param[p][1]; } }
static void walk(int idx, int depth) {
    if (btree21wd_steps[depth] == 0) { int lo[6], hi[6]; box(idx, lo, hi); leaves++;
        printf("L %d %d %d", (int)((N[idx] >> 48) & 0xFF), lo[4], hi[4]);
        for (int d = 0; d < 6; d++) if (d != 4) printf(" %d %d", lo[d], hi[d]); printf("\n"); return; }
    uint32_t step; do { step = btree21wd_steps[depth]; depth++; } while (idx + step >= LEN);
    int inner = N[idx] >> 48, plo[6], phi[6]; box(idx, plo, phi);
    for (int i = 0; i < btree21wd_order; i++) { int clo[6], chi[6]; box(inner, clo, chi);
        if (idx != 0) for (int d = 0; d < 6; d++) if (clo[d] < plo[d] || chi[d] > phi[d]) { bad++; break; }
        walk(inner, depth); inner += step; if (inner >= LEN) break; }
}
int main(void) { walk(0, 0); printf("B %ld %ld\n", bad, leaves); return 0; }
'''


def test_tree_facts(tmp_path):
    """Lemma 26a needs every non-root node's box to contain its children's; Proposition 26 needs the depth classes;
    Lemma 26b needs the [0,0] and [1,1] classes to pair up leaf by leaf (same biome, same other five intervals)."""
    src = tmp_path / "tree.c"; src.write_text(TREE_C)
    exe = str(tmp_path / "tree")
    subprocess.run(["gcc", "-O2", f"-I{CUBI}", "-o", exe, str(src)], check=True)
    out = subprocess.run([exe], capture_output=True, text=True, check=True).stdout.splitlines()
    bad, n = map(int, out[-1].split()[1:])
    assert bad == 0 and n > 7000
    L = [list(map(int, l.split()[1:])) for l in out[:-1]]
    classes = {(x[1], x[2]) for x in L}
    assert classes == {(0, 0), (10000, 10000), (11000, 11000), (2000, 9000)}
    key = lambda x: (x[0], *x[3:])
    a = sorted(key(x) for x in L if x[1:3] == [0, 0]); b = sorted(key(x) for x in L if x[1:3] == [10000, 10000])
    assert a == b and len(set(a)) == len(a)


def _run(exe, d, name, *args):
    out = str(d / name)
    subprocess.run([exe, *map(str, args), "--out", out], check=True, timeout=1200)
    return open(out, "rb").read()


STOP = ",".join(map(str, list(range(0, 54)) + sorted(CAVES)))
CONFIGS = {
    "walk": ["--seeds", 2, "--rays", 2, "--rmax", 30000, "--radii", "0,16", "--seed0", 10000000000, "--threads", 4,
             "--stopset", STOP, "--layers", "all"],
    "full": ["--seeds", 3, "--rays", 2, "--rmax", 6000, "--radii", "0,128", "--seed0", 99, "--threads", 3, "--layers", "all"],
}


@pytest.mark.parametrize("name", list(CONFIGS))
def test_fast_equals_reference(bins, name):
    a = _run(bins["fast"], bins["dir"], name + ".fast.csv", *CONFIGS[name])
    b = _run(bins["ref"], bins["dir"], name + ".ref.csv", *CONFIGS[name])
    assert len(a) > 100 and a == b


def _rows(data):
    d = {}
    for r in csv.DictReader(io.StringIO(data.decode())):
        if r["level"] == "1" and r["biome"] != "256":
            d[(r["seed"], r["ray"], r["mode"], int(r["biome"]))] = int(r["dist"])
    return d


def test_column_superset_of_surface_and_caves_found(bins):
    args = ["--seeds", 6, "--rays", 4, "--rmax", 20000, "--radii", "0,64,128", "--seed0", 4242, "--threads", 6]
    s = _rows(_run(bins["fast"], bins["dir"], "s.csv", *args))
    c = _rows(_run(bins["fast"], bins["dir"], "c.csv", *args, "--layers", "all"))
    assert s and all(k in c and c[k] <= v for k, v in s.items())
    assert CAVES <= {k[3] for k in c}


def test_threads_do_not_change_column_output(bins):
    base = ["--seeds", 5, "--rays", 3, "--rmax", 8000, "--radii", "0,64", "--seed0", 5, "--layers", "all"]
    assert _run(bins["fast"], bins["dir"], "c1.csv", *base, "--threads", 1) == _run(bins["fast"], bins["dir"], "c6.csv", *base, "--threads", 6)


def test_debug_column_uses_brute_force(bins):
    """--debug (used by certwalk verify) takes the brute force column, so verify checks the fast path independently."""
    args = ["--seed0", 77, "--rays", 4, "--rmax", 3000, "--radii", "0,64", "--layers", "all", "--debug", "2,1"]
    a = subprocess.run([bins["fast"], *map(str, args)], capture_output=True, check=True).stdout
    b = subprocess.run([bins["ref"], *map(str, args)], capture_output=True, check=True).stdout
    assert a.count(b"\n") > 100 and a == b


def test_plan_layers_reach_discexact():
    """A plan made with layers="all" passes --layers all to every discexact call and the hash covers it."""
    import sys
    sys.path.insert(0, ROOT)
    import certrun as cr, certwalk as cw
    plan = dict(seed0=1, rays=4, uniform_L=10, radii=[0], cap=1000, caps={}, chunk=1, alpha=0.1, alpha_rest=0.01,
                biomes=[1, 2], target_biomes=[1], target={"0": 0.1}, alpha_each={}, priors={}, n_star={"0": 1},
                n_max={"0": 2}, arm_radii={"spawn": [0], "uniform": []}, out="x", layers="all")
    g = cw.arm_plan(plan, "spawn")
    assert cr._origin(g)[-2:] == ["--layers", "all"]
    h = cw.plan_hash(plan); plan["layers"] = "surface"
    assert cw.plan_hash(plan) != h
    del plan["layers"]
    assert "--layers" not in cr._origin(cw.arm_plan(plan, "spawn"))
