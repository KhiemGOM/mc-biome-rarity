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
