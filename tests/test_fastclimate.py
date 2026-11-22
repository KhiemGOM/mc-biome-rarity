"""fastclimate.h (cached, branchless Perlin for the surface biome lookup) must be bit-exact with Cubiomes.

1. the C equivalence harness tests/test_fastclimate.c: every np value and biome id, random points, strip walks,
   seed switches and two generators on one cache;
2. discexact built on fastclimate (default) vs discexact built with -DDISCEXACT_REFERENCE (plain Cubiomes):
   byte-identical CSV for the certrun configuration, the certwalk configuration (early stop, uniform origin),
   the --debug dump, and across thread counts.
"""
import os, subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUBI = os.environ.get("CUBIOMES", os.path.expanduser("~/cubiomes-xp"))
LIB = os.path.join(CUBI, "libcubiomes.a")
pytestmark = pytest.mark.skipif(not os.path.exists(LIB), reason="needs a built Cubiomes (./build.sh)")
FLAGS = ["-O3", "-fwrapv", "-ffp-contract=off", "-fno-fast-math", f"-I{CUBI}"]


def _cc(out, src, *extra):
    subprocess.run(["gcc", *FLAGS, *extra, "-o", out, src, LIB, "-lm", "-pthread"], check=True, cwd=ROOT)
    return out


@pytest.fixture(scope="module")
def bins(tmp_path_factory):
    d = tmp_path_factory.mktemp("fc")
    return dict(fast=_cc(str(d / "dx_fast"), "discexact.c"),
                ref=_cc(str(d / "dx_ref"), "discexact.c", "-DDISCEXACT_REFERENCE"), dir=d)


def test_c_harness_np_and_biome_identical(tmp_path):
    exe = _cc(str(tmp_path / "tfc"), "tests/test_fastclimate.c")
    p = subprocess.run([exe, "6", "150000"], capture_output=True, text=True, timeout=600)
    assert p.returncode == 0 and p.stdout.startswith("OK"), p.stdout + p.stderr


def _run(exe, d, name, *args):
    out = str(d / name)
    subprocess.run([exe, *map(str, args), "--out", out], check=True, timeout=900)
    return open(out, "rb").read()


CONFIGS = {
    "certrun": ["--seeds", 12, "--rays", 4, "--rmax", 20000, "--radii", "0,64,128", "--seed0", 9000000000, "--threads", 6],
    "certwalk_spawn": ["--seeds", 10, "--rays", 4, "--rmax", 540000, "--radii", "0", "--seed0", 10000000000, "--threads", 5,
                       "--stopset", ",".join(map(str, range(0, 54)))],
    "certwalk_uniform": ["--seeds", 10, "--rays", 4, "--rmax", 540000, "--radii", "0", "--seed0", 10000000000,
                         "--threads", 5, "--origin", "uniform:1000000", "--stopset", ",".join(map(str, range(0, 54)))],
    "few_seeds_many_threads": ["--seeds", 2, "--rays", 3, "--rmax", 3000, "--radii", "0,32", "--seed0", 7, "--threads", 16],
}


@pytest.mark.parametrize("name", list(CONFIGS))
def test_discexact_byte_identical(bins, name):
    a = _run(bins["fast"], bins["dir"], name + ".fast.csv", *CONFIGS[name])
    b = _run(bins["ref"], bins["dir"], name + ".ref.csv", *CONFIGS[name])
    assert len(a) > 100 and a == b


def test_thread_count_does_not_change_output(bins):
    base = CONFIGS["certrun"][:-2]
    one = _run(bins["fast"], bins["dir"], "t1.csv", *base, "--threads", 1)
    many = _run(bins["fast"], bins["dir"], "t7.csv", *base, "--threads", 7)
    assert one == many


def test_debug_dump_identical(bins):
    args = ["--seed0", 9000000000, "--rays", 4, "--rmax", 20000, "--radii", "0,64,128", "--debug", "3,1"]
    a = subprocess.run([bins["fast"], *map(str, args)], capture_output=True, check=True).stdout
    b = subprocess.run([bins["ref"], *map(str, args)], capture_output=True, check=True).stdout
    assert a.count(b"\n") > 1000 and a == b
