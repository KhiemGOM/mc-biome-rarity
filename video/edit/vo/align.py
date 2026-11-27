"""Match whisper word timestamps to script lines. Keeps the LAST good take of every line, so a flubbed line can
simply be read again. Words outside any chosen take (chatter, flubs, breaths) are left out."""
import re
from num2words import num2words
from rapidfuzz import fuzz

DROP = {"and", "uh", "um", "a"}


def _num(m):
    s = m.group(0).replace(",", "")
    try:
        if "." in s:
            whole, frac = s.split(".", 1)
            return num2words(int(whole)) + " point " + " ".join(num2words(int(c)) for c in frac if c.isdigit())
        return num2words(int(s))
    except ValueError:
        return s


def normalize(text):
    t = text.lower().replace("%", " percent ").replace("-", " ")
    t = re.sub(r"\d[\d,]*(?:\.\d+)?", _num, t)
    t = t.replace("-", " ")
    t = re.sub(r"[^a-z0-9' ]+", " ", t).replace("'", "")
    return " ".join(w for w in t.split() if w not in DROP)


def _candidates(target, toks, lo, threshold):
    """All windows toks[i:j] (i >= lo) whose fuzzy score against target clears threshold, best j per i."""
    n_t = len(target.split())
    out = []
    span = max(1, n_t // 4)
    for i in range(lo, len(toks)):
        best = None
        for j in range(i + max(1, n_t - span), min(len(toks), i + n_t + span) + 1):
            s = fuzz.ratio(target, " ".join(toks[i:j]))
            if s >= threshold and (best is None or s > best[0]):
                best = (s, i, j)
        if best:
            out.append(best)
    # keep only window starts that are local maxima (avoid off-by-one duplicates of the same take)
    keep = []
    for c in out:
        if keep and c[1] - keep[-1][1] < max(2, n_t // 2):
            if c[0] > keep[-1][0]:
                keep[-1] = c
            continue
        keep.append(c)
    return keep


def align(lines, words, threshold=80):
    """lines: [(id, text)]. words: [(word, start, end)] in time order.
    Returns ({id: (start, end)}, [missing ids])."""
    # map each normalized token back to its source word (one word can normalize to several tokens)
    toks, owner = [], []
    for k, (w, _, _) in enumerate(words):
        for t in normalize(w).split():
            toks.append(t)
            owner.append(k)
    targets = [(lid, normalize(txt)) for lid, txt in lines]
    cands = [_candidates(t, toks, 0, threshold) if t else [] for _, t in targets]
    res, missing, lo = {}, [], 0
    for idx, (lid, _) in enumerate(targets):
        mine = [c for c in cands[idx] if c[1] >= lo]
        if not mine:
            missing.append(lid)
            continue
        # the next line's first take (after my first take) bounds which of my takes can be the last one
        nxt_start = None
        for later in cands[idx + 1:]:
            ok = [c[1] for c in later if c[1] >= mine[0][2]]
            if ok:
                nxt_start = min(ok)
                break
        usable = [c for c in mine if nxt_start is None or c[2] <= nxt_start] or mine[:1]
        s, i, j = usable[-1]
        res[lid] = (words[owner[i]][1], words[owner[j - 1]][2])
        lo = j
    return res, missing
