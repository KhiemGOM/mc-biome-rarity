"""Write an FCPXML 1.9 timeline that DaVinci Resolve imports (File > Import > Timeline).
Visuals go on lane 1 (V2 in Resolve), the voice-over on lane -1 (A1), both connected to one gap on the main track."""
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import quoteattr

FPS = 60


@dataclass
class Clip:
    path: str
    start: float          # timeline seconds
    end: float
    kind: str = "video"   # "video" or "still"
    src_dur: float = 0.0  # source length (video), seconds
    src_in: float = 0.0   # in point in the source, seconds
    lane: int = 1         # 1 = base visuals (V2 in Resolve), 2 = overlays (V3)
    key: str = ""         # "V011#0": the line and slot it came from, so edits made in Resolve can be read back
    trans_in: float = 0.0 # cross dissolve into this shot, seconds (base shots only; skipped without enough footage)


def frames(sec, fps=FPS):
    return int(round(sec * fps))


def t(n, fps=FPS):
    return "0s" if n == 0 else f"{n}/{fps}s"


def url(path):
    p = Path(os.path.abspath(path)).as_posix()
    return "file:///" + quote(p.lstrip("/"), safe="/:")


def build_fcpxml(clips, vo=None, name="rough cut", fps=FPS, markers=(), audio=(), vo_pieces=None):
    """clips: [Clip]. vo: (wav path, duration seconds) or None. audio: extra [(path, seconds, lane, name)] from 0s,
    e.g. the music bed on lane -2 (A2). vo_pieces: [(src start, src end, timeline start, name)] puts the voice-over on
    A1 as one clip per line instead of one long clip. Returns (xml string, [warnings])."""
    for c in clips:
        if not os.path.exists(c.path):
            raise FileNotFoundError(c.path)
    for p in ([vo[0]] if vo else []) + [x[0] for x in audio]:
        if not os.path.exists(p):
            raise FileNotFoundError(p)
    warnings, assets, res, spans = [], {}, [], []
    res.append(f'<format id="r1" name="FFVideoFormat1080p{fps}" frameDuration="1/{fps}s" width="1920" height="1080"/>')

    def asset(path, kind, dur):
        key = os.path.abspath(path)
        if key not in assets:
            aid = f"a{len(assets) + 1}"
            assets[key] = aid
            dur_f = frames(dur if kind != "still" else 3600, fps)
            av = 'hasAudio="1" audioSources="1" audioChannels="1"' if kind == "audio" else 'hasVideo="1" format="r1"'
            res.append(f'<asset id="{aid}" name={quoteattr(os.path.basename(path))} start="0s" duration="{t(dur_f, fps)}" {av}>'
                       f'<media-rep kind="original-media" src={quoteattr(url(path))}/></asset>')
        return assets[key]

    # Base shots (lane 1) go on the main track, back to back with gaps, so Resolve gets real cross dissolves between
    # them. Everything else (overlays, voice-over, music, markers) hangs off the main-track element it starts in,
    # in that element's own time.
    base, conn, last_end, total = [], [], {}, 0
    for c in sorted(clips, key=lambda c: (c.lane, c.start)):
        s, e = frames(c.start, fps), frames(c.end, fps)
        s = max(s, last_end.get(c.lane, 0))  # never overlap the previous clip on the same lane
        if e <= s:
            continue
        if c.kind == "video":
            avail = frames(c.src_dur - c.src_in, fps)
            if e - s > avail:
                warnings.append(f"{os.path.basename(c.path)}: slot {(e - s) / fps:.1f}s is longer than the clip "
                                f"({avail / fps:.1f}s from the in point); left a gap")
                e = s + avail
        aid = asset(c.path, c.kind, c.src_dur)
        nm = quoteattr((c.key + " " if c.key else "") + os.path.basename(c.path))
        src = frames(c.src_in, fps)
        if c.lane == 1:
            base.append({"s": s, "e": e, "src": src, "aid": aid, "name": nm, "still": c.kind == "still",
                         "src_end": frames(c.src_dur, fps), "trans": 2 * (frames(c.trans_in, fps) // 2)})
        else:
            conn.append((s, f'<asset-clip ref="{aid}" lane="{c.lane}" offset="@OFF@" start="{t(src, fps)}" '
                            f'duration="{t(e - s, fps)}" name={nm}/>'))
        last_end[c.lane] = e
        total = max(total, e)
    if vo:
        vd = frames(vo[1], fps)
        aid = asset(vo[0], "audio", vo[1])
        if vo_pieces is None:
            conn.append((0, f'<asset-clip ref="{aid}" lane="-1" offset="@OFF@" start="0s" duration="{t(vd, fps)}" name="voice over"/>'))
        for a, b, at, nm in vo_pieces or ():
            fa, fb, fo = frames(a, fps), frames(b, fps), frames(at, fps)
            conn.append((fo, f'<asset-clip ref="{aid}" lane="-1" offset="@OFF@" start="{t(fa, fps)}" '
                             f'duration="{t(fb - fa, fps)}" name={quoteattr(nm)}/>'))
        total = max(total, vd)
    for path, dur, lane, nm in audio:
        d = frames(dur, fps)
        aid = asset(path, "audio", dur)
        conn.append((0, f'<asset-clip ref="{aid}" lane="{lane}" offset="@OFF@" start="0s" duration="{t(d, fps)}" name={quoteattr(nm)}/>'))
        total = max(total, d)
    for sec, txt in markers:
        conn.append((frames(sec, fps), f'<marker start="@OFF@" duration="1/{fps}s" value={quoteattr(txt)}/>'))
    total = max(total, 1)

    # main track: gap, shot, gap, shot... from 0 to the end, no holes
    elems, cur = [], 0
    for b in base:
        if b["s"] > cur:
            elems.append({"gap": True, "off": cur, "dur": b["s"] - cur, "start": 0})
        elems.append({"gap": False, "off": b["s"], "dur": b["e"] - b["s"], "start": b["src"], **b})
        cur = b["e"]
    if total > cur:
        elems.append({"gap": True, "off": cur, "dur": total - cur, "start": 0})
    for el in elems:
        el["kids"] = []
    for at, tpl in sorted(conn, key=lambda x: x[0]):
        parent = [el for el in elems if el["off"] <= at][-1]
        parent["kids"].append(tpl.replace("@OFF@", t(parent["start"] + at - parent["off"], fps)))

    def handles(prev, cur, d):
        """A dissolve needs d/2 of footage past the outgoing shot's end and before the incoming shot's start."""
        h = d // 2
        if h > prev["dur"] or h > cur["dur"]:
            return False
        head = cur.get("still") or cur["src"] >= h
        tail = prev["gap"] or prev.get("still") or prev["src_end"] - (prev["src"] + prev["dur"]) >= h
        return head and tail

    spine = []
    for k, el in enumerate(elems):
        if not el["gap"] and el["trans"] and k > 0 and handles(elems[k - 1], el, el["trans"]):
            spine.append(f'<transition name="Cross Dissolve" offset="{t(el["off"] - el["trans"] // 2, fps)}" '
                         f'duration="{t(el["trans"], fps)}"/>')
        kids = "".join(el["kids"])
        if el["gap"]:
            spine.append(f'<gap name="gap" offset="{t(el["off"], fps)}" start="0s" duration="{t(el["dur"], fps)}">{kids}</gap>')
        else:
            spine.append(f'<asset-clip ref="{el["aid"]}" offset="{t(el["off"], fps)}" start="{t(el["start"], fps)}" '
                         f'duration="{t(el["dur"], fps)}" name={el["name"]}>{kids}</asset-clip>')
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE fcpxml>\n<fcpxml version="1.9"><resources>' + "".join(res) +
           f'</resources><library><event name={quoteattr(name)}><project name={quoteattr(name)}>'
           f'<sequence format="r1" duration="{t(total, fps)}" tcStart="0s" tcFormat="NDF"><spine>' + "".join(spine) +
           '</spine></sequence></project></event></library></fcpxml>\n')
    return xml, warnings
