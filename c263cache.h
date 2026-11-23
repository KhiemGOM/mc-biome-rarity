// c263cache.h: the same 26.3 climate as c263climate.h with a lattice cache. Bit-identical to c263_column / c263_sample6
// (tests/test_c263.py, gamecheck/c263cachecheck.c): the permutation chain of a Perlin sample depends only on the low
// 8 bits of its lattice corner (ix, iy, iz), so the 8 gradient indices are cached per (layer, call site) and reused
// while the corner stays the same; every floating point operation is unchanged.
#ifndef C263CACHE_H_
#define C263CACHE_H_

#include "c263climate.h"

typedef struct { uint32_t key; uint8_t g[8]; } C263CEnt;            // key = (ix & 255) | (iy & 255) << 8 | (iz & 255) << 16 | 1 << 24
#define C263C_SETS 7                                                 // 0..4 the climate noises, 5 shift_x, 6 shift_z (offset noise)
typedef struct { const C263 *c; uint64_t seed; C263CEnt e[C263C_SETS][2 * C263_MAX_OCT]; } C263Cache;

static inline void c263c_bind(C263Cache *k, const C263 *c) {
    if (k->c == c && k->seed == c->seed) return;
    memset(k->e, 0, sizeof k->e);                                    // key 0 is never valid (bit 24 set in every key)
    k->c = c; k->seed = c->seed;
}
static inline float c263c_perlin(const C263Perlin *n, C263CEnt *e, double x, double y, double z) {
    double X = c263_wrap(x) + n->ox, Y = c263_wrap(y) + n->oy, Z = c263_wrap(z) + n->oz;
    int ix = (int)floor(X), iy = (int)floor(Y), iz = (int)floor(Z);
    float fx = (float)(X - ix), fy = (float)(Y - iy), fz = (float)(Z - iz);
    uint32_t key = (uint32_t)(ix & 255) | (uint32_t)(iy & 255) << 8 | (uint32_t)(iz & 255) << 16 | 1u << 24;
    if (e->key != key) {
        const uint8_t *p = n->p;
        int a = p[ix & 255], b = p[(ix + 1) & 255];
        int aa = p[(a + iy) & 255], ab = p[(a + iy + 1) & 255], ba = p[(b + iy) & 255], bb = p[(b + iy + 1) & 255];
        e->g[0] = p[(aa + iz) & 255]; e->g[1] = p[(ba + iz) & 255]; e->g[2] = p[(ab + iz) & 255]; e->g[3] = p[(bb + iz) & 255];
        e->g[4] = p[(aa + iz + 1) & 255]; e->g[5] = p[(ba + iz + 1) & 255]; e->g[6] = p[(ab + iz + 1) & 255]; e->g[7] = p[(bb + iz + 1) & 255];
        e->key = key;
    }
    const uint8_t *g = e->g;
    float v000 = c263_grad(g[0], fx, fy, fz);
    float v100 = c263_grad(g[1], fx - 1.0f, fy, fz);
    float v010 = c263_grad(g[2], fx, fy - 1.0f, fz);
    float v110 = c263_grad(g[3], fx - 1.0f, fy - 1.0f, fz);
    float v001 = c263_grad(g[4], fx, fy, fz - 1.0f);
    float v101 = c263_grad(g[5], fx - 1.0f, fy, fz - 1.0f);
    float v011 = c263_grad(g[6], fx, fy - 1.0f, fz - 1.0f);
    float v111 = c263_grad(g[7], fx - 1.0f, fy - 1.0f, fz - 1.0f);
    float sx = c263_smooth(fx), sy = c263_smooth(fy), sz = c263_smooth(fz);
    float a0 = c263_lerp(sy, c263_lerp(sx, v000, v100), c263_lerp(sx, v010, v110));
    float a1 = c263_lerp(sy, c263_lerp(sx, v001, v101), c263_lerp(sx, v011, v111));
    return c263_lerp(sz, a0, a1);
}
static inline float c263c_noise(const C263Noise *no, C263CEnt *es, double x, double y, double z) {
    float v = 0.0f;
    for (int i = 0; i < no->n; i++) {
        double f = no->freq[i];
        v = v + no->amp[i] * c263c_perlin(&no->per[i], &es[i], x * f, y * f, z * f);
    }
    return v;
}
static inline float c263c_climate_noise(const C263 *c, C263Cache *k, int n, int x, int y, int z, float sx, float sz) {
    double px = (double)x * 0.25 + (double)sx, py = (double)y * 0.0, pz = (double)z * 0.25 + (double)sz;
    return c263c_noise(&c->no[n], k->e[n], px, py, pz);
}
// = c263_column (np[0..3,5] and the returned spline offset), bit for bit
static inline float c263c_column(const C263 *c, C263Cache *k, int qx, int qz, int64_t np[6]) {
    c263c_bind(k, c);
    int x = qx * 4, z = qz * 4;
    float sx = c263c_noise(&c->no[C263_OFF], k->e[5], (double)x * 0.25, (double)0 * 0.0, (double)z * 0.25) * 4.0f;
    float sz = c263c_noise(&c->no[C263_OFF], k->e[6], (double)z * 0.25, (double)x * 0.25, 0.0) * 4.0f;
    float t = c263c_climate_noise(c, k, C263_T, x, 0, z, sx, sz);
    float h = c263c_climate_noise(c, k, C263_H, x, 0, z, sx, sz);
    float cc = c263c_climate_noise(c, k, C263_C, x, 0, z, sx, sz);
    float e = c263c_climate_noise(c, k, C263_E, x, 0, z, sx, sz);
    float w = c263c_climate_noise(c, k, C263_W, x, 0, z, sx, sz);
    float in[4] = {cc, e, c263_ridges_folded(w), w};
    np[0] = c263_quantize(t); np[1] = c263_quantize(h); np[2] = c263_quantize(cc); np[3] = c263_quantize(e); np[4] = 0; np[5] = c263_quantize(w);
    return c263_spline(0, in) + -0.50375f;
}
// = c263_sample6, bit for bit
static inline void c263c_sample6(const C263 *c, C263Cache *k, int qx, int qy, int qz, int64_t np[6]) {
    float off = c263c_column(c, k, qx, qz, np);
    np[4] = c263_depth_at(off, qy);
}

#endif
