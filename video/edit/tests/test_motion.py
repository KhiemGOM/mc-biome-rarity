"""Slow push-in baked onto stills, so charts and screenshots don't sit there flat."""
import os, time
import pytest
from vo.motion import HANDLE, ZOOM_MAX, motion_filter, motion_path, zoom_amount


def test_zoom_grows_with_the_shot_and_is_capped():
    assert 0 < zoom_amount(2.0) < zoom_amount(4.0) <= ZOOM_MAX
    assert zoom_amount(60.0) == ZOOM_MAX and ZOOM_MAX <= 0.08  # never a big obvious zoom


def test_filter_ends_on_the_zoom_amount_over_the_whole_clip():
    f = motion_filter(frames=300, zoom=0.05)
    assert "zoompan" in f and "0.05" in f and "300" in f and "s=1920x1080" in f


def test_same_still_and_length_reuse_one_file(tmp_path):
    p = tmp_path / "chart.png"; p.write_bytes(b"x")
    assert motion_path(str(p), 4.0, str(tmp_path)) == motion_path(str(p), 4.0, str(tmp_path))


def test_new_length_or_edited_image_makes_a_new_file(tmp_path):
    p = tmp_path / "chart.png"; p.write_bytes(b"x")
    a = motion_path(str(p), 4.0, str(tmp_path))
    assert motion_path(str(p), 5.0, str(tmp_path)) != a
    p.write_bytes(b"xy"); os.utime(p, (time.time() + 10, time.time() + 10))
    assert motion_path(str(p), 4.0, str(tmp_path)) != a


def test_clip_has_handles_for_dissolves():
    assert HANDLE >= 0.4  # half of the longest (section) dissolve


# --- freeze-frame padding: hold the first/last frame when a clip has no spare footage for a dissolve or its slot
from vo.motion import pad_needed, pad_path


def test_no_padding_when_there_is_footage_to_spare():
    assert pad_needed(src_in=2.0, slot=3.0, src_dur=20.0) == (0.0, 0.0)


def test_clip_starting_at_zero_gets_its_first_frame_held():
    head, tail = pad_needed(src_in=0.0, slot=3.0, src_dur=20.0)
    assert head >= HANDLE and tail == 0.0


def test_clip_shorter_than_its_slot_holds_its_last_frame_to_fill_it():
    head, tail = pad_needed(src_in=2.0, slot=10.0, src_dur=8.0)  # 6 s of footage for a 10 s slot
    assert head == 0.0 and tail >= 4.0 + HANDLE


def test_padding_is_never_a_frame_short():
    head, tail = pad_needed(src_in=0.13, slot=3.0, src_dur=3.2)
    assert 0.13 + head >= HANDLE - 1e-9 and (3.2 + head + tail) - (0.13 + head) - 3.0 >= HANDLE - 1e-9


def test_padded_copy_is_cached_per_amount(tmp_path):
    p = tmp_path / "clip.mp4"; p.write_bytes(b"x")
    assert pad_path(str(p), 0.4, 0.0, str(tmp_path)) == pad_path(str(p), 0.4, 0.0, str(tmp_path))
    assert pad_path(str(p), 0.4, 0.5, str(tmp_path)) != pad_path(str(p), 0.4, 0.0, str(tmp_path))
