// c263spawn: compare c263_spawn with the game's NoiseSpawnFinder ("S seed x z" lines from GameCheck / SpawnDump).
#include <stdio.h>
#include <inttypes.h>
#include "../c263climate.h"

int main(void) {
    char line[512]; long n = 0, bad = 0;
    while (fgets(line, sizeof line, stdin)) {
        int64_t seed; int x, z;
        if (sscanf(line, "S %" SCNd64 " %d %d", &seed, &x, &z) != 3) continue;
        C263 c; c263_init(&c, (uint64_t)seed);
        int mx, mz; c263_spawn(&c, &mx, &mz);
        n++;
        if (mx != x || mz != z) { bad++; if (bad <= 10) printf("S fail seed %" PRId64 ": ours (%d,%d) game (%d,%d)\n", seed, mx, mz, x, z); }
    }
    printf("S checked %ld spawn_mismatch %ld\n", n, bad);
    return bad != 0;
}
