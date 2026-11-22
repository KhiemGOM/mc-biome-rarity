// gamecheck: compare our 26.3 model with values printed by the real game (GameCheck.java), THEORY.md 0.
// Climate and spawn: c263climate.h (our bit-exact port). Biome: the fork's btree263 lookup, hint-free.
// stdin lines (one per check, whitespace separated, biome names without the "minecraft:" prefix):
//   N seed qx qy qz t h c e d w biome   the game's climate target point (point path) at quart cell (qx,qy,qz) and its biome
//   V seed qx qy qz t h c e d w biome   the same from the real chunk path (createResolverForChunk, volume sampling)
//   T t h c e d w biome                 a random target point and the biome the game's parameter list returns
//   S seed x z                          the game's NoiseSpawnFinder result
// Prints per kind "<kind> checked <n> np_mismatch <a> biome_mismatch <b> exact_ties <t>" (a biome mismatch with equal
// climate is checked for an exact distance tie by brute force over the parameter table), the tie rate, the tie pairs,
// and the first few failures. Exit status 0 iff np_mismatch = 0, spawn_mismatch = 0 and every biome mismatch is a tie.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>
#include "generator.h"
#include "finders.h"
#include "util.h"
#include "tables/btree263.h"
#include "../c263climate.h"

#define MCV MC_26_3
#define NP (sizeof(btree263_param) / sizeof(btree263_param[0]))
static int name2id(const char *s) {
    for (int i = 0; i < 256; i++) { const char *n = biome2str(MCV, i); if (n && !strcmp(n, s)) return i; }
    return -1;
}
// leaves of the fork's tree (same traversal as its search); the biome of a leaf is node >> 48
static const int TLEN = sizeof(btree263_nodes) / sizeof(uint64_t);
static uint8_t IS_LEAF[1 << 16];
static void mark(int idx, int depth) {
    if (btree263_steps[depth] == 0) { IS_LEAF[idx] = 1; return; }
    uint32_t step;
    do { step = btree263_steps[depth]; depth++; } while (idx + step >= (uint32_t)TLEN);
    int inner = btree263_nodes[idx] >> 48;
    for (int i = 0; i < btree263_order; i++) { mark(inner, depth); inner += step; if (inner >= TLEN) break; }
}
// least distance over the leaves of biome b
static uint64_t mindist(const int64_t np[6], int b) {
    uint64_t best = (uint64_t)-1;
    for (int i = 0; i < TLEN; i++) {
        if (!IS_LEAF[i]) continue;
        uint64_t node = btree263_nodes[i];
        if ((int)((node >> 48) & 0xFF) != b) continue;
        uint64_t ds = 0;
        for (int k = 0; k < 6; k++) {
            int idx = (node >> 8 * k) & 0xFF;
            int64_t a = np[k] - btree263_param[idx][1], c = btree263_param[idx][0] - np[k];
            int64_t d = a > 0 ? a : (c > 0 ? c : 0);
            ds += (uint64_t)(d * d);
        }
        if (ds < best) best = ds;
    }
    return best;
}
typedef struct { long n, npbad, bbad, ties; } Stat;
static long pairs[256][256];
int main(void) {
    char line[512], kind[4], bname[128];
    Stat sN = {0}, sV = {0}, sT = {0}; long nS = 0, sbad = 0, shown = 0;
    C263 c; int64_t cur = 0; int have = 0;
    mark(0, 0);
    while (fgets(line, sizeof line, stdin)) {
        if (sscanf(line, "%3s", kind) != 1) continue;
        if (kind[0] == 'N' || kind[0] == 'V') {
            Stat *st = kind[0] == 'N' ? &sN : &sV;
            int64_t seed, v[6]; int qx, qy, qz;
            if (sscanf(line + 1, " %" SCNd64 " %d %d %d %" SCNd64 " %" SCNd64 " %" SCNd64 " %" SCNd64 " %" SCNd64 " %" SCNd64 " %127s",
                       &seed, &qx, &qy, &qz, &v[0], &v[1], &v[2], &v[3], &v[4], &v[5], bname) != 11) { fprintf(stderr, "bad: %s", line); return 2; }
            if (!have || seed != cur) { c263_init(&c, (uint64_t)seed); cur = seed; have = 1; }
            int64_t np[6]; c263_sample6(&c, qx, qy, qz, np);
            int bad = 0; for (int i = 0; i < 6; i++) bad |= np[i] != v[i];
            int ours = climateToBiome(MCV, (const uint64_t *)np, NULL), game = name2id(bname);
            st->n++; st->npbad += bad;
            if (ours != game) {
                st->bbad++;
                if (!bad) {
                    // exact tie: our pick and the game's pick have the same distance (the fork's search returns a
                    // least distance leaf, so the game's biome must reach that distance too)
                    uint64_t dgame = mindist(np, game), dours = mindist(np, ours);
                    if (dgame == dours) { st->ties++; if (ours >= 0 && game >= 0) pairs[ours][game]++; }
                }
            }
            if ((bad || ours != game) && shown++ < 10)
                printf("%c fail seed %" PRId64 " (%d,%d,%d): ours %s game %s np_diff %d\n", kind[0], seed, qx, qy, qz, biome2str(MCV, ours), bname, bad);
        } else if (kind[0] == 'T') {
            int64_t v[6];
            if (sscanf(line, "T %" SCNd64 " %" SCNd64 " %" SCNd64 " %" SCNd64 " %" SCNd64 " %" SCNd64 " %127s",
                       &v[0], &v[1], &v[2], &v[3], &v[4], &v[5], bname) != 7) { fprintf(stderr, "bad: %s", line); return 2; }
            int ours = climateToBiome(MCV, (const uint64_t *)v, NULL), game = name2id(bname);
            sT.n++;
            if (ours != game) {
                sT.bbad++;
                uint64_t dgame = mindist(v, game), dours = mindist(v, ours);
                if (dgame == dours) { sT.ties++; if (ours >= 0 && game >= 0) pairs[ours][game]++; }
                if (shown++ < 10) printf("T fail %" PRId64 " %" PRId64 " %" PRId64 " %" PRId64 " %" PRId64 " %" PRId64 ": ours %s game %s\n",
                                         v[0], v[1], v[2], v[3], v[4], v[5], biome2str(MCV, ours), bname);
            }
        } else if (kind[0] == 'S') {
            int64_t seed; int x, z;
            if (sscanf(line, "S %" SCNd64 " %d %d", &seed, &x, &z) != 3) { fprintf(stderr, "bad: %s", line); return 2; }
            c263_init(&c, (uint64_t)seed); cur = seed; have = 1;
            int px, pz; c263_spawn(&c, &px, &pz);
            sbad += px != x || pz != z; nS++;
            if ((px != x || pz != z) && shown++ < 10)
                printf("S fail seed %" PRId64 ": ours (%d,%d) game (%d,%d)\n", seed, px, pz, x, z);
        }
    }
    printf("N checked %ld np_mismatch %ld biome_mismatch %ld exact_ties %ld tie_rate %.3g\n", sN.n, sN.npbad, sN.bbad, sN.ties, sN.n ? (double)sN.ties / sN.n : 0.0);
    if (sV.n) printf("V checked %ld np_mismatch %ld biome_mismatch %ld exact_ties %ld tie_rate %.3g\n", sV.n, sV.npbad, sV.bbad, sV.ties, (double)sV.ties / sV.n);
    printf("T checked %ld biome_mismatch %ld exact_ties %ld\n", sT.n, sT.bbad, sT.ties);
    printf("S checked %ld spawn_mismatch %ld\n", nS, sbad);
    printf("tie pairs (ours vs game, all kinds):");
    for (int a = 0; a < 256; a++) for (int b = 0; b < 256; b++) if (pairs[a][b]) printf(" %s/%s %ld", biome2str(MCV, a), biome2str(MCV, b), pairs[a][b]);
    printf("\n");
    int ok = sN.npbad == 0 && sV.npbad == 0 && sN.bbad == sN.ties && sV.bbad == sV.ties && sT.bbad == sT.ties && sbad == 0;
    return ok ? 0 : 1;
}
