import array, json
import pytest
from vo.labels import parse_getinfo, takes_from_labels, speech_bounds, join_labels

IDS = ["V001", "V002", "V003"]
SR = 1000  # small sample rate keeps the synthetic audio tiny


def tone(sec, amp=8000):
    return [amp if i % 2 else -amp for i in range(int(sec * SR))]


def silence(sec, amp=0):
    return [amp] * int(sec * SR)


# --- parse_getinfo: Audacity "GetInfo: Type=Labels Format=JSON" -> sorted [(t, text)]

def test_parse_getinfo_basic():
    raw = json.dumps([[1, [[2.5, 2.5, "V002"], [0.5, 0.5, "V001"]]]])
    assert parse_getinfo(raw) == [(0.5, "V001"), (2.5, "V002")]


def test_parse_getinfo_several_label_tracks_and_empty():
    raw = json.dumps([[1, [[3.0, 3.0, "V003"]]], [4, [[1.0, 1.0, "V001"]]], [5, []]])
    assert parse_getinfo(raw) == [(1.0, "V001"), (3.0, "V003")]
    assert parse_getinfo("[]") == []


def test_parse_getinfo_strips_text():
    assert parse_getinfo(json.dumps([[0, [[1.0, 1.0, " V001 "]]]])) == [(1.0, "V001")]


# --- takes_from_labels: last good take per line, ends at the next label of any kind

def test_takes_basic_order():
    labels = [(1.0, "V001"), (4.0, "V002"), (9.0, "V003")]
    t, missing = takes_from_labels(labels, IDS, end=12.0)
    assert t == {"V001": (1.0, 4.0), "V002": (4.0, 9.0), "V003": (9.0, 12.0)}
    assert missing == []


def test_takes_retake_keeps_last():
    labels = [(1.0, "V001"), (3.0, "V001"), (6.0, "V002")]
    t, _ = takes_from_labels(labels, IDS[:2], end=8.0)
    assert t["V001"] == (3.0, 6.0)


def test_takes_unsorted_and_unknown_labels_ignored_but_still_end_a_take():
    labels = [(5.0, "note: cough"), (1.0, "V001"), (7.0, "V002")]
    t, _ = takes_from_labels(labels, IDS[:2], end=9.0)
    assert t["V001"] == (1.0, 5.0)  # an unknown label still marks where the take stops
    assert t["V002"] == (7.0, 9.0)


def test_takes_too_short_falls_back_to_previous_take():
    # double press: the last V001 take is 0.1 s long, so the earlier full take is used
    labels = [(1.0, "V001"), (4.0, "V001"), (4.1, "V002")]
    t, _ = takes_from_labels(labels, IDS[:2], end=8.0, min_len=0.4)
    assert t["V001"] == (1.0, 4.0)


def test_takes_missing_lines_reported_in_script_order():
    t, missing = takes_from_labels([(1.0, "V002")], IDS, end=3.0)
    assert list(t) == ["V002"]
    assert missing == ["V001", "V003"]


def test_takes_only_too_short_take_is_missing():
    t, missing = takes_from_labels([(1.0, "V001"), (1.1, "V002")], IDS[:2], end=5.0, min_len=0.4)
    assert "V001" not in t and missing == ["V001"]


def test_takes_no_labels():
    assert takes_from_labels([], IDS, end=5.0) == ({}, IDS)


# --- join_labels: several files -> one timeline, offset by the earlier files' lengths

def test_join_labels_offsets():
    a = [(1.0, "V001")]
    b = [(0.5, "V002"), (2.0, "V003")]
    # each file's end becomes a boundary marker ("|"), so a take never runs into the next file
    assert join_labels([(a, 10.0), (b, 5.0)]) == [(1.0, "V001"), (10.0, "|"), (10.5, "V002"), (12.0, "V003"), (15.0, "|")]


def test_join_labels_file_boundary_ends_a_take():
    # the last take of file 1 must not run into file 2's room tone: a boundary marker ends it
    out = join_labels([([(1.0, "V001")], 10.0), ([(3.0, "V002")], 5.0)])
    t, _ = takes_from_labels(out, IDS[:2], end=15.0)
    assert t["V001"] == (1.0, 10.0)
    assert t["V002"] == (13.0, 15.0)


# --- speech_bounds: trim silence and the keypress click inside a take

def test_speech_bounds_trims_silence():
    a = array.array("h", silence(1.0) + tone(2.0) + silence(1.0))
    s, e = speech_bounds(a, SR, 0.0, 4.0, skip=0.0, pad=0.0)
    assert abs(s - 1.0) < 0.03 and abs(e - 3.0) < 0.03


def test_speech_bounds_skips_key_click():
    # a loud 20 ms click right at the label, then silence, then speech
    a = array.array("h", tone(0.02, 30000) + silence(0.5) + tone(1.0) + silence(0.5))
    s, e = speech_bounds(a, SR, 0.0, 2.02, skip=0.15, pad=0.0)
    assert abs(s - 0.52) < 0.03


def test_speech_bounds_with_room_noise():
    a = array.array("h", silence(1.0, 200) + tone(1.0) + silence(1.0, 200))
    s, e = speech_bounds(a, SR, 0.0, 3.0, skip=0.0, pad=0.0)
    assert abs(s - 1.0) < 0.03 and abs(e - 2.0) < 0.03


def test_speech_bounds_pad_and_clamp():
    a = array.array("h", tone(1.0) + silence(1.0))
    s, e = speech_bounds(a, SR, 0.0, 2.0, skip=0.0, pad=0.1)
    assert s == 0.0 and abs(e - 1.1) < 0.03


def test_speech_bounds_all_silent_returns_none():
    a = array.array("h", silence(2.0))
    assert speech_bounds(a, SR, 0.0, 2.0) is None


# --- label_takes: joined files + audio -> trimmed takes, the way the align step uses it

from vo.labels import label_takes


def test_label_takes_two_files_trimmed_and_retake():
    # file 1 (4 s): V001 read, flubbed, retaken.  file 2 (3 s): V002.
    f1 = silence(0.3) + tone(0.5) + silence(0.7) + silence(0.3) + tone(1.5) + silence(0.7)   # 4.0 s
    f2 = silence(0.5) + tone(2.0) + silence(0.5)                                             # 3.0 s
    a = array.array("h", f1 + f2)
    files = [([(0.0, "V001"), (1.5, "V001")], 4.0), ([(0.2, "V002")], 3.0)]
    takes, missing = label_takes(files, IDS[:2], a, SR, pad=0.0)
    assert missing == []
    s, e = takes["V001"]; assert abs(s - 1.8) < 0.03 and abs(e - 3.3) < 0.03
    s, e = takes["V002"]; assert abs(s - 4.5) < 0.03 and abs(e - 6.5) < 0.03


def test_label_takes_silent_take_is_missing():
    a = array.array("h", silence(3.0))
    takes, missing = label_takes([([(0.0, "V001")], 3.0)], IDS[:1], a, SR)
    assert takes == {} and missing == ["V001"]
