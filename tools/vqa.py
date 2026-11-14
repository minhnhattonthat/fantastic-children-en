"""vqa.py: visual-QA verdicts with codex (Orca allows no subagents): one `codex exec -s read-only` per qa_gate chunk.

    python -X utf8 tools/vqa.py CHUNKDIR [chunk_001 ..] [--jobs 3] [--index work/qa/p8/tour/qa/index.tsv]
    python -X utf8 tools/vqa.py CHUNKDIR --check

CHUNKDIR holds qa_gate.py's chunk_NNN.txt (one sheet path per line, from `qa_gate.py todo ... --out-dir`). Each run
gets docs/visual-qa-brief.md + glossary.md inline, the chunk's sheets attached as images (in order), and for each
sheet which scenes its tiles show (index.tsv). The reviewer's final message must be verdict lines only,
`id<TAB>ok|issue<TAB>note`, one per sheet; the run's answer goes to CHUNKDIR/answer_NNN.txt and, when every id of
the chunk has exactly one valid line, to work/qa/verdicts/chunk_NNN.tsv (qa_gate's verdict dir). --check lists
chunks without a complete verdict file.
"""
import argparse
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERDICTS = ROOT / "work" / "qa" / "verdicts"
DOCS = ("docs/visual-qa-brief.md", "glossary.md")


def sheets(chunk):
    return [Path(ln.strip()) for ln in chunk.read_text(encoding="utf-8").splitlines() if ln.strip()]


def sheet_id(p, root):
    return Path(p).resolve().relative_to(root.resolve()).with_suffix("").as_posix()


def scenes(index):
    out = {}
    if index.exists():
        for ln in index.read_text(encoding="utf-8").splitlines()[1:]:
            f = ln.split("\t")
            if len(f) >= 3:
                out.setdefault(f[0], []).append(f"{f[1]} ({f[2]} tiles)")
    return out


def prompt(chunk, root, index):
    sc = scenes(index)
    parts = [f"=== {d} ===\n" + (ROOT / d).read_text(encoding="utf-8") for d in DOCS]
    lines = []
    for i, p in enumerate(sheets(chunk), 1):
        sid = sheet_id(p, root)
        lines.append(f"image {i}: id {sid} - scenes in reading order: " + ", ".join(sc.get(Path(p).stem, ["?"])))
    parts.append(
        "=== This run ===\n"
        "The sheets are attached as images, in this order (4 tiles per row, 240x160 each, left to right, top to "
        "bottom; each scene's tiles are consecutive):\n" + "\n".join(lines) + "\n\n"
        "You may run read-only commands (e.g. the brief's sheet.py/inkbox.py with --out under your temp dir) but "
        "need not. Judge every sheet. Your FINAL message must be only the verdict lines, one per sheet id above, "
        "`id<TAB>ok|issue<TAB>note` (a real tab; for an issue name the scene, the tile and what is wrong), nothing "
        "else.")
    return "\n\n".join(parts)


def parse(text, ids):
    got = {}
    for ln in text.splitlines():
        f = re.split(r"\t| {2,}", ln.strip().strip("`"), maxsplit=2)
        if len(f) >= 2 and f[0] in ids and f[1] in ("ok", "issue"):
            got.setdefault(f[0], []).append((f[1], f[2] if len(f) > 2 else ""))
    return got


def run(d, chunk, root, index):
    nn = chunk.stem.split("_")[1]
    ans = d / f"answer_{nn}.txt"
    cmd = ["codex", "exec", "-s", "read-only", "--skip-git-repo-check", "-o", str(ans)]
    for p in sheets(chunk):
        cmd += ["-i", str(p)]
    with open(d / f"log_{nn}.txt", "w", encoding="utf-8") as log:
        r = subprocess.run(cmd + ["-"], input=prompt(chunk, root, index), text=True, encoding="utf-8",
                           stdout=log, stderr=subprocess.STDOUT, cwd=ROOT)
    return nn, r.returncode, save(d, chunk, root)


def save(d, chunk, root):
    nn = chunk.stem.split("_")[1]
    ans = d / f"answer_{nn}.txt"
    ids = [sheet_id(p, root) for p in sheets(chunk)]
    got = parse(ans.read_text(encoding="utf-8"), set(ids)) if ans.exists() else {}
    missing = [i for i in ids if len(got.get(i, [])) != 1]
    if missing:
        return f"incomplete: {len(missing)} of {len(ids)} ids without exactly one verdict"
    VERDICTS.mkdir(parents=True, exist_ok=True)
    (VERDICTS / f"chunk_{nn}.tsv").write_text(
        "".join(f"{i}\t{got[i][0][0]}\t{got[i][0][1]}\n" for i in ids), encoding="utf-8", newline="\n")
    issues = sum(got[i][0][0] == "issue" for i in ids)
    return f"saved {len(ids)} verdicts, {issues} issue(s)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("nn", nargs="*")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--root", default="work/qa/p8/tour/qa", help="the dir qa_gate init got (ids are relative to it)")
    ap.add_argument("--index", default="work/qa/p8/tour/qa/index.tsv")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    d, root, index = Path(a.dir), ROOT / a.root, ROOT / a.index
    chunks = sorted(d.glob("chunk_*.txt"))
    if a.nn:
        chunks = [c for c in chunks if c.stem in a.nn or c.stem.split("_")[1] in a.nn]
    if a.check:
        bad = [c.stem for c in chunks if not (VERDICTS / f"{c.stem}.tsv").exists()]
        print(f"{len(chunks) - len(bad)}/{len(chunks)} chunks have verdicts" + (": missing " + " ".join(bad) if bad else ""))
        return 1 if bad else 0
    with ThreadPoolExecutor(a.jobs) as ex:
        for nn, rc, msg in ex.map(lambda c: run(d, c, root, index), chunks):
            print(f"chunk_{nn}: exit {rc}, {msg}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
