"""Driver: plan (from pilot) -> run (chunked, resumable) -> report (certificates + checks).

  python3 cert_pipeline.py plan   --eps 0.02
  python3 cert_pipeline.py run    --n-seeds N --n-calib NC
  python3 cert_pipeline.py report --n-seeds N --n-calib NC --eps 0.02
"""
import argparse, json, os, subprocess, sys, time
import numpy as np
import certify as ct

R0, R, RAYS = 4000.0, 20000.0, 4
OUT = "out/cert"
PILOT_SEED0, PILOT_N = 5_000_000_000, 1500
PROD_SEED0 = 7_000_000_000
MAIN_STEP, MAIN_LEVELS = 8, 3          # 8, 16, 32
CAL_STEP, CAL_LEVELS = 1, 6            # 1, 2, 4, 8, 16, 32
CHUNK_MAIN, CHUNK_CAL = 4000, 1000
TARGETS = ["mushroom_fields", "pale_garden", "windswept_gravelly_hills", "stony_peaks", "ice_spikes"]

NAMES = {int(a): b for a, b in (l.strip().split(",", 1) for l in open("out/names.csv"))}
IDS = {v: k for k, v in NAMES.items()}


def chunks(total, size):
    return [(i, min(size, total - i)) for i in range(0, total, size)]


def colsim(seed0, n, step, levels, path, threads=2):
    cmd = ["./colsim", "--mc", "1.21", "--seeds", str(n), "--rays", str(RAYS), "--rmax", str(int(R)),
           "--step", str(step), "--nested", str(levels), "--seed0", str(seed0), "--threads", str(threads),
           "--no-column", "--out-surface", path, "--out-column", path + ".col"]
    subprocess.run(cmd, check=True)
    os.remove(path + ".col")


def load_run(prefix, total, size, step_levels, rays=RAYS):
    """Concatenate chunk files into {biome: {level: D (total, rays)}}; level m means step * 2^m."""
    parts = []
    for off, n in chunks(total, size):
        parts.append((off, n, ct.load_nested(f"{prefix}_{off}.csv", n, rays, step_levels)))
    biomes = set()
    for _, _, d in parts:
        biomes |= set(d)
    out = {b: {m: np.full((total, rays), np.inf) for m in range(step_levels)} for b in biomes}
    for off, n, d in parts:
        for b, lv in d.items():
            for m, A in lv.items():
                out[b][m][off:off + n] = A
    return out


def by_step(lv, step):
    return {step * 2 ** m: A for m, A in lv.items()}


def terms_for(main_b, cal_b, n_cal):
    main = by_step(main_b, MAIN_STEP)
    cal = {h: A[:n_cal] for h, A in by_step(cal_b, CAL_STEP).items()}
    return ct.build_terms(main, cal, R0, R, lo=8, hi=16)


def cmd_plan(a):
    pil = ct.load_nested(f"{OUT}/pilot.csv", PILOT_N, RAYS, CAL_LEVELS)
    best = {}
    print(f"{'biome':28s} {'pilot M':>9s} {'events':>6s} {'N seeds':>8s} {'n_calib':>8s}")
    for nm in TARGETS:
        b = IDS[nm]
        lv = by_step(pil[b], CAL_STEP)
        t = ct.build_terms({8: lv[8], 16: lv[16]}, lv, R0, R)
        p = ct.plan(t, a.eps, cost_ratio=a.cost_ratio)
        est = ct.combo(t)[0]
        print(f"{nm:28s} {est:9.0f} {int(t[0].E.sum()):6d} {p['n_seeds']:8d} {p['n_calib']:8d}")
        best[nm] = p
    # one run serves every target: take the largest N, and the n_calib that keeps every target's projection under eps
    N = max(p["n_seeds"] for p in best.values())
    nc = max(p["n_calib"] for p in best.values())
    for _ in range(200):
        ok = True
        for nm in TARGETS:
            b = IDS[nm]; lv = by_step(pil[b], CAL_STEP)
            t = ct.build_terms({8: lv[8], 16: lv[16]}, lv, R0, R)
            if ct.projected_rel_half(t, N, nc) > a.eps:
                ok = False
        if ok:
            break
        N = int(N * 1.03)
    N = int(np.ceil(N / 100.0) * 100); nc = int(np.ceil(nc / 100.0) * 100)
    print(f"\nproduction: N={N} seeds ({N * RAYS} rays), n_calib={nc} seeds at step 1")
    json.dump(dict(n_seeds=N, n_calib=nc, eps=a.eps), open(f"{OUT}/plan.json", "w"))


def cmd_run(a):
    t0 = time.time()
    for off, n in chunks(a.n_calib, CHUNK_CAL):
        p = f"{OUT}/cal_{off}.csv"
        if not os.path.exists(p):
            colsim(PROD_SEED0 + off, n, CAL_STEP, CAL_LEVELS, p)
            print(f"cal chunk {off} done  {time.time() - t0:.0f}s", flush=True)
    for off, n in chunks(a.n_seeds, CHUNK_MAIN):
        p = f"{OUT}/main_{off}.csv"
        if not os.path.exists(p):
            colsim(PROD_SEED0 + off, n, MAIN_STEP, MAIN_LEVELS, p)
            print(f"main chunk {off} done  {time.time() - t0:.0f}s", flush=True)


def cmd_report(a):
    main = load_run(f"{OUT}/main", a.n_seeds, CHUNK_MAIN, MAIN_LEVELS)
    cal = load_run(f"{OUT}/cal", a.n_calib, CHUNK_CAL, CAL_LEVELS)
    rng = np.random.default_rng(12345)
    rows = {}
    for b in sorted(main):
        if b not in cal:
            continue
        t = terms_for(main[b], cal[b], a.n_calib)
        if t[0].E.sum() < ct.MIN_EVENTS:
            continue
        c = ct.certificate(t, a.eps, n_boot=a.boot, rng=rng)
        c["name"] = NAMES.get(b, str(b))
        c["raw_h8"] = ct.combo([ct.Term(1.0, *ct.stats(by_step(main[b], 8)[8], R0, R))])[0]
        c["rich_all"] = ct.combo(t[:2])[0]
        rows[b] = (c, t)
    out = {}
    for b, (c, t) in rows.items():
        entry = dict(c)
        if c["name"] in TARGETS:
            fc = ct.fold_check(t, 8)
            entry["fold"] = dict(chi2=fc["chi2"], dof=fc["dof"], p=fc["p"])
            D8 = by_step(main[b], 8)[8]
            entry["hazard_bins"] = ct.bin_hazards(D8, R0, R, 4)
            cl = by_step(cal[b], 1)
            curve = {}
            for h in (1, 2, 4, 8, 16, 32):
                Eh, Xh = ct.stats(cl[h][:a.n_calib], R0, R)
                curve[h] = float(Xh.sum() / Eh.sum()) if Eh.sum() else None
            entry["bias_curve_calib"] = curve
        out[c["name"]] = entry
    json.dump(dict(n_seeds=a.n_seeds, n_calib=a.n_calib, eps=a.eps, results=out), open(f"{OUT}/cert.json", "w"), indent=1)
    order = sorted(out, key=lambda k: -out[k]["est"])
    print(f"{'biome':28s} {'M_hat':>9s} {'+-95%':>8s} {'rel':>6s} {'events':>7s}  cert")
    for k in order[:14]:
        e = out[k]
        print(f"{k:28s} {e['est']:9.0f} {e['half']:8.0f} {100 * e['rel_half']:5.2f}% {e['events']:7d}  {e['certified']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["plan", "run", "report"])
    ap.add_argument("--eps", type=float, default=0.02)
    ap.add_argument("--cost-ratio", type=float, default=8.5)
    ap.add_argument("--n-seeds", type=int)
    ap.add_argument("--n-calib", type=int)
    ap.add_argument("--boot", type=int, default=600)
    a = ap.parse_args()
    if a.cmd != "plan" and (a.n_seeds is None or a.n_calib is None):
        pl = json.load(open(f"{OUT}/plan.json"))
        a.n_seeds, a.n_calib = pl["n_seeds"], pl["n_calib"]
    {"plan": cmd_plan, "run": cmd_run, "report": cmd_report}[a.cmd](a)
