// gamecheck: compare the Cubiomes fork (MC_26_3) with values printed by the real game (GameCheck.java), THEORY.md 0.
// stdin lines (one per check, whitespace separated, biome names without the "minecraft:" prefix):
//   N seed qx qy qz t h c e d w biome   the game's climate target point at quart cell (qx,qy,qz) and its biome
//   T t h c e d w biome                 a random target point and the biome the game's parameter list returns
//   S seed x z                          the game's climate spawn position (findSpawnPosition, before the surface search)
// Prints one summary line per kind: "<kind> checked <n> np_mismatch <a> biome_mismatch <b>" and the first few failures.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>
#include "generator.h"
#include "finders.h"
#include "util.h"

#define MCV MC_26_3
static int name2id(const char *s) {
    for (int i = 0; i < 256; i++) { const char *n = biome2str(MCV, i); if (n && !strcmp(n, s)) return i; }
    return -1;
}
int main(void) {
    char line[512], kind[4], bname[128];
    long nN = 0, nT = 0, nS = 0, npbad = 0, bbadN = 0, bbadT = 0, sbad = 0, shown = 0;
    Generator g; setupGenerator(&g, MCV, 0); int64_t cur = 0; int have = 0;
    while (fgets(line, sizeof line, stdin)) {
        if (sscanf(line, "%3s", kind) != 1) continue;
        if (kind[0] == 'N') {
            int64_t seed, v[6]; int qx, qy, qz;
            if (sscanf(line, "N %" SCNd64 " %d %d %d %" SCNd64 " %" SCNd64 " %" SCNd64 " %" SCNd64 " %" SCNd64 " %" SCNd64 " %127s",
                       &seed, &qx, &qy, &qz, &v[0], &v[1], &v[2], &v[3], &v[4], &v[5], bname) != 11) { fprintf(stderr, "bad: %s", line); return 2; }
            if (!have || seed != cur) { applySeed(&g, DIM_OVERWORLD, (uint64_t)seed); cur = seed; have = 1; }
            int64_t np[6]; sampleBiomeNoise(&g.bn, np, qx, qy, qz, NULL, SAMPLE_NO_BIOME);
            int bad = 0; for (int i = 0; i < 6; i++) bad |= np[i] != v[i];
            int ours = climateToBiome(MCV, (const uint64_t *)np, NULL), game = name2id(bname);
            npbad += bad; bbadN += ours != game; nN++;
            if ((bad || ours != game) && shown++ < 10)
                printf("N fail seed %" PRId64 " (%d,%d,%d): ours %s game %s np_diff %d\n", seed, qx, qy, qz, biome2str(MCV, ours), bname, bad);
        } else if (kind[0] == 'T') {
            int64_t v[6];
            if (sscanf(line, "T %" SCNd64 " %" SCNd64 " %" SCNd64 " %" SCNd64 " %" SCNd64 " %" SCNd64 " %127s",
                       &v[0], &v[1], &v[2], &v[3], &v[4], &v[5], bname) != 7) { fprintf(stderr, "bad: %s", line); return 2; }
            int ours = climateToBiome(MCV, (const uint64_t *)v, NULL), game = name2id(bname);
            bbadT += ours != game; nT++;
            if (ours != game && shown++ < 10)
                printf("T fail %" PRId64 " %" PRId64 " %" PRId64 " %" PRId64 " %" PRId64 " %" PRId64 ": ours %s game %s\n",
                       v[0], v[1], v[2], v[3], v[4], v[5], biome2str(MCV, ours), bname);
        } else if (kind[0] == 'S') {
            int64_t seed; int x, z;
            if (sscanf(line, "S %" SCNd64 " %d %d", &seed, &x, &z) != 3) { fprintf(stderr, "bad: %s", line); return 2; }
            applySeed(&g, DIM_OVERWORLD, (uint64_t)seed); cur = seed; have = 1;
            Pos p = estimateSpawn(&g, NULL);
            sbad += p.x != x || p.z != z; nS++;
            if ((p.x != x || p.z != z) && shown++ < 10)
                printf("S fail seed %" PRId64 ": ours (%d,%d) game (%d,%d)\n", seed, p.x, p.z, x, z);
        }
    }
    printf("N checked %ld np_mismatch %ld biome_mismatch %ld\n", nN, npbad, bbadN);
    printf("T checked %ld biome_mismatch %ld\n", nT, bbadT);
    printf("S checked %ld spawn_mismatch %ld\n", nS, sbad);
    return (npbad || bbadN || bbadT || sbad) ? 1 : 0;
}
