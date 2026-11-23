// c263cachecheck: the lattice-cached climate (c263cache.h) against c263climate.h, every int64 and the spline offset bits.
//   1) 10,000,000 random quart points over 20 seeds (c263c_sample6 vs c263_sample6)
//   2) 50 seeds, full ray paths from the game's spawn: every cell of a 520,000 block centre line, and a 129 cell wide
//      strip for the first 60,000 blocks in scan order (qx outer, qz inner), column values and spline offset
#include <stdio.h>
#include <math.h>
#include <string.h>
#include <inttypes.h>
#include "../c263cache.h"

static uint64_t sm(uint64_t *x) { uint64_t z = (*x += 0x9E3779B97F4A7C15ULL); z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL; z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL; return z ^ (z >> 31); }
static long N, BAD;
static void cmpcol(const C263 *c, C263Cache *k, int qx, int qz) {
    int64_t a[6], b[6]; float oa = c263_column(c, qx, qz, a), ob = c263c_column(c, k, qx, qz, b);
    uint32_t ba, bb; memcpy(&ba, &oa, 4); memcpy(&bb, &ob, 4);
    N++; if (memcmp(a, b, sizeof a) || ba != bb) { if (BAD++ < 5) printf("column differs at %d %d\n", qx, qz); }
}
int main(void) {
    static C263 c; static C263Cache k; memset(&k, 0, sizeof k);
    uint64_t st = 2026;
    long n1 = 0, b1 = 0;
    for (int s = 0; s < 20; s++) {
        c263_init(&c, sm(&st));
        for (int i = 0; i < 500000; i++) {
            uint64_t r = sm(&st);
            int qx, qz, qy = (int)(r % 96) - 16;
            if (i % 3 == 0) { qx = (int)(sm(&st) % 15000001) - 7500000; qz = (int)(sm(&st) % 15000001) - 7500000; }   // up to +-30M blocks
            else if (i % 3 == 1) { qx = (int)(sm(&st) % 2001) - 1000; qz = (int)(sm(&st) % 2001) - 1000; }
            else { qx = (int)(sm(&st) % 64) - 32 + (i & 255); qz = (int)(sm(&st) % 64) - 32; }        // clustered: cache hits
            int64_t a[6], b[6]; c263_sample6(&c, qx, qy, qz, a); c263c_sample6(&c, &k, qx, qy, qz, b);
            n1++; if (memcmp(a, b, sizeof a)) { if (b1++ < 5) printf("sample6 differs seed %d at %d %d %d\n", s, qx, qy, qz); }
        }
    }
    printf("random points %ld differ %ld\n", n1, b1);
    for (int s = 0; s < 50; s++) {
        uint64_t seed = sm(&st); c263_init(&c, seed);
        int sx, sz; c263_spawn(&c, &sx, &sz);
        double ang = (double)(sm(&st) >> 11) / 9007199254740992.0 * 6.283185307179586, ux = cos(ang), uz = sin(ang);
        int lqx = 1 << 30, lqz = 1 << 30;
        for (long d = 0; d <= 520000; d += 2) {                      // centre line, every cell it enters
            int qx = (int)floor((sx + d * ux + 0.5) / 4.0), qz = (int)floor((sz + d * uz + 0.5) / 4.0);
            if (qx == lqx && qz == lqz) continue;
            lqx = qx; lqz = qz; cmpcol(&c, &k, qx, qz);
        }
        int qx0 = (int)floor(fmin(sx, sx + 60000 * ux) / 4.0) - 64, qx1 = (int)floor(fmax(sx, sx + 60000 * ux) / 4.0) + 64;
        for (int qx = qx0; qx <= qx1; qx++) {                        // 129 cell strip around the first 60,000 blocks, scan order
            double t = fabs(ux) > 1e-9 ? ((qx * 4.0 - sx) / ux) : 0;
            if (t < -600 || t > 60600) continue;
            int qzc = (int)floor((sz + t * uz) / 4.0);
            if (fabs(ux) < 0.05) { if (qx > qx0 + 129) break; }
            for (int qz = qzc - 64; qz <= qzc + 64; qz++) cmpcol(&c, &k, qx, qz);
        }
    }
    printf("ray path cells %ld differ %ld\n", N, BAD);
    return (b1 || BAD) ? 1 : 0;
}
