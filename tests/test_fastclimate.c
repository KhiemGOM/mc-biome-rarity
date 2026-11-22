// Equivalence test: fastclimate.h must reproduce Cubiomes' sampleBiomeNoise (SAMPLE_NO_BIOME) and discexact's
// surface_only exactly (every np value and every biome id), for random points, strip walks (cache hits), seed
// switches on one cache, and two generators sharing one cache. Prints "OK <n>" or the first mismatch.
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "biomes.h"
#include "biomenoise.h"
#include "generator.h"
#include "util.h"
#include "../fastclimate.h"

static uint64_t sm(uint64_t *x) {
    uint64_t z = (*x += 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL; z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}

static int ref_surface(const Generator *g, int qx, int qz) {     // discexact.c surface_only, verbatim
    int64_t np[6];
    sampleBiomeNoise(&g->bn, np, qx, FC_QY_REF, qz, NULL, SAMPLE_NO_BIOME);
    double dref = (double)np[4] / 10000.0;
    int qs = (int)floor(FC_QY_REF + 32.0 * dref + 0.5);
    if (qs < FC_QY_MIN) qs = FC_QY_MIN;
    if (qs > FC_QY_MAX) qs = FC_QY_MAX;
    float d = (float)(dref + (double)(FC_QY_REF - qs) / 32.0);
    np[4] = (int64_t)(10000.0F * d);
    return climateToBiome(g->mc, (const uint64_t *)np, NULL);
}

static long checked = 0;
static int check(const Generator *g, FastCache *fc, int x, int y, int z) {
    int64_t a[6], b[6];
    sampleBiomeNoise(&g->bn, a, x, y, z, NULL, SAMPLE_NO_BIOME);
    fast_np(&g->bn, fc, b, x, y, z);
    for (int i = 0; i < 6; i++)
        if (a[i] != b[i]) { printf("NP MISMATCH seed=%llu x=%d y=%d z=%d i=%d ref=%lld fast=%lld\n",
                                   (unsigned long long)g->seed, x, y, z, i, (long long)a[i], (long long)b[i]); return 1; }
    if (y == FC_QY_REF) {
        int r = ref_surface(g, x, z), f = fast_surface(g, fc, x, z);
        if (r != f) { printf("BIOME MISMATCH seed=%llu x=%d z=%d ref=%d fast=%d\n", (unsigned long long)g->seed, x, z, r, f); return 1; }
    }
    checked++;
    return 0;
}

int main(int argc, char **argv) {
    int nseeds = argc > 1 ? atoi(argv[1]) : 6;
    long npts = argc > 2 ? atol(argv[2]) : 200000;
    Generator g, g2; setupGenerator(&g, str2mc("1.21"), 0); setupGenerator(&g2, str2mc("1.21"), 0);
    FastCache fc; fast_cache_init(&fc);
    uint64_t st = 42;
    for (int s = 0; s < nseeds; s++) {
        uint64_t seed = sm(&st);
        if (s == 0) seed = 0; if (s == 1) seed = (uint64_t)-1;     // edge seeds
        applySeed(&g, 0, seed);
        if (g.bn.nptype >= 0) { printf("unexpected nptype %d\n", g.bn.nptype); return 1; }
        // 1) random points over several ranges, including negatives and the far uniform-origin range
        static const int range[] = {64, 4096, 400000, 8000000};
        for (long i = 0; i < npts; i++) {
            int R = range[i % 4];
            int x = (int)(sm(&st) % (2 * (uint64_t)R + 1)) - R, z = (int)(sm(&st) % (2 * (uint64_t)R + 1)) - R;
            int y = (i % 3 == 0) ? (int)(sm(&st) % 200) - 64 : FC_QY_REF;
            if (check(&g, &fc, x, y, z)) return 1;
        }
        // 2) strip walks in scan_ray order (fixed qx, consecutive qz): the cache-hit path, both signs of the axes
        for (int w = 0; w < 8; w++) {
            int x0 = (int)(sm(&st) % 200001) - 100000, z0 = (int)(sm(&st) % 200001) - 100000;
            for (int qx = x0; qx < x0 + 40; qx++)
                for (int qz = z0; qz < z0 + 300; qz++)
                    if (check(&g, &fc, qx, FC_QY_REF, qz)) return 1;
        }
        // 3) the same cache alternating between two generators with different seeds (stale-cache guard)
        applySeed(&g2, 0, seed ^ 0x5DEECE66DULL);
        for (int qz = -500; qz < 500; qz++) {
            if (check(&g, &fc, 17, FC_QY_REF, qz)) return 1;
            if (check(&g2, &fc, 17, FC_QY_REF, qz)) return 1;
        }
    }
    // 4) reseeding the same generator, then revisiting the same cells (cache must not survive a seed change)
    for (int s = 0; s < 4; s++) {
        applySeed(&g, 0, 1000 + s);
        for (int qz = 0; qz < 400; qz++) if (check(&g, &fc, 3, FC_QY_REF, qz)) return 1;
    }
    printf("OK %ld\n", checked);
    return 0;
}
