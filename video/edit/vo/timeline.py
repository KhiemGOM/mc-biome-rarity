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

    body, last_end, total = [], {}, 0
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
        body.append(f'<asset-clip ref="{aid}" lane="{c.lane}" offset="{t(s, fps)}" start="{t(frames(c.src_in, fps), fps)}" '
                    f'duration="{t(e - s, fps)}" name={quoteattr((c.key + " " if c.key else "") + os.path.basename(c.path))}/>')
        last_end[c.lane] = e
        total = max(total, e)
    if vo:
        vd = frames(vo[1], fps)
        aid = asset(vo[0], "audio", vo[1])
        if vo_pieces is None:
            body.append(f'<asset-clip ref="{aid}" lane="-1" offset="0s" start="0s" duration="{t(vd, fps)}" name="voice over"/>')
        for a, b, at, nm in vo_pieces or ():
            fa, fb, fo = frames(a, fps), frames(b, fps), frames(at, fps)
            body.append(f'<asset-clip ref="{aid}" lane="-1" offset="{t(fo, fps)}" start="{t(fa, fps)}" '
                        f'duration="{t(fb - fa, fps)}" name={quoteattr(nm)}/>')
        total = max(total, vd)
    for path, dur, lane, nm in audio:
        d = frames(dur, fps)
        aid = asset(path, "audio", dur)
        body.append(f'<asset-clip ref="{aid}" lane="{lane}" offset="0s" start="0s" duration="{t(d, fps)}" name={quoteattr(nm)}/>')
        total = max(total, d)
    marks = "".join(f'<marker start="{t(frames(sec, fps), fps)}" duration="1/{fps}s" value={quoteattr(txt)}/>'
                    for sec, txt in markers)
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE fcpxml>\n<fcpxml version="1.9"><resources>' + "".join(res) +
           f'</resources><library><event name={quoteattr(name)}><project name={quoteattr(name)}>'
           f'<sequence format="r1" duration="{t(total, fps)}" tcStart="0s" tcFormat="NDF"><spine>'
           f'<gap name="base" offset="0s" start="0s" duration="{t(total, fps)}">' + marks + "".join(body) +
           '</gap></spine></sequence></project></event></library></fcpxml>\n')
    return xml, warnings
