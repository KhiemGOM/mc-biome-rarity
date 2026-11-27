"""Walk shapes for the "why a straight line" comparison (VIDEO_SCRIPT section 1, Khiem's argument). Every walk gets
the same budget of blocks and is sampled every `step` blocks along its length, so they are compared fairly."""
import math, random


def _along(segments, x, z, budget, step):
    """segments: iterable of (dx, dz, length), unit direction. Points every `step` along the path, `budget` long."""
    pts, done, seg_left = [(x, z)], 0.0, 0.0
    it = iter(segments)
    dx = dz = 0.0
    n = int(round(budget / step)) if step else 0
    for _ in range(n):
        need = step
        while need > 1e-12:
            if seg_left <= 1e-12:
                dx, dz, seg_left = next(it)
            d = min(need, seg_left)
            x, z = x + dx * d, z + dz * d
            need -= d; seg_left -= d
        pts.append((x, z))
    return pts


def straight(x, z, ang, budget, step):
    c, s = math.cos(ang), math.sin(ang)
    return _along(iter(lambda: (c, s, math.inf), None), x, z, budget, step)


def lawnmower(x, z, ang, budget, step, leg, gap):
    """Back and forth: `leg` blocks forward, `gap` blocks sideways, `leg` back, `gap` sideways, ..."""
    f, s = (math.cos(ang), math.sin(ang)), (-math.sin(ang), math.cos(ang))

    def segs():
        sign = 1
        while True:
            yield (f[0] * sign, f[1] * sign, leg)
            yield (s[0], s[1], gap)
            sign = -sign
    return _along(segs(), x, z, budget, step)


def wander(x, z, ang, budget, step, turn, seed):
    """Random walk with momentum: the heading drifts by a normal(0, turn) radians every step."""
    rng, pts = random.Random(seed), [(x, z)]
    for _ in range(int(round(budget / step))):
        ang += rng.gauss(0, turn)
        x, z = x + step * math.cos(ang), z + step * math.sin(ang)
        pts.append((x, z))
    return pts


def cells(pts):
    """Biome cells (4x4 block quarts) along a path, consecutive repeats removed."""
    out = []
    for x, z in pts:
        c = (math.floor(x / 4), math.floor(z / 4))
        if not out or out[-1] != c:
            out.append(c)
    return out


def distinct_curve(ids, checkpoints):
    """Number of different biomes seen in ids[0..c] for each checkpoint index c."""
    seen, out, k = set(), [], 0
    for c in checkpoints:
        while k <= min(c, len(ids) - 1):
            seen.add(ids[k]); k += 1
        out.append(len(seen))
    return out
