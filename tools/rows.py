"""Show script rows with their current English, for writing fixes.

    python -X utf8 tools/rows.py ID [ID2 | ID..ID2] ... [-c N]

Each argument is an id or a range FIRST..LAST (script order); -c N adds N rows of context on each side (default 1).
Columns: id, form (dlg / dlg+break / choice / sys), pixel limit, JP, then the current EN on the next line.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import batches  # noqa: E402


def main(argv):
    ctx = 1
    if "-c" in argv:
        k = argv.index("-c")
        ctx = int(argv[k + 1])
        argv = argv[:k] + argv[k + 2:]
    rows = batches.ordered()
    pos = {r["id"]: n for n, r in enumerate(rows)}
    want = set()
    for a in argv:
        lo, _, hi = a.partition("..")
        a0, a1 = pos[lo], pos[hi or lo]
        want.update(range(max(0, a0 - ctx), min(len(rows), a1 + ctx + 1)))
    last = None
    for n in sorted(want):
        r = rows[n]
        if last is not None and n != last + 1:
            print("--")
        nxt = rows[n + 1] if n + 1 < len(rows) else None
        print(f"{r['id']} {batches.form_of(r, nxt)} {batches.limit_label(r)} | {r['jp']}")
        print(f"    EN: {r['en']}")
        last = n


if __name__ == "__main__":
    main(sys.argv[1:])
