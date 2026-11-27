import pytest
from vo.prompter import Session


class Fake:
    """Stands in for the Audacity pipe: records what the session asked for."""
    def __init__(self, existing_labels=0, fail=False):
        self.calls, self.n, self.fail = [], existing_labels, fail

    def _do(self, *c):
        if self.fail:
            raise OSError("pipe closed")
        self.calls.append(c)

    def record(self): self._do("record")
    def stop(self): self._do("stop")
    def label_count(self): self._do("count"); return self.n
    def add_label(self, index, text): self._do("label", index, text); self.n += 1
    def labels(self): self._do("labels"); return [(0.0, "V001")]
    def export(self, path): self._do("export", path)


IDS = ["V001", "V002", "V003"]


def labels_of(f):
    return [(c[1], c[2]) for c in f.calls if c[0] == "label"]


def test_start_labels_current_line():
    f = Fake(); s = Session(IDS, f)
    s.toggle_record()
    assert s.recording and f.calls[:2] == [("count",), ("record",)]
    assert labels_of(f) == [(0, "V001")]


def test_next_labels_each_new_line_while_recording():
    f = Fake(); s = Session(IDS, f)
    s.toggle_record(); s.next(); s.next()
    assert s.idx == 2 and labels_of(f) == [(0, "V001"), (1, "V002"), (2, "V003")]


def test_next_stops_at_last_line():
    f = Fake(); s = Session(IDS, f, start=2)
    s.toggle_record(); s.next()
    assert s.idx == 2 and labels_of(f) == [(0, "V003")]


def test_retake_relabels_same_line():
    f = Fake(); s = Session(IDS, f)
    s.toggle_record(); s.next(); s.retake()
    assert labels_of(f)[-2:] == [(1, "V002"), (2, "V002")]


def test_back_goes_to_previous_line_and_labels_it():
    f = Fake(); s = Session(IDS, f)
    s.toggle_record(); s.next(); s.back()
    assert s.idx == 0 and labels_of(f)[-1] == (2, "V001")


def test_back_at_first_line_does_nothing():
    f = Fake(); s = Session(IDS, f)
    s.toggle_record(); s.back()
    assert s.idx == 0 and labels_of(f) == [(0, "V001")]


def test_not_recording_moves_without_labels():
    f = Fake(); s = Session(IDS, f)
    s.next(); s.retake(); s.next(); s.back()
    assert s.idx == 1 and labels_of(f) == []


def test_label_index_continues_after_existing_labels():
    f = Fake(existing_labels=5); s = Session(IDS, f)
    s.toggle_record(); s.next()
    assert labels_of(f) == [(5, "V001"), (6, "V002")]


def test_stop_saves_audio_and_labels(tmp_path):
    f = Fake(); s = Session(IDS, f, out=str(tmp_path / "part1"))
    s.toggle_record(); s.toggle_record()
    assert not s.recording
    kinds = [c[0] for c in f.calls]
    assert kinds[-3:] == ["stop", "labels", "export"]
    assert f.calls[-1][1] == str(tmp_path / "part1.wav")
    assert (tmp_path / "part1.labels.json").read_text().strip().startswith("{")


def test_start_from_a_given_line():
    s = Session(IDS, Fake(), start=1)
    assert s.idx == 1 and s.line() == "V002"


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
