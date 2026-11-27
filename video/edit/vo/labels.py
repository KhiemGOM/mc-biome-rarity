"""Takes from teleprompter labels. The prompter drops an Audacity label with the line id (V001...) each time a line
comes up while recording, so a line's take runs from its LAST label to the next label of any kind, trimmed to the
speech. No transcription guesswork: retakes, ad-libs and changed wording all work."""
import json, math

BOUNDARY = "|"  # marks the end of each joined file


def parse_getinfo(raw):
    """Audacity 'GetInfo: Type=Labels Format=JSON' -> [(t, text)] sorted by time, all label tracks."""
    out = []
    for _track, labels in json.loads(raw or "[]"):
        out += [(float(s), str(t).strip()) for s, _e, t in labels]
    return sorted(out)


def join_labels(files):
    """[(labels, duration), ...] in recording order -> one list on the joined timeline, with a boundary marker at the
    end of every file so a take never runs into the next file."""
    out, off = [], 0.0
    for labels, dur in files:
        out += [(off + t, x) for t, x in sorted(labels)]
        off += dur
        out.append((off, BOUNDARY))
    return out


def takes_from_labels(labels, ids, end, min_len=0.4):
    """-> ({id: (start, end)}, missing ids in script order). Uses the last take of each line that is at least min_len
    long (a double press leaves a tiny take, so the earlier full take wins). Unknown labels only end takes."""
    labels = sorted(labels)
    known, spans = set(ids), {}
    for k, (t, x) in enumerate(labels):
        if x in known:
            stop = labels[k + 1][0] if k + 1 < len(labels) else end
            if stop - t >= min_len:
                spans[x] = (t, stop)
    takes = {i: spans[i] for i in ids if i in spans}
    return takes, [i for i in ids if i not in spans]


def speech_bounds(a, sr, start, stop, skip=0.15, pad=0.06, frame=0.01):
    """Trim a take to the speech inside [start, stop] seconds of 16-bit samples `a`. Skips `skip` seconds after the
    label (the keypress click). Threshold: 4x the take's quiet floor (10th percentile frame RMS), at least about
    -50 dBFS. Returns (s, e) in seconds with `pad` kept around the speech, or None if the take is silent."""
    n = max(1, int(frame * sr))
    i0, i1 = int((start + skip) * sr), min(len(a), int(stop * sr))
    rms = []
    for i in range(i0, i1, n):
        seg = a[i:i + n]
        rms.append(math.sqrt(sum(v * v for v in seg) / len(seg)) if len(seg) else 0.0)
    if not rms:
        return None
    floor = sorted(rms)[len(rms) // 10]
    th = max(4 * floor, 100.0)
    loud = [k for k, r in enumerate(rms) if r > th]
    if not loud:
        return None
    s = (i0 + loud[0] * n) / sr - pad
    e = (i0 + (loud[-1] + 1) * n) / sr + pad
    return max(start, s), min(stop, e)


def label_takes(files, ids, a, sr, pad=0.0, min_len=0.4):
    """files: [(labels, duration)] in the order they were joined into the samples `a`. -> ({id: (s, e)}, missing),
    each take trimmed to its speech. A take with no speech in it counts as missing."""
    joined = join_labels(files)
    spans, missing = takes_from_labels(joined, ids, end=sum(d for _, d in files), min_len=min_len)
    takes = {}
    for i, (s, e) in spans.items():
        b = speech_bounds(a, sr, s, e, pad=pad)
        if b:
            takes[i] = b
    return takes, [i for i in ids if i not in takes]
