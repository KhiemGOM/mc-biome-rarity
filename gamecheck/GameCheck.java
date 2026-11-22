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
import net.minecraft.world.level.levelgen.RandomState;
import net.minecraft.world.level.levelgen.synth.NormalNoise;

import java.io.BufferedWriter;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.util.SplittableRandom;

public class GameCheck {
    static String name(Holder<Biome> b) { return b.unwrapKey().orElseThrow().identifier().getPath(); }

    public static void main(String[] a) throws Exception {
        int seeds = Integer.parseInt(a[0]), cells = Integer.parseInt(a[1]), trees = Integer.parseInt(a[2]);
        SplittableRandom r = new SplittableRandom(Long.parseLong(a[3]));
        SharedConstants.tryDetectVersion();
        Bootstrap.bootStrap();
        HolderLookup.Provider reg = VanillaRegistries.createLookup();
        NoiseGeneratorSettings ns = reg.lookupOrThrow(Registries.NOISE_SETTINGS).getOrThrow(NoiseGeneratorSettings.OVERWORLD).value();
        HolderGetter<NormalNoise.NoiseParameters> noises = reg.lookupOrThrow(Registries.NOISE);
        Climate.ParameterList<Holder<Biome>> params = reg.lookupOrThrow(Registries.MULTI_NOISE_BIOME_SOURCE_PARAMETER_LIST)
                .getOrThrow(MultiNoiseBiomeSourceParameterLists.OVERWORLD).value().parameters();
        PrintWriter out = new PrintWriter(new BufferedWriter(new OutputStreamWriter(System.out), 1 << 20));
        for (int s = 0; s < seeds; s++) {
            long seed = r.nextLong();
            Climate.Sampler sm = RandomState.create(ns, noises, seed).sampler();
            BlockPos sp = sm.findSpawnPosition();
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
