import os, re, xml.etree.ElementTree as ET
import pytest
from vo.timeline import Clip, build_fcpxml, frames


@pytest.fixture
def media(tmp_path):
    d = tmp_path / "my media #1"
    d.mkdir()
    paths = {}
    for n in ("a.mp4", "b.png", "c.mp4", "vo.wav"):
        p = d / n
        p.write_bytes(b"x")
        paths[n] = str(p)
    return paths


def parse(xml):
    return ET.fromstring(xml)


def test_frames_rounding():
    assert frames(1.0, 60) == 60
    assert frames(1.009, 60) == 61  # rounds to nearest frame
    assert frames(0.0, 60) == 0


def test_valid_xml_with_visuals_and_vo(media):
    clips = [Clip(media["a.mp4"], 0.0, 5.0, kind="video", src_dur=20.0),
             Clip(media["b.png"], 5.0, 8.0, kind="still")]
    xml, warnings = build_fcpxml(clips, vo=(media["vo.wav"], 8.0), name="t")
    root = parse(xml)
    assert root.tag == "fcpxml"
    acs = root.findall(".//asset-clip")
    assert len(acs) == 3  # 2 visuals + vo
    lanes = sorted(int(a.get("lane")) for a in acs)
    assert lanes == [-1, 1, 1]
    assert warnings == []


def test_times_are_whole_frames(media):
    clips = [Clip(media["a.mp4"], 0.013, 4.987, kind="video", src_dur=20.0)]
    xml, _ = build_fcpxml(clips, vo=None, name="t")
    for v in re.findall(r'(?:offset|duration|start)="([^"]+)"', xml):
        if v == "0s":
            continue
        m = re.fullmatch(r"(\d+)/60s", v)
        assert m, v


def test_no_overlap_on_visual_lane(media):
    clips = [Clip(media["a.mp4"], 0.0, 6.0, kind="video", src_dur=20.0),
             Clip(media["c.mp4"], 5.0, 9.0, kind="video", src_dur=20.0)]
    xml, _ = build_fcpxml(clips, vo=None, name="t")
    spans = []
    for a in parse(xml).findall(".//asset-clip[@lane='1']"):
        f = lambda v: 0 if v == "0s" else int(v.split("/")[0])
        o = f(a.get("offset")); d = f(a.get("duration"))
        spans.append((o, o + d))
    spans.sort()
    for (s1, e1), (s2, e2) in zip(spans, spans[1:]):
        assert e1 <= s2


def test_video_shorter_than_slot_warns_and_is_capped(media):
    clips = [Clip(media["a.mp4"], 0.0, 30.0, kind="video", src_dur=20.0)]
    xml, warnings = build_fcpxml(clips, vo=None, name="t")
    a = parse(xml).find(".//asset-clip[@lane='1']")
    assert a.get("duration") == f"{20*60}/60s"
    assert warnings and "a.mp4" in warnings[0]


def test_in_point_is_used(media):
    clips = [Clip(media["a.mp4"], 0.0, 2.0, kind="video", src_dur=20.0, src_in=3.0)]
    xml, _ = build_fcpxml(clips, vo=None, name="t")
    assert parse(xml).find(".//asset-clip[@lane='1']").get("start") == "180/60s"


def test_paths_with_space_and_hash_are_url_encoded(media):
    xml, _ = build_fcpxml([Clip(media["b.png"], 0, 1, kind="still")], vo=None, name="t")
    srcs = [m.get("src") for m in parse(xml).findall(".//media-rep")]
    assert srcs and all(s.startswith("file:///") for s in srcs)
    assert "%20" in srcs[0] and "%23" in srcs[0] and " " not in srcs[0] and "#" not in srcs[0]


def test_missing_file_raises(media):
    with pytest.raises(FileNotFoundError, match="nope.mp4"):
        build_fcpxml([Clip(os.path.join(os.path.dirname(media["a.mp4"]), "nope.mp4"), 0, 1, kind="video", src_dur=5)], vo=None, name="t")


def test_same_file_twice_uses_one_asset(media):
    clips = [Clip(media["a.mp4"], 0, 1, kind="video", src_dur=20), Clip(media["a.mp4"], 1, 2, kind="video", src_dur=20, src_in=5)]
    xml, _ = build_fcpxml(clips, vo=None, name="t")
    assert len(parse(xml).findall(".//asset")) == 1


def test_markers_for_script_lines(media):
    xml, _ = build_fcpxml([Clip(media["b.png"], 0, 5, kind="still")], vo=None, name="t",
                          markers=[(0.0, "V001 first line"), (2.5, "V002 <quote> & more")])
    ms = parse(xml).findall(".//marker")
    assert [m.get("value") for m in ms] == ["V001 first line", "V002 <quote> & more"]
    assert ms[1].get("start") == "150/60s"


def test_overlay_lane(media):
    clips = [Clip(media["a.mp4"], 0, 5, kind="video", src_dur=20), Clip(media["b.png"], 1, 3, kind="still", lane=2)]
    xml, _ = build_fcpxml(clips, vo=None, name="t")
    lanes = sorted(a.get("lane") for a in parse(xml).findall(".//asset-clip"))
    assert lanes == ["1", "2"]


def test_overlay_does_not_push_base_lane(media):
    clips = [Clip(media["b.png"], 0, 4, kind="still", lane=2), Clip(media["a.mp4"], 0, 5, kind="video", src_dur=20)]
    xml, _ = build_fcpxml(clips, vo=None, name="t")
    base = parse(xml).find(".//asset-clip[@lane='1']")
    assert base.get("offset") == "0s" and base.get("duration") == "300/60s"


def test_music_bed_goes_on_its_own_audio_lane(media):
    xml, _ = build_fcpxml([Clip(media["b.png"], 0, 5, kind="still")], vo=(media["vo.wav"], 5.0), name="t",
                          audio=[(media["c.mp4"], 6.0, -2, "music")])
    a = parse(xml).find(".//asset-clip[@lane='-2']")
    assert a is not None and a.get("name") == "music" and a.get("duration") == "360/60s"
    assert parse(xml).find(".//sequence").get("duration") == "360/60s"  # timeline grows to hold it


def test_missing_music_file_raises(media):
    with pytest.raises(FileNotFoundError, match="bed.wav"):
        build_fcpxml([], vo=None, name="t", audio=[(os.path.join(os.path.dirname(media["a.mp4"]), "bed.wav"), 3.0, -2, "m")])
