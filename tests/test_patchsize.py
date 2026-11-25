import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import patchsize as ps


def m(rho, w, r):
    return 1.0 / (rho * (w + 2 * r))


def test_roundtrip_and_all_pairs():
    rho, w = 3e-8, 250.0
    for ra, rb in ps.PAIRS:
        a, b = m(rho, w, ra), m(rho, w, rb)
        (wl, we, wh), (rl, re, rh) = ps.width_rho((a, a, a), (b, b, b), ra, rb)
        assert math.isclose(we, w, rel_tol=1e-9) and math.isclose(re, rho, rel_tol=1e-9)


def test_interval_contains_truth_and_is_monotone():
    rho, w = 3e-8, 250.0
    a, b = m(rho, w, 0), m(rho, w, 128)
    (wl, we, wh), (rl, re, rh) = ps.width_rho((a * 0.95, a, a * 1.05), (b * 0.95, b, b * 1.05), 0, 128)
    assert wl < w < wh and rl < rho < rh


def test_unbounded_when_no_gain():
    (wl, we, wh), _ = ps.width_rho((90.0, 100.0, 110.0), (95.0, 100.0, 105.0), 0, 128)
    assert wh == float("inf") and wl >= 0
