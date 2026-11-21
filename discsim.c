// discsim: capsule discovery model. A walker moves along the ray from spawn; a biome is "discovered" when a
// block of it first lies within radius r of the walker (the swept shape is a rectangle with 2 semicircles).
// D = path to first discovery + r, or the straight distance from spawn if the block is already within r at spawn.
// Samples sit on a 16-block lattice (s along the ray, t across it). Mode 0 = centerline only (t = 0, s >= 0),
// which equals colsim --step 16, so the comparison is paired and uses the same grid.
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
#include "util.h"

#define G 16
#define QY_REF 15
#define QY_MIN (-16)
#define QY_MAX 79
#define MAXR 8

typedef struct { char *s; size_t n; } SeedOut;
typedef struct { int tid, nth, rays, nr, radii[MAXR]; long seeds, rmax; uint64_t seed0; SeedOut *out; } Job;

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

// identical arithmetic to colsim surface_only, hint-free
static int surface_only(const Generator *g, int qx, int qz) {
    int64_t np[6];
    sampleBiomeNoise(&g->bn, np, qx, QY_REF, qz, NULL, SAMPLE_NO_BIOME);
    double dref = (double)np[4] / 10000.0;
    int qs = (int)floor(QY_REF + 32.0 * dref + 0.5);
    if (qs < QY_MIN) qs = QY_MIN;
    if (qs > QY_MAX) qs = QY_MAX;
    float d = (float)(dref + (double)(QY_REF - qs) / 32.0);
    np[4] = (int64_t)(10000.0F * d);
    return climateToBiome(g->mc, (const uint64_t *)np, NULL);
}

static void *worker(void *arg) {
    Job *j = (Job *)arg;
    Generator g; setupGenerator(&g, str2mc("1.21"), 0);
    int rmaxr = 0;
    for (int i = 0; i < j->nr; i++) if (j->radii[i] > rmaxr) rmaxr = j->radii[i];
    for (long i = j->tid; i < j->seeds; i += j->nth) {
        uint64_t st = j->seed0 + (uint64_t)i;
        uint64_t seed = splitmix64(&st);
        uint64_t ust = seed ^ 0xD1B54A32D192ED03ULL;
        double u = (double)(splitmix64(&ust) >> 11) / 9007199254740992.0;
        applySeed(&g, 0, seed);
        Pos sp = estimateSpawn(&g, NULL);
        char *buf = NULL; size_t len = 0, cap = 0; char line[160];
        for (int k = 0; k < j->rays; k++) {
            double ang = 2.0 * M_PI * ((double)k + u) / (double)j->rays;
            double ca = cos(ang), sa = sin(ang);
            int fm[1 + MAXR][256];
            for (int m = 0; m <= j->nr; m++) for (int b = 0; b < 256; b++) fm[m][b] = -1;
            for (long s = -rmaxr; s <= j->rmax; s += G) {
                for (int t = -rmaxr; t <= rmaxr; t += G) {
                    double dist2 = (double)s * s + (double)t * t;
                    int center = (t == 0 && s >= 0);
                    int any = center;
                    for (int m = 0; m < j->nr && !any; m++) {
                        long r = j->radii[m];
                        if (labs(t) <= r && (s >= 0 || dist2 <= (double)r * r)) any = 1;
                    }
                    if (!any) continue;
                    double px = (double)s * ca - (double)t * sa, pz = (double)s * sa + (double)t * ca;
                    int x = sp.x + (int)floor(px + 0.5), z = sp.z + (int)floor(pz + 0.5);
                    int b = surface_only(&g, x >> 2, z >> 2);
                    if (b < 0 || b >= 256) continue;
                    if (center && (fm[0][b] < 0 || s < fm[0][b])) fm[0][b] = (int)s;
                    for (int m = 0; m < j->nr; m++) {
                        long r = j->radii[m];
                        if (labs(t) > r) continue;
                        double dd;
                        if (dist2 <= (double)r * r) dd = sqrt(dist2);                 // visible from spawn
                        else if (s < 0) continue;                                    // behind spawn and outside r
                        else dd = (double)s - sqrt((double)r * r - (double)t * t) + (double)r;
                        int di = (int)floor(dd + 0.5);
                        if (di > j->rmax) continue;
                        if (fm[1 + m][b] < 0 || di < fm[1 + m][b]) fm[1 + m][b] = di;
                    }
                }
            }
            for (int m = 0; m <= j->nr; m++)
                for (int b = 0; b < 256; b++)
                    if (fm[m][b] >= 0) {
                        int n = snprintf(line, sizeof line, "%lld,%d,%.17g,%d,%d,%d\n", (long long)(int64_t)seed, k, ang, b,
                                         fm[m][b], m == 0 ? 0 : j->radii[m - 1]);
                        append(&buf, &len, &cap, line, (size_t)n);
                    }
        }
        j->out[i].s = buf; j->out[i].n = len;
    }
    return NULL;
}

static int bad(const char *m) { fprintf(stderr, "discsim: %s\n", m); return 2; }

int main(int argc, char **argv) {
    long seeds = 100, rmax = 20000; int rays = 4, threads = 1, nr = 0, radii[MAXR]; uint64_t seed0 = 1; const char *out = NULL;
    const char *rs = "64,128";
    for (int i = 1; i < argc; i++) {
        if (i + 1 >= argc) return bad("missing value");
        const char *a = argv[i], *v = argv[++i];
        if (!strcmp(a, "--seeds")) seeds = atol(v);
        else if (!strcmp(a, "--rays")) rays = atoi(v);
        else if (!strcmp(a, "--rmax")) rmax = atol(v);
        else if (!strcmp(a, "--radii")) rs = v;
        else if (!strcmp(a, "--seed0")) seed0 = strtoull(v, NULL, 10);
        else if (!strcmp(a, "--threads")) threads = atoi(v);
        else if (!strcmp(a, "--out")) out = v;
        else return bad("unknown option");
    }
    if (!out) return bad("need --out");
    if (seeds < 1 || rays < 1 || rmax < 0) return bad("bad seeds/rays/rmax");
    if (threads < 1) threads = 1;
    char tmp[256]; strncpy(tmp, rs, sizeof tmp - 1); tmp[sizeof tmp - 1] = 0;
    for (char *tok = strtok(tmp, ","); tok; tok = strtok(NULL, ",")) {
        char *end; long r = strtol(tok, &end, 10);
        if (*end || r <= 0 || r % G || nr >= MAXR) return bad("radii must be positive multiples of 16 (max 8 of them)");
        radii[nr++] = (int)r;
    }
    if (nr == 0) return bad("no radii");
    SeedOut *o = (SeedOut *)calloc((size_t)seeds, sizeof(SeedOut));
    Job *jobs = (Job *)calloc((size_t)threads, sizeof(Job)); pthread_t *th = (pthread_t *)calloc((size_t)threads, sizeof(pthread_t));
    for (int t = 0; t < threads; t++) {
        jobs[t] = (Job){t, threads, rays, nr, {0}, seeds, rmax, seed0, o};
        memcpy(jobs[t].radii, radii, sizeof radii);
        pthread_create(&th[t], NULL, worker, &jobs[t]);
    }
    for (int t = 0; t < threads; t++) pthread_join(th[t], NULL);
    char t1[1100]; snprintf(t1, sizeof t1, "%s.tmp", out);
    FILE *f = fopen(t1, "w"); if (!f) return bad("cannot open output");
    fputs("seed,ray,angle,biome,dist,mode\n", f);
    for (long i = 0; i < seeds; i++) { if (o[i].s) fwrite(o[i].s, 1, o[i].n, f); free(o[i].s); }
    fclose(f);
    if (rename(t1, out)) return bad("rename failed");
    return 0;
}
