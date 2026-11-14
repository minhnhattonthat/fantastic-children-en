"""Ranges the English build may change (Phase 7 romdiff check), from the RE constants, not from what the build did.

    python -X utf8 tools/allowed.py [OUT]        writes the ranges file (default build/allowed.txt)
    python -X utf8 tools/allowed.py --check      builds nothing: romdiff rom/ vs build/fantastic_children_en.gba

Allowed: free space 0x70F96C- (VWF hook/tables, relocated pages and page lists, system strings; the ROM may grow),
the message table (repointed), each system string's pointer holder (script/sys_*.tsv `ref`), and the two code
patches in vwf.apply (type_line hook, glyph upload skip). Everything else must equal the original.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import msgs  # noqa: E402
import vwf  # noqa: E402
from script_tsv import load  # noqa: E402

FREE = 0x70F96C            # docs/re/text.md §Free space (trap-tested to 0x7FFFFF)
ROM_MAX = 0x2000000        # 32 MiB, the GBA cartridge window


def ranges():
    out = [(FREE, ROM_MAX - 1, "free space: VWF, relocated text"),
           (msgs.MSG_TABLE, msgs.MSG_TABLE + 4 * msgs.MSG_COUNT - 1, "message table, repointed"),
           (vwf.TYPE_LINE + 2 - vwf.BUS, vwf.TYPE_LINE + 2 - vwf.BUS + 9, "type_line hook"),
           (vwf.UPLOAD_SKIP - vwf.BUS, vwf.UPLOAD_SKIP - vwf.BUS + 1, "glyph upload skip")]
    for r in load().values():
        if r["id"][0] == "s":
            for h in r["ref"].split(","):
                h = int(h, 16)
                out.append((h, h + 3, f"pointer to {r['id']}"))
    return out


def write(path):
    path.parent.mkdir(exist_ok=True)
    path.write_text("".join(f"{a:X}-{b:X}  # {why}\n" for a, b, why in ranges()), encoding="utf-8", newline="\n")
    return path


def romdiff(orig, new):
    """romdiff.py's exit code and output for ORIG vs NEW over ranges()."""
    args = [f"{a:X}-{b:X}" for a, b, _ in ranges()]
    r = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "tools" / "romdiff.py"), str(orig), str(new)] + args,
                       capture_output=True, text=True, encoding="utf-8")
    return r.returncode, (r.stdout + r.stderr).strip()


if __name__ == "__main__":
    if sys.argv[1:] == ["--check"]:
        rc, out = romdiff(ROOT / "rom" / "Fantastic Children (Japan).gba", ROOT / "build" / "fantastic_children_en.gba")
        print(out)
        sys.exit(rc)
    print(write(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "build" / "allowed.txt"))
