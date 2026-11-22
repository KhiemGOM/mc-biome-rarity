// bench263: points per second, one thread: c263_sample6 (our bit-exact 26.3 climate) vs the fork's
// sampleBiomeNoise(MC_26_3, SAMPLE_NO_BIOME), same random quart points; also the spawn search per seed.
#include <stdio.h>
#include <time.h>
#include <inttypes.h>
#include "generator.h"
#include "finders.h"
#include "../c263climate.h"

static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }
int main(void) {
    const int N = 2000000; static int Q[2000000][3];
    uint64_t s = 99;
    for (int i = 0; i < N; i++) { s = s * 6364136223846793005ULL + 1442695040888963407ULL;
        Q[i][0] = (int)((s >> 33) % 500001) - 250000; Q[i][1] = (int)((s >> 20) % 96) - 16; Q[i][2] = (int)((s >> 5) % 500001) - 250000; }
    C263 c; c263_init(&c, 123456789);
    Generator g; setupGenerator(&g, MC_26_3, 0); applySeed(&g, 0, 123456789);
    int64_t np[6]; volatile int64_t sink = 0;
    double t0 = now();
    for (int i = 0; i < N; i++) { c263_sample6(&c, Q[i][0], Q[i][1], Q[i][2], np); sink += np[4]; }
    double t1 = now();
    for (int i = 0; i < N; i++) { sampleBiomeNoise(&g.bn, np, Q[i][0], Q[i][1], Q[i][2], NULL, SAMPLE_NO_BIOME); sink += np[4]; }
    double t2 = now();
    int x, z; const int S = 200; double t3 = now();
    for (int k = 0; k < S; k++) { C263 cc; c263_init(&cc, (uint64_t)k * 7777); c263_spawn(&cc, &x, &z); sink += x; }
    double t4 = now();
    for (int k = 0; k < S; k++) { applySeed(&g, 0, (uint64_t)k * 7777); Pos p = estimateSpawn(&g, NULL); sink += p.x; }
    double t5 = now();
    printf("c263_sample6 %.3g points/s | fork sampleBiomeNoise %.3g points/s | ratio %.2f\n", N / (t1 - t0), N / (t2 - t1), (t2 - t1) / (t1 - t0));
    printf("c263 init+spawn %.3g ms/seed | fork applySeed+estimateSpawn %.3g ms/seed\n", (t4 - t3) / S * 1e3, (t5 - t4) / S * 1e3);
    return (int)(sink & 0);
}
