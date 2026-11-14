"""Pairs files for the reviewer pass: every translated row as `>> id | ref | JP` / `EN`, with +-2 context rows.

    python -X utf8 tools/pairs.py OUTDIR [--chunks N] [--ids FILE]   writes OUTDIR/pairs_NN.txt, split on messages
    (--ids: only the rows listed in FILE, e.g. a re-review of fixed rows)

Rows are in script order (script/*.tsv by file name); blank Japanese rows are context only.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from script_tsv import load  # noqa: E402


def rows():
    return list(load().values())   # script order: files by name, rows in file order


def msg(r):
    return (r["file"], r["ref"].split(",")[0].split(".")[0])


def blocks(rs, ctx=2, only=None):
    """One text block per translated row (or per row in `only`): context rows (indented) around the `>>` row."""
    out = []
    for i, r in enumerate(rs):
        if not r["jp"].strip() or (only is not None and r["id"] not in only):
            continue
        lines = []
        for j in range(max(0, i - ctx), min(len(rs), i + ctx + 1)):
            c = rs[j]
            if j == i:
                lines.append(f">> {c['id']} | {c['ref']} | {c['jp']}\n   EN: {c['en']}")
            elif msg(c) == msg(r):
                lines.append(f"   ({c['id']}) {c['jp']} -> {c['en']}")
        out.append((msg(r), "\n".join(lines)))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("outdir")
    ap.add_argument("--chunks", type=int, default=8)
    ap.add_argument("--ids", help="file whose lines start with the row ids to include (e.g. a fixes .out.tsv)")
    a = ap.parse_args()
    only = None
    if a.ids:
        only = {ln.split("\t")[0].strip() for ln in Path(a.ids).read_text(encoding="utf-8").splitlines() if ln.strip()}
    bl = blocks(rows(), only=only)
    size = -(-len(bl) // a.chunks)
    chunks, cur = [], []
    for k, (m, text) in enumerate(bl):
        if len(cur) >= size and m != bl[k - 1][0]:
            chunks.append(cur)
            cur = []
        cur.append(text)
    if cur:
        chunks.append(cur)
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    for n, c in enumerate(chunks, 1):
        (out / f"pairs_{n:02d}.txt").write_text("\n\n".join(c) + "\n", encoding="utf-8")
        print(f"{out / f'pairs_{n:02d}.txt'}: {len(c)} rows")


if __name__ == "__main__":
    main()
