import pytest
from vo.cuts import parse_files, segments


def test_parse_files_with_in_points():
    assert parse_files("a/x.mp4@12.5; b/y.png") == [("a/x.mp4", 12.5), ("b/y.png", 0.0)]
    assert parse_files("") == []


def test_visual_holds_until_next_line_with_files():
    times = {"V001": (0, 4), "V002": (4, 9), "V003": (9, 12)}
    cuts = {"V001": "a.png", "V002": "", "V003": "b.png"}
    segs = segments(["V001", "V002", "V003"], times, cuts, end=15)
    assert segs == [("a.png", 0.0, 0, 9), ("b.png", 0.0, 9, 15)]


def test_two_files_split_the_slot_evenly():
    segs = segments(["V001"], {"V001": (0, 10)}, {"V001": "a.mp4; b.mp4@3"}, end=10)
    assert segs == [("a.mp4", 0.0, 0, 5), ("b.mp4", 3.0, 5, 10)]


def test_first_line_without_files_leaves_a_gap():
    segs = segments(["V001", "V002"], {"V001": (0, 2), "V002": (2, 5)}, {"V002": "a.png"}, end=5)
    assert segs == [("a.png", 0.0, 2, 5)]


def test_unknown_id_in_cuts_raises():
    with pytest.raises(KeyError, match="V999"):
        segments(["V001"], {"V001": (0, 1)}, {"V999": "a.png"}, end=1)


def test_line_missing_from_recording_is_skipped_not_fatal():
    times = {"V001": (0, 4), "V003": (4, 8)}
    segs = segments(["V001", "V002", "V003"], times, {"V001": "a.png", "V002": "b.png", "V003": "c.png"}, end=8)
    assert segs == [("a.png", 0.0, 0, 4), ("c.png", 0.0, 4, 8)]


def test_overlays_cover_only_their_own_line():
    from vo.cuts import overlay_segments
    times = {"V001": (0, 4), "V002": (4.3, 9), "V003": (9.2, 12)}
    segs = overlay_segments(["V001", "V002", "V003"], times, {"V002": "lt.png"})
    assert segs == [("lt.png", 0.0, 4.3, 9)]
