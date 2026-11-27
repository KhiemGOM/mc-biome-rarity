"""Turn cuts.csv (line id -> files) and line times into visual segments (file, in point, start, end)."""
import csv


def parse_files(cell):
    out = []
    for part in (cell or "").split(";"):
        part = part.strip()
        if not part:
            continue
        path, _, src_in = part.partition("@")
        out.append((path.strip(), float(src_in) if src_in else 0.0))
    return out


def load(path):
    with open(path, encoding="utf-8", newline="") as f:
        return {r["id"]: r["files"] for r in csv.DictReader(f)}


def segments(order, times, cuts, end):
    """order: item ids in script order. times: {id: (start, end)} for items that exist in the edit.
    A line with files starts a new visual that holds until the next line with files (or `end`)."""
    for k in cuts:
        if k not in order:
            raise KeyError(f"cuts.csv names {k}, which is not in the script")
    starts = [(times[i][0], parse_files(cuts.get(i, ""))) for i in order if i in times and parse_files(cuts.get(i, ""))]
    segs = []
    for n, (s, files) in enumerate(starts):
        e = starts[n + 1][0] if n + 1 < len(starts) else end
        step = (e - s) / len(files)
        for k, (path, src_in) in enumerate(files):
            a = s + k * step
            b = e if k == len(files) - 1 else s + (k + 1) * step
            segs.append((path, src_in, a, b))
    return segs


def load_overlays(path):
    with open(path, encoding="utf-8", newline="") as f:
        return {r["id"]: r.get("overlay", "") for r in csv.DictReader(f)}


def overlay_segments(order, times, overlays):
    """Overlays (lower thirds, notes) show for their own line only, not held."""
    segs = []
    for i in order:
        if i in times:
            for path, src_in in parse_files(overlays.get(i, "")):
                segs.append((path, src_in, times[i][0], times[i][1]))
    return segs
