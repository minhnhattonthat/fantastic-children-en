"""events.py: catalogue the event scripts in the 36-byte event-record table (docs/re/events.md).

    python -X utf8 tools/events.py [--tsv OUT]

A script starts at record 0 or after a record whose next field (+0x20) is 0xFFFE (end). For each script it lists
the record range, the message ids it shows (+0xC), the battle ids it starts (+0x19), the jump targets, and the
first page of its first message, plus which stage areas use it as their entry event (area table +0xE).
"""
import argparse
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from dec import ROM, message, page  # noqa: E402
from tbl import Table  # noqa: E402

REC_BASE, REC_COUNT, REC_SIZE = 0x66F30, 2713, 36
AREA_TABLE = 0x20D0FC                     # 7 world pointers -> 20-byte area entries
WORLD_AREAS = [1, 9, 14, 10, 13, 8, 5]    # areas per world (pointer gaps)


def records(d):
    return [struct.unpack_from("<18H", d, REC_BASE + REC_SIZE * i) for i in range(REC_COUNT)]


def areas(d):
    """(stage byte, entry event record or None) for every area; stage byte = world | area << 4."""
    out = []
    for w, n in enumerate(WORLD_AREAS):
        base = struct.unpack_from("<I", d, AREA_TABLE + 4 * w)[0] - 0x08000000
        for a in range(n):
            ev = struct.unpack_from("<H", d, base + 20 * a + 0xE)[0]
            out.append((w | a << 4, None if ev & 0x8000 else ev))
    return out


def scripts(recs):
    starts = [0] + [i + 1 for i, r in enumerate(recs[:-1]) if r[16] == 0xFFFE]
    out = []
    for k, s in enumerate(starts):
        e = (starts[k + 1] if k + 1 < len(starts) else len(recs)) - 1
        msgs = [r[6] for r in recs[s:e + 1] if r[6] != 0xFFFF]
        bats = [r[12] >> 8 for r in recs[s:e + 1] if r[12] >> 8 != 0xFF]
        jumps = [r[16] for r in recs[s:e + 1] if r[16] < 0xFFFE]
        out.append((s, e, msgs, bats, jumps))
    return out


def cond(rec):
    """(flag, jump target) of a record's condition, flag signed (> 0: jump if set, < 0: jump if clear), or None."""
    f0 = rec[0] - 0x10000 if rec[0] & 0x8000 else rec[0]
    return None if f0 == 0x7FFF else (f0, rec[1])


def flow(recs, start, first=None):
    """Records reachable from `start` the way the runner walks them: a condition may jump (both ways followed),
    `next` 0xFFFF steps on, 0xFFFE ends, else jumps. `first`: True/False forces the start record's condition
    taken/not taken. Returns the records in visiting order (first-seen, depth first along the fall-through)."""
    seen, order, todo = set(), [], [(start, first)]
    while todo:
        i, force = todo.pop()
        while 0 <= i < len(recs) and i not in seen:
            seen.add(i)
            order.append(i)
            r, c = recs[i], cond(recs[i])
            if c and force is not False:
                if force is True:  # resolve() jumps before the record runs: it shows nothing
                    order.pop()
                    seen.discard(i)
                    i, force = c[1], None
                    continue
                todo.append((c[1], None))
            force = None
            if r[7] != 0xFFFF:  # choice list (+0x0E message): +0x10/+0x12/+0x14 = record per answer
                todo.extend((t, None) for t in r[8:11] if t < len(recs))
            nxt = r[16]
            if nxt == 0xFFFE:
                break
            i = i + 1 if nxt == 0xFFFF else nxt
    return order


def flow_msgs(recs, start, first=None):
    """Messages (+0x0C text, +0x0E choice list) the records reachable from `start` show."""
    return [m for i in flow(recs, start, first) for m in recs[i][6:8] if m != 0xFFFF]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tsv", type=Path)
    a = ap.parse_args()
    d = ROM.read_bytes()
    t = Table.load(ROOT / "tbl" / "jp.tbl")
    recs = records(d)
    entry = {}
    for stg, ev in areas(d):
        if ev is not None:
            entry.setdefault(ev, []).append(f"{stg:02X}")
    lines = ["start\tend\tentry_of\tmsgs\tbattles\tjumps\tfirst_text"]
    for s, e, msgs, bats, jumps in scripts(recs):
        first = ""
        if msgs:
            pages = message(d, msgs[0])
            if pages:
                first = page(t, d, pages[0])[0][:30]
        ent = ",".join(sorted(set(sum((entry.get(i, []) for i in range(s, e + 1)), []))))
        lines.append(f"{s}\t{e}\t{ent}\t{','.join(map(str, msgs))}\t{','.join(map(str, bats))}\t"
                     f"{','.join(map(str, jumps))}\t{first}")
    out = "\n".join(lines) + "\n"
    if a.tsv:
        a.tsv.write_text(out, encoding="utf-8")
    else:
        sys.stdout.write(out)


if __name__ == "__main__":
    main()
