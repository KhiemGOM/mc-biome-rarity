"""Resolve round trip: read an edited timeline back, turn the edits into tweaks anchored to script lines, apply them."""
import xml.etree.ElementTree as ET
from fractions import Fraction
import pytest
from vo.script_lines import Item
from vo.timeline import Clip, build_fcpxml
from vo.tweaks import (Placed, anchor_of, apply_visuals, gap_for, merge, parse_fcpxml, positions, read_back, resolve,
                       update_clip_times)

FPS = 60


@pytest.fixture
def media(tmp_path):
    paths = {}
    for n in ("a.mp4", "b.png", "c.mp4", "d.png", "gag.png", "vo_edit.wav", "music_bed.wav"):
        p = tmp_path / n
        p.write_bytes(b"x")
        paths[n] = str(p)
    return paths


ITEMS = [Item("V001", "vo", "0", "one"), Item("K001", "clip", "0", "camman", clip=("abc", 10.0, 14.0)),
         Item("V002", "vo", "0", "two"), Item("V003", "vo", "0", "three")]
TIMES = {"V001": (0.0, 3.0), "K001": (3.6, 7.6), "V002": (8.2, 11.0), "V003": (11.45, 15.0)}


def generated(media):
    """A small generated timeline: per-line VO pieces, keyed visuals, one overlay, the music bed."""
    clips = [Clip(media["a.mp4"], 0.0, 3.6, kind="video", src_dur=60, src_in=2.0, key="V001#0"),
             Clip(media["c.mp4"], 3.6, 8.2, kind="video", src_dur=60, src_in=10.0, key="K001#0"),
             Clip(media["b.png"], 8.2, 11.45, kind="still", key="V002#0"),
             Clip(media["d.png"], 11.45, 15.0, kind="still", key="V003#0"),
             Clip(media["gag.png"], 9.0, 11.0, kind="still", lane=2, key="ov:V002#0")]
    pieces = [(a, b, a, i) for i, (a, b) in TIMES.items()]
    xml, _ = build_fcpxml(clips, vo=(media["vo_edit.wav"], 15.0), name="t", vo_pieces=pieces,
                          audio=[(media["music_bed.wav"], 15.0, -2, "music bed")])
    return xml


def edit(xml, fn):
    """Apply fn to every asset-clip element (as a user would in Resolve) and return the new XML."""
    root = ET.fromstring(xml)
    for el in root.iter("asset-clip"):
        fn(el)
    return ET.tostring(root, encoding="unicode")


def sec(v):
    return float(Fraction(v[:-1])) if v != "0s" else 0.0


def setsec(el, attr, s):
    el.set(attr, f"{round(s * FPS)}/{FPS}s")


def attach(root, at, **attrs):
    """Hang a new clip off the main-track element playing at `at` seconds, in that element's own time (as Resolve does)."""
    els = [el for el in root.find(".//sequence/spine") if el.tag != "transition"]
    parent = [el for el in els if sec(el.get("offset")) <= at + 1e-9][-1]
    local = sec(parent.get("start") or "0s") + at - sec(parent.get("offset"))
    ET.SubElement(parent, "asset-clip", offset=f"{round(local * FPS)}/{FPS}s", **attrs)


def tw(media, new_xml, gen_xml=None):
    gen_xml = gen_xml or generated(media)
    return read_back(parse_fcpxml(new_xml), parse_fcpxml(gen_xml), ITEMS, TIMES, vo_name="vo_edit.wav",
                     music_name="music_bed.wav", media=str(media and __import__("os").path.dirname(media["a.mp4"])))


# --- the generated timeline carries what the round trip needs

def test_voice_over_is_one_clip_per_line(media):
    vo = sorted([p for p in parse_fcpxml(generated(media)) if p.lane == -1], key=lambda p: p.start)
    assert [p.name for p in vo] == ["V001", "K001", "V002", "V003"]
    assert vo[2].start == pytest.approx(8.2, abs=1 / FPS) and vo[2].src_in == pytest.approx(8.2, abs=1 / FPS)


def test_generated_clips_carry_their_key_in_the_name(media):
    names = [p.name for p in sorted(parse_fcpxml(generated(media)), key=lambda p: p.start) if p.lane == 0]
    assert names[0].startswith("V001#0 ")


# --- parsing

def test_parse_gives_absolute_times_lanes_and_files(media):
    ps = parse_fcpxml(generated(media))
    v2 = [p for p in ps if p.name.startswith("V002#0")][0]
    assert v2.lane == 0 and v2.path.endswith("b.png")  # base shots sit on the main track and v2.start == pytest.approx(8.2, abs=0.02)
    assert v2.end == pytest.approx(11.45, abs=0.02)


def test_parse_handles_resolve_style_nesting_and_odd_rationals(tmp_path):
    # Resolve puts connected clips inside a spine clip whose own start is not 0: child times are in the parent's time
    f = tmp_path / "x.mp4"; f.write_bytes(b"x")
    xml = f"""<?xml version="1.0"?><fcpxml version="1.9"><resources>
      <asset id="r1" name="x"><media-rep kind="original-media" src="file:///{str(f).replace(chr(92), '/')}"/></asset></resources>
      <library><event><project><sequence><spine>
        <asset-clip ref="r1" offset="10s" start="100s" duration="20s" name="base">
          <asset-clip ref="r1" lane="1" offset="105s" start="3003/1000s" duration="2s" name="over"/>
        </asset-clip></spine></sequence></project></event></library></fcpxml>"""
    ps = {p.name: p for p in parse_fcpxml(xml)}
    assert ps["base"].start == 10 and ps["base"].lane == 0 and ps["base"].src_in == 100
    assert ps["over"].start == pytest.approx(15.0) and ps["over"].lane == 1 and ps["over"].src_in == pytest.approx(3.003)


# --- line positions from the voice-over pieces

def test_positions_follow_dragged_voice_pieces(media):
    def drag(el):
        if el.get("name") in ("V002", "V003"):
            setsec(el, "offset", sec(el.get("offset")) + 1.0)
    pos = positions(parse_fcpxml(edit(generated(media), drag)), ITEMS, TIMES, "vo_edit.wav")
    assert pos["V002"][0] == pytest.approx(9.2, abs=0.02) and pos["V001"][0] == pytest.approx(0.0, abs=0.02)


# --- reading edits back

def test_untouched_timeline_gives_no_tweaks(media):
    t, notes = tw(media, generated(media))
    assert t == {"gap_after": {}, "visual": {}, "extra": [], "clip_times": {}}


def test_more_room_after_a_line_becomes_a_gap_tweak(media):
    def drag(el):
        if el.get("name") in ("V002", "V003"):
            setsec(el, "offset", sec(el.get("offset")) + 1.0)
    t, _ = tw(media, edit(generated(media), drag))
    assert t["gap_after"] == {"K001": pytest.approx(1.6, abs=0.02)}  # 0.6 s gap became 1.6 s, nothing else changed


def test_shot_end_moved_is_anchored_to_a_line(media):
    def trim(el):
        if (el.get("name") or "").startswith("V001#0"):
            setsec(el, "duration", 2.5)  # ends 0.5 s before V001's line ends
    t, _ = tw(media, edit(generated(media), trim))
    assert t["visual"] == {"V001#0": {"end": ["V001", pytest.approx(2.5, abs=0.02)]}}


def test_swapped_shot_and_new_in_point(media):
    def swap(el):
        if (el.get("name") or "").startswith("V002#0"):
            el.set("ref", [a for a in ET.fromstring(generated(media)).iter("asset") if a.get("name") == "a.mp4"][0].get("id"))
            setsec(el, "start", 30.0)
    t, _ = tw(media, edit(generated(media), swap))
    v = t["visual"]["V002#0"]
    assert v["file"] == "a.mp4" and v["src_in"] == pytest.approx(30.0, abs=0.02)


def test_deleted_shot(media):
    root = ET.fromstring(generated(media))
    for parent in root.iter():
        for el in list(parent):
            if el.tag == "asset-clip" and (el.get("name") or "").startswith("ov:V002#0"):
                parent.remove(el)
    t, _ = tw(media, ET.tostring(root, encoding="unicode"))
    assert t["visual"] == {"ov:V002#0": {"deleted": True}}


def test_added_shot_is_an_extra_anchored_to_lines(media):
    root = ET.fromstring(generated(media))
    ref = [a for a in root.iter("asset") if a.get("name") == "gag.png"][0].get("id")
    attach(root, 12.0, ref=ref, lane="2", start="0s", duration=f"{2 * FPS}/{FPS}s", name="gag.png")
    t, _ = tw(media, ET.tostring(root, encoding="unicode"))
    (x,) = t["extra"]
    assert x["file"] == "gag.png" and x["lane"] == "overlay"
    assert x["start"] == ["V003", pytest.approx(0.55, abs=0.02)] and x["end"] == ["V003", pytest.approx(2.55, abs=0.02)]


def test_trimmed_camman_clip_becomes_new_clip_times(media):
    def trim(el):
        if el.get("name") == "K001":  # trim 1 s off the front of his clip on A1
            setsec(el, "start", 4.6); setsec(el, "offset", sec(el.get("offset")) + 1.0); setsec(el, "duration", 3.0)
    t, _ = tw(media, edit(generated(media), trim))
    assert t["clip_times"] == {"K001": [pytest.approx(11.0, abs=0.02), pytest.approx(14.0, abs=0.02)]}


def test_linked_audio_of_video_clips_is_ignored(media):
    root = ET.fromstring(generated(media))
    ref = [a for a in root.iter("asset") if a.get("name") == "c.mp4"][0].get("id")
    attach(root, 3.6, ref=ref, lane="-3", start="600/60s", duration=f"{4 * FPS}/{FPS}s", name="c.mp4")
    t, _ = tw(media, ET.tostring(root, encoding="unicode"))
    assert t["extra"] == []


def test_a_line_missing_from_the_import_is_reported_not_a_crash(media):
    root = ET.fromstring(generated(media))
    for parent in root.iter():
        for el in list(parent):
            if el.tag == "asset-clip" and el.get("name") == "V003":
                parent.remove(el)
    t, notes = tw(media, ET.tostring(root, encoding="unicode"))
    assert any("V003" in n for n in notes) and t["gap_after"] == {}


# --- applying tweaks on the next build

def test_anchor_round_trip():
    pos = {"V001": (0.0, 3.0), "V002": (8.2, 11.0)}
    assert anchor_of(9.0, pos) == ["V002", pytest.approx(0.8)] and resolve(["V002", 0.8], pos) == pytest.approx(9.0)


def test_anchor_follows_new_timing():
    assert resolve(["V002", 0.8], {"V002": (20.0, 25.0)}) == pytest.approx(20.8)  # re-recorded: V002 now at 20 s


def test_apply_visuals_moves_swaps_deletes_and_adds():
    segs = [("V001#0", "a.mp4", 2.0, 0.0, 3.6, 1), ("V002#0", "b.png", 0.0, 8.2, 11.45, 1),
            ("ov:V002#0", "gag.png", 0.0, 9.0, 11.0, 2)]
    tweaks = {"visual": {"V001#0": {"end": ["V001", 2.5]}, "V002#0": {"file": "a.mp4", "src_in": 30.0},
                         "ov:V002#0": {"deleted": True}},
              "extra": [{"lane": "overlay", "file": "gag.png", "src_in": 0.0, "start": ["V003", 0.55], "end": ["V003", 2.55]}]}
    out, notes = apply_visuals(segs, tweaks, TIMES)
    assert ("a.mp4", 2.0, 0.0, 2.5, 1) in out and ("a.mp4", 30.0, 8.2, 11.45, 1) in out
    assert not any(o[0] == "gag.png" and o[2] == 9.0 for o in out)
    assert ("gag.png", 0.0, pytest.approx(12.0), pytest.approx(14.0), 2) in out


def test_tweak_for_a_line_that_no_longer_exists_is_skipped_with_a_note():
    out, notes = apply_visuals([("V001#0", "a.mp4", 0.0, 0.0, 3.0, 1)],
                               {"visual": {"V001#0": {"end": ["V099", 1.0]}}, "extra": []}, TIMES)
    assert out == [("a.mp4", 0.0, 0.0, 3.0, 1)] and any("V099" in n for n in notes)


def test_gap_tweak_overrides_the_default():
    assert gap_for("V002", 0.45, {"gap_after": {"V002": 1.2}}) == 1.2 and gap_for("V003", 0.45, {"gap_after": {}}) == 0.45


def test_merging_a_second_import_keeps_earlier_tweaks():
    old = {"gap_after": {"V001": 1.0}, "visual": {"V001#0": {"end": ["V001", 2.5]}}, "extra": [], "clip_times": {}}
    new = {"gap_after": {"V002": 0.9}, "visual": {"V001#0": {"src_in": 4.0}}, "extra": [], "clip_times": {}}
    m = merge(old, new)
    assert m["gap_after"] == {"V001": 1.0, "V002": 0.9}
    assert m["visual"]["V001#0"] == {"end": ["V001", 2.5], "src_in": 4.0}


def test_clip_times_are_written_into_the_script():
    s = 'intro\n[CLIP: abc 10.00-14.00 "camman talking"]\nmore\n'
    assert update_clip_times(s, "abc", (10.0, 14.0), (11.0, 14.0)) == 'intro\n[CLIP: abc 11.00-14.00 "camman talking"]\nmore\n'


def test_moving_only_voice_clips_leaves_shots_following_their_lines(media):
    # you dragged V002 and V003 later but didn't touch the pictures: they should keep following the lines
    def drag(el):
        if el.get("name") in ("V002", "V003"):
            setsec(el, "offset", sec(el.get("offset")) + 1.0)
    t, _ = tw(media, edit(generated(media), drag))
    assert t["visual"] == {} and t["extra"] == []


def test_trimming_camman_audio_never_pulls_his_video_out_of_sync(media):
    def trim(el):
        if el.get("name") == "K001":
            setsec(el, "start", 4.6); setsec(el, "offset", sec(el.get("offset")) + 1.0); setsec(el, "duration", 3.0)
        if (el.get("name") or "").startswith("K001#0"):  # even if you also drag his picture somewhere odd
            setsec(el, "offset", 5.0); setsec(el, "start", 99.0)
    t, _ = tw(media, edit(generated(media), trim))
    assert "start" not in t["visual"].get("K001#0", {}) and "src_in" not in t["visual"].get("K001#0", {})


def test_apply_ignores_start_and_in_point_tweaks_on_camman_clips():
    out, _ = apply_visuals([("K001#0", "c.mp4", 10.0, 3.6, 8.2, 1)],
                           {"visual": {"K001#0": {"start": ["V001", 1.0], "src_in": 50.0, "end": ["V002", 0.5]}}}, TIMES)
    assert out == [("c.mp4", 10.0, 3.6, pytest.approx(8.7), 1)]
