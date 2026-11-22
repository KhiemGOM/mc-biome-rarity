// GameCheck: print what the real Minecraft 26.3 server code computes, for gamecheck.c to compare with Cubiomes.
// Build/run against the unbundled server jar (26.x is not obfuscated), see README.md in this folder.
//   java -cp <server+libs>:. GameCheck <seeds> <cells per seed> <tree points> <rng seed>  > game.txt
import net.minecraft.SharedConstants;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderGetter;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.data.registries.VanillaRegistries;
import net.minecraft.server.Bootstrap;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.biome.Climate;
import net.minecraft.world.level.biome.MultiNoiseBiomeSourceParameterList;
import net.minecraft.world.level.biome.MultiNoiseBiomeSourceParameterLists;
import net.minecraft.world.level.levelgen.NoiseGeneratorSettings;
import net.minecraft.world.level.levelgen.NoiseSpawnFinder;
import net.minecraft.world.level.levelgen.densityfunction.SamplerContext;
import net.minecraft.world.level.levelgen.densityfunction.DensityBuffer;
import net.minecraft.world.level.levelgen.densityfunction.DensitySampler;
import net.minecraft.world.level.levelgen.densityfunction.DensityVolume;
import net.minecraft.world.level.biome.BiomeResolver;
import net.minecraft.world.level.biome.MultiNoiseBiomeSource;
import net.minecraft.world.level.biome.MultiNoiseBiomeSourceParameterList;
import net.minecraft.world.level.levelgen.RandomState;
import net.minecraft.world.level.levelgen.synth.NormalNoise;

import java.io.BufferedWriter;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.util.SplittableRandom;

public class GameCheck {
    static String name(Holder<Biome> b) { return b.unwrapKey().orElseThrow().identifier().getPath(); }

    // Mode V: the real chunk path (MultiNoiseBiomeSource.createResolverForChunk, volume sampling with the chunk
    // generator's caching context) against the point path (Climate.Sampler.sample, uncached), per quart cell of whole
    // chunk columns (4 x 96 x 4 quarts, y = -64..319). Prints V lines (volume climate + chunk-path biome) for gamecheck.c
    // and a summary on stderr: climate mismatches per parameter, biome mismatches split into exact ties and others.
    //   java ... GameCheck V <seeds> <chunks per seed> <rng seed>
    static void modeV(String[] a) throws Exception {
        int seeds = Integer.parseInt(a[1]), chunks = Integer.parseInt(a[2]);
        SplittableRandom r = new SplittableRandom(Long.parseLong(a[3]));
        SharedConstants.tryDetectVersion();
        Bootstrap.bootStrap();
        HolderLookup.Provider reg = VanillaRegistries.createWorldLookup();
        NoiseGeneratorSettings ns = reg.lookupOrThrow(Registries.NOISE_SETTINGS).getOrThrow(NoiseGeneratorSettings.OVERWORLD).value();
        HolderGetter<NormalNoise> noises = reg.lookupOrThrow(Registries.NOISE);
        Holder<MultiNoiseBiomeSourceParameterList> preset = reg.lookupOrThrow(Registries.MULTI_NOISE_BIOME_SOURCE_PARAMETER_LIST)
                .getOrThrow(MultiNoiseBiomeSourceParameterLists.OVERWORLD);
        MultiNoiseBiomeSource src = MultiNoiseBiomeSource.createFromPreset(preset);
        Climate.ParameterList<Holder<Biome>> params = preset.value().parameters();
        PrintWriter out = new PrintWriter(new BufferedWriter(new OutputStreamWriter(System.out), 1 << 20));
        long cellsN = 0, biomeBad = 0, biomeTie = 0; long[] npBad = new long[6]; long anyBad = 0;
        for (int s = 0; s < seeds; s++) {
            long seed = r.nextLong();
            RandomState rs = RandomState.create(noises, seed, ns);
            Climate.Sampler point = rs.createClimateSampler(SamplerContext.EMPTY_UNCACHED);
            Climate.Sampler chunkS = rs.createClimateSampler(SamplerContext.builder().enableCaches().build());   // as ChunkGenerator
            for (int c = 0; c < chunks; c++) {
                int cx = c % 2 == 0 ? r.nextInt(-62500, 62501) : r.nextInt(-40, 41);     // anywhere (+-1M blocks) / near the origin
                int cz = c % 2 == 0 ? r.nextInt(-62500, 62501) : r.nextInt(-40, 41);
                int qx0 = cx * 4, qy0 = -16, qz0 = cz * 4, sx = 4, sy = 96, sz = 4;      // = QuartPos.fromBlock(minBlock), height 384
                BiomeResolver res = src.createResolverForChunk(chunkS, qx0, qy0, qz0, sx, sy, sz);
                DensityVolume vol = new DensityVolume(sx, sy, sz, qx0 << 2, qy0 << 2, qz0 << 2, 4, 4, 4);
                DensityBuffer[] b = new DensityBuffer[6];
                DensitySampler.Bound[] f = {chunkS.temperature(), chunkS.humidity(), chunkS.continentalness(), chunkS.erosion(), chunkS.depth(), chunkS.weirdness()};
                for (int k = 0; k < 6; k++) { b[k] = DensityBuffer.createUnpooled(vol.size()); f[k].sampleVolume(b[k], vol); }
                for (int dx = 0; dx < sx; dx++) for (int dy = 0; dy < sy; dy++) for (int dz = 0; dz < sz; dz++) {
                    int qx = qx0 + dx, qy = qy0 + dy, qz = qz0 + dz, i = vol.indexUnchecked(dx, dy, dz);
                    Climate.TargetPoint tv = Climate.target(b[0].get(i), b[1].get(i), b[2].get(i), b[3].get(i), b[4].get(i), b[5].get(i));
                    Climate.TargetPoint tp = point.sample(qx, qy, qz);
                    Holder<Biome> bv = res.getNoiseBiome(qx, qy, qz);                 // the real chunk path
                    Holder<Biome> bp = params.findValue(tp);
                    long[] vv = {tv.temperature(), tv.humidity(), tv.continentalness(), tv.erosion(), tv.depth(), tv.weirdness()};
                    long[] pv = {tp.temperature(), tp.humidity(), tp.continentalness(), tp.erosion(), tp.depth(), tp.weirdness()};
                    boolean bad = false;
                    for (int k = 0; k < 6; k++) if (vv[k] != pv[k]) { npBad[k]++; bad = true; }
                    if (bad) anyBad++;
                    if (!bv.equals(bp)) {
                        biomeBad++;
                        if (!bad) {                                                 // same climate: is it an exact tie?
                            long best = Long.MAX_VALUE, bvBest = Long.MAX_VALUE, bpBest = Long.MAX_VALUE;
                            for (com.mojang.datafixers.util.Pair<Climate.ParameterPoint, Holder<Biome>> p : params.values()) {
                                long fit = p.getFirst().fitness(tv); best = Math.min(best, fit);
                                if (p.getSecond().equals(bv)) bvBest = Math.min(bvBest, fit);
                                if (p.getSecond().equals(bp)) bpBest = Math.min(bpBest, fit);
                            }
                            if (bvBest == best && bpBest == best) biomeTie++;
                        }
                    }
                    cellsN++;
                    out.println("V " + seed + " " + qx + " " + qy + " " + qz + " " + vv[0] + " " + vv[1] + " " + vv[2] + " " + vv[3] + " " + vv[4] + " " + vv[5] + " " + name(bv));
                }
            }
        }
        out.flush();
        System.err.println("VSUMMARY cells " + cellsN + " volume_vs_point_climate_mismatch " + anyBad + " per_param t,h,c,e,d,w "
                + npBad[0] + "," + npBad[1] + "," + npBad[2] + "," + npBad[3] + "," + npBad[4] + "," + npBad[5]
                + " biome_mismatch " + biomeBad + " of_which_exact_ties_with_equal_climate " + biomeTie);
    }

    public static void main(String[] a) throws Exception {
        if (a[0].equals("V")) { modeV(a); return; }
        int seeds = Integer.parseInt(a[0]), cells = Integer.parseInt(a[1]), trees = Integer.parseInt(a[2]);
        SplittableRandom r = new SplittableRandom(Long.parseLong(a[3]));
        SharedConstants.tryDetectVersion();
        Bootstrap.bootStrap();
        HolderLookup.Provider reg = VanillaRegistries.createWorldLookup();                     // 26.3: was createLookup()
        NoiseGeneratorSettings ns = reg.lookupOrThrow(Registries.NOISE_SETTINGS).getOrThrow(NoiseGeneratorSettings.OVERWORLD).value();
        HolderGetter<NormalNoise> noises = reg.lookupOrThrow(Registries.NOISE);                  // 26.3: NormalNoise is the registry type
        Climate.ParameterList<Holder<Biome>> params = reg.lookupOrThrow(Registries.MULTI_NOISE_BIOME_SOURCE_PARAMETER_LIST)
                .getOrThrow(MultiNoiseBiomeSourceParameterLists.OVERWORLD).value().parameters();
        PrintWriter out = new PrintWriter(new BufferedWriter(new OutputStreamWriter(System.out), 1 << 20));
        for (int s = 0; s < seeds; s++) {
            long seed = r.nextLong();
            // 26.3: RandomState.create(noises, seed, settings); the climate sampler and the spawn search take a
            // SamplerContext, and the spawn search moved to NoiseSpawnFinder with the settings' spawn target points.
            RandomState rs = RandomState.create(noises, seed, ns);
            Climate.Sampler sm = rs.createClimateSampler(SamplerContext.EMPTY_UNCACHED);
            BlockPos sp = NoiseSpawnFinder.findSpawnPosition(ns.spawnTarget(), rs.samplersWithContext(SamplerContext.EMPTY_UNCACHED));
            out.println("S " + seed + " " + sp.getX() + " " + sp.getZ());
            for (int c = 0; c < cells; c++) {
                int qx, qz;
                if (c % 2 == 0) { qx = r.nextInt(-262144, 262145); qz = r.nextInt(-262144, 262145); }   // anywhere (+-1M blocks)
                else { qx = (sp.getX() >> 2) + r.nextInt(-512, 513); qz = (sp.getZ() >> 2) + r.nextInt(-512, 513); } // near spawn
                int qy = r.nextInt(-16, 80);                                                              // y = -64..319
                Climate.TargetPoint t = sm.sample(qx, qy, qz);
                out.println("N " + seed + " " + qx + " " + qy + " " + qz + " " + t.temperature() + " " + t.humidity() + " "
                        + t.continentalness() + " " + t.erosion() + " " + t.depth() + " " + t.weirdness() + " " + name(params.findValue(t)));
            }
        }
        for (int i = 0; i < trees; i++) {
            long[] v = new long[6];
            for (int k = 0; k < 6; k++) v[k] = k == 4 ? r.nextLong(-20000, 30001) : r.nextLong(-15000, 15001);
            Climate.TargetPoint t = new Climate.TargetPoint(v[0], v[1], v[2], v[3], v[4], v[5]);
            out.println("T " + v[0] + " " + v[1] + " " + v[2] + " " + v[3] + " " + v[4] + " " + v[5] + " " + name(params.findValue(t)));
        }
        out.flush();
    }
}
