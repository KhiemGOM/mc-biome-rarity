from vo.script_lines import parse, read_script

SAMPLE = """# Title

Intro text that is not voice over.

---

## 0. Cold open

[VISUAL: thumbnail wall]

First line of voice over.

[VISUAL: clip A]
[GAG: titles stack]

Second line, with 215,000 worlds.

[beat]

[CHECK: confirm something]
[NOTE: a note]
[data: on screen fact]

Third line.

[VISUAL: title card]

---

## 4b. Now open your eyes

[VISUAL: table]
[mushroom fields: #1, 149,522 | #1, 73,730]

Fourth line.
"""


def test_ids_sections_and_text():
    items = parse(SAMPLE)
    vo = [i for i in items if i.kind == "vo"]
    assert [i.id for i in vo] == ["V001", "V002", "V003", "V004"]
    assert [i.section for i in vo] == ["0", "0", "0", "4b"]
    assert vo[1].text == "Second line, with 215,000 worlds."


def test_text_before_first_section_is_ignored():
    assert all("Intro text" not in i.text for i in parse(SAMPLE))


def test_visuals_attach_to_the_next_line():
    vo = [i for i in parse(SAMPLE) if i.kind == "vo"]
    assert vo[0].visuals == ["VISUAL: thumbnail wall"]
    assert vo[1].visuals == ["VISUAL: clip A"]
    assert vo[2].visuals == []


def test_gag_attaches_to_the_previous_line_and_never_makes_a_card():
    items = parse(SAMPLE + "\n[GAG: end gag]\n")
    vo = [i for i in items if i.kind == "vo"]
    assert vo[0].gags == ["GAG: titles stack"]
    assert vo[3].gags == ["GAG: end gag"]
    assert sum(i.kind == "card" for i in items) == 1


def test_beat_marks_pause_on_previous_line():
    vo = [i for i in parse(SAMPLE) if i.kind == "vo"]
    assert vo[1].pause_after and not vo[0].pause_after and not vo[2].pause_after


def test_notes_checks_data_and_table_rows_are_never_spoken():
    joined = " ".join(i.text for i in parse(SAMPLE))
    for s in ("confirm something", "a note", "on screen fact", "149,522"):
        assert s not in joined


def test_trailing_visual_becomes_silent_card_in_its_section():
    items = parse(SAMPLE)
    cards = [i for i in items if i.kind == "card"]
    assert len(cards) == 1
    assert cards[0].section == "0" and cards[0].visuals == ["VISUAL: title card"] and cards[0].text == ""
    # order: card sits after V003, before V004
    ids = [i.id for i in items]
    assert ids.index(cards[0].id) == ids.index("V003") + 1


def test_read_script_has_every_line_and_pause_marks():
    md = read_script(parse(SAMPLE))
    for vid in ("V001", "V002", "V003", "V004"):
        assert vid in md
    assert "(pause)" in md
    assert "VISUAL" not in md and "CHECK" not in md


def test_real_script_parses():
    import os
    p = os.path.join(os.path.dirname(__file__), "..", "..", "VIDEO_SCRIPT.md")
    items = parse(open(p, encoding="utf-8").read())
    vo = [i for i in items if i.kind == "vo"]
    assert len(vo) > 60
    assert {i.section for i in vo} == {"0", "1", "2", "3", "4", "4b", "4c", "5"}
    assert not any(i.text.startswith("[") for i in vo)
