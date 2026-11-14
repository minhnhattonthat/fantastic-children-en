"""build.py: the one build entry point.

    python -X utf8 build.py              # -> build/fantastic_children_en.gba (until Phase 4/5: same as --identity)
    python -X utf8 build.py --identity   # unpack + repack with no edits -> build/identity.gba, must equal the dump

Checks the dump against rom.sha1 first.
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
    """Every rebuildable part unpacked and written back. No edits yet: the output must equal the input."""
    s = Script.unpack(d)
    return s.repack(d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--identity", action="store_true")
    a = ap.parse_args()
    check_rom.check()
    d = ROM.read_bytes()
    out = repack(d)
    BUILD.mkdir(exist_ok=True)
    path = BUILD / ("identity.gba" if a.identity else "fantastic_children_en.gba")
    path.write_bytes(out)
    print(f"{path.relative_to(ROOT)}  {len(out)} bytes  sha1 {hashlib.sha1(out).hexdigest()}")
    if a.identity:
        if out != d:
            diff = next(i for i in range(min(len(d), len(out))) if d[i] != out[i]) if len(d) == len(out) else -1
            sys.exit(f"identity build differs from the dump (first diff at {diff:#x})")
        print("identical")


if __name__ == "__main__":
    main()
