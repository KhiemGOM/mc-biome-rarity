"""Keep the cut list in step after VIDEO_SCRIPT.md is edited. Line ids (V001...) are just positions, so adding,
splitting or deleting a paragraph shifts every id after it. This matches old lines to new ones by their words and
renames the ids in make_cuts.py, EDIT_PLAN.md and tweaks.json. Run from video/edit, BEFORE committing the script edit:

  .venv\\Scripts\\python -m vo.remap            # old script = last commit, new = the file on disk
  .venv\\Scripts\\python -m vo.remap --dry-run  # just print the mapping

Lines that no longer match anything are reported, and their cut-list entries renamed OLD_Vxxx so nothing silently
lands under the wrong words. New lines get no visual (the previous one keeps showing) until you give them one."""
import os, re, subprocess, sys
from rapidfuzz import fuzz

ID = re.compile(r"\bV\d{3}\b")


def similarity(a, b):
    """0-100. Whole-line similarity, or a slightly discounted partial match so a split paragraph's pieces still
    recognise the paragraph they came from."""
    a, b = a.lower(), b.lower()
    return max(fuzz.ratio(a, b), 0.9 * fuzz.partial_ratio(a, b) if min(len(a), len(b)) >= 25 else 0)


def match_lines(old, new, threshold=60):
    """old, new: [(id, text)] in script order -> ({old_id: new_id}, [dropped old ids]). Order-preserving: the best
    total similarity over matchings that never cross (weighted longest common subsequence)."""
    n, m = len(old), len(new)
    sim = [[similarity(o[1], w[1]) for w in new] for o in old]
    best = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            take = sim[i][j] + best[i + 1][j + 1] if sim[i][j] >= threshold else -1
            best[i][j] = max(take, best[i + 1][j], best[i][j + 1])
    mapping, i, j = {}, 0, 0
    while i < n and j < m:
        if sim[i][j] >= threshold and best[i][j] == sim[i][j] + best[i + 1][j + 1]:
            mapping[old[i][0]] = new[j][0]; i += 1; j += 1
        elif best[i][j] == best[i + 1][j]:
            i += 1
        else:
            j += 1
    return mapping, [o[0] for o in old if o[0] not in mapping]


def rewrite_ids(text, mapping, dropped):
    """Rename every standalone Vxxx in one pass (so V010->V012 never chains into V012->V014). Dropped ids become
    OLD_Vxxx. -> (new text, number of ids changed)."""
    count = [0]

    def sub(mo):
        k = mo.group(0)
        v = mapping.get(k, f"OLD_{k}" if k in dropped else k)
        count[0] += v != k
        return v
    return ID.sub(sub, text), count[0]


def main():
    from .script_lines import parse
    edit = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script = os.path.join(edit, "..", "VIDEO_SCRIPT.md")
    ref = next((a for a in sys.argv[1:] if not a.startswith("--")), "HEAD")
    old_text = subprocess.run(["git", "show", f"{ref}:video/VIDEO_SCRIPT.md"], capture_output=True, text=True,
                              encoding="utf-8", check=True, cwd=edit).stdout
    vo = lambda t: [(i.id, i.text) for i in parse(t) if i.kind == "vo"]
    old, new = vo(old_text), vo(open(script, encoding="utf-8").read())
    mapping, dropped = match_lines(old, new)
    moved = {k: v for k, v in mapping.items() if k != v}
    added = [i for i, _ in new if i not in set(mapping.values())]
    print(f"{len(old)} -> {len(new)} lines. moved {len(moved)}, dropped {len(dropped)}, new {len(added)}")
    for k, v in moved.items():
        print(f"  {k} -> {v}")
    for k in dropped:
        print(f"  DROPPED {k}: {dict(old)[k][:70]}")
    for k in added:
        print(f"  NEW {k}: {dict(new)[k][:70]}")
    if "--dry-run" in sys.argv:
        return
    for name in ("make_cuts.py", "EDIT_PLAN.md", "tweaks.json"):
        p = os.path.join(edit, name)
        if not os.path.exists(p):  # tweaks.json only exists after a Resolve import
            continue
        text, n = rewrite_ids(open(p, encoding="utf-8", newline="").read(), mapping, dropped)
        open(p, "w", encoding="utf-8", newline="").write(text)
        print(f"{name}: {n} ids renamed")


if __name__ == "__main__":
    main()
