"""c263climate.h: bit-exact port of the Minecraft 26.3 climate and spawn search (gamecheck/, Climate_26.3.md).

The pinned values were printed by the real 26.3 server jar (gamecheck/GameCheck.java: N = Climate.Sampler.sample,
V = the chunk path createResolverForChunk, S = NoiseSpawnFinder). The full comparison is gamecheck.c against
GameCheck 200 5000 2000000 1, GameCheck V and SpawnDump 500 (gamecheck/result_26.3.txt).
"""
import os, subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUBI = os.environ.get("CUBIOMES", os.path.expanduser("~/cubiomes-xp"))
LIB = os.path.join(CUBI, "libcubiomes.a")
FLAGS = ["-O2", "-fwrapv", "-ffp-contract=off", "-fno-fast-math"]

# seed qx qy qz -> t h c e d w, biome (from the game)
CLIMATE = """
N -7995527694508729151 169457 57 68181 -5997 885 6158 -4465 -8785 3192 grove
N -7395478950850766697 85302 0 -64916 -2646 1380 8676 -5462 8770 -2277 dripstone_caves
N -7306852646597190783 258138 29 -144149 4946 -2901 1736 3414 -3276 7261 savanna
N 3244594241245886887 -57429 62 251923 3341 -2356 2633 2261 -14197 -4173 savanna
N 7425307051678139595 -92696 36 247121 -918 804 737 3537 -6324 -1172 forest
N -2135988175878413151 61061 -7 -89103 -8393 -2103 -5670 4960 4928 -4111 deep_frozen_ocean
N -135285792857410113 -131565 -16 193845 -7743 -1982 3566 -2739 11267 1189 deep_dark
N 897765151642547995 31592 42 -38977 1835 -1059 -5795 -42 -10384 -2709 deep_ocean
N 6822267176175700414 -104745 67 -96223 -833 -5425 -443 -475 -16102 -991 flower_forest
N -4799816026958307094 188315 74 -74537 3048 2091 -3488 247 -19362 -2415 lukewarm_ocean
N 664465988392411016 -232052 34 -171780 379 -2546 577 -4336 -6043 -843 plains
N -5009610649457996257 49276 39 187641 1235 490 -1959 -1529 -8425 2553 ocean
N 4895766943758564920 -231611 65 -155614 -4914 -3308 -2473 -7867 -16550 -3117 frozen_ocean
N -7091866049613194039 -13134 51 -81716 -5956 2836 8040 3936 -10848 -957 snowy_taiga
N 2848402741261745512 155725 0 -208713 -2703 -1722 -2921 4832 3762 -63 cold_ocean
N -6571251299216828022 -245172 29 -92364 -3597 2337 -1055 3979 -4135 3451 taiga
N 5565958372651049277 -121476 60 33374 3522 53 -530 902 -13072 -5746 forest
N -1533255857305339251 9726 34 259601 -6399 -1324 2479 2887 -6387 -200 frozen_river
N 7209246176534697576 -2597 37 54701 7939 -971 -2110 -348 -7800 -7820 warm_ocean
N -1839972837525038802 -190071 11 -194699 -656 2831 -5 -98 1109 -506 birch_forest
V 7134611160154358618 169360 -15 -49386 588 -4254 1554 -1233 9829 2477 sunflower_plains
V 1243081640783311616 -7 9 -101 -818 -248 351 962 1803 577 forest
V 8063302348174001649 -750 34 -10548 2990 707 4727 -1883 -5452 -974 forest
V -3651343285202881171 -9 58 117 3561 -2757 583 4515 -13787 361 river
V -1091701366366546633 -79 -14 42 -3466 -2721 -1556 3678 9245 -1774 beach
"""
# the game's NoiseSpawnFinder results
SPAWNS = """
S 7191089600892374487 12 41
S 309689372594955804 23 -33
S -1830642326893942270 -486 420
S -7693578145408079413 0 0
S 8632209307422871798 -53 -76
S 6051947643683389182 215 214
S 7205499895333846239 281 431
S -740192640177446100 176 627
S -2373510095968312272 -225 -872
S 7068487416905635272 -689 60
S 6599697964279942024 64 615
S -8998774008689024504 -650 -100
S 4912838792830128920 -965 503
"""

PROBE_C = r'''
#include <stdio.h>
#include <inttypes.h>
#include <string.h>
#include "c263climate.h"
int main(int argc, char **argv) {
    char line[512];
    if (argc > 1 && !strcmp(argv[1], "column")) {      // column + depth_at == sample6 at every layer
        long bad = 0, n = 0; uint64_t st = 12345;
        for (int s = 0; s < 3; s++) {
            C263 c; c263_init(&c, st * 0x9E3779B97F4A7C15ULL + (uint64_t)s);
            for (int k = 0; k < 300; k++) {
                int qx = (int)((k * 7919u) % 200001) - 100000, qz = (int)((k * 104729u) % 200001) - 100000;
                int64_t col[6]; float off = c263_column(&c, qx, qz, col);
                for (int y = -16; y <= 79; y++) {
                    int64_t a[6]; c263_sample6(&c, qx, y, qz, a);
                    col[4] = c263_depth_at(off, y);
                    n++; bad += memcmp(a, col, sizeof a) != 0;
                }
            }
        }
        printf("%ld %ld\n", n, bad); return 0;
    }
    while (fgets(line, sizeof line, stdin)) {
        int64_t seed; int a, b, c3; int64_t v[6]; char bn[64];
        if (line[0] == 'S' && sscanf(line, "S %" SCNd64 " %d %d", &seed, &a, &b) == 3) {
            C263 c; c263_init(&c, (uint64_t)seed); int x, z; c263_spawn(&c, &x, &z);
            printf("S %d %d\n", x == a && z == b, 0);
        } else if ((line[0] == 'N' || line[0] == 'V') && sscanf(line + 1, " %" SCNd64 " %d %d %d %" SCNd64 " %" SCNd64 " %" SCNd64 " %" SCNd64 " %" SCNd64 " %" SCNd64 " %63s",
                   &seed, &a, &b, &c3, &v[0], &v[1], &v[2], &v[3], &v[4], &v[5], bn) == 11) {
            C263 c; c263_init(&c, (uint64_t)seed); int64_t np[6]; c263_sample6(&c, a, b, c3, np);
            printf("N %d\n", memcmp(np, v, sizeof np) == 0);
        }
    }
    return 0;
}
'''


@pytest.fixture(scope="module")
def probe(tmp_path_factory):
    d = tmp_path_factory.mktemp("c263")
    src = d / "p.c"; src.write_text(PROBE_C)
    exe = str(d / "p")
    subprocess.run(["gcc", *FLAGS, f"-I{ROOT}", "-o", exe, str(src), "-lm"], check=True)
    return exe


def test_climate_matches_the_game_bit_for_bit(probe):
    out = subprocess.run([probe], input=CLIMATE, capture_output=True, text=True, check=True).stdout.split("\n")
    res = [l for l in out if l.startswith("N")]
    assert len(res) == 25 and all(l == "N 1" for l in res), out


def test_spawn_matches_the_game(probe):
    out = subprocess.run([probe], input=SPAWNS, capture_output=True, text=True, check=True).stdout.split("\n")
    res = [l for l in out if l.startswith("S")]
    assert len(res) == 13 and all(l.startswith("S 1") for l in res), out


def test_column_shortcut_equals_full_sample(probe):
    n, bad = map(int, subprocess.run([probe, "column"], capture_output=True, text=True, check=True).stdout.split())
    assert n == 3 * 300 * 96 and bad == 0


@pytest.mark.skipif(not os.path.exists(LIB), reason="needs a built Cubiomes fork (./build.sh)")
def test_biome_lookup_on_pinned_points(tmp_path):
    """The fork's hint-free btree263 lookup on our exact climate gives the game's biome on these points (none is a tie)."""
    src = tmp_path / "b.c"
    src.write_text(r'''
#include <stdio.h>
#include <string.h>
#include <inttypes.h>
#include "generator.h"
#include "util.h"
#include "c263climate.h"
int main(void) { char line[512]; long ok = 0, n = 0;
  while (fgets(line, sizeof line, stdin)) { int64_t seed, v[6]; int a, b, c3; char bn[64];
    if (sscanf(line + 1, " %" SCNd64 " %d %d %d %" SCNd64 " %" SCNd64 " %" SCNd64 " %" SCNd64 " %" SCNd64 " %" SCNd64 " %63s",
               &seed, &a, &b, &c3, &v[0], &v[1], &v[2], &v[3], &v[4], &v[5], bn) != 11) continue;
    C263 c; c263_init(&c, (uint64_t)seed); int64_t np[6]; c263_sample6(&c, a, b, c3, np);
    int id = climateToBiome(MC_26_3, (const uint64_t *)np, NULL); n++; ok += !strcmp(biome2str(MC_26_3, id), bn); }
  printf("%ld %ld\n", n, ok); return 0; }
''')
    exe = str(tmp_path / "b")
    subprocess.run(["gcc", *FLAGS, f"-I{ROOT}", f"-I{CUBI}", "-o", exe, str(src), LIB, "-lm", "-pthread"], check=True)
    n, ok = map(int, subprocess.run([exe], input=CLIMATE, capture_output=True, text=True, check=True).stdout.split())
    assert n == 25 and ok == 25


def test_no_x87_and_no_fma_in_the_climate_code(tmp_path):
    src = tmp_path / "s.c"
    src.write_text('#include "c263climate.h"\nvoid f(const C263 *c, int64_t *np) { c263_sample6(c, 1, 2, 3, np); }\n'
                   'void g(const C263 *c, int *x, int *z) { c263_spawn(c, x, z); }\n')
    asm = subprocess.run(["gcc", *FLAGS, f"-I{ROOT}", "-S", "-o", "-", str(src)], capture_output=True, text=True, check=True).stdout
    import re
    assert not re.search(r"\bf(ld|stp|add|mul|sub|div)[slt]?\b", asm)
    assert "fmadd" not in asm and "fmsub" not in asm
