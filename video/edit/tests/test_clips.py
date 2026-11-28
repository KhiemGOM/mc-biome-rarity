"""Finding the source file for a [CLIP] and turning clips into visual cuts."""
import os
import pytest
from vo.script_lines import Item
from vo.clips import clip_cuts, find_clip


@pytest.fixture
def media(tmp_path):
    for rel in ("00_cold_open/20210427_RTu-RkcdXpE_The Rarest Biome.mp4", "00_cold_open/20210427_RTu-RkcdXpE_The Rarest Biome.jpg",
                "05_outro/20210427_RTu-RkcdXpE_The Rarest Biome.mp4",  # same file linked into a second bin
                "00_cold_open/a_dup_XYZ.mp4", "02_monte_carlo/b_dup_XYZ.mp4"):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x")
    return str(tmp_path)


def test_finds_the_video_by_its_youtube_id(media):
    assert find_clip(media, "RTu-RkcdXpE") == os.path.join("00_cold_open", "20210427_RTu-RkcdXpE_The Rarest Biome.mp4")


def test_unknown_id_names_it(media):
    with pytest.raises(FileNotFoundError, match="nope123"):
        find_clip(media, "nope123")


def test_id_matching_two_different_files_is_an_error(media):
    with pytest.raises(ValueError, match="XYZ"):
        find_clip(media, "XYZ")


def test_clip_cuts_point_at_the_in_point(media):
    its = [Item("V001", "vo", "0", "hi"), Item("K001", "clip", "0", "quote", clip=("RTu-RkcdXpE", 7.85, 11.2))]
    rel = os.path.join("00_cold_open", "20210427_RTu-RkcdXpE_The Rarest Biome.mp4")
    assert clip_cuts(its, media) == {"K001": f"{rel}@7.85"}


# soft edges on camman's clips: his background music must not snap on or off
import array
from vo.clips import fade_edges


def test_fade_edges_starts_and_ends_silent_and_keeps_the_middle():
    a = array.array("h", [10000] * 1000)
    out = fade_edges(a, 1000, 0.05)
    assert abs(out[0]) < 300 and abs(out[-1]) < 300 and out[500] == 10000 and len(out) == 1000


def test_fade_edges_on_a_clip_shorter_than_two_fades_does_not_crash():
    out = fade_edges(array.array("h", [10000] * 30), 1000, 0.05)
    assert len(out) == 30 and max(out) <= 10000
