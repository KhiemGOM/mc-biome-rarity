// Prints the overworld spawn target points (density function id -> Climate.Parameter) and, for N seeds,
// the NoiseSpawnFinder result plus the final world spawn after the surface step if it can be computed cheaply.
import net.minecraft.SharedConstants;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderGetter;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.data.registries.VanillaRegistries;
import net.minecraft.server.Bootstrap;
import net.minecraft.world.level.biome.Climate;
import net.minecraft.world.level.levelgen.NoiseGeneratorSettings;
import net.minecraft.world.level.levelgen.NoiseSpawnFinder;
import net.minecraft.world.level.levelgen.RandomState;
import net.minecraft.world.level.levelgen.SpawnTargetPoint;
import net.minecraft.world.level.levelgen.densityfunction.DensityFunction;
import net.minecraft.world.level.levelgen.densityfunction.SamplerContext;
import net.minecraft.world.level.levelgen.synth.NormalNoise;

import java.util.Map;
import java.util.SplittableRandom;

public class SpawnDump {
    public static void main(String[] a) throws Exception {
        int n = Integer.parseInt(a[0]);
        SplittableRandom r = new SplittableRandom(Long.parseLong(a[1]));
        SharedConstants.tryDetectVersion();
        Bootstrap.bootStrap();
        HolderLookup.Provider reg = VanillaRegistries.createWorldLookup();
        NoiseGeneratorSettings ns = reg.lookupOrThrow(Registries.NOISE_SETTINGS).getOrThrow(NoiseGeneratorSettings.OVERWORLD).value();
        HolderGetter<NormalNoise> noises = reg.lookupOrThrow(Registries.NOISE);
        int i = 0;
        for (SpawnTargetPoint p : ns.spawnTarget()) {
            for (Map.Entry<Holder<DensityFunction>, Climate.Parameter> e : p.parameters().entrySet()) {
                String id = e.getKey().unwrapKey().map(k -> k.identifier().toString()).orElse("<inline " + e.getKey().value() + ">");
                System.out.println("TARGET " + i + " " + id + " min " + e.getValue().min() + " max " + e.getValue().max());
            }
            i++;
        }
        for (int s = 0; s < n; s++) {
            long seed = r.nextLong();
            RandomState rs = RandomState.create(noises, seed, ns);
            BlockPos sp = NoiseSpawnFinder.findSpawnPosition(ns.spawnTarget(), rs.samplersWithContext(SamplerContext.EMPTY_UNCACHED));
            System.out.println("S " + seed + " " + sp.getX() + " " + sp.getZ());
        }
    }
}
