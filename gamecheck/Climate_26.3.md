# How 26.3 computes the climate target point and the biome (read with javap from the 26.3 server jar)

Main finding: in 26.3 the density-function engine and Perlin noise were rewritten to work in **float**
(`DensitySampler.sampleValue(...)F`, `Noise.get(DDD)F`, `PerlinNoise.sampleAndLerp(IIIFFFF)F`). In 1.21.4 this was
double up to a single final cast. Off-by-one quantized climate values are what float evaluation produces, so a
bit-exact model has to follow the float order of operations below.

Second finding, important for what we check: **chunk biome generation does not use the point path.**
`MultiNoiseBiomeSource.createResolverForChunk(sampler, ...)` fills six `DensityBuffer`s with
`DensitySampler.Bound.sampleVolume(buffer, volume)` (volume path, 4x4x4 quart steps) and then looks up biomes from
those buffers. `GameCheck`'s `N` lines use `Climate.Sampler.sample(qx,qy,qz)` (point path, `sampleValue`). The
volume path has separate code (`sampleVolume`, `PerlinNoise.addToVolume`, `DensityBuffer`) and may round
differently. The spawn search uses the point path (`DensitySamplerSet.sampleValue`). **We should check the fork
against the volume path for biomes and the point path for spawn.** The next GameCheck step is to dump biomes through
`createResolverForChunk`.

## (a) Climate.Sampler.sample(int qx, int qy, int qz) -> TargetPoint (point path)

```
int x = QuartPos.toBlock(qx);   // qx << 2
int y = QuartPos.toBlock(qy);   // qy << 2   (block y, used by all six, but only depth depends on it)
int z = QuartPos.toBlock(qz);
float t = temperature.sampleValue(x, y, z);       // DensitySampler.Bound.sampleValue(III)F, each returns float
float h = humidity.sampleValue(x, y, z);          // "vegetation"
float c = continentalness.sampleValue(x, y, z);   // "continents"
float e = erosion.sampleValue(x, y, z);
float d = depth.sampleValue(x, y, z);
float w = weirdness.sampleValue(x, y, z);         // "ridges"
return Climate.target(t, h, c, e, d, w);
```
`Climate.target(float...)` = `new TargetPoint(quantizeCoord(t), ..., quantizeCoord(w))`.
`quantizeCoord(float f) = (long)(f * 10000.0f)` (float multiply, f2l, truncation toward zero, Java saturating).
The sampler comes from `RandomState.createClimateSampler(SamplerContext)` and is bound to the router functions below.

### Router (data/minecraft/worldgen/noise_settings/overworld.json + density_function/overworld/*.json)

| climate | router entry | definition |
|---|---|---|
| temperature | overworld/temperature | `noise(temperature, shift_x, shift_z, xz_scale 0.25, y_scale 0)` |
| humidity | overworld/vegetation | `noise(vegetation, shift_x, shift_z, 0.25, 0)` |
| continentalness | overworld/continents | `cache(noise(continentalness, shift_x, shift_z, 0.25, 0))` |
| erosion | overworld/erosion | `cache(noise(erosion, shift_x, shift_z, 0.25, 0))` |
| weirdness | overworld/ridges | `cache(noise(ridge, shift_x, shift_z, 0.25, 0))` |
| depth | overworld/depth | `add(gradient(axis y, from -64 -> 1.5, to 320 -> -1.5), overworld/offset)` |

`overworld/offset` = `cache(lerp(alpha = blend_alpha, first = blend_offset, second = add(-0.50375, spline(...))))`.
The spline has coordinates continents / erosion / ridges_folded / ridges, the same structure as 1.18+. The
constant is `-0.50375` = `-83/160 + 0.015`, stored as **float** `-0.50375f`.

`cache` only memoises. It does not change the value.

### Noise with shift (`NoiseFunction.ShiftedXzSampler.sampleValue(ctx, x, y, z)`)
```
double sx = (double) x * xzScale + (double) shiftX.sampleValue(ctx, x, y, z);   // shiftX returns float, widened
double sy = (double) y * yScale;                                                  // yScale = 0 -> 0.0
double sz = (double) z * xzScale + (double) shiftZ.sampleValue(ctx, x, y, z);
return noise.get(sx, sy, sz);                                                     // Noise.get(DDD) returns float
```
Difference from 1.21.4: the shift offset is a **float** before it is added (was double). `xzScale = 0.25` (double).
`shift_x` / `shift_z` are `ShiftNoiseFunction.ShiftA/ShiftB` over the `offset` noise (their compiled samplers are
in `ShiftNoiseFunction$ShiftB$1` and so on, and return float). The exact shift formula (x/4 scaling, the x4
multiplier) still needs to be read from those classes. Not yet transcribed.

### Perlin (`PerlinNoise.get(double x, double y, double z)`)
```
double X = wrap(x) + offsetX;  double Y = wrap(y) + offsetY;  double Z = wrap(z) + offsetZ;   // wrap(): GradientNoise.wrap, see below
int ix = Mth.floor(X), iy = Mth.floor(Y), iz = Mth.floor(Z);
float fx = (float)(X - ix), fy = (float)(Y - iy), fz = (float)(Z - iz);   // fractional parts rounded to FLOAT
return sampleAndLerp(ix, iy, iz, fx, fy, fz, fy);
```
`sampleAndLerp` (all float): permutation chain `permute(ix)`, `permute(ix+1)`, then `permute(p + iy)`, `permute(p + iy + 1)`
and so on (same corner order as vanilla), 8 corner values `gradDot(permute(... + iz [+1]), fx[-1], fy[-1], fz[-1])` in float.
Then `Mth.lerp3(smoothstep(fx), smoothstep(fy_orig), smoothstep(fz), v000, v100, v010, v110, v001, v101, v011, v111)`, all float.
The octave sum happens in `NoiseStack` / `NoiseStack$Perlin.get(DDD)F` (layers with double frequency and float
amplitude), and `NormalNoise.create(...)` builds the two-stack "double Perlin" with its normalisation. Still to transcribe
(classes dumped): `GradientNoise.wrap/permute/gradDot`, `Mth.smoothstep(F)F`, `Mth.lerp3`, `NoiseStack$Perlin.get`,
`NormalNoise.create` (normalisation factor as float or double), and `CubicSpline` evaluation (float).

### Depth
```
float g = fromValue + (float)(clamp(y, minCoordinate, maxCoordinate) - fromCoordinate) * coordinateFactor;
          // GradientFunction.ClampedSampler.compute(int): int clamp, int subtract, i2f, float multiply, float add
          // here fromValue = 1.5f, fromCoordinate = -64, coordinateFactor = -3/384 = -0.0078125f (exact), clamp to [-64, 320]
float off = blendLerp(alpha, blend_offset, -0.50375f + spline(c, e, ridges_folded, w));   // ConstAddSampler: input + const, float add
          // LerpFunction.ConstFirstSampler: a = alpha(); if a == 0 -> first; if a == 1 -> second; else Mth.lerp(a, first, second)
          // with no blending, alpha = 1, so off = second exactly
float d = g + off;                                   // BinaryFunction.AddSampler: float add
```
Compare with Cubiomes (1.18 to 1.21 model): `d = (float)(1.0 - (y*4)/128.0 - 83.0/160.0 + (double)(spline + 0.015F))`, all in
double then one rounding. 26.3 instead rounds `spline + (-0.50375f)` to float, then adds the float gradient in float.
Those two extra roundings and the different constant (`-0.50375f` vs `-83/160 + 0.015f`) explain the +1 bias in
depth we see (44,178 of 1,000,000 cells, mostly ours = game + 1).

## (b) Climate.ParameterList.findValue and the RTree

- `ParameterList.findValue(t)` -> `findValueIndex(t)` -> `index.search(t, Climate.RTree.Node::distance)`.
- `RTree.search(t, metric)`:
  ```
  long[] p = t.toParameterArray();
  Leaf leaf = root.search(p, lastResult.get(), metric);   // lastResult is a ThreadLocal<Leaf>: yes, the per-thread hint is still there
  lastResult.set(leaf);
  return leaf.value;
  ```
- `SubTree.search(p, hint, metric)`: `best = hint == null ? Long.MAX_VALUE : metric.distance(hint, p)`, `leaf = hint`.
  For each child in order: `d = distance(child)`; `if (best > d) { l2 = child.search(p, leaf, metric); d2 = (child == l2) ? d : distance(l2); if (best > d2) { best = d2; leaf = l2; } }`.
  Strict `>`: on equal distance the current leaf (initially the hint) is kept. So **game results at exact ties depend on
  the previous lookup on the same thread** (query order). Cubiomes' hint-free search is a fixed tie-break. As
  measured: every T and N biome mismatch with identical climate is an exact tie (955 + 185, TieCheck.java).
- `findValueBruteForce` (not used by worldgen): scans `values()` in list order, keeps the first minimum (`fitness < best`).
- World generation: `MultiNoiseBiomeSource.getNoiseBiome(TargetPoint)` = `parameters().findValue(t)`.
  `createResolverForChunk(sampler, ...)` computes the climate for the whole chunk section through the volume path, then
  calls `getNoiseBiome` per quart cell in the resolver's order. So in-game ties depend on the cell order inside a chunk
  and on what the worker thread looked up before. It is not a pure function of the point.
