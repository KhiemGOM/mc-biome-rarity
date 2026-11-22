// fastclimate.h: bit-exact fast path for the 1.18+ surface biome lookup used by discexact (surface_only).
//
// Same arithmetic as Cubiomes (pinned e61f905) sampleBiomeNoise(..., SAMPLE_NO_BIOME) + climateToBiome(hint-free);
// two changes that do not alter a single floating point operation:
//  1. lattice cache: the permutation-table chain of samplePerlin depends only on the lattice corner (h1, h2, h3)
//     of each octave. Neighbouring cells usually share it in every low-frequency octave, so the 8 gradient indices
//     are cached per (octave, call site) and the chain is only redone when the corner changes. The cache is tied
//     to (BiomeNoise address, world seed) and cleared on any change, so it can never serve another seed's table.
//  2. branchless gradient: indexedLerp's 16-way switch becomes two table-selected operands with +-1 signs.
//     s * x with s = +-1 is an exact negation, and the operand order matches every case (e.g. case 13: -b + c),
//     so each gradient value is bitwise identical, signed zeros included.
// Verified by tests/test_fastclimate.c (np values and biome ids) and tests/test_fastclimate.py (discexact bytes).
#ifndef FASTCLIMATE_H_
#define FASTCLIMATE_H_

#include <math.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include "biomenoise.h"
#include "generator.h"

#define FC_QY_REF 15
#define FC_QY_MIN (-16)
#define FC_QY_MAX 79
#define FC_NOCT (2 * 23)     // size of BiomeNoise.oct
#define FC_SETS 2            // call sites with different argument order: shift(x,0,z) and shift(z,x,0)

float getSpline(const Spline *sp, const float *vals);          // exported by biomenoise.c

typedef struct { uint8_t h1, h2, h3, valid; uint8_t g[8]; } FcEntry;
typedef struct {
    const BiomeNoise *bn; uint64_t seed; int bound;
    FcEntry e[FC_SETS][FC_NOCT];
} FastCache;

static inline void fast_cache_init(FastCache *fc) { memset(fc, 0, sizeof *fc); }

static inline void fast_cache_bind(FastCache *fc, const BiomeNoise *bn, uint64_t seed) {
    if (fc->bound && fc->bn == bn && fc->seed == seed) return;
    for (int k = 0; k < NP_MAX; k++) {                         // the cache is indexed by octave offset in bn->oct
        const OctaveNoise *o[2] = {&bn->climate[k].octA, &bn->climate[k].octB};
        for (int j = 0; j < 2; j++)
            if (o[j]->octcnt > 0 && (o[j]->octaves < bn->oct || o[j]->octaves + o[j]->octcnt > bn->oct + FC_NOCT)) abort();
    }
    memset(fc->e, 0, sizeof fc->e);
    fc->bn = bn; fc->seed = seed; fc->bound = 1;
}

// indexedLerp, case by case: (first operand, its sign, second operand, its sign); operands 0 = a, 1 = b, 2 = c
static const uint8_t FC_I1[16] = {0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 1, 0, 1};
static const uint8_t FC_I2[16] = {1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 1, 2};
static const double FC_S1[16] = {1, -1, 1, -1, 1, -1, 1, -1, 1, -1, 1, -1, 1, -1, -1, -1};
static const double FC_S2[16] = {1, 1, -1, -1, 1, 1, -1, -1, 1, 1, -1, -1, 1, 1, 1, -1};

static inline double fc_grad(uint8_t idx, double a, double b, double c) {
    const double v[3] = {a, b, c};
    idx &= 0xf;
    return FC_S1[idx] * v[FC_I1[idx]] + FC_S2[idx] * v[FC_I2[idx]];
}

static inline double fc_lerp(double part, double from, double to) { return from + part * (to - from); }

// samplePerlin(noise, d1, d2, d3, 0, 0), with the corner chain cached in e
static inline double fc_perlin(const PerlinNoise *noise, FcEntry *e, double d1, double d2, double d3) {
    uint8_t h1, h2, h3;
    double t1, t2, t3;
    if (d2 == 0.0) { d2 = noise->d2; h2 = noise->h2; t2 = noise->t2; }
    else {
        d2 += noise->b;
        double i2 = floor(d2);
        d2 -= i2;
        h2 = (int)i2;
        t2 = d2 * d2 * d2 * (d2 * (d2 * 6.0 - 15.0) + 10.0);
    }
    d1 += noise->a;
    d3 += noise->c;
    double i1 = floor(d1);
    double i3 = floor(d3);
    d1 -= i1;
    d3 -= i3;
    h1 = (int)i1;
    h3 = (int)i3;
    t1 = d1 * d1 * d1 * (d1 * (d1 * 6.0 - 15.0) + 10.0);
    t3 = d3 * d3 * d3 * (d3 * (d3 * 6.0 - 15.0) + 10.0);

    if (!(e->valid && e->h1 == h1 && e->h2 == h2 && e->h3 == h3)) {
        const uint8_t *idx = noise->d;
        uint8_t a1 = idx[h1] + h2, b1 = idx[h1 + 1] + h2;
        uint8_t a2 = idx[a1] + h3, b2 = idx[a1 + 1] + h3;      // v2 = {idx[v1.a], idx[v1.a+1]} + h3
        uint8_t a3 = idx[b1] + h3, b3 = idx[b1 + 1] + h3;      // v3 = {idx[v1.b], idx[v1.b+1]} + h3
        e->g[0] = idx[a2]; e->g[1] = idx[a2 + 1];              // v4
        e->g[2] = idx[b2]; e->g[3] = idx[b2 + 1];              // v5
        e->g[4] = idx[a3]; e->g[5] = idx[a3 + 1];              // v6
        e->g[6] = idx[b3]; e->g[7] = idx[b3 + 1];              // v7
        e->h1 = h1; e->h2 = h2; e->h3 = h3; e->valid = 1;
    }
    const uint8_t *g = e->g;
    double l1 = fc_grad(g[0], d1, d2, d3);
    double l5 = fc_grad(g[1], d1, d2, d3 - 1);
    double l2 = fc_grad(g[4], d1 - 1, d2, d3);
    double l6 = fc_grad(g[5], d1 - 1, d2, d3 - 1);
    double l3 = fc_grad(g[2], d1, d2 - 1, d3);
    double l7 = fc_grad(g[3], d1, d2 - 1, d3 - 1);
    double l4 = fc_grad(g[6], d1 - 1, d2 - 1, d3);
    double l8 = fc_grad(g[7], d1 - 1, d2 - 1, d3 - 1);

    l1 = fc_lerp(t1, l1, l2);
    l3 = fc_lerp(t1, l3, l4);
    l5 = fc_lerp(t1, l5, l6);
    l7 = fc_lerp(t1, l7, l8);
    l1 = fc_lerp(t2, l1, l3);
    l5 = fc_lerp(t2, l5, l7);
    return fc_lerp(t3, l1, l5);
}

static inline double fc_octave(const BiomeNoise *bn, const OctaveNoise *noise, FcEntry *es, double x, double y, double z) {
    double v = 0;
    for (int i = 0; i < noise->octcnt; i++) {
        const PerlinNoise *p = noise->octaves + i;
        double lf = p->lacunarity;
        double ax = maintainPrecision(x * lf);
        double ay = maintainPrecision(y * lf);
        double az = maintainPrecision(z * lf);
        double pv = fc_perlin(p, &es[p - bn->oct], ax, ay, az);
        v += p->amplitude * pv;
    }
    return v;
}

static inline double fc_double(const BiomeNoise *bn, const DoublePerlinNoise *noise, FcEntry *es, double x, double y, double z) {
    const double f = 337.0 / 331.0;
    double v = 0;
    v += fc_octave(bn, &noise->octA, es, x, y, z);
    v += fc_octave(bn, &noise->octB, es, x * f, y * f, z * f);
    return v * noise->amplitude;
}

// sampleBiomeNoise(bn, np, x, y, z, NULL, SAMPLE_NO_BIOME) for a full climate generator (nptype < 0), MC >= 1.18.
// The caller binds fc to (bn, seed) first; fast_surface does that itself.
static inline void fast_np_bound(const BiomeNoise *bn, FastCache *fc, int64_t *np, int x, int y, int z) {
    float t = 0, h = 0, c = 0, e = 0, d = 0, w = 0;
    double px = x, pz = z;
    px += fc_double(bn, &bn->climate[NP_SHIFT], fc->e[0], x, 0, z) * 4.0;
    pz += fc_double(bn, &bn->climate[NP_SHIFT], fc->e[1], z, x, 0) * 4.0;

    c = fc_double(bn, &bn->climate[NP_CONTINENTALNESS], fc->e[0], px, 0, pz);
    e = fc_double(bn, &bn->climate[NP_EROSION], fc->e[0], px, 0, pz);
    w = fc_double(bn, &bn->climate[NP_WEIRDNESS], fc->e[0], px, 0, pz);
    {
        float np_param[] = {c, e, -3.0F * (fabsf(fabsf(w) - 0.6666667F) - 0.33333334F), w};
        double off = getSpline(bn->sp, np_param) + 0.015F;
        d = 1.0 - (y * 4) / 128.0 - 83.0 / 160.0 + off;
    }
    t = fc_double(bn, &bn->climate[NP_TEMPERATURE], fc->e[0], px, 0, pz);
    h = fc_double(bn, &bn->climate[NP_HUMIDITY], fc->e[0], px, 0, pz);

    np[0] = (int64_t)(10000.0F * t);
    np[1] = (int64_t)(10000.0F * h);
    np[2] = (int64_t)(10000.0F * c);
    np[3] = (int64_t)(10000.0F * e);
    np[4] = (int64_t)(10000.0F * d);
    np[5] = (int64_t)(10000.0F * w);
}

// same, binding the cache itself; bn must be the bn member of a Generator (the seed is read from it)
static inline void fast_np(const BiomeNoise *bn, FastCache *fc, int64_t *np, int x, int y, int z) {
    const Generator *g = (const Generator *)((const char *)bn - offsetof(Generator, bn));
    fast_cache_bind(fc, bn, g->seed);
    fast_np_bound(bn, fc, np, x, y, z);
}

// discexact surface_only: climate at QY_REF, depth moved to the surface quart, then the hint-free tree search
static inline int fast_surface(const Generator *g, FastCache *fc, int qx, int qz) {
    int64_t np[6];
    fast_cache_bind(fc, &g->bn, g->seed);
    fast_np_bound(&g->bn, fc, np, qx, FC_QY_REF, qz);
    double dref = (double)np[4] / 10000.0;
    int qs = (int)floor(FC_QY_REF + 32.0 * dref + 0.5);
    if (qs < FC_QY_MIN) qs = FC_QY_MIN;
    if (qs > FC_QY_MAX) qs = FC_QY_MAX;
    float d = (float)(dref + (double)(FC_QY_REF - qs) / 32.0);
    np[4] = (int64_t)(10000.0F * d);
    return climateToBiome(g->mc, (const uint64_t *)np, NULL);
}

// Full column (all 96 quart layers, y = -16..79): the five depth-free climates and the spline offset `off`, so that the
// depth at quart y is exactly Cubiomes' float d = 1.0 - (y * 4) / 128.0 - 83.0 / 160.0 + off (sampleBiomeNoise).
// The other five values do not depend on y (Cubiomes samples them at y = 0), so np at layer y is this np with np[4]
// replaced by fast_depth_at(off, y).
static inline double fast_np_column(const Generator *g, FastCache *fc, int64_t *np, int x, int z) {
    const BiomeNoise *bn = &g->bn;
    fast_cache_bind(fc, bn, g->seed);
    float t = 0, h = 0, c = 0, e = 0, w = 0;
    double px = x, pz = z;
    px += fc_double(bn, &bn->climate[NP_SHIFT], fc->e[0], x, 0, z) * 4.0;
    pz += fc_double(bn, &bn->climate[NP_SHIFT], fc->e[1], z, x, 0) * 4.0;
    c = fc_double(bn, &bn->climate[NP_CONTINENTALNESS], fc->e[0], px, 0, pz);
    e = fc_double(bn, &bn->climate[NP_EROSION], fc->e[0], px, 0, pz);
    w = fc_double(bn, &bn->climate[NP_WEIRDNESS], fc->e[0], px, 0, pz);
    float np_param[] = {c, e, -3.0F * (fabsf(fabsf(w) - 0.6666667F) - 0.33333334F), w};
    double off = getSpline(bn->sp, np_param) + 0.015F;
    t = fc_double(bn, &bn->climate[NP_TEMPERATURE], fc->e[0], px, 0, pz);
    h = fc_double(bn, &bn->climate[NP_HUMIDITY], fc->e[0], px, 0, pz);
    np[0] = (int64_t)(10000.0F * t);
    np[1] = (int64_t)(10000.0F * h);
    np[2] = (int64_t)(10000.0F * c);
    np[3] = (int64_t)(10000.0F * e);
    np[4] = 0;
    np[5] = (int64_t)(10000.0F * w);
    return off;
}

static inline int64_t fast_depth_at(double off, int y) {
    float d = 1.0 - (y * 4) / 128.0 - 83.0 / 160.0 + off;
    return (int64_t)(10000.0F * d);
}

#endif
