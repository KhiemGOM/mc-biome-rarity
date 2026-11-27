from vo.align import align, normalize


def words(text, t0, step=0.3):
    out, t = [], t0
    for w in text.split():
        out.append((w, t, t + step * 0.9))
        t += step
    return out, t


LINES = [("V001", "So I used the oldest trick in the book."),
         ("V002", "One dart tells you nothing, thousands of darts and you know pi."),
         ("V003", "Then a new world, and another, two hundred and fifteen thousand times.")]


def build(*chunks):
    ws, t = [], 0.0
    for c in chunks:
        w, t = words(c, t + 1.0)
        ws += w
    return ws


def test_normalize_numbers_and_punctuation():
    assert normalize("215,000 worlds!") == normalize("two hundred fifteen thousand worlds")
    assert normalize("43 percent") == normalize("43%")
    assert normalize("Ice-spikes, ok?") == "ice spikes ok"


def test_single_clean_take():
    ws = build(*[t for _, t in LINES])
    res, missing = align(LINES, ws)
    assert missing == []
    assert res["V001"][0] == ws[0][1]
    assert res["V003"][1] == ws[-1][2]
    assert res["V001"][1] < res["V002"][0] < res["V003"][0]


def test_retake_picks_the_last_full_take():
    ws = build(LINES[0][1], LINES[1][1], LINES[1][1], LINES[2][1])
    res, _ = align(LINES, ws)
    n0 = len(LINES[0][1].split()); n1 = len(LINES[1][1].split())
    second_take_start = ws[n0 + n1][1]
    assert abs(res["V002"][0] - second_take_start) < 1e-9


def test_flubbed_partial_then_full_take():
    ws = build(LINES[0][1], "One dart tells you", "uh wait let me redo that", LINES[1][1], LINES[2][1])
    res, _ = align(LINES, ws)
    n0 = len(LINES[0][1].split())
    full_start = ws[n0 + 4 + 6][1]
    assert abs(res["V002"][0] - full_start) < 1e-9


def test_numbers_spoken_vs_written():
    lines = [("V001", "So I generated 215,000 Minecraft worlds.")]
    ws = build("so I generated two hundred and fifteen thousand minecraft worlds")
    res, missing = align(lines, ws)
    assert missing == [] and "V001" in res


def test_missing_line_reported_others_kept():
    ws = build(LINES[0][1], LINES[2][1])
    res, missing = align(LINES, ws)
    assert missing == ["V002"]
    assert set(res) == {"V001", "V003"}


def test_chatter_between_lines_is_not_included():
    ws = build(LINES[0][1], "okay hang on drinking water", LINES[1][1])
    res, _ = align(LINES[:2], ws)
    n0 = len(LINES[0][1].split())
    assert res["V001"][1] == ws[n0 - 1][2]
    assert res["V002"][0] == ws[n0 + 5][1]
