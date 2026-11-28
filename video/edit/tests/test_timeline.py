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


def placed(xml):
    """Every media clip with absolute times (base shots are lane 0, the main track)."""
    from vo.tweaks import parse_fcpxml
    return parse_fcpxml(xml)


def lane(xml, n):
    return sorted([p for p in placed(xml) if p.lane == n], key=lambda p: p.start)


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
    assert sorted(p.lane for p in placed(xml)) == [-1, 0, 0]  # shots on the main track, VO below
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
    spans = [(p.start, p.end) for p in lane(xml, 0)]
    for (s1, e1), (s2, e2) in zip(spans, spans[1:]):
        assert e1 <= s2 + 1e-9


def test_video_shorter_than_slot_warns_and_is_capped(media):
    clips = [Clip(media["a.mp4"], 0.0, 30.0, kind="video", src_dur=20.0)]
    xml, warnings = build_fcpxml(clips, vo=None, name="t")
    a = lane(xml, 0)[0]
    assert a.end - a.start == pytest.approx(20.0)
    assert warnings and "a.mp4" in warnings[0]


def test_in_point_is_used(media):
    clips = [Clip(media["a.mp4"], 0.0, 2.0, kind="video", src_dur=20.0, src_in=3.0)]
    xml, _ = build_fcpxml(clips, vo=None, name="t")
    assert lane(xml, 0)[0].src_in == pytest.approx(3.0)


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
    assert sorted(p.lane for p in placed(xml)) == [0, 2]  # overlay above the main track


def test_overlay_does_not_push_base_lane(media):
    clips = [Clip(media["b.png"], 0, 4, kind="still", lane=2), Clip(media["a.mp4"], 0, 5, kind="video", src_dur=20)]
    xml, _ = build_fcpxml(clips, vo=None, name="t")
    base = lane(xml, 0)[0]
    assert base.start == 0 and base.end == pytest.approx(5.0)


def test_music_bed_goes_on_its_own_audio_lane(media):
    xml, _ = build_fcpxml([Clip(media["b.png"], 0, 5, kind="still")], vo=(media["vo.wav"], 5.0), name="t",
                          audio=[(media["c.mp4"], 6.0, -2, "music")])
    a = parse(xml).find(".//asset-clip[@lane='-2']")
    assert a is not None and a.get("name") == "music" and a.get("duration") == "360/60s"
    (m,) = lane(xml, -2)
    assert m.start == 0 and m.end == pytest.approx(6.0)
    assert parse(xml).find(".//sequence").get("duration") == "360/60s"  # timeline grows to hold it


def test_missing_music_file_raises(media):
    with pytest.raises(FileNotFoundError, match="bed.wav"):
        build_fcpxml([], vo=None, name="t", audio=[(os.path.join(os.path.dirname(media["a.mp4"]), "bed.wav"), 3.0, -2, "m")])



# --- shots on the main track, so Resolve gets real cross dissolves between them

def test_timeline_has_no_holes_on_the_main_track(media):
    clips = [Clip(media["a.mp4"], 1.0, 3.0, kind="video", src_dur=20, src_in=5), Clip(media["b.png"], 4.0, 6.0, kind="still")]
    root = parse(build_fcpxml(clips, vo=(media["vo.wav"], 7.0), name="t")[0])
    spine = root.find(".//sequence/spine")
    f = lambda v: 0 if v == "0s" else int(v.split("/")[0])
    t = 0
    for el in spine:
        if el.tag == "transition":
            continue
        assert f(el.get("offset")) == t  # gap, clip, gap, clip, gap: back to back from 0
        t += f(el.get("duration"))
    assert t == 7 * 60


def test_cross_dissolve_between_two_shots(media):
    clips = [Clip(media["a.mp4"], 0.0, 3.0, kind="video", src_dur=20, src_in=2),
             Clip(media["c.mp4"], 3.0, 6.0, kind="video", src_dur=20, src_in=2, trans_in=0.4)]
    root = parse(build_fcpxml(clips, vo=None, name="t")[0])
    (tr,) = root.findall(".//spine/transition")
    assert tr.get("offset") == f"{int(2.8 * 60)}/60s" and tr.get("duration") == "24/60s"  # centred on the cut
    assert "Dissolve" in tr.get("name")


def test_no_dissolve_when_the_clip_has_no_footage_before_its_in_point(media):
    clips = [Clip(media["a.mp4"], 0.0, 3.0, kind="video", src_dur=20, src_in=2),
             Clip(media["c.mp4"], 3.0, 6.0, kind="video", src_dur=20, src_in=0.0, trans_in=0.4)]  # starts at 0
    assert parse(build_fcpxml(clips, vo=None, name="t")[0]).findall(".//spine/transition") == []


def test_no_dissolve_when_the_outgoing_clip_has_no_footage_left(media):
    clips = [Clip(media["a.mp4"], 0.0, 3.0, kind="video", src_dur=3.0, src_in=0.0),  # ends exactly at its last frame
             Clip(media["b.png"], 3.0, 6.0, kind="still", trans_in=0.4)]
    assert parse(build_fcpxml(clips, vo=None, name="t")[0]).findall(".//spine/transition") == []


def test_stills_can_always_dissolve(media):
    clips = [Clip(media["b.png"], 0.0, 3.0, kind="still"), Clip(media["b.png"], 3.0, 6.0, kind="still", trans_in=0.8)]
    (tr,) = parse(build_fcpxml(clips, vo=None, name="t")[0]).findall(".//spine/transition")
    assert tr.get("duration") == "48/60s"


def test_connected_clips_keep_their_absolute_times_inside_a_shot_with_an_in_point(media):
    # an overlay starting during a shot whose source in point is 5 s: it hangs off that shot, in the shot's own time
    clips = [Clip(media["a.mp4"], 1.0, 6.0, kind="video", src_dur=20, src_in=5.0), Clip(media["b.png"], 2.5, 4.0, kind="still", lane=2)]
    xml, _ = build_fcpxml(clips, vo=(media["vo.wav"], 7.0), name="t", vo_pieces=[(1.2, 3.0, 1.2, "V001")])
    (ov,) = lane(xml, 2)
    (vo,) = lane(xml, -1)
    assert ov.start == pytest.approx(2.5) and ov.end == pytest.approx(4.0)
    assert vo.start == pytest.approx(1.2) and vo.src_in == pytest.approx(1.2)


def test_markers_still_land_on_their_lines(media):
    clips = [Clip(media["a.mp4"], 1.0, 6.0, kind="video", src_dur=20, src_in=5.0)]
    root = parse(build_fcpxml(clips, vo=(media["vo.wav"], 7.0), name="t", markers=[(3.0, "V002 x")])[0])
    (m,) = root.findall(".//marker")
    parent = [el for el in root.iter() if m in list(el)][0]
    f = lambda v: 0 if v in (None, "0s") else int(v.split("/")[0]) / 60
    assert f(parent.get("offset")) + (f(m.get("start")) - f(parent.get("start"))) == pytest.approx(3.0)
