// c263world.h: one world view for the simulators. For MC_26_3 the climate and the spawn come from c263climate.h (the
// bit-exact port of the game); the biome is the fork's btree263 lookup on that climate, hint-free (climateToBiome
// with NULL), the same tie rule as before. Any other version keeps the plain Cubiomes path.
#ifndef C263WORLD_H_
#define C263WORLD_H_

#include "biomes.h"
#include "biomenoise.h"
#include "finders.h"
#include "generator.h"
#include "c263climate.h"

typedef struct { Generator g; C263 c; int is263; } World;

static inline void world_setup(World *w, int mc) { setupGenerator(&w->g, mc, 0); w->is263 = mc == MC_26_3; }
static inline void world_seed(World *w, uint64_t seed) {
    applySeed(&w->g, DIM_OVERWORLD, seed);
    if (w->is263) c263_init(&w->c, seed);
}
static inline Pos world_spawn(World *w) {
    if (w->is263) { Pos p; c263_spawn(&w->c, &p.x, &p.z); return p; }
    return estimateSpawn(&w->g, NULL);
}
// the six quantized climate values at quart (qx, qy, qz): Climate.Sampler.sample for 26.3, sampleBiomeNoise otherwise
static inline void world_np(const World *w, int qx, int qy, int qz, int64_t np[6]) {
    if (w->is263) c263_sample6(&w->c, qx, qy, qz, np);
    else sampleBiomeNoise(&w->g.bn, np, qx, qy, qz, NULL, SAMPLE_NO_BIOME);
}
// biome at quart (qx, qy, qz) (getBiomeAt(g, 4, ...) for other versions)
static inline int world_biome(const World *w, int qx, int qy, int qz) {
    if (w->is263) { int64_t np[6]; c263_sample6(&w->c, qx, qy, qz, np); return climateToBiome(MC_26_3, (const uint64_t *)np, NULL); }
    return getBiomeAt(&w->g, 4, qx, qy, qz);
}

#endif
