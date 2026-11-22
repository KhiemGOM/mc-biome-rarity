// Every (angle, radius) NoiseSpawnFinder evaluates is seed independent: print Math.sin/cos bits and the int offsets.
public class SinCos {
    public static void main(String[] a) {
        float[][] passes = {{2048f, 512f}, {512f, 32f}};
        for (float[] p : passes) {
            float max = p[0], step = p[1], angle = 0f, radius = step;
            while (radius <= max) {
                double s = Math.sin((double) angle), c = Math.cos((double) angle);
                System.out.println(Float.floatToRawIntBits(angle) + " " + Float.floatToRawIntBits(radius) + " " + Long.toHexString(Double.doubleToRawLongBits(s)) + " "
                        + Long.toHexString(Double.doubleToRawLongBits(c)) + " " + (int) (s * (double) radius) + " " + (int) (c * (double) radius)
                        + " " + Long.toHexString(Double.doubleToRawLongBits(StrictMath.sin((double) angle))) + " " + Long.toHexString(Double.doubleToRawLongBits(StrictMath.cos((double) angle))));
                angle += step / radius;
                if ((double) angle > 6.283185307179586) { angle = 0f; radius += step; }
            }
        }
    }
}
