// c263ties.h: the exact tie set of the biome lookup. For a climate point p the game returns SOME leaf of the argmin set
// T(p) = { leaves of least distance } (its R-tree search keeps a per-thread hint only when the hint ties the best),
// so its biome is one of the biomes of T(p); our hint-free lookup is one fixed member. This header finds the least
// distance with a pruned search of the fork's tree and then collects every leaf at that distance (pruning only boxes
// strictly farther), so the biome set is exact (checked against brute force over all leaves, gamecheck/gamecheck.c).
#ifndef C263TIES_H_
#define C263TIES_H_

#include <stdint.h>
#include <string.h>

typedef struct { const uint32_t *steps; const int32_t *param; const uint64_t *nodes; int order; int len; } TTree;
typedef struct { uint64_t m[4]; } BSet;                                 // a set of biome ids 0..255

static inline void bset_clear(BSet *s) { memset(s, 0, sizeof *s); }
static inline void bset_add(BSet *s, int b) { s->m[(b >> 6) & 3] |= 1ULL << (b & 63); }
static inline int bset_has(const BSet *s, int b) { return (int)((s->m[(b >> 6) & 3] >> (b & 63)) & 1); }
static inline int bset_count(const BSet *s) { return __builtin_popcountll(s->m[0]) + __builtin_popcountll(s->m[1]) + __builtin_popcountll(s->m[2]) + __builtin_popcountll(s->m[3]); }
static inline void bset_union(BSet *a, const BSet *b) { for (int i = 0; i < 4; i++) a->m[i] |= b->m[i]; }
static inline int bset_single(const BSet *s) {                          // the only member, or -1
    if (bset_count(s) != 1) return -1;
    for (int i = 0; i < 4; i++) if (s->m[i]) return i * 64 + __builtin_ctzll(s->m[i]);
    return -1;
}

// same distance as the fork's get_np_dist (unsigned arithmetic)
static inline uint64_t tt_dist(const TTree *t, const int64_t np[6], int idx) {
    uint64_t ds = 0, node = t->nodes[idx];
    for (int i = 0; i < 6; i++) {
        int k = (node >> 8 * i) & 0xFF;
        uint64_t a = (uint64_t)np[i] - (uint64_t)(int64_t)t->param[2 * k + 1], b = (uint64_t)(int64_t)t->param[2 * k + 0] - (uint64_t)np[i];
        uint64_t d = (int64_t)a > 0 ? a : (int64_t)b > 0 ? b : 0;
        ds += d * d;
    }
    return ds;
}
static void tt_min(const TTree *t, const int64_t np[6], int idx, int depth, uint64_t *best) {
    if (t->steps[depth] == 0) { uint64_t d = tt_dist(t, np, idx); if (d < *best) *best = d; return; }
    uint32_t step;
    do { step = t->steps[depth]; depth++; } while (idx + step >= (uint32_t)t->len);
    int inner = t->nodes[idx] >> 48;
    for (int i = 0; i < t->order; i++) {
        if (tt_dist(t, np, inner) < *best) tt_min(t, np, inner, depth, best);
        inner += step;
        if (inner >= t->len) break;
    }
}
static void tt_collect(const TTree *t, const int64_t np[6], int idx, int depth, uint64_t best, BSet *out, int *nleaf) {
    if (t->steps[depth] == 0) {
        if (tt_dist(t, np, idx) == best) { bset_add(out, (int)((t->nodes[idx] >> 48) & 0xFF)); (*nleaf)++; }
        return;
    }
    uint32_t step;
    do { step = t->steps[depth]; depth++; } while (idx + step >= (uint32_t)t->len);
    int inner = t->nodes[idx] >> 48;
    for (int i = 0; i < t->order; i++) {
        if (tt_dist(t, np, inner) <= best) tt_collect(t, np, inner, depth, best, out, nleaf);
        inner += step;
        if (inner >= t->len) break;
    }
}
// biomes of T(p); returns the least distance. *nleaf = number of leaves at that distance.
static inline uint64_t tt_tieset(const TTree *t, const int64_t np[6], BSet *out, int *nleaf) {
    uint64_t best = (uint64_t)-1;
    tt_min(t, np, 0, 0, &best);
    bset_clear(out); *nleaf = 0;
    tt_collect(t, np, 0, 0, best, out, nleaf);
    return best;
}

#endif
