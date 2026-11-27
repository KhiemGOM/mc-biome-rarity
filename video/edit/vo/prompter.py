"""Teleprompter that drives Audacity. Run from video/edit with Audacity open (mod-script-pipe enabled):

  .venv\\Scripts\\python -m vo.prompter [name] [--from V030]

Keys: S start/stop recording | Space, Right or Enter: next line | R: retake this line | Left or Backspace: previous
line | Up/Down: text size | Esc: stop and quit.

While recording, every line that comes up drops an Audacity label with its id (V001...). On stop, the project is
exported to rec/<name>.wav (or you export it with Ctrl+Shift+E if Audacity's scripted export fails) and the labels
to rec/<name>.labels.json, which the align step uses instead of guessing.
Without Audacity it still works as a plain teleprompter."""
import json, os, sys, time
from .labels import parse_getinfo

EDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REC = os.path.join(EDIT, "rec")


class AudacityPipe:
    """Audacity's mod-script-pipe (Windows named pipes)."""
    TO, FROM, EOL = r"\\.\pipe\ToSrvPipe", r"\\.\pipe\FromSrvPipe", "\r\n\0"

    def __init__(self):
        self.to = open(self.TO, "w")
        self.fr = open(self.FROM, "r")

    def do(self, command):
        self.to.write(command + self.EOL); self.to.flush()
        out = []
        while True:
            line = self.fr.readline()
            if line == "":
                raise OSError("Audacity closed the pipe")
            if line == "\n" and out and out[-1].startswith("BatchCommand finished"):
                break
            out.append(line.rstrip("\n"))
        if out and "Failed" in out[-1]:
            raise OSError(f"Audacity: {command} -> {' '.join(out)[:200]}")
        return "\n".join(out[:-1])

    def record(self): self.do("Record1stChoice:")
    def stop(self): self.do("Stop:")
    def labels(self): return parse_getinfo(self.do("GetInfo: Type=Labels Format=JSON"))
    def label_count(self): return len(self.labels())

    def mark(self):  # empty label at the record position (SetLabel during recording would stop it)
        self.do("AddLabelPlaying:")

    def set_label(self, index, text):
        self.do(f'SetLabel: Label={index} Text="{text}"')

    def export(self, path):
        self.do("SelectAll:")
        self.do(f'Export2: Filename="{path}" NumChannels=1')


class Session:
    """What the keys do, independent of the window (tested with a fake client)."""

    def __init__(self, ids, client, start=0, out=None):
        self.ids, self.client, self.idx = list(ids), client, start
        self.out = out or os.path.join(REC, time.strftime("part_%H%M%S"))
        self.recording, self.n, self.marked, self.saved = False, 0, [], []
        self.status = "Ready. S to record." if client else "No Audacity connection: teleprompter only (enable mod-script-pipe)."

    def line(self):
        return self.ids[self.idx]

    def _call(self, fn, *a):
        if not self.client:
            return None
        try:
            return fn(*a)
        except Exception as e:  # Audacity closed or refused: keep the teleprompter alive
            self.client, self.recording = None, False
            self.status = f"Lost the Audacity connection ({str(e)[:80]}). Teleprompter only."
            return None

    def _label(self):
        if self.recording and self.client:
            self._call(self.client.mark)
            if self.client:  # still connected, so the label went in
                self.marked.append(self.line())

    def toggle_record(self):
        if not self.client:
            self.status = "No Audacity connection: can't record from here. Teleprompter only."
            return
        if not self.recording:
            n = self._call(self.client.label_count)
            if not self.client:
                return
            self.n, self.marked = n or 0, []
            self._call(self.client.record)
            if not self.client:
                return
            self.recording, self.status = True, "Recording"
            self._label()
            return
        self._call(self.client.stop)
        self.recording = False
        labels = self._call(self.client.labels)
        if not self.client:
            return
        new = (labels or [])[self.n:]  # this recording's labels, in time order
        pairs = [(t, i) for (t, _), i in zip(new, self.marked)]
        for k, (_, i) in enumerate(pairs):
            self._call(self.client.set_label, self.n + k, i)
        os.makedirs(os.path.dirname(self.out) or ".", exist_ok=True)
        try:  # Audacity 3.7's scripted export fails on some setups: then the WAV is one manual export
            self.client.export(self.out + ".wav"); exported = True
        except OSError:
            exported = False
        self.saved += pairs  # the export holds the whole project, so keep earlier recordings' labels too
        json.dump({"labels": self.saved}, open(self.out + ".labels.json", "w"), indent=1)
        name = os.path.basename(self.out)
        if exported:
            self.status = f"Saved {name}.wav + {len(pairs)} labels. S to record more."
        else:
            self.status = (f"Saved {len(pairs)} labels. Now in Audacity: Ctrl+Shift+E, export the whole project as "
                           f"rec\\{name}.wav (don't trim anything first). S to record more.")
        if len(new) != len(self.marked):
            self.status += f" Label mismatch: Audacity has {len(new)}, expected {len(self.marked)}."

    def next(self):
        if self.idx < len(self.ids) - 1:
            self.idx += 1
            self._label()

    def retake(self):
        self._label()

    def back(self):
        if self.idx > 0:
            self.idx -= 1
            self._label()


def main():
    import tkinter as tk
    from .run import items
    a = sys.argv[1:]
    start_id = a[a.index("--from") + 1] if "--from" in a else None
    names = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] != "--from")]
    vo = [i for i in items() if i.kind == "vo"]
    by = {i.id: i for i in vo}
    try:
        client = AudacityPipe()
    except OSError:
        client = None
    out = os.path.join(REC, names[0]) if names else None
    s = Session([i.id for i in vo], client, start=[i.id for i in vo].index(start_id) if start_id else 0, out=out)

    BG, FG, DIM, RED, MUT = "#0E1116", "#F2F4F8", "#5B6575", "#FF5A5A", "#97A3B6"
    root = tk.Tk(); root.title("Teleprompter"); root.configure(bg=BG); root.geometry("1400x800")
    size = [44]
    top = tk.Label(root, bg=BG, fg=MUT, font=("Segoe UI", 16), anchor="w"); top.pack(fill="x", padx=40, pady=(20, 0))
    cur = tk.Label(root, bg=BG, fg=FG, justify="left", anchor="nw"); cur.pack(fill="both", expand=True, padx=60, pady=20)
    nxt = tk.Label(root, bg=BG, fg=DIM, justify="left", anchor="nw"); nxt.pack(fill="x", padx=60)
    bot = tk.Label(root, bg=BG, fg=DIM, font=("Segoe UI", 12), anchor="w",
                   text="S record/stop   Space/Right next   R retake   Left back   Up/Down size   Esc quit")
    bot.pack(fill="x", padx=40, pady=(10, 20))

    def draw(*_):
        it = by[s.line()]
        w = max(400, root.winfo_width() - 140)
        rec = "  ● REC" if s.recording else ""
        top.config(text=f"{it.section}   {it.id}  ({s.idx + 1}/{len(s.ids)}){rec}     {s.status}", fg=RED if s.recording else MUT)
        cur.config(text=it.text + ("\n\n(pause)" if it.pause_after else ""), font=("Segoe UI", size[0]), wraplength=w)
        n = by[s.ids[s.idx + 1]].text if s.idx + 1 < len(s.ids) else "(end)"
        nxt.config(text=n, font=("Segoe UI", max(14, size[0] // 2)), wraplength=w)

    def key(fn):
        return lambda e: (fn(), draw())

    for k in ("<space>", "<Right>", "<Return>"):
        root.bind(k, key(s.next))
    for k in ("<Left>", "<BackSpace>"):
        root.bind(k, key(s.back))
    root.bind("r", key(s.retake)); root.bind("s", key(s.toggle_record))
    root.bind("<Up>", lambda e: (size.__setitem__(0, size[0] + 4), draw()))
    root.bind("<Down>", lambda e: (size.__setitem__(0, max(16, size[0] - 4)), draw()))

    def quit_(e=None):
        if s.recording:
            s.toggle_record()
        root.destroy()
    root.bind("<Escape>", quit_); root.protocol("WM_DELETE_WINDOW", quit_)
    root.bind("<Configure>", draw)
    draw(); root.mainloop()


if __name__ == "__main__":
    main()
