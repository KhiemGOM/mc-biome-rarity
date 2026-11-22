// For each "T t h c e d w ours game" line: the game's best fitness, and the best fitness among entries of biome "ours".
// tie = ours's best equals the global minimum (so the mismatch is only a tie-break difference).
import net.minecraft.SharedConstants;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.Registries;
import net.minecraft.data.registries.VanillaRegistries;
import net.minecraft.server.Bootstrap;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.biome.Climate;
import net.minecraft.world.level.biome.MultiNoiseBiomeSourceParameterLists;
import com.mojang.datafixers.util.Pair;
import java.io.*;
import java.util.*;

public class TieCheck {
    static String name(Holder<Biome> b) { return b.unwrapKey().orElseThrow().identifier().getPath(); }
    public static void main(String[] a) throws Exception {
        SharedConstants.tryDetectVersion(); Bootstrap.bootStrap();
        HolderLookup.Provider reg = VanillaRegistries.createWorldLookup();
        Climate.ParameterList<Holder<Biome>> params = reg.lookupOrThrow(Registries.MULTI_NOISE_BIOME_SOURCE_PARAMETER_LIST)
                .getOrThrow(MultiNoiseBiomeSourceParameterLists.OVERWORLD).value().parameters();
        if (a.length > 0 && a[0].equals("dump")) {             // print the full parameter list (for comparing with the fork's tree)
            for (Pair<Climate.ParameterPoint, Holder<Biome>> p : params.values()) {
                Climate.ParameterPoint q = p.getFirst();
                System.out.println(name(p.getSecond()) + " " + q.temperature().min() + " " + q.temperature().max() + " " + q.humidity().min() + " " + q.humidity().max()
                        + " " + q.continentalness().min() + " " + q.continentalness().max() + " " + q.erosion().min() + " " + q.erosion().max()
                        + " " + q.depth().min() + " " + q.depth().max() + " " + q.weirdness().min() + " " + q.weirdness().max() + " " + q.offset());
            }
            return;
        }
        BufferedReader in = new BufferedReader(new InputStreamReader(System.in));
        int ties = 0, notie = 0; String l;
        while ((l = in.readLine()) != null) {
            String[] f = l.trim().split("\\s+");
            if (f.length < 9) continue;
            Climate.TargetPoint t = new Climate.TargetPoint(Long.parseLong(f[1]), Long.parseLong(f[2]), Long.parseLong(f[3]),
                    Long.parseLong(f[4]), Long.parseLong(f[5]), Long.parseLong(f[6]));
            long best = Long.MAX_VALUE, bestOurs = Long.MAX_VALUE;
            for (Pair<Climate.ParameterPoint, Holder<Biome>> p : params.values()) {
                long fit = p.getFirst().fitness(t);
                best = Math.min(best, fit);
                if (name(p.getSecond()).equals(f[7])) bestOurs = Math.min(bestOurs, fit);
            }
            boolean tie = bestOurs == best;
            if (tie) ties++; else { notie++; if (notie <= 5) System.out.println("NOT TIE " + l + " best " + best + " ours_best " + bestOurs + " brute " + name(params.findValueBruteForce(t))); }
        }
        System.out.println("ties " + ties + " not_ties " + notie);
    }
}
