"""Independent re-derivation of the certificate from the raw csv files.

Shares NO code with certify.py: plain csv + dicts + loops. Recomputes, for each target biome,
  E_i, X_i per seed at each level, the two-phase estimate, the delta-method SE, and a delete-one-seed
  jackknife SE, then compares with cert.json. Prints PASS/FAIL per check.
"""
import csv, json, math, sys

R0, R, RAYS = 4000, 20000, 4
OUT = "out/cert"
plan = json.load(open(f"{OUT}/plan.json"))
cert = json.load(open(f"{OUT}/cert.json"))
N, NC = plan["n_seeds"], plan["n_calib"]
NAMES = {int(a): b for a, b in (l.strip().split(",", 1) for l in open("out/names.csv"))}
TARGETS = ["mushroom_fields", "pale_garden", "windswept_gravelly_hills", "stony_peaks", "ice_spikes"]
IDS = {NAMES[i]: i for i in NAMES}


def read_run(prefix, total, size, levels):
    """first[(biome)][level] = {(global_seed_index, ray): dist}. Seed index from order of appearance per chunk."""
    first = {IDS[t]: [dict() for _ in range(levels)] for t in TARGETS}
    for off in range(0, total, size):
        n = min(size, total - off)
        order = {}
        with open(f"{prefix}_{off}.csv") as f:
            for row in csv.DictReader(f):
                s = row["seed"]
                if s not in order:
                    order[s] = off + len(order)
                b = int(row["biome"])
                if b in first:
                    first[b][int(row["level"])][(order[s], int(row["ray"]))] = int(row["dist"])
        assert len(order) == n, f"chunk {off}: {len(order)} seeds, expected {n}"
    return first


def per_seed(d, n_seeds):
    E = [0] * n_seeds
    X = [0] * n_seeds
    for i in range(n_seeds):
        for r in range(RAYS):
            D = d.get((i, r), math.inf)
            if D >= R0:
                X[i] += min(D, R) - R0
                if D <= R:
                    E[i] += 1
    return E, X


main = read_run(f"{OUT}/main", N, 4000, 3)
cal = read_run(f"{OUT}/cal", NC, 1000, 6)
fails = 0
for name in TARGETS:
    b = IDS[name]
    # terms: (coef, E, X) ; main level 0 = step 8, level 1 = step 16 ; cal level 0 = step 1, 3 = step 8, 4 = step 16
    terms = []
    for coef, src, lvl, n in ((2, main, 0, N), (-1, main, 1, N), (1, cal, 0, NC), (-2, cal, 3, NC), (1, cal, 4, NC)):
        E, X = per_seed(src[b][lvl], n)
        terms.append((coef, E, X))
    sE = [sum(t[1]) for t in terms]
    sX = [sum(t[2]) for t in terms]
    est = sum(t[0] * sx / se for t, sx, se in zip(terms, sX, sE))
    # delta SE
    z = [0.0] * N
    for (c, E, X), se, sx in zip(terms, sE, sX):
        m = sx / se
        for i in range(len(E)):
            z[i] += c * (X[i] - m * E[i]) / se
    se_delta = math.sqrt(sum(v * v for v in z) * N / (N - 1))
    # jackknife
    loo = []
    for i in range(N):
        s = 0.0
        for (c, E, X), se, sx in zip(terms, sE, sX):
            if i < len(E):
                s += c * (sx - X[i]) / (se - E[i])
            else:
                s += c * sx / se
        loo.append(s)
    mean = sum(loo) / N
    se_jack = math.sqrt((N - 1) / N * sum((v - mean) ** 2 for v in loo))
    c = cert["results"][name]
    ok_est = abs(est - c["est"]) <= 1e-6 * est
    ok_se = abs(se_delta - c["se_delta"]) <= 1e-6 * se_delta
    ok_jack = abs(se_jack / se_delta - 1) < 0.05
    ok_boot = abs(c["se_boot"] / se_delta - 1) < 0.10
    eps_ind = 1.96 * max(se_delta, se_jack, c["se_boot"]) / est
    ok_cert = eps_ind <= cert["eps"]
    for lab, ok in (("estimate equals certify.py", ok_est), ("delta SE equals certify.py", ok_se),
                    ("jackknife SE within 5% of delta", ok_jack), ("bootstrap SE within 10% of delta", ok_boot),
                    ("independent epsilon <= target", ok_cert)):
        fails += (not ok)
        print(f"{'PASS' if ok else 'FAIL'}  {name:26s} {lab}")
    print(f"      est {est:.1f}  se_delta {se_delta:.1f}  se_jack {se_jack:.1f}  se_boot {c['se_boot']:.1f}  eps {100 * eps_ind:.3f}%")
sys.exit(1 if fails else 0)
