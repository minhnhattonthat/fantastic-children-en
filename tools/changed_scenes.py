"""changed_scenes.py: scenes to re-shoot after text fixes (Phase 8 visual QA).

    python -X utf8 tools/changed_scenes.py REV RUN_DIR [RUN_DIR ...] [--force tools/debug/force.gba.txt]

Messages whose English differs between git revision REV and the working tree (script/*.tsv, by page id; a page
counts for every message in its ref list). A scene shows a message when its log.txt has `MSG id` (warp.lua logs
every get_msg) or, for forced scenes, when the id is in its `force=` list. Prints the scene names, one per line,
sorted; the count goes to stderr.
"""
import csv
import io
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_tsv(text):
    return {r["id"]: r for r in csv.DictReader(io.StringIO(text), delimiter="\t", quoting=csv.QUOTE_NONE)}


def changed_messages(rev):
    out = set()
    for path in sorted((ROOT / "script").glob("*.tsv")):
        rel = path.relative_to(ROOT).as_posix()
        try:
            old_text = subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=ROOT, capture_output=True, check=True,
                                      encoding="utf-8").stdout
        except subprocess.CalledProcessError:
            old_text = ""
        old, new = read_tsv(old_text), read_tsv(path.read_text(encoding="utf-8"))
        for rid, r in new.items():
            if rid[0] == "p" and old.get(rid, {}).get("en") != r["en"]:
                out.update(int(ref[1:].split(".")[0]) for ref in r["ref"].split(","))
    return out


def main(argv):
    force_file = None
    if "--force" in argv:
        k = argv.index("--force")
        force_file = Path(argv[k + 1])
        argv = argv[:k] + argv[k + 2:]
    if len(argv) < 2:
        sys.exit(__doc__)
    msgs = changed_messages(argv[0])
    forced = {}
    if force_file:
        for line in force_file.read_text(encoding="utf-8").splitlines():
            m = re.match(r"(\S+)\s.*\bforce=([\d,]+)", line)
            if m:
                forced[m.group(1)] = {int(x) for x in m.group(2).split(",")}
    scenes = set()
    for run in argv[1:]:
        for log in Path(run).glob("*/log.txt"):
            name = log.parent.name
            shown = {int(x) for x in re.findall(r"\bMSG (\d+)", log.read_text(encoding="utf-8", errors="replace"))}
            if shown & msgs or forced.get(name, set()) & msgs:
                scenes.add(name)
    print(f"{len(msgs)} changed messages, {len(scenes)} scenes", file=sys.stderr)
    print("\n".join(sorted(scenes)))


if __name__ == "__main__":
    main(sys.argv[1:])
