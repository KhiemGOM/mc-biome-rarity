# NoiseSpawnFinder in Minecraft 26.3 (the climate spawn search)

Read from the 26.3 server jar with `javap -c -p -constants` (classes `net.minecraft.world.level.levelgen.NoiseSpawnFinder`,
`SpawnTargetPoint`, `Climate`, `Climate.Parameter`, `QuartPos`, `Mth`). 26.3 no longer has
`Climate.Sampler.findSpawnPosition`. This search replaces it, and it is what `GameCheck.java` prints on its `S` lines.
The world spawn then gets a surface/safety step on top (`PlayerSpawnFinder`), which is not covered here.

## Inputs

- `targets = NoiseGeneratorSettings.spawnTarget()` for the overworld, a `List<SpawnTargetPoint>`. Each
  `SpawnTargetPoint` is a map {density function -> `Climate.Parameter`}. From `data/minecraft/worldgen/noise_settings/overworld.json`
  (`spawn_target`) and confirmed at runtime by `SpawnDump.java`, there are two target points. They differ only in ridges:

  | target | overworld/continents | overworld/erosion | overworld/ridges | overworld/temperature | overworld/vegetation |
  |---|---|---|---|---|---|
  | 0 | [-1100, 10000] | [-10000, 10000] | [-10000, -1600] | [-10000, 10000] | [-10000, 10000] |
  | 1 | [-1100, 10000] | [-10000, 10000] | [1600, 10000] | [-10000, 10000] | [-10000, 10000] |

  (Quantized longs, i.e. value x 10000. The JSON has [-0.11, 1.0], [-1, -0.16] / [0.16, 1].) Ridges is the
  weirdness function. Depth is not used. Temperature, vegetation (humidity) and erosion span the whole range, so their
  distance is always 0. In practice only continentalness and ridges matter.
- `samplers = RandomState.samplersWithContext(SamplerContext.EMPTY_UNCACHED)`, a `DensitySamplerSet`.
  `samplers.sampleValue(df, x, y, z)` evaluates density function `df` at block (x, y, z) and returns a **float**
  (point path, not the volume path).

## Fitness of a block position (static `getSpawnPositionAndFitness(samplers, targets, int x, int z)`)

```
int qx = QuartPos.toBlock(QuartPos.fromBlock(x));   // (x >> 2) << 2 : arithmetic shift, floors toward -inf
int qz = QuartPos.toBlock(QuartPos.fromBlock(z));
long best = Long.MAX_VALUE;                          // 9223372036854775807
for (SpawnTargetPoint t : targets)                   // list order: target 0 then 1
    best = Math.min(best, t.sampleFitness(samplers, qx, 0, qz));      // y = 0 (block y 0)
long dist2 = Mth.square((long) x) + Mth.square((long) z);           // UNSNAPPED x, z;  square(v) = v * v (long)
long fitness = best * Mth.square(2048L) + dist2;                    // best * 4194304 + x^2 + z^2   (long, wraps on overflow)
return Result(new BlockPos(x, 0, z), fitness);                      // location is the UNSNAPPED (x, 0, z)
```

`SpawnTargetPoint.sampleFitness(samplers, x, y, z)`:
```
long s = 0;
for (entry (df, param) : parameters)                 // Map iteration order; irrelevant, integer sum is exact
    long v = Climate.quantizeCoord(samplers.sampleValue(df, x, y, z));   // quantizeCoord(float f) = (long)(f * 10000.0f)  (float multiply, then f2l truncation toward 0)
    s += Mth.square(param.distance(v));
return s;
```
`Climate.Parameter.distance(long v)`: `a = v - max; b = min - v; return a > 0 ? a : Math.max(b, 0);` (long).

Notes:
- The climate is sampled at the snapped block (qx, 0, qz), which is quart (x>>2, 0, z>>2) at block y = 0. The distance
  penalty uses the raw x, z.
- `quantizeCoord` multiplies in **float** (`10000.0f`), not double.

## Search (constructor, then `findSpawnPosition` returns `result.location()`)

```
result = getSpawnPositionAndFitness(samplers, targets, 0, 0);
radialSearch(samplers, targets, 2048.0f, 512.0f);   // (maxRadius, step)
radialSearch(samplers, targets,  512.0f,  32.0f);
return result.location();
```

`radialSearch(samplers, targets, float maxRadius, float step)`:
```
float angle = 0.0f;
float radius = step;                                 // starts at step, not 0
BlockPos center = result.location();                 // read ONCE at entry; fixed for this whole pass
while (radius <= maxRadius) {                        // fcmpg; exits when radius > maxRadius (NaN would also exit)
    int x = center.getX() + (int) (Math.sin((double) angle) * (double) radius);   // sin of the float widened to double; product in double; d2i truncates toward 0
    int z = center.getZ() + (int) (Math.cos((double) angle) * (double) radius);   // note: x uses sin, z uses cos
    Result r = getSpawnPositionAndFitness(samplers, targets, x, z);
    if (r.fitness() < result.fitness()) result = r;  // strict <: on equal fitness the earlier result is kept
    angle += step / radius;                          // float division, float add
    if ((double) angle > 6.283185307179586) {        // compares the float widened to double against 2*pi (double)
        angle = 0.0f;
        radius += step;                              // float add
    }
}
```

Points of exactness:
1. `angle` and `radius` are floats. `step / radius` and `angle + ...` round to float each iteration. The angle
   sequence must be reproduced in float, then widened to double for `Math.sin`/`Math.cos` (Java's StrictMath-like
   `Math.sin`; C `sin` on glibc agrees to the last bit for these arguments in practice, but that is an assumption to test).
2. The ring test is `(double)angle > 2*pi` after the increment. The point with that angle has already been
   evaluated, and the reset happens after it. So each ring's last evaluated point has an angle up to just under 2*pi,
   and the next ring restarts at angle 0.
3. The centre of each pass is the best result at the start of that pass. Updates during the pass do not move the centre.
4. Ties: strict `<`. The first-found point wins (pass order, ring order, angle order).
5. Pass 1: rings r = 512, 1024, 1536, 2048 (4 rings) around (0,0). Pass 2: rings r = 32, 64, ..., 512 (16 rings)
   around pass 1's best. Angle step per ring = step / r, so pass 1 has about 2*pi*r/512 points per ring.
6. The final spawn is a block position (not quart aligned), e.g. game (-77, 190) where the old model gave (-80, 176).
   That is the S mismatch we see (126/200, and 306/500 in spawn500).

`MAX_RADIUS = 2048L` is a static field. It is not used in the code above beyond the literal 2048 (`Mth.square(2048L)`
uses the constant `ldc2_w 2048`).
