"""Resolve round trip. Edit the imported rough cut in DaVinci Resolve, export it (File > Export > Timeline > FCPXML 1.9)
into video/edit/work/, then from video/edit:

  .venv\\Scripts\\python -m vo.tweaks import work/<export>.fcpxml

Your edits are compared with what was generated and saved to video/edit/tweaks.json, every one anchored to a script
line ("1.2 s of silence after V011", "this shot ends 0.5 s into V014"), so they survive re-recording the voice-over.
Then the edit is rebuilt with them. What carries over: spacing between lines (drag the A1 clips), where shots start and
end, swapped shots and in points, deleted and added shots and overlays, trims of camman's clips (written into the
[CLIP] times in VIDEO_SCRIPT.md). What doesn't: color, effects, keyframes, transitions, titles, volume; do those last.

Shots you don't touch keep following their lines, so dragging voice clips apart is enough for more room. Only shot edges
you actually move get pinned to where you put them. Camman's picture always stays in sync with his voice."""
import json, os, re, sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from difflib import SequenceMatcher
from fractions import Fraction
from urllib.parse import unquote

EPS = 0.02          # a frame at 60 fps is 0.0167 s
STILL = (".png", ".jpg", ".jpeg")
EMPTY = lambda: {"gap_after": {}, "visual": {}, "extra": [], "clip_times": {}}


@dataclass
class Placed:
    path: str
    lane: int
    start: float
    end: float
    src_in: float
    name: str = ""


def _t(v):
    if not v:
        return Fraction(0)
    v = v.strip()
    return Fraction(v[:-1] if v.endswith("s") else v)


def _path(src):
    p = unquote(src)
    for pre in ("file://localhost/", "file:///", "file://"):
        if p.startswith(pre):
            p = p[len(pre):]
            break
    if re.match(r"^/[A-Za-z]:", p):
        p = p[1:]
    return os.path.normpath(p)


def parse_fcpxml(xml):
    """Every media clip in a timeline with its absolute start/end, lane and source in point. Handles clips connected
    inside other clips (their times are in the parent's own time) and any rational time ("3003/1000s")."""
    root = ET.fromstring(xml)
    assets = {}
    for a in root.iter("asset"):
        mr = a.find("media-rep")
        src = mr.get("src") if mr is not None else a.get("src")
        if src:
            assets[a.get("id")] = _path(src)
    out = []
    timed = {"asset-clip", "clip", "gap", "ref-clip", "sync-clip", "mc-clip", "title", "video", "audio"}

    def walk(children, abs_parent, local_parent, lane):
        for ch in children:
            if ch.tag == "spine":  # secondary storyline: offset in the parent's time, children in its own
                a = abs_parent + (_t(ch.get("offset")) - local_parent)
                walk(list(ch), a, Fraction(0), int(ch.get("lane", lane)))
                continue
            if ch.tag not in timed:
                continue
            start, dur = _t(ch.get("start")), _t(ch.get("duration"))
            a = abs_parent + (_t(ch.get("offset")) - local_parent)
            ln = int(ch.get("lane")) if ch.get("lane") is not None else lane
            kids = list(ch)
            if ch.tag in ("asset-clip", "video", "audio") and ch.get("ref") in assets:
                out.append(Placed(assets[ch.get("ref")], ln, float(a), float(a + dur), float(start), ch.get("name") or ""))
            elif ch.tag == "clip":
                inner = next((c for c in kids if c.tag in ("video", "audio") and c.get("ref") in assets), None)
                if inner is not None:
                    src_in = _t(inner.get("start")) + (start - _t(inner.get("offset")))
                    out.append(Placed(assets[inner.get("ref")], ln, float(a), float(a + dur), float(src_in), ch.get("name") or ""))
                    kids = [c for c in kids if c is not inner]
            walk(kids, a, start, ln)

    spine = root.find(".//sequence/spine")
    walk(list(spine) if spine is not None else [], Fraction(0), Fraction(0), 0)
    return out


def _piece(pieces, a, b):
    best, ov = None, 0.0
    for p in pieces:
        o = min(b, p.src_in + (p.end - p.start)) - max(a, p.src_in)
        if o > ov:
            best, ov = p, o
    return best


def _pieces(placed, vo_name):
    return [p for p in placed if p.lane < 0 and os.path.basename(p.path) == vo_name]


def positions(placed, items, times, vo_name):
    """{item id: (start, end)} on the timeline, from where each line's voice-over clip sits. A camman clip uses its
    trimmed bounds; your own lines keep their full length (trimming your takes isn't a tweak, re-record instead)."""
    pieces, pos = _pieces(placed, vo_name), {}
    for it in items:
        if it.id not in times:
            continue
        a, b = times[it.id]
        p = _piece(pieces, a, b)
        if p is None:
            continue
        s = p.start + (a - p.src_in)
        pos[it.id] = (max(s, p.start), min(s + (b - a), p.end)) if it.kind == "clip" else (s, s + (b - a))
    return pos


def anchor_of(t, pos):
    """[line id, seconds after that line starts] for the last line starting at or before t."""
    starts = sorted((s, i) for i, (s, _) in pos.items())
    cand = [(s, i) for s, i in starts if s <= t + EPS] or starts[:1]
    s, i = cand[-1]
    return [i, round(t - s, 3)]


def resolve(anchor, pos):
    i, off = anchor
    return pos[i][0] + off


def _rel(path, media):
    try:
        r = os.path.relpath(path, media)
        return r.replace("\\", "/") if not r.startswith("..") else path
    except ValueError:  # another drive
        return path


def _visuals(placed, vo_name, music_name):
    vis = [p for p in placed if p.lane >= 0 and os.path.basename(p.path) not in (vo_name, music_name)]
    base = min((p.lane for p in vis), default=0)
    return {"base": sorted([p for p in vis if p.lane == base], key=lambda p: p.start),
            "overlay": sorted([p for p in vis if p.lane != base], key=lambda p: (p.start, p.lane))}


def _key(p):
    k = p.name.split(" ", 1)[0]
    return k if "#" in k else None


def read_back(imported, generated, items, times, vo_name, music_name, media):
    """Edits in `imported` relative to `generated` (the timeline that was imported into Resolve) -> (tweaks, notes)."""
    t, notes = EMPTY(), []
    new, old = positions(imported, items, times, vo_name), positions(generated, items, times, vo_name)
    order = [it for it in items if it.id in old]
    for it in order:
        if it.id not in new:
            notes.append(f"{it.id}: not on the voice-over track in the export, left as it was (cut lines in the script)")
    for cur, nxt in zip(order, order[1:]):
        if cur.id in new and nxt.id in new:
            g_new, g_old = new[nxt.id][0] - new[cur.id][1], old[nxt.id][0] - old[cur.id][1]
            if abs(g_new - g_old) > EPS:
                t["gap_after"][cur.id] = round(g_new, 3)
    pieces = _pieces(imported, vo_name)
    for it in order:
        if it.kind == "clip" and it.id in new:
            a, b = times[it.id]
            p = _piece(pieces, a, b)
            s0, s1 = max(a, p.src_in), min(b, p.src_in + (p.end - p.start))
            if abs(s0 - a) > EPS or abs(s1 - b) > EPS:
                t["clip_times"][it.id] = [round(it.clip[1] + (s0 - a), 2), round(it.clip[1] + (s1 - a), 2)]
    gv, iv = _visuals(generated, vo_name, music_name), _visuals(imported, vo_name, music_name)
    for cls in ("base", "overlay"):
        g, i = gv[cls], iv[cls]
        sm = SequenceMatcher(None, [os.path.basename(p.path) for p in g], [os.path.basename(p.path) for p in i], autojunk=False)
        for op, g0, g1, i0, i1 in sm.get_opcodes():
            pairs = list(zip(g[g0:g1], i[i0:i1])) if op in ("equal", "replace") else []
            for gp, ip in pairs:
                ch, synced = {}, (_key(gp) or "").startswith("K")  # camman's picture stays locked to his voice
                if os.path.basename(gp.path) != os.path.basename(ip.path):
                    ch["file"] = _rel(ip.path, media)
                if not synced and (ch or not gp.path.lower().endswith(STILL)) and abs(gp.src_in - ip.src_in) > EPS:
                    ch["src_in"] = round(ip.src_in, 3)
                for edge in ("start", "end"):
                    if (edge == "start" and synced) or abs(getattr(gp, edge) - getattr(ip, edge)) <= EPS:
                        continue  # untouched edges keep following their line
                    ga, ia = anchor_of(getattr(gp, edge), old), anchor_of(getattr(ip, edge), new)
                    if ga[0] != ia[0] or abs(ga[1] - ia[1]) > EPS:
                        ch[edge] = ia
                if ch:
                    if _key(gp):
                        t["visual"][_key(gp)] = ch
                    else:
                        notes.append(f"{gp.name or gp.path}: changed but has no line key, skipped")
            for gp in g[g0 + len(pairs):g1]:
                if _key(gp):
                    t["visual"][_key(gp)] = {"deleted": True}
            for ip in i[i0 + len(pairs):i1]:
                t["extra"].append({"lane": cls, "file": _rel(ip.path, media), "src_in": round(ip.src_in, 3),
                                   "start": anchor_of(ip.start, new), "end": anchor_of(ip.end, new)})
    return t, notes


def merge(old, new):
    out = EMPTY()
    for k in ("gap_after", "clip_times"):
        out[k] = {**old.get(k, {}), **new.get(k, {})}
    out["visual"] = {k: dict(v) for k, v in old.get("visual", {}).items()}
    for k, v in new.get("visual", {}).items():
        out["visual"][k] = {**out["visual"].get(k, {}), **v}
    out["extra"] = list(old.get("extra", [])) + [x for x in new.get("extra", []) if x not in old.get("extra", [])]
    return out


def gap_for(item_id, default, tweaks):
    return tweaks.get("gap_after", {}).get(item_id, default)


def apply_visuals_keyed(segs, tweaks, pos):
    """segs: [(key, path, src_in, start, end, lane)] as generated. -> ([(key, path, src_in, start, end, lane)], notes)
    with the saved tweaks applied and the saved extra shots added (keys extra#n)."""
    vis, out, notes = tweaks.get("visual", {}), [], []
    extras = [(f"extra#{n}", x["file"], x.get("src_in", 0.0), x["start"], x["end"], 2 if x["lane"] == "overlay" else 1)
              for n, x in enumerate(tweaks.get("extra", []))]
    for key, path, src_in, a, b, lane in list(segs) + extras:
        ch = vis.get(key, {})
        if key.startswith("K"):  # camman's clips: picture always starts with his voice, at his in point
            ch = {k: v for k, v in ch.items() if k not in ("start", "src_in")}
        if ch.get("deleted"):
            continue
        try:
            a = resolve(ch["start"], pos) if "start" in ch else (resolve(a, pos) if isinstance(a, list) else a)
            b = resolve(ch["end"], pos) if "end" in ch else (resolve(b, pos) if isinstance(b, list) else b)
        except KeyError as e:
            notes.append(f"tweak for {key} points at {e.args[0]}, which isn't in the script any more: skipped")
            if isinstance(a, list) or isinstance(b, list):
                continue
            out.append((key, path, src_in, a, b, lane))
            continue
        out.append((key, ch.get("file", path), ch.get("src_in", src_in), a, b, lane))
    return out, notes


def apply_visuals(segs, tweaks, pos):
    out, notes = apply_visuals_keyed(segs, tweaks, pos)
    return [o[1:] for o in out], notes


def update_clip_times(text, ref, old, new):
    def sub(m):
        if abs(float(m.group(2)) - old[0]) < 0.005 and abs(float(m.group(3)) - old[1]) < 0.005:
            return f"{m.group(1)}{new[0]:.2f}-{new[1]:.2f}"
        return m.group(0)
    return re.sub(r"(\[CLIP:\s*" + re.escape(ref) + r"\s+)(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)", sub, text)


def load(path):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else EMPTY()


def cmd_import(export):
    from . import run
    gen_path = os.path.join(run.WORK, "rough_cut.fcpxml")
    if os.path.getmtime(gen_path) > os.path.getmtime(export):
        print("warning: the current rough cut is newer than this export. If you edited an older import, re-import "
              "work/rough_cut.fcpxml into Resolve, redo the edits there and export again.")
    m = json.load(open(os.path.join(run.WORK, "vo_edit_map.json")))
    times = {k: tuple(v) for k, v in m["edit"].items()}
    its = run.items()
    delta, notes = read_back(parse_fcpxml(open(export, encoding="utf-8").read()),
                             parse_fcpxml(open(gen_path, encoding="utf-8").read()), its, times,
                             vo_name="vo_edit.wav", music_name="music_bed.wav", media=run.MEDIA)
    clip_times = delta.pop("clip_times")
    path = os.path.join(run.EDIT, "tweaks.json")
    json.dump(merge(load(path), delta), open(path, "w", encoding="utf-8"), indent=1)
    if clip_times:
        script = open(run.SCRIPT, encoding="utf-8").read()
        by = {it.id: it for it in its}
        for i, (a, b) in clip_times.items():
            script = update_clip_times(script, by[i].clip[0], by[i].clip[1:], (a, b))
        open(run.SCRIPT, "w", encoding="utf-8").write(script)
    print(f"tweaks.json: {len(delta['gap_after'])} spacing, {len(delta['visual'])} shot, {len(delta['extra'])} added; "
          f"{len(clip_times)} camman clip trims written to VIDEO_SCRIPT.md")
    for n in notes:
        print("  note:", n)
    recs = m.get("recs")
    if recs:
        run.cmd_align(*recs)
        run.cmd_timeline()
    else:
        print("Now rebuild: .venv\\Scripts\\python -m vo.run all <your rec files>  (or align work/scratch_raw.wav + timeline)")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 2 or a[0] != "import":
        sys.exit(__doc__)
    cmd_import(a[1])
