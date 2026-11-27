"""Walk geometry for the "why a straight line" comparison. Run: python -m pytest -q test_walks.py (from this folder)."""
import math
from walks import straight, lawnmower, wander, cells, distinct_curve


def length(pts):
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


def test_every_walk_is_exactly_the_budget_long():
    for pts in (straight(0, 0, 0.7, 5000, 2), lawnmower(0, 0, 0.7, 5000, 2, leg=1000, gap=128),
                wander(0, 0, 0.7, 5000, 2, turn=0.2, seed=3)):
        assert abs(length(pts) - 5000) <= 2.01


def test_points_are_evenly_spaced():
    for pts in (straight(5, 5, 1.0, 1000, 2), lawnmower(5, 5, 1.0, 1000, 2, leg=300, gap=64)):
        steps = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
        assert max(steps) <= 2.0 + 1e-9 and min(steps) >= 2.0 - 1e-9


def test_straight_starts_at_spawn_and_goes_the_right_way():
    pts = straight(100, -50, 0.0, 1000, 2)
    assert pts[0] == (100, -50) and abs(pts[-1][0] - 1100) < 1e-6 and abs(pts[-1][1] + 50) < 1e-6


def test_lawnmower_legs_are_parallel_and_gap_apart():
    pts = lawnmower(0, 0, 0.0, 2000 + 64 + 2000, 1, leg=2000, gap=64)
    assert abs(pts[2000][0] - 2000) < 1e-6 and abs(pts[2000][1]) < 1e-6           # end of leg 1
    assert abs(pts[2064][0] - 2000) < 1e-6 and abs(pts[2064][1] - 64) < 1e-6      # across the gap
    assert abs(pts[-1][0]) < 1e-6 and abs(pts[-1][1] - 64) < 1e-6                 # back along leg 2


def test_lawnmower_stays_inside_its_strip_box():
    pts = lawnmower(0, 0, 0.0, 20000, 4, leg=1000, gap=128)
    assert all(-1e-6 <= x <= 1000 + 1e-6 for x, _ in pts)


def test_wander_is_repeatable_and_differs_by_seed():
    assert wander(0, 0, 0, 500, 2, 0.3, seed=1) == wander(0, 0, 0, 500, 2, 0.3, seed=1)
    assert wander(0, 0, 0, 500, 2, 0.3, seed=1) != wander(0, 0, 0, 500, 2, 0.3, seed=2)


def test_cells_are_biome_quarts_and_dedupe_consecutive_repeats():
    assert cells([(0, 0), (1, 1), (3.9, 3.9), (4, 0), (-0.1, 0)]) == [(0, 0), (1, 0), (-1, 0)]


def test_distinct_curve_counts_new_biomes_at_checkpoints():
    ids = [1, 1, 2, 1, 3, 3, 2, 4]
    assert distinct_curve(ids, [0, 2, 5, 7, 99]) == [1, 2, 3, 4, 4]


def test_zero_budget_is_just_spawn():
    assert straight(3, 4, 1.0, 0, 2) == [(3, 4)]
    assert lawnmower(3, 4, 1.0, 0, 2, leg=10, gap=5) == [(3, 4)]
