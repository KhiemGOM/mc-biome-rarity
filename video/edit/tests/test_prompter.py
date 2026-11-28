import json
import pytest
from vo.prompter import Session

# Live test against Audacity 3.7 showed SetLabel stops a recording, so while recording the session only drops empty
# labels ("mark") and remembers the line ids itself; on stop it pairs the new labels with those ids, names them in
# Audacity (safe once stopped) and saves the JSON.


class Fake:
    """Stands in for the Audacity pipe: records calls, keeps labels with times 1, 2, 3... per mark."""
    def __init__(self, existing=0, fail=False):
        self.calls, self.fail = [], fail
        self.lab = [(0.5 + k * 0.01, "old") for k in range(existing)]

    def _do(self, *c):
        if self.fail:
            raise OSError("pipe closed")
        self.calls.append(c)

    def record(self): self._do("record")
    def stop(self): self._do("stop")
    def labels(self): self._do("labels"); return sorted(self.lab)
    def label_count(self): self._do("count"); return len(self.lab)
    def mark(self): self._do("mark"); self.lab.append((float(len(self.lab) + 1), ""))
    def set_label(self, index, text): self._do("set", index, text)
    def export(self, path): self._do("export", path)


IDS = ["V001", "V002", "V003"]


def marks(f):
    return sum(1 for c in f.calls if c[0] == "mark")


def test_start_marks_current_line():
    f = Fake(); s = Session(IDS, f)
    s.toggle_record()
    assert s.recording and f.calls[:2] == [("count",), ("record",)]
    assert marks(f) == 1 and s.marked == ["V001"]


def test_next_marks_each_new_line_while_recording():
    f = Fake(); s = Session(IDS, f)
    s.toggle_record(); s.next(); s.next()
    assert s.idx == 2 and s.marked == ["V001", "V002", "V003"] and marks(f) == 3


def test_no_setlabel_while_recording():
    f = Fake(); s = Session(IDS, f)
    s.toggle_record(); s.next(); s.retake(); s.back()
    assert not any(c[0] == "set" for c in f.calls)


def test_next_stops_at_last_line():
    f = Fake(); s = Session(IDS, f, start=2)
    s.toggle_record(); s.next()
    assert s.idx == 2 and s.marked == ["V003"]


def test_retake_marks_same_line_again():
    f = Fake(); s = Session(IDS, f)
    s.toggle_record(); s.next(); s.retake()
    assert s.marked == ["V001", "V002", "V002"]


def test_retake_says_so_on_screen():
    # R leaves the flubbed audio in the recording (the align step cuts it); the window must show it registered
    f = Fake(); s = Session(IDS, f)
    s.toggle_record(); s.retake()
    assert "retake" in s.status.lower() and "V001" in s.status and "2" in s.status
    s.retake()
    assert "3" in s.status


def test_retake_when_not_recording_explains():
    f = Fake(); s = Session(IDS, f)
    s.retake()
    assert marks(f) == 0 and "not recording" in s.status.lower()


def test_next_line_after_retake_shows_recording_again():
    f = Fake(); s = Session(IDS, f)
    s.toggle_record(); s.retake(); s.next()
    assert s.status == "Recording"


def test_back_goes_to_previous_line_and_marks_it():
    f = Fake(); s = Session(IDS, f)
    s.toggle_record(); s.next(); s.back()
    assert s.idx == 0 and s.marked[-1] == "V001"


def test_back_at_first_line_does_nothing():
    f = Fake(); s = Session(IDS, f)
    s.toggle_record(); s.back()
    assert s.idx == 0 and s.marked == ["V001"]


def test_not_recording_moves_without_marks():
    f = Fake(); s = Session(IDS, f)
    s.next(); s.retake(); s.next(); s.back()
    assert s.idx == 1 and marks(f) == 0


def test_stop_names_new_labels_after_existing_and_saves(tmp_path):
    f = Fake(existing=2); s = Session(IDS, f, out=str(tmp_path / "part1"))
    s.toggle_record(); s.next(); s.toggle_record()
    assert not s.recording
    assert [c for c in f.calls if c[0] == "set"] == [("set", 2, "V001"), ("set", 3, "V002")]
    assert f.calls[-1] == ("export", str(tmp_path / "part1.wav"))
    saved = json.loads((tmp_path / "part1.labels.json").read_text())["labels"]
    assert saved == [[3.0, "V001"], [4.0, "V002"]]  # only this session's labels, paired in order


def test_stop_with_label_count_mismatch_keeps_what_pairs_and_warns(tmp_path):
    f = Fake(); s = Session(IDS, f, out=str(tmp_path / "p"))
    s.toggle_record(); s.next()
    f.lab.pop()  # Audacity lost one label
    s.toggle_record()
    saved = json.loads((tmp_path / "p.labels.json").read_text())["labels"]
    assert saved == [[1.0, "V001"]] and "mismatch" in s.status.lower()


def test_start_from_a_given_line():
    s = Session(IDS, Fake(), start=1)
    assert s.idx == 1 and s.line() == "V002"


def test_second_recording_in_same_session_starts_fresh(tmp_path):
    f = Fake(); s = Session(IDS, f, out=str(tmp_path / "p"))
    s.toggle_record(); s.toggle_record(); s.next(); s.toggle_record()
    assert s.marked == ["V002"]


def test_no_audacity_still_works_as_teleprompter():
    s = Session(IDS, None)
    s.next(); s.toggle_record(); s.next()
    assert s.idx == 2 and not s.recording and "Audacity" in s.status


def test_pipe_dies_mid_session_is_reported_not_raised():
    f = Fake(); s = Session(IDS, f)
    s.toggle_record()
    f.fail = True
    s.next()  # must not raise
    assert s.idx == 1 and "lost" in s.status.lower()


def test_export_failure_keeps_connection_and_asks_for_manual_export(tmp_path):
    # Audacity 3.7's scripted Export2 fails on this PC: labels must still be saved and the pipe kept
    class NoExport(Fake):
        def export(self, path): raise OSError("Could not export to WAV format!")
    f = NoExport(); s = Session(IDS, f, out=str(tmp_path / "part1"))
    s.toggle_record(); s.toggle_record()
    assert s.client is f
    assert (tmp_path / "part1.labels.json").exists()
    assert "ctrl+shift+e" in s.status.lower() and "part1.wav" in s.status
    s.next(); s.toggle_record()  # can keep recording afterwards
    assert s.recording


# --- listen back (P): hear your last take of the line on screen

class Player(Fake):
    def play(self, a, b): self._do("play", a, b)


def plays(f):
    return [c for c in f.calls if c[0] == "play"]


def test_listen_plays_this_lines_take_up_to_the_next_label(tmp_path):
    f = Player(); s = Session(IDS, f, out=str(tmp_path / "p"))
    s.toggle_record(); s.next(); s.next(); s.toggle_record()  # labels at 1, 2, 3
    s.back()  # on V002
    s.listen()
    assert plays(f) == [("play", 2.0, 3.0)] and "V002" in s.status


def test_listen_while_recording_stops_and_saves_first(tmp_path):
    f = Player(); s = Session(IDS, f, out=str(tmp_path / "p"))
    s.toggle_record(); s.next()
    s.listen()
    assert not s.recording and (tmp_path / "p.labels.json").exists()
    assert plays(f) and plays(f)[0][1] == 2.0  # V002, the line on screen


def test_listen_after_a_retake_plays_the_newest_take(tmp_path):
    f = Player(); s = Session(IDS, f, out=str(tmp_path / "p"))
    s.toggle_record(); s.retake(); s.next(); s.toggle_record()  # V001 at 1 and 2, V002 at 3
    s.back(); s.listen()
    assert plays(f) == [("play", 2.0, 3.0)]


def test_listen_on_the_last_recorded_line_plays_to_the_end(tmp_path):
    f = Player(); s = Session(IDS, f, out=str(tmp_path / "p"))
    s.toggle_record(); s.toggle_record()
    s.listen()
    (_, a, b), = plays(f)
    assert a == 1.0 and b > a + 30  # no next label: let Audacity play until the audio runs out


def test_listen_on_a_line_with_no_take_says_so(tmp_path):
    f = Player(); s = Session(IDS, f, out=str(tmp_path / "p"))
    s.toggle_record(); s.toggle_record()
    s.next(); s.listen()
    assert plays(f) == [] and "no take" in s.status.lower() and "V002" in s.status


def test_listen_without_audacity_explains():
    s = Session(IDS, None)
    s.listen()
    assert "audacity" in s.status.lower()


def test_listen_survives_audacity_failing(tmp_path):
    f = Player(); s = Session(IDS, f, out=str(tmp_path / "p"))
    s.toggle_record(); s.toggle_record()
    f.fail = True
    s.listen()
    assert s.client is None and "lost" in s.status.lower()


def test_recording_always_starts_at_the_end_of_the_project():
    # after listening, Audacity's cursor sits inside an old take: a new recording there would land on top of it
    from vo.prompter import AudacityPipe
    p = AudacityPipe.__new__(AudacityPipe); sent = []
    p.do = lambda c: sent.append(c) or ""
    p.record()
    assert sent[-1] == "Record1stChoice:" and any(c.startswith("CursProjectEnd") for c in sent[:-1])
