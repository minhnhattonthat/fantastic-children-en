"""script_tsv.py: extract every string to script/*.tsv and load it back (see docs/re/text.md §Text inventory).

    python -X utf8 tools/script_tsv.py extract          # writes missing files only
    python -X utf8 tools/script_tsv.py extract --force  # rewrites jp/ref from the ROM, keeps en and notes by id
    python -X utf8 tools/script_tsv.py stats

    from script_tsv import rom_rows, load
    rows = rom_rows(rom)   # [Row]: every string in the ROM, in file order
    tsv = load()           # {id: {"id", "ref", "jp", "en", "notes"}} from script/

Two kinds of string, same encoding (16-bit codes, end code 0x8000 | word count, no newline code):
  - pages (id `pXXXXXX`): one line of a dialogue message; message table -> page lists -> pages (msgs.Script).
    ref = the messages showing it, `m<id>.<page index>`. Files `script/msg_NNNN.tsv`, by first message, 100 per file.
  - system strings (id `sXXXXXX`): menus, area names, item and card text, battle lines; stored back to back in
    SYS_RANGES and reached by u32 pointers from code literal pools and the tables at 0x219BC0-0x21C000.
    ref = the pointer holders (file offsets). Files `script/sys_<range>.tsv`.
Ids are the ROM file offset of the string, so they stay stable across re-extracts.
"""
import argparse
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from msgs import BUS, END, Script  # noqa: E402
from tbl import Table  # noqa: E402

ROM = ROOT / "rom" / "Fantastic Children (Japan).gba"
SCRIPT = ROOT / "script"
COLUMNS = ["id", "ref", "jp", "en", "notes"]
PAGES_TEXT_END = 0x9C140     # pages tile 0x7ECB4-0x9C140 exactly; 0x9C140-0x9C610 is a data block (ptr at 0x3112C)
# system strings, back to back; the gaps between ranges are data (docs/re/text.md §Text inventory)
SYS_RANGES = [
    ("menu", 0x9C610, 0x9CFB2),    # save/file menus, area names, save messages
    ("menu", 0x9CFB4, 0x9D030),    # after a 2-byte pad; 0x9D030-0x9D510 is a u16 data block
    ("items", 0x9D510, 0x9F6B4),   # equip menus, card/item descriptions; 0x9F6B4-0x9F6C4 = u16 0..7 (ptr 0x373DC)
    ("battle", 0x9F6C4, 0xA0632),  # battle and talk-battle lines, pickups; palettes follow at 0xA0632
    ("menu", 0x669F4, 0x66A04),    # cursor strings ▼ / blank / ▶ / blank (ptrs at 0x2E6EC, 0x2E768)
]
HOLDERS = [(0x0, 0x40000), (0x219BC0, 0x21C000)]  # where u32 pointers to system strings live (code pools, tables)
MSGS_PER_FILE = 100


@dataclass
class Row:
    id: str
    off: int
    size: int      # bytes including the end code
    jp: str
    ref: str
    file: str


ENDFLAG = "{endflag}"   # end code bit 14 (0x4000): 11 battle lines set it, meaning unknown; kept as a trailing token
FLAG = 0x4000


def _end(d, a):
    o = a
    while not struct.unpack_from("<H", d, o)[0] & END:
        o += 2
    return o


def encode(tbl, text):
    """String bytes for `text` as the ROM stores it: codes, then the end code 0x8000 | word count (| 0x4000 when
    the text ends with {endflag})."""
    flag = FLAG if text.endswith(ENDFLAG) else 0
    codes = tbl.encode(text[:-len(ENDFLAG)] if flag else text)
    n = len(codes) // 2
    if len(codes) % 2 or n > 0xFF:
        raise ValueError(f"bad length ({len(codes)} bytes) for {text!r}")
    return codes + struct.pack("<H", END | flag | n)


def sys_holders(d):
    """{string offset: [holder offsets]} for every u32 in HOLDERS pointing into a system range."""
    out = {}
    for lo, hi in HOLDERS:
        for o in range(lo, hi - 3, 4):
            w = struct.unpack_from("<I", d, o)[0] - BUS
            if any(a <= w < b for _, a, b in SYS_RANGES):
                out.setdefault(w, []).append(o)
    return out


def rom_rows(d, tbl=None):
    tbl = tbl or Table.load(ROOT / "tbl" / "jp.tbl")
    s = Script.unpack(d, tbl)
    first = {}
    for n, offs in s.messages():
        for i, off in enumerate(offs):
            first.setdefault(off, []).append((n, i))
    rows = []
    for off in sorted(first, key=lambda o: (first[o][0], o)):
        n0 = first[off][0][0]
        rows.append(Row(f"p{off:06X}", off, s.sizes[off], s.pages[off],
                        ",".join(f"m{n}.{i}" for n, i in first[off]),
                        f"msg_{n0 // MSGS_PER_FILE * MSGS_PER_FILE:04d}.tsv"))
    holders = sys_holders(d)
    for name, lo, hi in SYS_RANGES:
        a = lo
        while a < hi:
            o = _end(d, a)
            text, used = tbl.decode(d[a:o], 0, o - a)
            assert used == o - a
            end = struct.unpack_from("<H", d, o)[0]
            if end & 0x7F00 not in (0, FLAG):
                raise ValueError(f"string {a:#x}: unknown end code {end:#06x}")
            text += ENDFLAG if end & FLAG else ""
            rows.append(Row(f"s{a:06X}", a, o + 2 - a, text,
                            ",".join(f"{h:X}" for h in holders.get(a, [])), f"sys_{name}.tsv"))
            a = o + 2
    return rows


def read_tsv(path):
    lines = path.read_text(encoding="utf-8").split("\n")
    if lines[0].split("\t") != COLUMNS:
        raise ValueError(f"{path}: header is not {COLUMNS}")
    out = []
    for n, line in enumerate(lines[1:], 2):
        if line == "":
            continue
        f = line.split("\t")
        if len(f) != len(COLUMNS):
            raise ValueError(f"{path}:{n}: {len(f)} fields, want {len(COLUMNS)}")
        out.append(dict(zip(COLUMNS, f)))
    return out


def load(folder=SCRIPT):
    out = {}
    for p in sorted(Path(folder).glob("*.tsv")):
        for r in read_tsv(p):
            if r["id"] in out:
                raise ValueError(f"{p}: duplicate id {r['id']}")
            r["file"] = p.name
            out[r["id"]] = r
    return out


def write_tsv(path, rows):
    lines = ["\t".join(COLUMNS)]
    for r in rows:
        for k in COLUMNS:
            if "\t" in r[k] or "\n" in r[k] or "\r" in r[k]:
                raise ValueError(f"{r['id']}: tab or newline in {k}")
        lines.append("\t".join(r[k] for k in COLUMNS))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def extract(d, force=False, folder=SCRIPT):
    folder = Path(folder)
    folder.mkdir(exist_ok=True)
    old = load(folder) if force else {}
    files = {}
    for r in rom_rows(d):
        files.setdefault(r.file, []).append(r)
    wrote, kept = [], []
    for name, rows in files.items():
        path = folder / name
        if path.exists() and not force:
            kept.append(name)
            continue
        out = []
        for r in rows:
            prev = old.get(r.id, {})
            out.append({"id": r.id, "ref": r.ref, "jp": r.jp, "en": prev.get("en", ""), "notes": prev.get("notes", "")})
        write_tsv(path, out)
        wrote.append(name)
    lost = set(old) - {r.id for rows in files.values() for r in rows}
    if lost:
        raise SystemExit(f"ids in script/ no longer in the ROM: {sorted(lost)[:10]}")
    return wrote, kept


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["extract", "stats"])
    ap.add_argument("--force", action="store_true", help="rewrite existing files (en and notes are kept by id)")
    a = ap.parse_args()
    d = ROM.read_bytes()
    if a.cmd == "extract":
        wrote, kept = extract(d, a.force)
        print(f"wrote {len(wrote)} files, kept {len(kept)} existing (use --force to refresh jp)")
    else:
        t = load()
        done = sum(1 for r in t.values() if r["en"])
        print(f"{len(t)} rows, {done} translated, {len(t) - done} to go")


if __name__ == "__main__":
    main()
