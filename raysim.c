// raysim: first-hit distance of every biome along straight rays from spawn.
// Build: see Makefile. Conventions are documented in PLAN.md and pinned by tests.
#include <math.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "biomes.h"
#include "finders.h"
#include "generator.h"
#include "util.h"
#include "c263world.h"   // --mc 26.3: bit-exact 26.3 climate and spawn (c263climate.h)

typedef struct { char *first; size_t nfirst; char *far; size_t nfar; } SeedOut;

typedef struct {
    int mc, rays, step, far_from, tid, nthreads;
    long rmax, seeds;
    uint64_t seed0;
    SeedOut *out;
} Job;

static uint64_t splitmix64(uint64_t *x) {
    uint64_t z = (*x += 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}

static void append(char **buf, size_t *len, size_t *cap, const char *s, size_t n) {
    if (*len + n + 1 > *cap) {
        *cap = (*cap + n + 1) * 2;
        *buf = (char *)realloc(*buf, *cap);
    }
    memcpy(*buf + *len, s, n);
    *len += n;
    (*buf)[*len] = 0;
}

static void *worker(void *arg) {
    Job *j = (Job *)arg;
    World w;
    world_setup(&w, j->mc);
    for (long i = j->tid; i < j->seeds; i += j->nthreads) {
        uint64_t st = j->seed0 + (uint64_t)i;
        uint64_t seed = splitmix64(&st);
        uint64_t ust = seed ^ 0xD1B54A32D192ED03ULL;
        double u = (double)(splitmix64(&ust) >> 11) / 9007199254740992.0;
        world_seed(&w, seed);
        Pos sp = world_spawn(&w);

        char *fb = NULL, *gb = NULL;
        size_t fl = 0, fc = 0, gl = 0, gc = 0;
        char line[160];
        for (int k = 0; k < j->rays; k++) {
            double ang = 2.0 * M_PI * ((double)k + u) / (double)j->rays;
            double ca = cos(ang), sa = sin(ang);
            int first[256], in[256], ent[256];
            for (int b = 0; b < 256; b++) { first[b] = -1; in[b] = 0; ent[b] = 0; }
            long total = 0;
            int prev = -2;
            for (long r = 0; r <= j->rmax; r += j->step) {
                int x = sp.x + (int)floor((double)r * ca + 0.5);
                int z = sp.z + (int)floor((double)r * sa + 0.5);
                int b = world_biome(&w, x >> 2, 15, z >> 2);
                if (b < 0 || b > 255) { prev = -2; continue; }
                if (first[b] < 0) first[b] = (int)r;
                if (r >= j->far_from) {
                    total++;
                    in[b]++;
                    if (b != prev) ent[b]++;
                }
                prev = b;
            }
            for (int b = 0; b < 256; b++) {
                if (first[b] >= 0) {
                    int n = snprintf(line, sizeof line, "%lld,%d,%.17g,%d,%d\n",
                                     (long long)(int64_t)seed, k, ang, b, first[b]);
                    append(&fb, &fl, &fc, line, (size_t)n);
                }
                if (in[b] > 0) {
                    int n = snprintf(line, sizeof line, "%lld,%d,%d,%d,%d,%ld\n",
                                     (long long)(int64_t)seed, k, b, in[b], ent[b], total);
                    append(&gb, &gl, &gc, line, (size_t)n);
                }
            }
        }
        j->out[i].first = fb; j->out[i].nfirst = fl;
        j->out[i].far = gb;   j->out[i].nfar = gl;
    }
    return NULL;
}

static int bad(const char *msg) { fprintf(stderr, "raysim: %s\n", msg); return 2; }

int main(int argc, char **argv) {
    const char *mcs = "1.21", *of = NULL, *og = NULL;
    long seeds = 100, rmax = 20000;
    int rays = 8, step = 16, far_from = 5000, threads = 1;
    uint64_t seed0 = 1;
    for (int i = 1; i < argc; i++) {
        const char *a = argv[i];
        if (i + 1 >= argc) return bad("missing value");
        const char *v = argv[++i];
        if (!strcmp(a, "--mc")) mcs = v;
        else if (!strcmp(a, "--seeds")) seeds = atol(v);
        else if (!strcmp(a, "--rays")) rays = atoi(v);
        else if (!strcmp(a, "--rmax")) rmax = atol(v);
        else if (!strcmp(a, "--step")) step = atoi(v);
        else if (!strcmp(a, "--seed0")) seed0 = strtoull(v, NULL, 10);
        else if (!strcmp(a, "--far-from")) far_from = atoi(v);
        else if (!strcmp(a, "--threads")) threads = atoi(v);
        else if (!strcmp(a, "--out-first")) of = v;
        else if (!strcmp(a, "--out-far")) og = v;
        else return bad("unknown option");
    }
    int mc = str2mc(mcs);
    if (mc <= 0) return bad("unknown Minecraft version");
    if (seeds < 1) return bad("seeds must be >= 1");
    if (rays < 1) return bad("rays must be >= 1");
    if (step < 1) return bad("step must be >= 1");
    if (rmax < 0) return bad("rmax must be >= 0");
    if (far_from < 0) return bad("far-from must be >= 0");
    if (threads < 1) threads = 1;
    if (!of || !og) return bad("need --out-first and --out-far");

    SeedOut *out = (SeedOut *)calloc((size_t)seeds, sizeof(SeedOut));
    Job *jobs = (Job *)calloc((size_t)threads, sizeof(Job));
    pthread_t *th = (pthread_t *)calloc((size_t)threads, sizeof(pthread_t));
    for (int t = 0; t < threads; t++) {
        jobs[t] = (Job){mc, rays, step, far_from, t, threads, rmax, seeds, seed0, out};
        pthread_create(&th[t], NULL, worker, &jobs[t]);
    }
    for (int t = 0; t < threads; t++) pthread_join(th[t], NULL);

    // write to temporary names, rename on success (a stopped run leaves no short file)
    char tf[1024], tg[1024];
    snprintf(tf, sizeof tf, "%s.tmp", of);
    snprintf(tg, sizeof tg, "%s.tmp", og);
    FILE *f = fopen(tf, "w"), *g2 = fopen(tg, "w");
    if (!f || !g2) return bad("cannot open output");
    fputs("seed,ray,angle,biome,dist\n", f);
    fputs("seed,ray,biome,samples_in,entries,samples_total\n", g2);
    for (long i = 0; i < seeds; i++) {
        if (out[i].first) fwrite(out[i].first, 1, out[i].nfirst, f);
        if (out[i].far) fwrite(out[i].far, 1, out[i].nfar, g2);
        free(out[i].first); free(out[i].far);
    }
    fclose(f); fclose(g2);
    if (rename(tf, of) || rename(tg, og)) return bad("rename failed");
    free(out); free(jobs); free(th);
    return 0;
}
