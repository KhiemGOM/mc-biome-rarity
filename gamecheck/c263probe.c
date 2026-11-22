// c263probe: compare c263climate.h piece by piece with the game's dumps (Probe.java).
//   ./c263probe noise <seed> < probe_noise.txt     Perlin offsets and permutations of every layer
//   ./c263probe vals  <seed> < probe_vals.txt      shift_x, shift_z, t, h, c, e, w, ridges_folded, offset, depth (float bits)
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>
#include "../c263climate.h"

static uint32_t fb(float f) { uint32_t b; memcpy(&b, &f, 4); return b; }
static uint64_t db(double d) { uint64_t b; memcpy(&b, &d, 8); return b; }

int main(int argc, char **argv) {
    if (argc < 3) return 2;
    uint64_t seed = (uint64_t)strtoll(argv[2], NULL, 10);
    C263 c; c263_init(&c, seed);
    char line[4096]; long n = 0, bad = 0;
    const char *names[6] = {"temperature", "vegetation", "continentalness", "erosion", "ridge", "offset"};
    if (!strcmp(argv[1], "noise")) {
        while (fgets(line, sizeof line, stdin)) {
            char nm[64], perms[600]; int i; uint64_t fr, ox, oy, oz; uint32_t am; float amf;
            if (sscanf(line, "L %63s %d freq %" SCNx64 " amp %x %f off %" SCNx64 " %" SCNx64 " %" SCNx64 " PerlinNoise perms %599s",
                       nm, &i, &fr, &am, &amf, &ox, &oy, &oz, perms) != 9) continue;
            int k = -1; for (int j = 0; j < 6; j++) if (!strcmp(nm, names[j])) k = j;
            const C263Noise *no = &c.no[k]; const C263Perlin *p = &no->per[i];
            char mine[600]; for (int j = 0; j < 256; j++) sprintf(mine + 2 * j, "%02x", p->p[j]);
            int ok = db(no->freq[i]) == fr && fb(no->amp[i]) == am && db(p->ox) == ox && db(p->oy) == oy && db(p->oz) == oz && !strcmp(mine, perms);
            n++; bad += !ok;
            if (!ok && bad <= 5) printf("noise %s layer %d differs: freq %d amp %d off %d %d %d perms %d\n", nm, i, db(no->freq[i]) == fr, fb(no->amp[i]) == am,
                                        db(p->ox) == ox, db(p->oy) == oy, db(p->oz) == oz, !strcmp(mine, perms));
        }
        printf("noise layers checked %ld bad %ld\n", n, bad);
        return bad != 0;
    }
    long badk[10] = {0};
    while (fgets(line, sizeof line, stdin)) {
        int x, y, z; uint32_t g[10];
        if (sscanf(line, "P %d %d %d %x %x %x %x %x %x %x %x %x %x", &x, &y, &z, &g[0], &g[1], &g[2], &g[3], &g[4], &g[5], &g[6], &g[7], &g[8], &g[9]) != 13) continue;
        float sx = c263_shift_x(&c, x, y, z), sz = c263_shift_z(&c, x, y, z);
        float v[6]; c263_floats(&c, x, y, z, v);
        float rf = c263_ridges_folded(v[5]);
        float in[4] = {v[2], v[3], rf, v[5]};
        float off = c263_spline(0, in) + -0.50375f;
        float mine[10] = {sx, sz, v[0], v[1], v[2], v[3], v[5], rf, off, v[4]};
        int any = 0;
        for (int k = 0; k < 10; k++) if (fb(mine[k]) != g[k]) { badk[k]++; any = 1; }
        n++; bad += any;
        if (any && bad <= 8) {
            printf("P %d %d %d:", x, y, z);
            for (int k = 0; k < 10; k++) if (fb(mine[k]) != g[k]) { float gf; memcpy(&gf, &g[k], 4); printf(" [%d] ours %.9g game %.9g", k, mine[k], gf); }
            printf("\n");
        }
    }
    printf("points %ld bad %ld | shift_x %ld shift_z %ld t %ld h %ld c %ld e %ld w %ld rf %ld offset %ld depth %ld\n", n, bad,
           badk[0], badk[1], badk[2], badk[3], badk[4], badk[5], badk[6], badk[7], badk[8], badk[9]);
    return bad != 0;
}
