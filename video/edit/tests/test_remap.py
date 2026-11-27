from vo.remap import match_lines, rewrite_ids

A = ("V001", "If you've ever googled the rarest biome in Minecraft, you've watched camman18.")
B = ("V002", "First, in 2021, modified jungle edge. Then a couple of months later, still modified jungle edge.")
C = ("V003", "Then in 2026, the real rarest biome. So the first two were fake? Now it's the pale garden.")
D = ("V004", "And the rest of the internet? Worse. Everyone has an answer. Nobody has a proof.")


def ren(lines):  # renumber like the parser does
    return [(f"V{k + 1:03d}", t) for k, (_, t) in enumerate(lines)]


def test_identical_script_maps_to_itself():
    m, dropped = match_lines([A, B, C, D], [A, B, C, D])
    assert m == {"V001": "V001", "V002": "V002", "V003": "V003", "V004": "V004"} and dropped == []


def test_inserted_line_shifts_everything_after_it():
    new = ren([A, B, ("", "So where do I come in? Simulating worlds isn't new."), C, D])
    m, dropped = match_lines([A, B, C, D], new)
    assert m == {"V001": "V001", "V002": "V002", "V003": "V004", "V004": "V005"} and dropped == []


def test_lightly_edited_line_still_matches():
    new = ren([A, B, ("", "Then in 2026: the REAL rarest biome. Oh. So the first two were fake? Now it's pale garden."), D])
    m, _ = match_lines([A, B, C, D], new)
    assert m["V003"] == "V003"


def test_deleted_line_is_reported_not_reassigned():
    m, dropped = match_lines([A, B, C, D], ren([A, B, D]))
    assert dropped == ["V003"] and "V003" not in m and m["V004"] == "V003"


def test_split_paragraph_maps_to_its_closest_piece_and_later_lines_shift():
    long = ("V002", "Why a straight line? Pro players pick one direction and keep going. A grid walk keeps re-checking "
                    "ground that is correlated with what you already saw, so the straight line finds new biomes faster.")
    new = ren([A, ("", "Why a straight line? Pro players pick one direction and keep going."),
               ("", "A grid walk keeps re-checking ground that is correlated with what you already saw."),
               ("", "So the straight line finds new biomes faster."), C])
    m, dropped = match_lines([A, long, C], ren([A, long, C])[:1] + new[1:])
    assert m["V001"] == "V001" and m["V002"] in ("V002", "V003", "V004") and m["V003"] == "V005" and dropped == []


def test_near_duplicate_lines_match_in_order():
    x = "Not once in two hundred and fifteen thousand worlds. The game would rather die than spawn you in water."
    y = "Not once in two hundred and fifteen thousand worlds. That push probably makes the walk a tiny bit longer."
    old = ren([(None, x), (None, B[1]), (None, y)])
    new = ren([(None, A[1]), (None, x), (None, B[1]), (None, y)])
    m, _ = match_lines(old, new)
    assert m == {"V001": "V002", "V002": "V003", "V003": "V004"}


def test_completely_rewritten_line_counts_as_dropped():
    m, dropped = match_lines([A, B], ren([A, ("", "Totally unrelated words about llamas and pizza toppings.")]))
    assert dropped == ["V002"]


def test_rewrite_is_one_pass_no_chaining():
    src = '"V001": [a],\n"V002": [b],\n"V003": [c],'
    out, _ = rewrite_ids(src, {"V001": "V002", "V002": "V003", "V003": "V004"}, dropped=[])
    assert out == '"V002": [a],\n"V003": [b],\n"V004": [c],'


def test_rewrite_marks_dropped_ids_and_counts_changes():
    out, n = rewrite_ids('"V001": [a], "V002": [b]', {"V001": "V001"}, dropped=["V002"])
    assert out == '"V001": [a], "OLD_V002": [b]' and n == 1


def test_rewrite_ignores_lookalikes_and_cards():
    src = '"V0010" XV001 C001 V001x "V001"'
    out, _ = rewrite_ids(src, {"V001": "V009"}, dropped=[])
    assert out == '"V0010" XV001 C001 V001x "V009"'


def test_rewrite_handles_plain_ids_in_markdown_tables():
    out, _ = rewrite_ids("| V006 | gag |\n| V011 | stamp |", {"V006": "V006", "V011": "V012"}, dropped=[])
    assert out == "| V006 | gag |\n| V012 | stamp |"
