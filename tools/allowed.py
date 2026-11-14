"""Ranges the English build may change (Phase 7 romdiff check), from the RE constants, not from what the build did.

    python -X utf8 tools/allowed.py [OUT]        writes the ranges file (default build/allowed.txt)
    python -X utf8 tools/allowed.py --check      builds nothing: romdiff rom/ vs build/fantastic_children_en.gba,
                                                 with build/writes.txt (build.py's write log) when it exists

Allowed: free space 0x70F96C- (VWF hook/tables, relocated pages and page lists, system strings; the ROM may grow),
the message table (repointed), each system string's pointer holder (script/sys_*.tsv `ref`), and the two code
patches in vwf.apply (type_line hook, glyph upload skip), the 4 title backgrounds (G1/G2: block slot + record).
Everything else must equal the original.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import devlogo_gfx  # noqa: E402
import msgs  # noqa: E402
import title_gfx  # noqa: E402
import vwf  # noqa: E402
from script_tsv import load  # noqa: E402

FREE = 0x70F96C            # docs/re/text.md §Free space (trap-tested to 0x7FFFFF)
ROM_MAX = 0x2000000        # 32 MiB, the GBA cartridge window


def ranges():
    out = [(FREE, ROM_MAX - 1, "free space: VWF, relocated text"),
           (msgs.MSG_TABLE, msgs.MSG_TABLE + 4 * msgs.MSG_COUNT - 1, "message table, repointed"),
           (vwf.TYPE_LINE + 2 - vwf.BUS, vwf.TYPE_LINE + 2 - vwf.BUS + 9, "type_line hook"),
           (vwf.UPLOAD_SKIP - vwf.BUS, vwf.UPLOAD_SKIP - vwf.BUS + 1, "glyph upload skip")]
    rom = (ROOT / "rom" / "Fantastic Children (Japan).gba").read_bytes()
    for n, (b, rec) in enumerate(zip(title_gfx.BLOCKS, title_gfx.RECORDS)):
        out.append((b, b + title_gfx.slot(rom, n) - 1, f"title bg {n} (G1/G2), rewritten in place"))
        out.append((rec, rec + 7, f"title bg {n} record (offset, size) if the block moves"))
    out.append((devlogo_gfx.tile_off(devlogo_gfx.FIRST), devlogo_gfx.tile_off(devlogo_gfx.LAST) + 31,
                "boot developer logo tiles (G3)"))
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


def romdiff(orig, new, writes=None):
    """romdiff.py's exit code and output for ORIG vs NEW.
    writes=None: over ranges(). writes=PATH (the build's write log, writelog.WriteLog.save): no ranges at all, so
    every changed byte must belong to a logged write whose original bytes match ORIG and that no later write
    overwrote; on top, every logged write must lie inside ranges()."""
    if writes is None:
        args = [f"{a:X}-{b:X}" for a, b, _ in ranges()]
    else:
        args = ["--writes", str(writes)]
        rs = ranges()
        bad = []
        for ln in Path(writes).read_text(encoding="utf-8").splitlines():
            off, a, _, by = ln.split(" ", 3)
            o, n = int(off, 16), len(a) // 2
            if not any(lo <= o and o + n - 1 <= hi for lo, hi, _ in rs):
                bad.append(f"0x{o:06X}: {by} ({n} bytes) is outside the allowed ranges")
        if bad:
            return 1, "\n".join(bad[:50])
    r = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "tools" / "romdiff.py"), str(orig), str(new)] + args,
                       capture_output=True, text=True, encoding="utf-8")
    return r.returncode, (r.stdout + r.stderr).strip()


if __name__ == "__main__":
    if sys.argv[1:] == ["--check"]:
        log = ROOT / "build" / "writes.txt"
        rc, out = romdiff(ROOT / "rom" / "Fantastic Children (Japan).gba", ROOT / "build" / "fantastic_children_en.gba",
                          log if log.exists() else None)
        print(out)
        sys.exit(rc)
    print(write(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "build" / "allowed.txt"))
