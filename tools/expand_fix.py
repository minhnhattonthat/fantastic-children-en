"""Expand hand-written fixes to every copy: work/tl/rNN.hand.tsv (id<TAB>EN) -> work/tl/rNN.out.tsv.

    python -X utf8 tools/expand_fix.py rNN      then: tools/tl.py fix rNN; tools/batches.py merge rNN --overwrite

A fix also goes to every other row with the same Japanese AND the same old English (a stored copy of the scene).
List ids that must not take a copy (their neighbours read differently) in work/tl/rNN.noexpand, space-separated.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import batches  # noqa: E402

TL = ROOT / "work" / "tl"


def main(b):
    rows = batches.ordered()
    byid = {r["id"]: r for r in rows}
    hand = {}
    for ln in (TL / f"{b}.hand.tsv").read_text(encoding="utf-8").splitlines():
        if "\t" in ln:
            i, e = ln.split("\t", 1)
            hand[i] = e
    no = TL / f"{b}.noexpand"
    skip = set(no.read_text(encoding="utf-8").split()) if no.exists() else set()
    out = dict(hand)
    for i, e in hand.items():
        r = byid[i]
        for s in rows:
            if s["id"] not in hand and s["id"] not in skip and s["jp"] == r["jp"] and s["en"] == r["en"]:
                out[s["id"]] = e
    (TL / f"{b}.out.tsv").write_text("".join(f"{r['id']}\t{out[r['id']]}\n" for r in rows if r["id"] in out),
                                     encoding="utf-8", newline="\n")
    print(f"{len(hand)} hand, {len(out)} with copies")


if __name__ == "__main__":
    main(sys.argv[1])
