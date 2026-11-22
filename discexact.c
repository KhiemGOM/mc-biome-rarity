// discexact: exact capsule discovery on the 4x4-block biome cells (see PLAN_DISC.md).
// For every cell within the largest radius of the path it computes D_c exactly (closed-form line / rounded-rectangle
// entry), looks the biome up once, and records first-hit D per biome for each radius and each sampling stride
// (level 1 = every cell, 2 = every 2nd cell in qx and qz, 4 = every 4th; nested subsets of the exact cell set).
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
#include "fastclimate.h"
// Minecraft version (THEORY.md 0): 263 = Java 26.3 (xpple/cubiomes fork, default), 214 = 1.21.4 (Winter Drop).
#ifndef DX_VERSION
#define DX_VERSION 263
#endif
#if DX_VERSION == 263
#include "tables/btree263.h"
#include "c263climate.h"   // 26.3 climate and spawn, bit-exact with the game (gamecheck/)
#define DX_MCV MC_26_3
#define DX_BT(x) btree263_##x
#elif DX_VERSION == 214
#include "tables/btree21wd.h"
#define DX_MCV MC_1_21_WD
#define DX_BT(x) btree21wd_##x
#else
#error "DX_VERSION must be 263 or 214"
#endif

#define QY_REF 15
#define QY_MIN (-16)
#define QY_MAX 79
#define MAXR 6
#define NLEV 3
static const int LEVELS[NLEV] = {1, 2, 4};

typedef struct { char *s; size_t n; } SeedOut;
typedef struct { int tid, nth, rays, nr; double radii[MAXR]; long seeds, rmax; uint64_t seed0; SeedOut *out; } Job;

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

static __thread FastCache FC_TLS;
#if DX_VERSION == 263
// per thread 26.3 climate state, (re)built when the generator's seed changes
static __thread C263 C263_TLS; static __thread uint64_t C263_SEED; static __thread int C263_READY = 0;
static inline const C263 *c263_of(const Generator *g) {
    if (!C263_READY || C263_SEED != g->seed) { c263_init(&C263_TLS, g->seed); C263_SEED = g->seed; C263_READY = 1; }
    return &C263_TLS;
}
// surface layer (same rule as before: the layer whose depth is nearest 0, from the depth at QY_REF), with 26.3's
// exact depth at that layer, then the fork's hint-free btree263 lookup
static int surface_only(const Generator *g, int qx, int qz) {
    const C263 *c = c263_of(g); int64_t np[6];
    float off = c263_column(c, qx, qz, np);
    double dref = (double)c263_depth_at(off, QY_REF) / 10000.0;
    int qs = (int)floor(QY_REF + 32.0 * dref + 0.5);
    if (qs < QY_MIN) qs = QY_MIN;
    if (qs > QY_MAX) qs = QY_MAX;
    np[4] = c263_depth_at(off, qs);
    return climateToBiome(g->mc, (const uint64_t *)np, NULL);
}
#elif defined(DISCEXACT_REFERENCE)
static int surface_only(const Generator *g, int qx, int qz) {          // hint-free, same arithmetic as colsim
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
#else
/* Same result bit for bit (fastclimate.h, tests/test_fastclimate.py): lattice-cached, branchless Perlin. */
static int surface_only(const Generator *g, int qx, int qz) { return fast_surface(g, &FC_TLS, qx, qz); }
#endif

// ---- full column (THEORY.md 8.9) ----------------------------------------------------------------------------
// The column of a cell is the set of biomes over all 96 quart layers y = -16..79 (world y = -64..319), each layer being
// exactly Cubiomes' sampleBiomeNoise(qx, y, qz) + hint-free climateToBiome. Only the depth np[4] changes with y.
static int LAYERS_ALL = 0;            /* 0: surface layer only; 1: every layer of the column */
static int COL_REF = 0;               /* --debug: brute force column (independent check of the fast path) */
#define NL (FC_QY_MAX - FC_QY_MIN + 1)
static const BiomeTree BT21 = { DX_BT(steps), &DX_BT(param)[0][0], DX_BT(nodes), DX_BT(order),
                                sizeof(DX_BT(nodes)) / sizeof(uint64_t) };
// Proposition 26 (THEORY.md 8.9). Every leaf's depth interval is one of a few classes (1.21: [0,0], [0.2,0.9], [1,1],
// [1.1,1.1]), and np[4] enters the distance only through (distance of np[4] to that interval)^2. So the cost of leaf i
// at a layer is c_i + g_class(i)(depth), where c_i is the distance over the other five values, which do not change
// with y. The search returns the first leaf in tree order among those of least cost (Lemma 26a), hence the best of
// the per class winners (per class: the first leaf in tree order with least c_i). Those are found once per cell (a
// filtered copy of the same search, or direct enumeration for tiny classes); each of the 96 layers is then 4 sums.
#define NCLS 8
static int NCLASS = 0, CLS_LO[NCLS], CLS_HI[NCLS], CLS_N[NCLS], CLS_LEAF[NCLS][4];
static int16_t LEAF_CLS[1 << 16]; static int32_t LEAF_POS[1 << 16], PARTNER[1 << 16];
static int BIG0 = -1, BIG1 = -1;       /* two large classes whose leaves pair up with identical biome and 5 value box */
static uint64_t dist5(const uint64_t np[6], int idx) {
    uint64_t ds = 0, node = BT21.nodes[idx];
    for (uint32_t i = 0; i < 6; i++) {
        if (i == 4) continue;
        int k = (node >> 8 * i) & 0xFF;
        uint64_t a = np[i] - BT21.param[2 * k + 1], b = BT21.param[2 * k + 0] - np[i];
        uint64_t d = (int64_t)a > 0 ? a : (int64_t)b > 0 ? b : 0;
        ds += d * d;
    }
    return ds;
}
// the depth term of np_dist for an interval of class c (same unsigned arithmetic)
static uint64_t gdepth(int64_t x, int c) {
    uint64_t a = (uint64_t)x - (uint64_t)(int64_t)CLS_HI[c], b = (uint64_t)(int64_t)CLS_LO[c] - (uint64_t)x;
    uint64_t d = (int64_t)a > 0 ? a : (int64_t)b > 0 ? b : 0;
    return d * d;
}
// a subtree can hold a class c leaf only if its depth box contains the class interval (boxes nest, Lemma 26a)
static inline int may_hold(int idx, int c) {
    int p = (BT21.nodes[idx] >> 32) & 0xFF;
    return BT21.param[2 * p] <= CLS_LO[c] && BT21.param[2 * p + 1] >= CLS_HI[c];
}
static int POS_NEXT = 0; static uint8_t LEAF_IS[1 << 16];
static void cls_walk(int idx, int depth) {               // leaves in the search's own traversal order
    if (BT21.steps[depth] == 0) {
        int p = (BT21.nodes[idx] >> 32) & 0xFF, lo = BT21.param[2 * p], hi = BT21.param[2 * p + 1], c;
        for (c = 0; c < NCLASS; c++) if (CLS_LO[c] == lo && CLS_HI[c] == hi) break;
        if (c == NCLASS) { if (NCLASS >= NCLS) abort(); CLS_LO[c] = lo; CLS_HI[c] = hi; CLS_N[c] = 0; NCLASS++; }
        if (CLS_N[c] < 4) CLS_LEAF[c][CLS_N[c]] = idx;
        CLS_N[c]++; LEAF_CLS[idx] = (int16_t)c; LEAF_POS[idx] = POS_NEXT++; LEAF_IS[idx] = 1;
        return;
    }
    uint32_t step;
    do { step = BT21.steps[depth]; depth++; } while (idx + step >= BT21.len);
    int inner = BT21.nodes[idx] >> 48;
    for (int i = 0; i < BT21.order; i++) { cls_walk(inner, depth); inner += step; if (inner >= (int)BT21.len) break; }
}
static pthread_once_t CLS_ONCE = PTHREAD_ONCE_INIT;
static int same_box(int i, int j) {
    uint64_t a = BT21.nodes[i], b = BT21.nodes[j];
    if (((a >> 48) & 0xFF) != ((b >> 48) & 0xFF)) return 0;
    for (int d = 0; d < 6; d++) {
        if (d == 4) continue;
        int p = (a >> 8 * d) & 0xFF, q = (b >> 8 * d) & 0xFF;
        if (BT21.param[2 * p] != BT21.param[2 * q] || BT21.param[2 * p + 1] != BT21.param[2 * q + 1]) return 0;
    }
    return 1;
}
static void cls_init(void) {
    if (BT21.len >= (1 << 16)) abort();
    cls_walk(0, 0);
    for (int c = 0; c < NCLASS; c++) if (CLS_N[c] > 4) { if (BIG0 < 0) BIG0 = c; else if (BIG1 < 0) BIG1 = c; else BIG1 = -2; }
    if (BIG0 < 0 || BIG1 < 0) { BIG1 = -1; return; }
    if (CLS_N[BIG0] != CLS_N[BIG1]) { BIG1 = -1; return; }
    for (int i = 0; i < (int)BT21.len; i++) PARTNER[i] = -1;
    int na = 0, la[1 << 13], lb[1 << 13], nb = 0;
    for (int i = 0; i < (int)BT21.len; i++) {
        if (!LEAF_IS[i]) continue;
        if (LEAF_CLS[i] == BIG0 && na < (1 << 13)) la[na++] = i;
        else if (LEAF_CLS[i] == BIG1 && nb < (1 << 13)) lb[nb++] = i;
    }
    if (na != CLS_N[BIG0] || nb != CLS_N[BIG1]) { BIG1 = -1; return; }
    static uint8_t used[1 << 13];
    for (int x = 0; x < na; x++) {
        int y; for (y = 0; y < nb; y++) if (!used[y] && same_box(la[x], lb[y])) break;
        if (y == nb) { BIG1 = -1; return; }        /* no pairing: separate searches */
        used[y] = 1; PARTNER[la[x]] = lb[y];
    }
}
// filtered search: the traversal of leaf_search, distance over the five depth free values, leaves of class c only.
// Returns the first leaf in tree order with least dist5 among class c leaves with dist5 < *ds (or best), *ds updated.
static int csearch(const uint64_t np[6], int idx, int best, uint64_t *ds, int depth, int c) {
    if (BT21.steps[depth] == 0) {
        if (LEAF_CLS[idx] != c) return best;
        uint64_t d = dist5(np, idx);
        if (d < *ds) { *ds = d; return idx; }
        return best;
    }
    uint32_t step;
    do { step = BT21.steps[depth]; depth++; } while (idx + step >= BT21.len);
    int inner = BT21.nodes[idx] >> 48;
    for (int i = 0; i < BT21.order; i++) {
        if (may_hold(inner, c) && dist5(np, inner) < *ds) best = csearch(np, inner, best, ds, depth, c);
        inner += step;
        if (inner >= (int)BT21.len) break;
    }
    return best;
}
// same, also exploring subtrees whose bound equals the best so far, and setting *tie if a second leaf reaches the minimum
static int csearch_tie(const uint64_t np[6], int idx, int best, uint64_t *ds, int depth, int c, int *tie) {
    if (BT21.steps[depth] == 0) {
        if (LEAF_CLS[idx] != c) return best;
        uint64_t d = dist5(np, idx);
        if (d < *ds) { *ds = d; *tie = 0; return idx; }
        if (d == *ds && best >= 0) *tie = 1;
        return best;
    }
    uint32_t step;
    do { step = BT21.steps[depth]; depth++; } while (idx + step >= BT21.len);
    int inner = BT21.nodes[idx] >> 48;
    for (int i = 0; i < BT21.order; i++) {
        if (may_hold(inner, c) && dist5(np, inner) <= *ds) best = csearch_tie(np, inner, best, ds, depth, c, tie);
        inner += step;
        if (inner >= (int)BT21.len) break;
    }
    return best;
}
static int column_set_ref(const Generator *g, int qx, int qz, int *out);
static int column_set(const Generator *g, int qx, int qz, int *out) {
#ifdef DISCEXACT_REFERENCE
    return column_set_ref(g, qx, qz, out);
#endif
    if (COL_REF) return column_set_ref(g, qx, qz, out);
    pthread_once(&CLS_ONCE, cls_init);
    int64_t np[6]; uint8_t seen[256] = {0};
#if DX_VERSION == 263
    float off = c263_column(c263_of(g), qx, qz, np);
#else
    double off = fast_np_column(g, &FC_TLS, np, qx, qz);
#endif
    const uint64_t *u = (const uint64_t *)np;
    int win[NCLS]; uint64_t cst[NCLS];
    int paired = 0;
    if (BIG1 >= 0) {                     /* Lemma 26b: a unique minimum in one class gives the other class's winner */
        uint64_t ds = (uint64_t)-1; int tie = 0;
        int w = csearch_tie(u, 0, -1, &ds, 0, BIG0, &tie);
        win[BIG0] = w; cst[BIG0] = ds;
        if (!tie) { win[BIG1] = PARTNER[w]; cst[BIG1] = ds; paired = 1; }
    }
    for (int c = 0; c < NCLASS; c++) {
        if (BIG1 >= 0 && (c == BIG0 || (c == BIG1 && paired))) continue;
        win[c] = -1; cst[c] = (uint64_t)-1;
        if (CLS_N[c] <= 4) {
            for (int q = 0; q < CLS_N[c]; q++) { uint64_t d = dist5(u, CLS_LEAF[c][q]); if (d < cst[c]) { cst[c] = d; win[c] = CLS_LEAF[c][q]; } }
        } else {
            uint64_t ds = (uint64_t)-1; win[c] = csearch(u, 0, -1, &ds, 0, c); cst[c] = ds;
        }
    }
    for (int y = FC_QY_MIN; y <= FC_QY_MAX; y++) {
#if DX_VERSION == 263
        int64_t x = c263_depth_at(off, y); int bw = -1; uint64_t bc = 0;
#else
        int64_t x = fast_depth_at(off, y); int bw = -1; uint64_t bc = 0;
#endif
        for (int c = 0; c < NCLASS; c++) {
            if (win[c] < 0) continue;
            uint64_t t = cst[c] + gdepth(x, c);
            if (bw < 0 || t < bc || (t == bc && LEAF_POS[win[c]] < LEAF_POS[bw])) { bw = win[c]; bc = t; }
        }
        seen[(BT21.nodes[bw] >> 48) & 0xFF] = 1;
    }
    int n = 0; for (int b = 0; b < 256; b++) if (seen[b]) out[n++] = b;
    return n;
}
// Reference: every layer, Cubiomes' own functions (no fast path, no class split).
static int column_set_ref(const Generator *g, int qx, int qz, int *out) {
    uint8_t seen[256] = {0}; int64_t np[6];
    for (int y = FC_QY_MIN; y <= FC_QY_MAX; y++) {
#if DX_VERSION == 263
        c263_sample6(c263_of(g), qx, y, qz, np);          // the game's point path (Climate.Sampler.sample)
#else
        sampleBiomeNoise(&g->bn, np, qx, y, qz, NULL, SAMPLE_NO_BIOME);
#endif
        seen[climateToBiome(g->mc, (const uint64_t *)np, NULL) & 0xFF] = 1;
    }
    int n = 0; for (int b = 0; b < 256; b++) if (seen[b]) out[n++] = b;
    return n;
}

// ---- geometry -----------------------------------------------------------------------------------------------
// interval of s where P0 + s*u lies in the axis-aligned rectangle [xa,xb] x [za,zb]; returns 0 if empty
static int slab(double px, double pz, double ux, double uz, double xa, double xb, double za, double zb, double *lo, double *hi) {
    double l = -1e300, h = 1e300;
    if (fabs(ux) < 1e-12) { if (px < xa || px > xb) return 0; }
    else { double t1 = (xa - px) / ux, t2 = (xb - px) / ux; if (t1 > t2) { double t = t1; t1 = t2; t2 = t; } if (t1 > l) l = t1; if (t2 < h) h = t2; }
    if (fabs(uz) < 1e-12) { if (pz < za || pz > zb) return 0; }
    else { double t1 = (za - pz) / uz, t2 = (zb - pz) / uz; if (t1 > t2) { double t = t1; t1 = t2; t2 = t; } if (t1 > l) l = t1; if (t2 < h) h = t2; }
    if (l > h) return 0;
    *lo = l; *hi = h; return 1;
}

static int disc(double px, double pz, double ux, double uz, double cx, double cz, double r, double *lo, double *hi) {
    double dx = px - cx, dz = pz - cz;
    double b = dx * ux + dz * uz, c = dx * dx + dz * dz - r * r, disc_ = b * b - c;
    if (disc_ < 0) return 0;
    double q = sqrt(disc_); *lo = -b - q; *hi = -b + q; return 1;
}

// first and last s (any sign) with dist(L(s), Q) <= r; Q = [x0,x1] x [z0,z1]. returns 0 if the line never gets that close
static int line_interval(double px, double pz, double ux, double uz, double x0, double x1, double z0, double z1, double r, double *lo, double *hi) {
    double l = 1e300, h = -1e300, a, b; int any = 0;
    if (slab(px, pz, ux, uz, x0 - r, x1 + r, z0, z1, &a, &b)) { any = 1; if (a < l) l = a; if (b > h) h = b; }
    if (r > 0) {
        if (slab(px, pz, ux, uz, x0, x1, z0 - r, z1 + r, &a, &b)) { any = 1; if (a < l) l = a; if (b > h) h = b; }
        double cx[2] = {x0, x1}, cz[2] = {z0, z1};
        for (int i = 0; i < 2; i++) for (int j = 0; j < 2; j++)
            if (disc(px, pz, ux, uz, cx[i], cz[j], r, &a, &b)) { any = 1; if (a < l) l = a; if (b > h) h = b; }
    } else {
        if (slab(px, pz, ux, uz, x0, x1, z0, z1, &a, &b)) { any = 1; if (a < l) l = a; if (b > h) h = b; }
    }
    if (!any) return 0;
    *lo = l; *hi = h; return 1;
}

static double rho_to(double px, double pz, double x0, double x1, double z0, double z1) {
    double dx = fmax(fmax(x0 - px, 0.0), px - x1), dz = fmax(fmax(z0 - pz, 0.0), pz - z1);
    return sqrt(dx * dx + dz * dz);
}

// D for radius r (or -1 if undiscovered within the cap). rho rule first, then path + r.
static double cell_D(double px, double pz, double ux, double uz, double x0, double x1, double z0, double z1, double r, double cap) {
    double rho = rho_to(px, pz, x0, x1, z0, z1);
    if (rho <= r) return rho <= cap ? rho : -1.0;
    double lo, hi;
    if (!line_interval(px, pz, ux, uz, x0, x1, z0, z1, r, &lo, &hi)) return -1.0;
    if (hi < 0) return -1.0;
    double s = lo > 0 ? lo : 0.0;
    double D = s + r;
    return D <= cap ? D : -1.0;
}

// ---- one ray --------------------------------------------------------------------------------------------------
typedef void (*emit_fn)(void *ctx, int qx, int qz, int biome, const double *D);

// Enumerate the cells within the active radii (+ margin) of the sub-segment [sa, sb] of the ray, keep those whose centre
// projection t_c = <c - p, u> lies in [tlo, thi), and emit their D (computed from the ray's own origin and the full cap,
// so values are identical to a single full scan). act[i] = 0 marks a radius that is no longer needed (D[i] = -1).
static void scan_core(const Generator *g, double px, double pz, double ux, double uz, double sa, double sb, double tlo,
                      double thi, const double *radii, const int *act, int nr, long rmax, emit_fn emit, void *ctx) {
    double rr = -1;
    for (int i = 0; i < nr; i++) if (act[i] && radii[i] > rr) rr = radii[i];
    if (rr < 0) return;
    double m = rr + 6.0;
    double ax = px + sa * ux, az = pz + sa * uz, ex = px + sb * ux, ez = pz + sb * uz;
    int qxa = (int)floor((fmin(ax, ex) - m) / 4.0), qxb = (int)floor((fmax(ax, ex) + m) / 4.0);
    double zbl = fmin(az, ez) - m, zbh = fmax(az, ez) + m;
    for (int qx = qxa; qx <= qxb; qx++) {
        double zl = zbl, zh = zbh;
        if (fabs(ux) > 1e-9) {
            double lo = 1e300, hi = -1e300;
            for (int e = 0; e < 2; e++) {
                double x = 4.0 * qx - 0.5 + 4.0 * e;
                double c1 = pz + ((x - px) * uz - m) / ux, c2 = pz + ((x - px) * uz + m) / ux;
                lo = fmin(lo, fmin(c1, c2)); hi = fmax(hi, fmax(c1, c2));
            }
            if (lo > zl) zl = lo;
            if (hi < zh) zh = hi;
        }
        int qza = (int)floor(zl / 4.0), qzb = (int)floor(zh / 4.0);
        for (int qz = qza; qz <= qzb; qz++) {
            double x0 = 4.0 * qx - 0.5, x1 = x0 + 4.0, z0 = 4.0 * qz - 0.5, z1 = z0 + 4.0;   // block i spans [i-0.5, i+0.5]: cells tile the plane
            double tc = (x0 + 2.0 - px) * ux + (z0 + 2.0 - pz) * uz;
            if (tc < tlo || tc >= thi) continue;
            double D[MAXR]; int any = 0;
            for (int i = 0; i < nr; i++) {
                D[i] = act[i] ? cell_D(px, pz, ux, uz, x0, x1, z0, z1, radii[i], (double)rmax) : -1.0;
                if (D[i] >= 0) any = 1;
            }
            if (!any) continue;
            if (!LAYERS_ALL) { emit(ctx, qx, qz, surface_only(g, qx, qz), D); continue; }
            int bs[256], nb = column_set(g, qx, qz, bs);
            for (int q = 0; q < nb; q++) emit(ctx, qx, qz, bs[q], D);
        }
    }
}

static void scan_ray(const Generator *g, double px, double pz, double ang, const double *radii, int nr, long rmax, emit_fn emit, void *ctx) {
    int act[MAXR]; for (int i = 0; i < MAXR; i++) act[i] = 1;
    scan_core(g, px, pz, cos(ang), sin(ang), 0.0, (double)rmax, -1e300, 1e300, radii, act, nr, rmax, emit, ctx);
}

typedef struct { int nr; int fm[NLEV][MAXR][256]; double dm[MAXR][256]; } Acc;

static void emit_min(void *ctx, int qx, int qz, int biome, const double *D) {
    Acc *a = (Acc *)ctx;
    if (biome < 0 || biome >= 256) return;
    for (int l = 0; l < NLEV; l++) {
        int k = LEVELS[l];
        if ((((qx % k) + k) % k) || (((qz % k) + k) % k)) continue;
        for (int i = 0; i < a->nr; i++) {
            if (D[i] < 0) continue;
            int di = (int)floor(D[i] + 0.5);
            if (a->fm[l][i][biome] < 0 || di < a->fm[l][i][biome]) a->fm[l][i][biome] = di;
            if (l == 0 && (a->dm[i][biome] < 0 || D[i] < a->dm[i][biome])) a->dm[i][biome] = D[i];
        }
    }
}

static int NSTOP = 0, STOPSET[256];   /* early stop set (THEORY.md 8.7); 0 = full scan to the cap */
#define SEG 1024.0
#define REACH_BIOME 256                /* row marker: dist = reach, every biome row with dist <= reach is exact */
static long ORIGIN_L = 0;          /* 0: spawn (estimateSpawn). L > 0: uniform cell-centre start in [-L, L]^2 */

/* Start point. The uniform start uses its own splitmix stream of the seed, independent of the angle stream. */
static Pos start_of(Generator *g, uint64_t seed) {
#if DX_VERSION == 263
    if (ORIGIN_L <= 0) { Pos p; c263_spawn(c263_of(g), &p.x, &p.z); return p; }   // NoiseSpawnFinder, bit-exact
#else
    if (ORIGIN_L <= 0) return estimateSpawn(g, NULL);
#endif
    uint64_t st = seed ^ 0x9E3779B97F4A7C15ULL ^ 0x5851F42D4C957F2DULL;
    uint64_t w = 2 * (uint64_t)ORIGIN_L + 1;
    Pos p; p.x = (int)((long)(splitmix64(&st) % w) - ORIGIN_L); p.z = (int)((long)(splitmix64(&st) % w) - ORIGIN_L);
    return p;
}

static void *worker(void *arg) {
    Job *j = (Job *)arg;
    Generator g; setupGenerator(&g, DX_MCV, 0);
    for (long i = j->tid; i < j->seeds; i += j->nth) {
        uint64_t st = j->seed0 + (uint64_t)i;
        uint64_t seed = splitmix64(&st);
        uint64_t ust = seed ^ 0xD1B54A32D192ED03ULL;
        double u = (double)(splitmix64(&ust) >> 11) / 9007199254740992.0;
        applySeed(&g, 0, seed);
        Pos sp = start_of(&g, seed);
        char *buf = NULL; size_t len = 0, cap = 0; char line[160];
        for (int k = 0; k < j->rays; k++) {
            double ang = 2.0 * M_PI * ((double)k + u) / (double)j->rays;
            Acc a; a.nr = j->nr;
            memset(a.fm, 0xff, sizeof a.fm);
            for (int r = 0; r < MAXR; r++) for (int b = 0; b < 256; b++) a.dm[r][b] = -1.0;
            double reach[MAXR];
            if (!NSTOP) {
                scan_ray(&g, (double)sp.x, (double)sp.z, ang, j->radii, j->nr, j->rmax, emit_min, &a);
                for (int r = 0; r < j->nr; r++) reach[r] = (double)j->rmax;
            } else {
                // Segments of the ray by centre projection. Lemma (THEORY.md 8.7): an unscanned cell with t_c >= T has
                // D >= T - 2*sqrt(2) > T - 3, so a radius is finished once T - 3 >= cap or every stop set biome has
                // min D <= T - 3. Its rows are then exactly those of the full scan for every biome with D <= T - 3.
                double ux = cos(ang), uz = sin(ang);
                int act[MAXR], nact = j->nr;
                for (int r = 0; r < MAXR; r++) act[r] = r < j->nr;
                for (int r = 0; r < j->nr; r++) reach[r] = (double)j->rmax;
                for (long sg = 0; nact > 0; sg++) {
                    double T = SEG * (double)(sg + 1);
                    double sa = fmax(0.0, SEG * (double)sg - 8.0), sb = fmin((double)j->rmax, T + 8.0);
                    if (sb < sa) sb = sa;
                    scan_core(&g, (double)sp.x, (double)sp.z, ux, uz, sa, sb, sg == 0 ? -1e300 : SEG * (double)sg, T,
                              j->radii, act, j->nr, j->rmax, emit_min, &a);
                    for (int r = 0; r < j->nr; r++) {
                        if (!act[r]) continue;
                        int done = T - 3.0 >= (double)j->rmax;
                        if (!done) {
                            done = 1;
                            for (int q = 0; q < NSTOP && done; q++) {
                                double d = a.dm[r][STOPSET[q]];
                                if (d < 0 || d > T - 3.0) done = 0;
                            }
                        }
                        if (done) { act[r] = 0; nact--; reach[r] = fmin(T - 3.0, (double)j->rmax); }
                    }
                }
            }
            for (int r = 0; r < j->nr && NSTOP; r++) {
                int n = snprintf(line, sizeof line, "%lld,%d,%.17g,%d,%ld,%d,%d\n", (long long)(int64_t)seed, k, ang, REACH_BIOME,
                                 (long)floor(reach[r]), (int)j->radii[r], 1);
                append(&buf, &len, &cap, line, (size_t)n);
            }
            for (int l = 0; l < (NSTOP ? 1 : NLEV); l++)
                for (int r = 0; r < j->nr; r++)
                    for (int b = 0; b < 256; b++)
                        if (a.fm[l][r][b] >= 0) {
                            int n = snprintf(line, sizeof line, "%lld,%d,%.17g,%d,%d,%d,%d\n", (long long)(int64_t)seed, k, ang, b,
                                             a.fm[l][r][b], (int)j->radii[r], LEVELS[l]);
                            append(&buf, &len, &cap, line, (size_t)n);
                        }
        }
        j->out[i].s = buf; j->out[i].n = len;
    }
    return NULL;
}

static void emit_print(void *ctx, int qx, int qz, int biome, const double *D) {
    int nr = *(int *)ctx;
    printf("%d,%d,%d", qx, qz, biome);
    for (int i = 0; i < nr; i++) printf(",%.6f", D[i]);
    printf("\n");
}

static int bad(const char *m) { fprintf(stderr, "discexact: %s\n", m); return 2; }

int main(int argc, char **argv) {
    long seeds = 100, rmax = 20000; int rays = 4, threads = 1, nr = 0; uint64_t seed0 = 1; const char *out = NULL, *rs = "0,64,128";
    double radii[MAXR]; long dbg_i = -1; int dbg_k = 0;
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
        else if (!strcmp(a, "--stopset")) {
            char t2[2048]; strncpy(t2, v, sizeof t2 - 1); t2[sizeof t2 - 1] = 0; NSTOP = 0;
            for (char *tok = strtok(t2, ","); tok; tok = strtok(NULL, ",")) {
                int b = atoi(tok); if (b < 0 || b > 255 || NSTOP >= 256) return bad("--stopset biome ids 0..255"); STOPSET[NSTOP++] = b;
            }
            if (!NSTOP) return bad("--stopset empty");
        }
        else if (!strcmp(a, "--origin")) { if (!strcmp(v, "spawn")) ORIGIN_L = 0; else if (sscanf(v, "uniform:%ld", &ORIGIN_L) != 1 || ORIGIN_L < 1 || ORIGIN_L > 20000000) return bad("--origin spawn|uniform:L"); }
        else if (!strcmp(a, "--layers")) { if (!strcmp(v, "surface")) LAYERS_ALL = 0; else if (!strcmp(v, "all")) LAYERS_ALL = 1; else return bad("--layers surface|all"); }
        else if (!strcmp(a, "--column-check")) {      /* n random cells per seed: fast bisection vs every layer */
            long n = atol(v); Generator g; setupGenerator(&g, DX_MCV, 0); long bad_ = 0, tot = 0;
            for (long s = 0; s < seeds; s++) {
                uint64_t st = seed0 + (uint64_t)s, seed = splitmix64(&st); applySeed(&g, 0, seed);
                for (long c = 0; c < n; c++) {
                    int qx = (int)(splitmix64(&st) % 2000001) - 1000000, qz = (int)(splitmix64(&st) % 2000001) - 1000000;
                    if (c % 4 == 1) { qx = (int)(splitmix64(&st) % 4001) - 2000; qz = (int)(splitmix64(&st) % 4001) - 2000; }
                    int A[256], B[256], na = column_set(&g, qx, qz, A), nb = column_set_ref(&g, qx, qz, B);
                    tot++; if (na != nb || memcmp(A, B, sizeof(int) * (size_t)na)) bad_++;
                }
            }
            printf("%ld %ld\n", tot, bad_); return bad_ != 0;
        }
        else if (!strcmp(a, "--debug")) { if (sscanf(v, "%ld,%d", &dbg_i, &dbg_k) != 2) return bad("--debug i,ray"); }
        else return bad("unknown option");
    }
    if (!out && dbg_i < 0) return bad("need --out");
    if (seeds < 1 || rays < 1 || rmax < 0) return bad("bad seeds/rays/rmax");
    if (threads < 1) threads = 1;
    char tmp[256]; strncpy(tmp, rs, sizeof tmp - 1); tmp[sizeof tmp - 1] = 0;
    if (!*tmp) return bad("no radii");
    char *save = tmp;
    for (;;) {
        char *comma = strchr(save, ','); if (comma) *comma = 0;
        char *end; double r = strtod(save, &end);
        if (!*save || *end || r < 0 || nr >= MAXR) return bad("radii must be non-negative numbers (max 6)");
        radii[nr++] = r;
        if (!comma) break;
        save = comma + 1;
    }
    if (dbg_i >= 0) {
        COL_REF = 1;
        uint64_t st = seed0 + (uint64_t)dbg_i, seed = splitmix64(&st);
        uint64_t ust = seed ^ 0xD1B54A32D192ED03ULL; double u = (double)(splitmix64(&ust) >> 11) / 9007199254740992.0;
        Generator g; setupGenerator(&g, DX_MCV, 0); applySeed(&g, 0, seed);
        Pos sp = start_of(&g, seed);
        double ang = 2.0 * M_PI * ((double)dbg_k + u) / (double)rays;
        printf("# %d %d %.17g\n", sp.x, sp.z, ang);
        scan_ray(&g, (double)sp.x, (double)sp.z, ang, radii, nr, rmax, emit_print, &nr);
        return 0;
    }
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
    fputs("seed,ray,angle,biome,dist,mode,level\n", f);
    for (long i = 0; i < seeds; i++) { if (o[i].s) fwrite(o[i].s, 1, o[i].n, f); free(o[i].s); }
    fclose(f);
    if (rename(t1, out)) return bad("rename failed");
    return 0;
}
