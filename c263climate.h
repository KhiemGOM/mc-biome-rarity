// c263climate.h: bit-exact port of the Minecraft 26.3 overworld climate (Climate.Sampler.sample, point path) and of
// NoiseSpawnFinder, read from the 26.3 server jar (gamecheck/Climate_26.3.md, gamecheck/NoiseSpawnFinder_26.3.md).
// 26.3 evaluates the density functions and Perlin noise in float; every float operation below mirrors the game's
// order. Build with -ffp-contract=off -fno-fast-math (x86-64 SSE; no x87).
//
//   C263 c; c263_init(&c, seed);
//   int64_t np[6]; c263_sample6(&c, qx, qy, qz, np);      // = Climate.Sampler.sample(qx, qy, qz): t, h, c, e, d, w
//   int x, z; c263_spawn(&c, &x, &z);                      // = NoiseSpawnFinder.findSpawnPosition (block x, z)
#ifndef C263CLIMATE_H_
#define C263CLIMATE_H_

#if defined(__FP_FAST_FMA) && !defined(C263_ALLOW_FMA)
// contraction would change results; the build passes -ffp-contract=off, which keeps fma out of the code below
#endif
#if defined(__i386__) && !defined(__SSE2_MATH__)
#error "c263climate.h needs SSE floating point (x87 excess precision would break bit-exactness)"
#endif

#include <math.h>
#include <stdint.h>
#include <string.h>

#include "c263data.h"

// ---------------------------------------------------------------- Xoroshiro128++ (XoroshiroRandomSource)
typedef struct { uint64_t lo, hi; } C263Rng;
static inline uint64_t c263_rotl(uint64_t x, int k) { return (x << k) | (x >> (64 - k)); }
static inline uint64_t c263_mix13(uint64_t z) {
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}
static inline void c263_rng_seed(C263Rng *r, uint64_t seed) {        // RandomSupport.upgradeSeedTo128bit
    uint64_t l = seed ^ 0x6a09e667f3bcc909ULL, h = l + 0x9e3779b97f4a7c15ULL;
    r->lo = c263_mix13(l); r->hi = c263_mix13(h);
}
static inline uint64_t c263_next_long(C263Rng *r) {
    uint64_t l = r->lo, h = r->hi, n = c263_rotl(l + h, 17) + l;
    h ^= l; r->lo = c263_rotl(l, 49) ^ h ^ (h << 21); r->hi = c263_rotl(h, 28);
    return n;
}
static inline int c263_next_int(C263Rng *r, uint32_t n) {           // XoroshiroRandomSource.nextInt(bound), Lemire
    uint64_t m = (c263_next_long(r) & 0xFFFFFFFFULL) * n;
    if ((uint32_t)m < n) {
        while ((uint32_t)m < (~n + 1) % n) m = (c263_next_long(r) & 0xFFFFFFFFULL) * n;
    }
    return (int)(m >> 32);
}
static inline double c263_next_double(C263Rng *r) { return (double)(c263_next_long(r) >> 11) * 1.1102230246251565E-16; }
typedef struct { uint64_t lo, hi; } C263Pos;                        // XoroshiroPositionalRandomFactory
static inline C263Pos c263_fork(C263Rng *r) { C263Pos p; p.lo = c263_next_long(r); p.hi = c263_next_long(r); return p; }
static inline C263Rng c263_from_hash(C263Pos p, const uint64_t md5[2]) { C263Rng r; r.lo = md5[0] ^ p.lo; r.hi = md5[1] ^ p.hi; return r; }

// ---------------------------------------------------------------- Perlin (GradientNoise / PerlinNoise, float)
typedef struct { uint8_t p[256]; double ox, oy, oz; } C263Perlin;
static inline void c263_perlin_init(C263Perlin *n, C263Rng *r) {
    n->ox = c263_next_double(r) * 256.0;
    n->oy = c263_next_double(r) * 256.0;
    n->oz = c263_next_double(r) * 256.0;
    for (int i = 0; i < 256; i++) n->p[i] = (uint8_t)i;
    for (int i = 0; i < 256; i++) {
        int j = c263_next_int(r, (uint32_t)(256 - i));
        uint8_t t = n->p[i]; n->p[i] = n->p[i + j]; n->p[i + j] = t;
    }
}
static const signed char C263_GRAD[16][3] = {{1,1,0},{-1,1,0},{1,-1,0},{-1,-1,0},{1,0,1},{-1,0,1},{1,0,-1},{-1,0,-1},
                                             {0,1,1},{0,-1,1},{0,1,-1},{0,-1,-1},{1,1,0},{0,-1,1},{-1,1,0},{0,-1,-1}};
static inline float c263_grad(int h, float x, float y, float z) {      // Gradient.dot(FFF): (gx*x + gy*y) + gz*z
    const signed char *g = C263_GRAD[h & 15];
    return (float)g[0] * x + (float)g[1] * y + (float)g[2] * z;
}
static inline float c263_lerp(float t, float a, float b) { return a + t * (b - a); }
static inline float c263_smooth(float t) { return t * t * t * (t * (t * 6.0f - 15.0f) + 10.0f); }
static inline double c263_wrap(double x) {
    const double HALF = 16777215.999999998;                           // Math.nextDown(2^24)
    if (x >= -HALF && x < HALF) return x;
    return x - floor(x / 33554432.0 + 0.5) * 33554432.0;
}
static inline float c263_perlin(const C263Perlin *n, double x, double y, double z) {
    double X = c263_wrap(x) + n->ox, Y = c263_wrap(y) + n->oy, Z = c263_wrap(z) + n->oz;
    int ix = (int)floor(X), iy = (int)floor(Y), iz = (int)floor(Z);
    float fx = (float)(X - ix), fy = (float)(Y - iy), fz = (float)(Z - iz);
    const uint8_t *p = n->p;
    int a = p[ix & 255], b = p[(ix + 1) & 255];
    int aa = p[(a + iy) & 255], ab = p[(a + iy + 1) & 255], ba = p[(b + iy) & 255], bb = p[(b + iy + 1) & 255];
    float v000 = c263_grad(p[(aa + iz) & 255], fx, fy, fz);
    float v100 = c263_grad(p[(ba + iz) & 255], fx - 1.0f, fy, fz);
    float v010 = c263_grad(p[(ab + iz) & 255], fx, fy - 1.0f, fz);
    float v110 = c263_grad(p[(bb + iz) & 255], fx - 1.0f, fy - 1.0f, fz);
    float v001 = c263_grad(p[(aa + iz + 1) & 255], fx, fy, fz - 1.0f);
    float v101 = c263_grad(p[(ba + iz + 1) & 255], fx - 1.0f, fy, fz - 1.0f);
    float v011 = c263_grad(p[(ab + iz + 1) & 255], fx, fy - 1.0f, fz - 1.0f);
    float v111 = c263_grad(p[(bb + iz + 1) & 255], fx - 1.0f, fy - 1.0f, fz - 1.0f);
    float sx = c263_smooth(fx), sy = c263_smooth(fy), sz = c263_smooth(fz);
    float a0 = c263_lerp(sy, c263_lerp(sx, v000, v100), c263_lerp(sx, v010, v110));   // lerp2
    float a1 = c263_lerp(sy, c263_lerp(sx, v001, v101), c263_lerp(sx, v011, v111));
    return c263_lerp(sz, a0, a1);
}

// ---------------------------------------------------------------- NormalNoise -> NoiseStack (layers A0,B0,A1,B1,...)
typedef struct { int n; C263Perlin per[2 * C263_MAX_OCT]; double freq[2 * C263_MAX_OCT]; float amp[2 * C263_MAX_OCT]; } C263Noise;
static inline float c263_f32(uint32_t b) { float f; memcpy(&f, &b, 4); return f; }
static inline void c263_noise_init(C263Noise *no, C263Pos world, const uint64_t id_md5[2], int count, const int *oct,
                                   const uint32_t *amp, const uint64_t (*octmd5)[2]) {
    C263Rng r = c263_from_hash(world, id_md5);                       // RandomState: random.fromHashOf("minecraft:<noise>")
    C263Pos A = c263_fork(&r), B = c263_fork(&r);                   // NormalNoise.create: two forkPositional, in order
    no->n = 2 * count;
    for (int i = 0; i < count; i++) {
        C263Rng ra = c263_from_hash(A, octmd5[i]), rb = c263_from_hash(B, octmd5[i]);   // fromHashOf("octave_<k>")
        c263_perlin_init(&no->per[2 * i], &ra);
        c263_perlin_init(&no->per[2 * i + 1], &rb);
        double f = ldexp(1.0, oct[i]);
        no->freq[2 * i] = f; no->freq[2 * i + 1] = f * 1.0181268882175227;
        no->amp[2 * i] = no->amp[2 * i + 1] = c263_f32(amp[i]);
    }
}
static inline float c263_noise(const C263Noise *no, double x, double y, double z) {   // NoiseStack.get(DDD)
    float v = 0.0f;
    for (int i = 0; i < no->n; i++) {
        double f = no->freq[i];
        v = v + no->amp[i] * c263_perlin(&no->per[i], x * f, y * f, z * f);
    }
    return v;
}

// ---------------------------------------------------------------- overworld climate
enum { C263_T, C263_H, C263_C, C263_E, C263_W, C263_OFF };            // noise slots: temperature, vegetation, continentalness, erosion, ridge, offset
typedef struct { uint64_t seed; C263Noise no[6]; } C263;

static inline void c263_init(C263 *c, uint64_t seed) {
    C263Rng r; c263_rng_seed(&r, seed);                              // WorldgenRandom.Algorithm.XOROSHIRO.newInstance(seed)
    C263Pos world = c263_fork(&r);                                   // .forkPositional()
    c->seed = seed;
    c263_noise_init(&c->no[0], world, C263_N0_MD5, C263_N0_COUNT, C263_N0_OCT, C263_N0_AMP, C263_N0_OCTMD5);
    c263_noise_init(&c->no[1], world, C263_N1_MD5, C263_N1_COUNT, C263_N1_OCT, C263_N1_AMP, C263_N1_OCTMD5);
    c263_noise_init(&c->no[2], world, C263_N2_MD5, C263_N2_COUNT, C263_N2_OCT, C263_N2_AMP, C263_N2_OCTMD5);
    c263_noise_init(&c->no[3], world, C263_N3_MD5, C263_N3_COUNT, C263_N3_OCT, C263_N3_AMP, C263_N3_OCTMD5);
    c263_noise_init(&c->no[4], world, C263_N4_MD5, C263_N4_COUNT, C263_N4_OCT, C263_N4_AMP, C263_N4_OCTMD5);
    c263_noise_init(&c->no[5], world, C263_N5_MD5, C263_N5_COUNT, C263_N5_OCT, C263_N5_AMP, C263_N5_OCTMD5);
}

// shift_x / shift_z at block (x, y, z): ShiftA = offset.get(x*0.25, y*0.0, z*0.25) * 4f; ShiftB = offset.get(z*0.25, x*0.25, 0) * 4f
static inline float c263_shift_x(const C263 *c, int x, int y, int z) { return c263_noise(&c->no[C263_OFF], (double)x * 0.25, (double)y * 0.0, (double)z * 0.25) * 4.0f; }
static inline float c263_shift_z(const C263 *c, int x, int y, int z) { (void)y; return c263_noise(&c->no[C263_OFF], (double)z * 0.25, (double)x * 0.25, 0.0) * 4.0f; }
// a shifted climate noise (NoiseFunction.ShiftedXzSampler, xz_scale 0.25, y_scale 0) given the two shifts
static inline float c263_climate_noise(const C263 *c, int k, int x, int y, int z, float sx, float sz) {
    double px = (double)x * 0.25 + (double)sx, py = (double)y * 0.0, pz = (double)z * 0.25 + (double)sz;
    return c263_noise(&c->no[k], px, py, pz);
}
static inline float c263_ridges_folded(float w) {                    // mul(add(abs(add(abs(w), -0.6666667)), -0.33333334), -3)
    return (fabsf(fabsf(w) + -0.6666667f) + -0.33333334f) * -3.0f;
}
static inline float c263_spline(int node, const float *in) {          // CubicSpline.Multipoint.sample
    int s = C263_SP_START[node], n = C263_SP_LEN[node];
    float f = in[C263_SP_COORD[node]];
    // findIntervalStart: (first k with f < loc[k]) - 1
    int lo = 0, len = n;
    while (len > 0) { int half = len / 2, mid = lo + half; if (f < c263_f32(C263_SP_LOC[s + mid])) len = half; else { lo = mid + 1; len -= half + 1; } }
    int i = lo - 1, last = n - 1;
#define C263_SPV(j) (C263_SP_KIND[s + (j)] ? c263_spline(C263_SP_IDX[s + (j)], in) : c263_f32(C263_SP_CONST[C263_SP_IDX[s + (j)]]))
    if (i < 0) {
        float v = C263_SPV(0), d = c263_f32(C263_SP_DER[s]);
        return d == 0.0f ? v : v + d * (f - c263_f32(C263_SP_LOC[s]));
    }
    if (i == last) {
        float v = C263_SPV(last), d = c263_f32(C263_SP_DER[s + last]);
        return d == 0.0f ? v : v + d * (f - c263_f32(C263_SP_LOC[s + last]));
    }
    float l0 = c263_f32(C263_SP_LOC[s + i]), l1 = c263_f32(C263_SP_LOC[s + i + 1]);
    float k = (f - l0) / (l1 - l0);
    float d0 = c263_f32(C263_SP_DER[s + i]), d1 = c263_f32(C263_SP_DER[s + i + 1]);
    float v0 = C263_SPV(i), v1 = C263_SPV(i + 1);
    float p = d0 * (l1 - l0) - (v1 - v0);
    float q = -d1 * (l1 - l0) + (v1 - v0);
    return c263_lerp(k, v0, v1) + k * (1.0f - k) * c263_lerp(k, p, q);
#undef C263_SPV
}
static inline float c263_gradient_y(int y) {                         // GradientFunction, axis y, -64 -> 1.5, 320 -> -1.5, clamped
    int yc = y < -64 ? -64 : (y > 320 ? 320 : y);
    return 1.5f + (float)(yc - (-64)) * -0.0078125f;
}
// all six climate floats at block (x, y, z), in Climate.Sampler order t, h, c, e, d, w
static inline void c263_floats(const C263 *c, int x, int y, int z, float out[6]) {
    float sx = c263_shift_x(c, x, y, z), sz = c263_shift_z(c, x, y, z);
    float t = c263_climate_noise(c, C263_T, x, y, z, sx, sz);
    float h = c263_climate_noise(c, C263_H, x, y, z, sx, sz);
    float cc = c263_climate_noise(c, C263_C, x, y, z, sx, sz);
    float e = c263_climate_noise(c, C263_E, x, y, z, sx, sz);
    float w = c263_climate_noise(c, C263_W, x, y, z, sx, sz);
    float in[4] = {cc, e, c263_ridges_folded(w), w};
    float off = c263_spline(0, in) + -0.50375f;                      // ConstAddSampler; blend_alpha = 1 -> lerp returns second
    float d = c263_gradient_y(y) + off;                              // AddSampler
    out[0] = t; out[1] = h; out[2] = cc; out[3] = e; out[4] = d; out[5] = w;
}
static inline int64_t c263_quantize(float f) { return (int64_t)(f * 10000.0f); }   // Climate.quantizeCoord
static inline void c263_sample6(const C263 *c, int qx, int qy, int qz, int64_t np[6]) {
    float v[6]; c263_floats(c, qx * 4, qy * 4, qz * 4, v);
    for (int i = 0; i < 6; i++) np[i] = c263_quantize(v[i]);
}

// Column at quart (qx, qz): t, h, c, e, w do not depend on y (every climate noise and both shifts sample y * 0.0),
// so np[0..3,5] hold for all 96 layers; the depth of layer qy is c263_depth_at(off, qy). np[4] is left 0.
// c263_sample6(qx, qy, qz) == this column with np[4] = c263_depth_at(off, qy), bit for bit (tests/test_c263.py).
static inline float c263_column(const C263 *c, int qx, int qz, int64_t np[6]) {
    int x = qx * 4, z = qz * 4;
    float sx = c263_shift_x(c, x, 0, z), sz = c263_shift_z(c, x, 0, z);
    float t = c263_climate_noise(c, C263_T, x, 0, z, sx, sz);
    float h = c263_climate_noise(c, C263_H, x, 0, z, sx, sz);
    float cc = c263_climate_noise(c, C263_C, x, 0, z, sx, sz);
    float e = c263_climate_noise(c, C263_E, x, 0, z, sx, sz);
    float w = c263_climate_noise(c, C263_W, x, 0, z, sx, sz);
    float in[4] = {cc, e, c263_ridges_folded(w), w};
    np[0] = c263_quantize(t); np[1] = c263_quantize(h); np[2] = c263_quantize(cc); np[3] = c263_quantize(e); np[4] = 0; np[5] = c263_quantize(w);
    return c263_spline(0, in) + -0.50375f;
}
static inline int64_t c263_depth_at(float off, int qy) { return c263_quantize(c263_gradient_y(qy * 4) + off); }

// ---------------------------------------------------------------- NoiseSpawnFinder (point path)
static inline int64_t c263_pdist(int64_t v, int64_t mn, int64_t mx) { int64_t a = v - mx, b = mn - v; return a > 0 ? a : (b > 0 ? b : 0); }
static inline int64_t c263_spawn_fitness(const C263 *c, int x, int z) {
    int qx = (x >> 2) << 2, qz = (z >> 2) << 2;                       // QuartPos.toBlock(fromBlock(x)), block y = 0
    float sx = c263_shift_x(c, qx, 0, qz), sz = c263_shift_z(c, qx, 0, qz);
    int64_t t = c263_quantize(c263_climate_noise(c, C263_T, qx, 0, qz, sx, sz));
    int64_t h = c263_quantize(c263_climate_noise(c, C263_H, qx, 0, qz, sx, sz));
    int64_t cc = c263_quantize(c263_climate_noise(c, C263_C, qx, 0, qz, sx, sz));
    int64_t e = c263_quantize(c263_climate_noise(c, C263_E, qx, 0, qz, sx, sz));
    int64_t w = c263_quantize(c263_climate_noise(c, C263_W, qx, 0, qz, sx, sz));
    int64_t common = 0, d;
    d = c263_pdist(t, -10000, 10000); common += d * d;
    d = c263_pdist(h, -10000, 10000); common += d * d;
    d = c263_pdist(e, -10000, 10000); common += d * d;
    d = c263_pdist(cc, -1100, 10000); common += d * d;
    int64_t d0 = c263_pdist(w, -10000, -1600), d1 = c263_pdist(w, 1600, 10000);
    int64_t f0 = common + d0 * d0, f1 = common + d1 * d1;
    int64_t best = f0 < f1 ? f0 : f1;
    int64_t xl = x, zl = z;
    return (int64_t)((uint64_t)best * (uint64_t)(2048LL * 2048LL) + (uint64_t)(xl * xl + zl * zl));   // long arithmetic, wraps like Java
}
// radialSearch(maxRadius, step): the angle/radius sequence (float angle += step / radius, ring reset when
// (double)angle > 2*pi) does not depend on the seed, so its integer offsets (int)(Math.sin(angle) * radius) and
// (int)(Math.cos(angle) * radius) are tabulated from the game's JVM (C263_SPAWN_DX/DZ, gamecheck/SinCos.java).
// The centre is the best point at the start of the pass; strict < keeps the first best.
static inline void c263_radial(const C263 *c, int *bx, int *bz, int64_t *bf, int from, int count) {
    int cx = *bx, cz = *bz;
    for (int i = from; i < from + count; i++) {
        int x = cx + C263_SPAWN_DX[i], z = cz + C263_SPAWN_DZ[i];
        int64_t f = c263_spawn_fitness(c, x, z);
        if (f < *bf) { *bf = f; *bx = x; *bz = z; }
    }
}
static inline void c263_spawn(const C263 *c, int *x, int *z) {
    int bx = 0, bz = 0; int64_t bf = c263_spawn_fitness(c, 0, 0);
    c263_radial(c, &bx, &bz, &bf, 0, C263_SPAWN_P1);
    c263_radial(c, &bx, &bz, &bf, C263_SPAWN_P1, C263_SPAWN_P2);
    *x = bx; *z = bz;
}

#endif
