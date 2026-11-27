"""Music bed: one track per section, ducked under the voice, muted on the cue lines."""
import numpy as np
import pytest
from vo.script_lines import Item
from vo.music import (CR, DUCK, OPEN, find_line, gain_curve, place, resolve_mutes, section_spans, speech_spans)


def its():
    return [Item("V001", "vo", "0", "Hello there."), Item("V002", "vo", "0", "Proven, within a margin."),
            Item("C001", "card", "0", "", ["VISUAL: title card"]),
            Item("V003", "vo", "1", "What does rare mean?"), Item("V004", "vo", "1", "And number one."),
            Item("V005", "vo", "1", "Mushroom fields.")]


TIMES = {"V001": (0.0, 2.0), "V002": (2.3, 5.0), "C001": (5.3, 8.3), "V003": (8.3, 12.0),
         "V004": (12.3, 13.0), "V005": (13.8, 20.0)}


def at(curve, sec):
    return curve[int(round(sec * CR))]


# sections
def test_sections_run_from_first_line_to_the_next_section():
    assert section_spans(its(), TIMES, 25.0) == [("0", 0.0, 8.3), ("1", 8.3, 25.0)]


def test_section_with_no_recorded_lines_is_skipped():
    t = {k: v for k, v in TIMES.items() if k in ("V003", "V004", "V005")}
    assert section_spans(its(), t, 25.0) == [("1", 8.3, 25.0)]


def test_speech_spans_are_voice_lines_only():
    assert speech_spans(its(), TIMES) == [(0.0, 2.0), (2.3, 5.0), (8.3, 12.0), (12.3, 13.0), (13.8, 20.0)]


# cue lines are found by their text, so renumbering the script doesn't break them
def test_find_line_by_text():
    assert find_line(its(), "number one") == "V004"


def test_find_line_missing_text_names_it():
    with pytest.raises(ValueError, match="pale garden"):
        find_line(its(), "pale garden")


def test_find_line_ambiguous_text_is_an_error():
    with pytest.raises(ValueError, match="2 lines"):
        find_line(its(), "e.")  # "there." and "one."


def test_mute_from_end_of_line_to_section_end():
    spans = section_spans(its(), TIMES, 25.0)
    assert resolve_mutes([("Proven", "end", None)], its(), TIMES, spans) == [(5.0, 8.3)]


def test_mute_from_start_of_line_to_start_of_another():
    spans = section_spans(its(), TIMES, 25.0)
    assert resolve_mutes([("number one", "start", "Mushroom fields")], its(), TIMES, spans) == [(12.3, 13.8)]


def test_mute_that_ends_before_it_starts_is_an_error():
    spans = section_spans(its(), TIMES, 25.0)
    with pytest.raises(ValueError):
        resolve_mutes([("Mushroom fields", "start", "number one")], its(), TIMES, spans)


# gain curve
def curve(mutes=(), level=None, length=25.0):
    return gain_curve(length, speech_spans(its(), TIMES), list(mutes), section_spans(its(), TIMES, length), level or {})


def test_music_is_ducked_under_speech():
    assert at(curve(), 10.0) == pytest.approx(DUCK, abs=1e-3)


def test_music_comes_up_in_a_long_gap():
    assert at(curve(), 23.0) == pytest.approx(OPEN, abs=1e-3)  # 5 s after the last line


def test_short_gaps_between_lines_stay_ducked():
    c = curve()
    assert max(c[int(12.0 * CR):int(12.3 * CR)]) <= DUCK + 1e-3


def test_muted_span_is_silent_and_comes_back():
    c = curve(mutes=[(12.3, 13.8)])
    assert at(c, 13.0) == 0 and at(c, 16.0) == pytest.approx(DUCK, abs=1e-3)


def test_gain_never_jumps_more_than_a_fade_allows():
    c = curve(mutes=[(5.0, 8.3), (12.3, 13.8)])
    assert np.max(np.abs(np.diff(c))) <= OPEN / (0.05 * CR) + 1e-9  # no step faster than a 50 ms fade


def test_gain_stays_between_silent_and_open():
    c = curve(mutes=[(12.3, 13.8)], level={"1": 1.5})
    assert c.min() >= 0 and c.max() <= OPEN + 1e-9


def test_section_level_scales_that_section_only():
    c = curve(level={"1": 0.5})
    assert at(c, 10.0) == pytest.approx(DUCK * 0.5, abs=1e-3) and at(c, 1.0) == pytest.approx(DUCK, abs=1e-3)


def test_music_fades_out_at_a_section_change():
    c = curve()
    assert at(c, 8.3 - 0.01) < 0.1 * DUCK


def test_curve_covers_the_whole_video():
    assert len(curve(length=25.0)) == int(25.0 * CR) + 1


# placing a track in its section
def test_long_track_is_trimmed_to_the_section():
    tr = np.ones((10 * 100, 2), np.float32)
    assert place(tr, 100, 4.0).shape == (400, 2)


def test_short_track_loops_to_fill_the_section():
    tr = np.ones((300, 2), np.float32)  # 3 s at 100 Hz
    out = place(tr, 100, 8.0, xfade=0.5)
    assert out.shape == (800, 2) and out[700:].min() > 0.99  # still playing at the end, no hole


def test_loop_crossfade_has_no_dip():
    tr = np.ones((300, 2), np.float32)
    out = place(tr, 100, 8.0, xfade=0.5)
    assert out.min() > 0.99  # equal-gain crossfade of a constant stays constant
