"""Silence between items in the edited voice-over."""
from vo.script_lines import Item
from vo.run import GAP, CLIP_GAP, PAUSE, gap_after

V = lambda pause=False: Item("V001", "vo", "0", "line", pause_after=pause)
K = lambda pause=False: Item("K001", "clip", "0", "camman", clip=("x", 0, 1), pause_after=pause)


def test_between_two_of_your_lines():
    assert gap_after(V(), V()) == GAP


def test_more_room_going_into_and_out_of_a_clip():
    assert gap_after(V(), K()) == CLIP_GAP and gap_after(K(), V()) == CLIP_GAP and gap_after(K(), K()) == CLIP_GAP


def test_beat_wins_when_it_is_longer():
    assert gap_after(V(pause=True), V()) == PAUSE and gap_after(K(pause=True), V()) == max(PAUSE, CLIP_GAP)


def test_last_item_gets_the_normal_gap():
    assert gap_after(V(), None) == GAP


def test_gaps_are_ordered_sensibly():
    assert 0.3 < GAP < CLIP_GAP <= PAUSE
