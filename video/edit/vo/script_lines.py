"""Parse video/VIDEO_SCRIPT.md into numbered voice-over lines (V001, ...) with the visuals that go with them."""
import re
from dataclasses import dataclass, field


@dataclass
class Item:
    id: str
    kind: str            # "vo" (spoken line), "clip" (someone else's video with its own audio) or "card" (silent visual)
    section: str
    text: str = ""
    visuals: list = field(default_factory=list)   # [VISUAL]s: shown from the start of this line
    gags: list = field(default_factory=list)      # [GAG]s: quick jokes reacting to this line
    pause_after: bool = False
    clip: tuple = None   # clips: (youtube id or file stem, in seconds, out seconds)


SECTION = re.compile(r"^##\s+([0-9]+[a-z]?)\.")
VISUAL = re.compile(r"^\[(VISUAL:.*)\]$")
GAG = re.compile(r"^\[(GAG:.*)\]$")
CLIP = re.compile(r'^\[CLIP:\s*([A-Za-z0-9_-]+)\s+(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s+"(.*)"\s*\]$')
CLIP_SPEAKER = "camman"


def parse(text):
    items, pending, section = [], [], None
    n_vo = n_card = n_clip = 0

    def flush_card():
        nonlocal n_card, pending
        if pending and section is not None:
            n_card += 1
            items.append(Item(f"C{n_card:03d}", "card", section, "", pending))
        pending = []

    for raw in text.splitlines():
        line = raw.strip()
        m = SECTION.match(line)
        if m:
            flush_card()
            section = m.group(1)
            continue
        if section is None or not line or line == "---" or line.startswith("#"):
            continue
        if line.startswith("[CLIP"):
            c = CLIP.match(line)
            if not c or float(c.group(2)) >= float(c.group(3)):
                raise ValueError(f"bad CLIP line (want [CLIP: <id> <in>-<out> \"quote\"], in before out): {line}")
            n_clip += 1
            items.append(Item(f"K{n_clip:03d}", "clip", section, c.group(4),
                              clip=(c.group(1), float(c.group(2)), float(c.group(3)))))
            continue
        if line.startswith("["):
            v, g = VISUAL.match(line), GAG.match(line)
            if v:
                pending.append(v.group(1).strip())
            elif g:
                for it in reversed(items):
                    if it.kind == "vo":
                        it.gags.append(g.group(1).strip())
                        break
            elif line.lower() == "[beat]":
                for it in reversed(items):
                    if it.kind in ("vo", "clip"):
                        it.pause_after = True
                        break
            continue  # CHECK, NOTE, data, table rows: never spoken
        n_vo += 1
        items.append(Item(f"V{n_vo:03d}", "vo", section, line, pending))
        pending = []
    flush_card()
    return items


def read_script(items):
    """Teleprompter markdown: one numbered line per paragraph, sections as headings, pauses marked."""
    out, cur = ["# Voice-over read script", ""], None
    for it in items:
        if it.kind == "card":
            continue
        if it.section != cur:
            cur = it.section
            out += [f"## Section {cur}", ""]
        if it.kind == "clip":
            out += [f"*({CLIP_SPEAKER}: \"{it.text}\")*" + ("  *(pause)*" if it.pause_after else ""), ""]
            continue
        out.append(f"**{it.id}**  {it.text}" + ("  *(pause)*" if it.pause_after else ""))
        out.append("")
    return "\n".join(out)
