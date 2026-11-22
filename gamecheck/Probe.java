// Probe: dump the 26.3 game's climate internals so the C port can be checked piece by piece.
//   Probe df                       density function trees of the climate router entries (record dump, floats as bits)
//   Probe noise <seed>             per noise: layers (frequency, amplitude) and Perlin state (offsets, perms)
//   Probe vals <seed> <n> <rng>    random block points: sampleValue of every climate function and helper (float bits)
import net.minecraft.SharedConstants;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderGetter;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.Registries;
import net.minecraft.data.registries.VanillaRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.Bootstrap;
import net.minecraft.world.level.levelgen.NoiseGeneratorSettings;
import net.minecraft.world.level.levelgen.RandomState;
import net.minecraft.world.level.levelgen.densityfunction.DensityFunction;
import net.minecraft.world.level.levelgen.densityfunction.SamplerContext;
import net.minecraft.world.level.levelgen.synth.Noise;
import net.minecraft.world.level.levelgen.synth.NormalNoise;

import java.lang.reflect.*;
import java.util.*;

public class Probe {
    static HolderLookup.Provider reg;
    static String fbits(float f) { return String.format("%08x", Float.floatToRawIntBits(f)); }
    static String dbits(double d) { return String.format("%016x", Double.doubleToRawLongBits(d)); }

    static void dump(Object o, String ind, int depth, Set<Object> seen) throws Exception {
        if (depth > 40) { System.out.println(ind + "..."); return; }
        if (o == null) { System.out.println(ind + "null"); return; }
        Class<?> c = o.getClass();
        if (o instanceof Holder<?> h) {
            String k = h.unwrapKey().map(x -> x.identifier().toString()).orElse("<direct>");
            System.out.println(ind + "Holder " + k);
            if (h.unwrapKey().isEmpty() || depth == 0 || !(h.value() instanceof NormalNoise)) {
                if (!(h.value() instanceof NormalNoise) && (h.unwrapKey().isEmpty() || depth < 3 || k.contains("overworld/") || k.contains("shift"))) dump(h.value(), ind + "  ", depth + 1, seen);
            }
            return;
        }
        if (o instanceof Float f) { System.out.println(ind + "float " + f + " " + fbits(f)); return; }
        if (o instanceof Double d) { System.out.println(ind + "double " + d + " " + dbits(d)); return; }
        if (o instanceof Number || o instanceof String || o instanceof Boolean || o instanceof Enum<?>) { System.out.println(ind + c.getSimpleName() + " " + o); return; }
        if (o instanceof float[] fa) { StringBuilder sb = new StringBuilder(ind + "float[] "); for (float f : fa) sb.append(f).append("/").append(fbits(f)).append(" "); System.out.println(sb); return; }
        if (o instanceof List<?> l) { System.out.println(ind + "List " + l.size()); for (Object e : l) dump(e, ind + "  ", depth + 1, seen); return; }
        if (c.isRecord()) {
            System.out.println(ind + c.getName());
            for (RecordComponent rc : c.getRecordComponents()) {
                Method m = rc.getAccessor(); m.setAccessible(true);
                System.out.println(ind + " ." + rc.getName() + ":");
                dump(m.invoke(o), ind + "    ", depth + 1, seen);
            }
            return;
        }
        System.out.println(ind + c.getName() + " (non-record) " + o);
        for (Field f : allFields(c)) {
            if (Modifier.isStatic(f.getModifiers())) continue;
            f.setAccessible(true);
            System.out.println(ind + " ." + f.getName() + ":");
            dump(f.get(o), ind + "    ", depth + 1, seen);
        }
    }
    static List<Field> allFields(Class<?> c) { List<Field> r = new ArrayList<>(); for (; c != null && c != Object.class; c = c.getSuperclass()) r.addAll(Arrays.asList(c.getDeclaredFields())); return r; }
    static Object field(Object o, String name) throws Exception {
        for (Field f : allFields(o.getClass())) if (f.getName().equals(name)) { f.setAccessible(true); return f.get(o); }
        throw new NoSuchFieldException(name + " in " + o.getClass());
    }

    static void printSpline(Object s, int d) throws Exception {
        String ind = "  ".repeat(d);
        if (s.getClass().getSimpleName().equals("Constant")) { System.out.println(ind + "C " + fbits((Float) field(s, "value"))); return; }
        Object coord = field(s, "coordinate");                 // SplineFunction.Coordinate(function = Holder)
        Object fn = field(coord, "function");
        String name = fn instanceof Holder<?> h ? h.unwrapKey().map(k -> k.identifier().toString()).orElse("?") : fn.getClass().getSimpleName();
        if (name.equals("?") || !(fn instanceof Holder<?>)) { Object inner = fn; try { inner = field(fn, "function"); } catch (Exception e) {} if (inner instanceof Holder<?> h2) name = h2.unwrapKey().map(k -> k.identifier().toString()).orElse("?"); }
        float[] loc = (float[]) field(s, "locations"), der = (float[]) field(s, "derivatives");
        List<?> vals = (List<?>) field(s, "values");
        System.out.println(ind + "M " + name + " " + loc.length);
        for (int i = 0; i < loc.length; i++) {
            System.out.println(ind + " P " + fbits(loc[i]) + " " + fbits(der[i]));
            printSpline(vals.get(i), d + 1);
        }
    }

    static DensityFunction df(String id) {
        return reg.lookupOrThrow(Registries.DENSITY_FUNCTION).getOrThrow(ResourceKey.create(Registries.DENSITY_FUNCTION, Identifier.parse(id))).value();
    }

    public static void main(String[] a) throws Exception {
        SharedConstants.tryDetectVersion(); Bootstrap.bootStrap();
        reg = VanillaRegistries.createWorldLookup();
        NoiseGeneratorSettings ns = reg.lookupOrThrow(Registries.NOISE_SETTINGS).getOrThrow(NoiseGeneratorSettings.OVERWORLD).value();
        HolderGetter<NormalNoise> noises = reg.lookupOrThrow(Registries.NOISE);
        String[] dfs = {"minecraft:shift_x", "minecraft:shift_z", "minecraft:overworld/temperature", "minecraft:overworld/vegetation", "minecraft:overworld/continents",
                "minecraft:overworld/erosion", "minecraft:overworld/ridges", "minecraft:overworld/ridges_folded", "minecraft:overworld/offset", "minecraft:overworld/depth"};
        if (a[0].equals("spline")) {      // the offset spline, compact: M <coord> <n> {<loc> <der> <value>}... / C <value>
            Object lerp = field(df("minecraft:overworld/offset"), "input");
            Object add = field(lerp, "second");
            Object sf = field(add, "right");
            printSpline(field(sf, "spline"), 0);
            return;
        }
        if (a[0].equals("df")) {
            for (String id : dfs) { System.out.println("=== " + id); dump(df(id), "", 0, new HashSet<>()); }
            return;
        }
        long seed = Long.parseLong(a[1]);
        RandomState rs = RandomState.create(noises, seed, ns);
        if (a[0].equals("noise")) {
            for (String n : new String[]{"temperature", "vegetation", "continentalness", "erosion", "ridge", "offset"}) {
                Noise no = rs.getOrCreateNoise(ResourceKey.create(Registries.NOISE, Identifier.parse("minecraft:" + n)));
                Object[] layers = (Object[]) field(no, "layers");
                System.out.println("NOISE " + n + " " + no.getClass().getName() + " layers " + layers.length);
                for (int i = 0; i < layers.length; i++) {
                    Object L = layers[i];
                    double fr = (Double) field(L, "frequency"); float am = (Float) field(L, "amplitude"); Object p = field(L, "noise");
                    byte[] perms = (byte[]) field(p, "perms");
                    StringBuilder sb = new StringBuilder();
                    for (int k = 0; k < 256; k++) sb.append(String.format("%02x", perms[k] & 255));
                    System.out.println("L " + n + " " + i + " freq " + dbits(fr) + " amp " + fbits(am) + " " + am + " off " + dbits((Double) field(p, "offsetX")) + " "
                            + dbits((Double) field(p, "offsetY")) + " " + dbits((Double) field(p, "offsetZ")) + " " + p.getClass().getSimpleName() + " perms " + sb);
                }
            }
            return;
        }
        if (a[0].equals("vals")) {
            int n = Integer.parseInt(a[2]); SplittableRandom r = new SplittableRandom(Long.parseLong(a[3]));
            List<net.minecraft.world.level.levelgen.densityfunction.DensitySampler> ss = new ArrayList<>();
            for (String id : dfs) ss.add(rs.getSampler(df(id)));
            for (int i = 0; i < n; i++) {
                int x, z, y = r.nextInt(-64, 320);
                if (i % 3 == 0) { x = r.nextInt(-1000000, 1000001); z = r.nextInt(-1000000, 1000001); }
                else if (i % 3 == 1) { x = r.nextInt(-3000, 3001); z = r.nextInt(-3000, 3001); }
                else { x = r.nextInt(-30000000, 30000001); z = r.nextInt(-30000000, 30000001); }
                if (i % 5 == 0) { x &= ~3; z &= ~3; y &= ~3; }
                StringBuilder sb = new StringBuilder("P " + x + " " + y + " " + z);
                for (var s : ss) sb.append(" ").append(fbits(s.sampleValue(SamplerContext.EMPTY_UNCACHED, x, y, z)));
                System.out.println(sb);
            }
        }
    }
}
