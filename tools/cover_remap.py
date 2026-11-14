"""cover_remap.py: carry text-coverage logs over a rebuild that moved the strings (not their text).

    python -X utf8 tools/cover_remap.py OLD_STRINGS.tsv NEW_STRINGS.tsv SRC_DIR OUT_DIR

textcover.py counts a string as shown when a log has "TEXT <address of its first byte>". A rebuild after a text
fix relocates nearly every string (build/strings.tsv), so the old tour's logs point at the old layout. For each
SRC_DIR/**/log.txt this writes OUT_DIR/<same relative dir>/log.txt holding, for every logged address that was a
string's first byte in OLD, "TEXT <that string's address in NEW>"; other addresses are dropped. Only valid for
strings whose text didn't change: re-shoot the scenes of the changed ones on the new build (Phase 8, reflow r24).
"""
import re
import sys
from pathlib import Path

TEXT = re.compile(r"^TEXT ([0-9A-Fa-f]+)", re.M)


def table(path):
    out = {}
    for ln in Path(path).read_text(encoding="utf-8").splitlines():
        f = ln.split("\t")
        if len(f) >= 2 and f[0] and not f[0].startswith("#"):
            out[f[0]] = int(f[1], 16)
    return out


def main(argv):
    if len(argv) != 4:
        sys.exit(__doc__)
    old, new, src, out = table(argv[0]), table(argv[1]), Path(argv[2]), Path(argv[3])
    by_addr = {a: i for i, a in old.items()}
    logs = ids = 0
    for log in sorted(src.rglob("log.txt")):
        seen = {by_addr[int(a, 16)] for a in TEXT.findall(log.read_text(encoding="utf-8", errors="replace"))
                if int(a, 16) in by_addr}
        seen = sorted(i for i in seen if i in new)
        dst = out / log.parent.relative_to(src) / "log.txt"
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(f"# remapped from {log.as_posix()} ({argv[0]} -> {argv[1]})\n"
                       + "".join(f"TEXT {new[i]:08X}\n" for i in seen), encoding="utf-8")
        logs += 1
        ids += len(seen)
    print(f"{logs} logs, {ids} string reads remapped into {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
