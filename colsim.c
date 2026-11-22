// colsim: like raysim, but checks the whole vertical column (y = -64..319) at each sample point.
// Only the depth climate value depends on y: depth(qy) = depth(qy0) + (qy0 - qy)/32  (qy = block y / 4).
#include <math.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "biomes.h"
#include "biomenoise.h"
#include "finders.h"
#include "generator.h"
#include "c263world.h"   // --mc 26.3: bit-exact 26.3 climate and spawn (c263climate.h)
#include "util.h"

#define QY_MIN (-16)
#define QY_MAX 79
#define NL (QY_MAX - QY_MIN + 1)
#define QY_REF 15

typedef struct { char *s; size_t ns; char *c; size_t nc; } SeedOut;
typedef struct { int mc, rays, step, tid, nthreads, nocol, nested; long rmax, seeds; uint64_t seed0; SeedOut *out; } Job;
#define MAX_NESTED 8

static uint64_t splitmix64(uint64_t *x) {
    uint64_t z = (*x += 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}

static void append(char **buf, size_t *len, size_t *cap, const char *s, size_t n) {
    if (*len + n + 1 > *cap) { *cap = (*cap + n + 1) * 2; *buf = (char *)realloc(*buf, *cap); }
    memcpy(*buf + *len, s, n); *len += n; (*buf)[*len] = 0;
}

// Fill layer[0..NL) with biome ids for the column at quart (qx,qz); return surface layer index in *surf.
static void column(const World *w, int qx, int qz, int *layer, int *depth_out, int *surf, uint64_t *dat) {
    const Generator *g = &w->g;
    int64_t np[6];
    float off = 0;
    if (w->is263) { off = c263_column(&w->c, qx, qz, np); np[4] = c263_depth_at(off, QY_REF); }   // 26.3: exact depth per layer
    else world_np(w, qx, QY_REF, qz, np);
    double dref = (double)np[4] / 10000.0;
    for (int i = 0; i < NL; i++) {
        int qy = QY_MIN + i;
        float d = (float)(dref + (double)(QY_REF - qy) / 32.0);
        np[4] = w->is263 ? c263_depth_at(off, qy) : (int64_t)(10000.0F * d);
        if (depth_out) depth_out[i] = (int)np[4];
        layer[i] = climateToBiome(g->mc, (const uint64_t *)np, dat);
    }
    // surface layer: depth closest to 0  =>  qy = QY_REF + 32*dref, clamped to the world
    int qs = (int)floor(QY_REF + 32.0 * dref + 0.5);
    if (qs < QY_MIN) qs = QY_MIN;
    if (qs > QY_MAX) qs = QY_MAX;
    *surf = qs - QY_MIN;
}

// Surface biome only: one climate sample, one table lookup (same arithmetic as column()).
// Hint-free lookup on purpose: with a hint, exact distance ties resolve to the previous sample's biome, so the
// result would depend on the path. Hint-free is deterministic per point (costs ~15% time).
static int surface_only(const World *w, int qx, int qz, uint64_t *dat) {
    const Generator *g = &w->g;
    int64_t np[6];
    float off = 0;
    if (w->is263) { off = c263_column(&w->c, qx, qz, np); np[4] = c263_depth_at(off, QY_REF); }
    else world_np(w, qx, QY_REF, qz, np);
    double dref = (double)np[4] / 10000.0;
    int qs = (int)floor(QY_REF + 32.0 * dref + 0.5);
    if (qs < QY_MIN) qs = QY_MIN;
    if (qs > QY_MAX) qs = QY_MAX;
    float d = (float)(dref + (double)(QY_REF - qs) / 32.0);
    np[4] = w->is263 ? c263_depth_at(off, qs) : (int64_t)(10000.0F * d);   // 26.3: the exact depth of the surface layer
    (void)dat; return climateToBiome(g->mc, (const uint64_t *)np, NULL);
}

static void *worker(void *arg) {
    Job *j = (Job *)arg;
    World w;
    world_setup(&w, j->mc);
    uint64_t dat = 0;
    for (long i = j->tid; i < j->seeds; i += j->nthreads) {
        uint64_t st = j->seed0 + (uint64_t)i;
        uint64_t seed = splitmix64(&st);
        uint64_t ust = seed ^ 0xD1B54A32D192ED03ULL;
        double u = (double)(splitmix64(&ust) >> 11) / 9007199254740992.0;
        world_seed(&w, seed);
        Pos sp = world_spawn(&w);
        char *sb = NULL, *cb = NULL; size_t sl = 0, sc = 0, cl = 0, cc = 0; char line[128];
        for (int k = 0; k < j->rays; k++) {
            double ang = 2.0 * M_PI * ((double)k + u) / (double)j->rays;
            double ca = cos(ang), sa = sin(ang);
            int fs[256], fc[256];
            int fn[MAX_NESTED][256];   // nested mode: first hit per level m (grid step * 2^m)
            for (int b = 0; b < 256; b++) { fs[b] = -1; fc[b] = -1; }
            for (int m = 0; m < MAX_NESTED; m++) for (int b = 0; b < 256; b++) fn[m][b] = -1;
            int layer[NL], surf;
            long idx = 0;
            for (long r = 0; r <= j->rmax; r += j->step, idx++) {
                int x = sp.x + (int)floor((double)r * ca + 0.5);
                int z = sp.z + (int)floor((double)r * sa + 0.5);
                int sbio;
                if (j->nocol) sbio = surface_only(&w, x >> 2, z >> 2, &dat);
                else { column(&w, x >> 2, z >> 2, layer, NULL, &surf, &dat); sbio = layer[surf]; }
                if (sbio >= 0 && sbio < 256 && fs[sbio] < 0) fs[sbio] = (int)r;
                if (j->nested > 0) {
                    // sample idx lies on level m's grid exactly when idx is a multiple of 2^m
                    for (int m = 0; m < j->nested && (idx & ((1L << m) - 1)) == 0; m++)
                        if (sbio >= 0 && sbio < 256 && fn[m][sbio] < 0) fn[m][sbio] = (int)r;
                }
                if (j->nocol) continue;
                for (int l = 0; l < NL; l++) {
                    int b = layer[l];
                    if (b >= 0 && b < 256 && fc[b] < 0) fc[b] = (int)r;
                }
            }
            if (j->nested > 0) {
                for (int m = 0; m < j->nested; m++)
                    for (int b = 0; b < 256; b++)
                        if (fn[m][b] >= 0) {
                            int n = snprintf(line, sizeof line, "%lld,%d,%.17g,%d,%d,%d\n", (long long)(int64_t)seed, k, ang, b, fn[m][b], m);
                            append(&sb, &sl, &sc, line, (size_t)n);
                        }
                continue;
            }
            for (int b = 0; b < 256; b++) {
                if (fs[b] >= 0) {
                    int n = snprintf(line, sizeof line, "%lld,%d,%.17g,%d,%d\n", (long long)(int64_t)seed, k, ang, b, fs[b]);
                    append(&sb, &sl, &sc, line, (size_t)n);
                }
                if (fc[b] >= 0) {
                    int n = snprintf(line, sizeof line, "%lld,%d,%.17g,%d,%d\n", (long long)(int64_t)seed, k, ang, b, fc[b]);
                    append(&cb, &cl, &cc, line, (size_t)n);
                }
            }
        }
        j->out[i].s = sb; j->out[i].ns = sl; j->out[i].c = cb; j->out[i].nc = cl;
    }
    return NULL;
}

static int bad(const char *m) { fprintf(stderr, "colsim: %s\n", m); return 2; }

static int do_probe(int mc, long long seed, int qx, int qz) {
    World w; world_setup(&w, mc); world_seed(&w, (uint64_t)seed);
    int layer[NL], dep[NL], surf; uint64_t dat = 0;
    column(&w, qx, qz, layer, dep, &surf, &dat);
    printf("# qy,depth_x10000,biome_reconstructed,biome_game,surface_qy\n");
    for (int i = 0; i < NL; i++) {
        int qy = QY_MIN + i;
        int game = world_biome(&w, qx, qy, qz);
        printf("%d,%d,%d,%d,%d\n", qy, dep[i], layer[i], game, QY_MIN + surf);
    }
    return 0;
}

int main(int argc, char **argv) {
    const char *mcs = "1.21", *os_ = NULL, *oc = NULL; int nest_given = 0;
    long seeds = 100, rmax = 20000; int rays = 4, step = 32, threads = 1, nocol = 0, nested = 0; uint64_t seed0 = 1;
    if (argc >= 5 && !strcmp(argv[1], "--probe"))
        return do_probe(str2mc("1.21"), atoll(argv[2]), atoi(argv[3]), atoi(argv[4]));
    for (int i = 1; i < argc; i++) {
        const char *a = argv[i];
        if (!strcmp(a, "--no-column")) { nocol = 1; continue; }
        if (i + 1 >= argc) return bad("missing value");
        const char *v = argv[++i];
        if (!strcmp(a, "--mc")) mcs = v;
        else if (!strcmp(a, "--seeds")) seeds = atol(v);
        else if (!strcmp(a, "--rays")) rays = atoi(v);
        else if (!strcmp(a, "--rmax")) rmax = atol(v);
        else if (!strcmp(a, "--step")) step = atoi(v);
        else if (!strcmp(a, "--seed0")) seed0 = strtoull(v, NULL, 10);
        else if (!strcmp(a, "--threads")) threads = atoi(v);
        else if (!strcmp(a, "--nested")) { nested = atoi(v); nest_given = 1; }
        else if (!strcmp(a, "--out-surface")) os_ = v;
        else if (!strcmp(a, "--out-column")) oc = v;
        else return bad("unknown option");
    }
    int mc = str2mc(mcs);
    if (mc <= 0) return bad("unknown Minecraft version");
    if (mc < MC_1_18) return bad("needs 1.18 or newer (3D biomes)");
    if (seeds < 1) return bad("seeds must be >= 1");
    if (rays < 1) return bad("rays must be >= 1");
    if (step < 1) return bad("step must be >= 1");
    if (rmax < 0) return bad("rmax must be >= 0");
    if (threads < 1) threads = 1;
    if (!os_ || !oc) return bad("need --out-surface and --out-column");
    if (nest_given && (nested < 1 || nested > MAX_NESTED)) return bad("--nested must be between 1 and 8");
    if (nested > 0 && !nocol) return bad("--nested needs --no-column");

    SeedOut *out = (SeedOut *)calloc((size_t)seeds, sizeof(SeedOut));
    Job *jobs = (Job *)calloc((size_t)threads, sizeof(Job));
    pthread_t *th = (pthread_t *)calloc((size_t)threads, sizeof(pthread_t));
    for (int t = 0; t < threads; t++) {
        jobs[t] = (Job){mc, rays, step, t, threads, nocol, nested, rmax, seeds, seed0, out};
        pthread_create(&th[t], NULL, worker, &jobs[t]);
    }
    for (int t = 0; t < threads; t++) pthread_join(th[t], NULL);
    char t1[1024], t2[1024];
    snprintf(t1, sizeof t1, "%s.tmp", os_); snprintf(t2, sizeof t2, "%s.tmp", oc);
    FILE *f = fopen(t1, "w"), *g2 = fopen(t2, "w");
    if (!f || !g2) return bad("cannot open output");
    fputs(nested > 0 ? "seed,ray,angle,biome,dist,level\n" : "seed,ray,angle,biome,dist\n", f);
    fputs("seed,ray,angle,biome,dist\n", g2);
    for (long i = 0; i < seeds; i++) {
        if (out[i].s) fwrite(out[i].s, 1, out[i].ns, f);
        if (out[i].c) fwrite(out[i].c, 1, out[i].nc, g2);
        free(out[i].s); free(out[i].c);
    }
    fclose(f); fclose(g2);
    if (rename(t1, os_) || rename(t2, oc)) return bad("rename failed");
    return 0;
}
