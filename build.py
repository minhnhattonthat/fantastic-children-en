"""build.py: the one build entry point.

    python -X utf8 build.py              # -> build/fantastic_children_en.gba: VWF + every `en` in script/
    python -X utf8 build.py --marker     # -> build/marker.gba: every string replaced by `[id] marker text`
    python -X utf8 build.py --identity   # unpack + repack with no edits -> build/identity.gba, must equal the dump

Checks the dump against rom.sha1 first. Every write is logged (build/writes.txt; romdiff.py --writes, tools/allowed.py).
"""
import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
import check_rom  # noqa: E402
from msgs import Script  # noqa: E402

ROM = ROOT / "rom" / "Fantastic Children (Japan).gba"
BUILD = ROOT / "build"


def repack(d):
    """Every rebuildable part unpacked and written back. No edits: the output must equal the input."""
    s = Script.unpack(d)
    return s.repack(d)


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--identity", action="store_true")
    g.add_argument("--marker", action="store_true")
    ap.add_argument("--marker-px", type=int, default=168, help="marker page width (192 = bottom box stress)")
    ap.add_argument("--qa", action="append", default=[], metavar="ID=TEXT",
                    help="override one row's text (stress tests); output build/qa.gba")
    a = ap.parse_args()
    check_rom.check()
    d = ROM.read_bytes()
    log = None
    if a.identity:
        out, name = repack(d), "identity.gba"
    else:
        from insert import build_rom
        from writelog import WriteLog
        qa = dict(q.split("=", 1) for q in a.qa)
        log, strings = WriteLog(d), {}
        out = build_rom(d, "marker" if a.marker else "en", a.marker_px, qa, log=log, strings=strings)
        name = (f"marker{'' if a.marker_px == 168 else a.marker_px}.gba" if a.marker else "fantastic_children_en.gba")
        name = "qa.gba" if qa else name
    BUILD.mkdir(exist_ok=True)
    path = BUILD / name
    path.write_bytes(out)
    if log is not None:   # romdiff.py --writes log: build/writes.txt for the English build, else <name>.writes.txt
        log.save(BUILD / ("writes.txt" if name == "fantastic_children_en.gba" else name[:-4] + ".writes.txt"))
        # textcover.py input: id -> the bus address the game reads the string's first byte from
        (BUILD / ("strings.tsv" if name == "fantastic_children_en.gba" else name[:-4] + ".strings.tsv")).write_text(
            "".join(f"{i}\t{a:X}\n" for i, a in sorted(strings.items())), encoding="utf-8", newline="\n")
    print(f"{path.relative_to(ROOT)}  {len(out)} bytes  sha1 {hashlib.sha1(out).hexdigest()}")
    if a.identity:
        if out != d:
            diff = next(i for i in range(min(len(d), len(out))) if d[i] != out[i]) if len(d) == len(out) else -1
            sys.exit(f"identity build differs from the dump (first diff at {diff:#x})")
        print("identical")


if __name__ == "__main__":
    main()
