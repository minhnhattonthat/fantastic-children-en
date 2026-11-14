"""Reviewer pass with codex, the chunk inlined in the prompt (no shell or file reads, so nothing gets cut).

    python -X utf8 tools/review.py DIR [NN ...] [--jobs 4]    DIR/pairs_NN.txt (tools/pairs.py) -> DIR/report_NN.md
    python -X utf8 tools/review.py DIR --check                 every report names its chunk's first and last id

The prompt = work/review/brief.md + glossary.md + docs/style-reference.md + docs/synopsis.md + the pairs chunk,
sent on stdin (`codex exec -s read-only -`). Each report must start with `Coverage: FIRST_ID .. LAST_ID (N rows)`;
--check compares that line with the chunk. Logs: DIR/log_NN.txt (the model name is in the log header).
"""
import argparse
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ["work/review/brief.md", "glossary.md", "docs/style-reference.md", "docs/synopsis.md"]


def span(pairs):
    ids = re.findall(r"^>> (\S+)", pairs.read_text(encoding="utf-8"), re.M)
    return ids[0], ids[-1], len(ids)


def prompt(pairs):
    first, last, n = span(pairs)
    parts = [f"=== {d} ===\n" + (ROOT / d).read_text(encoding="utf-8") for d in DOCS]
    parts.append(
        "=== Instructions for this run ===\n"
        "Everything you need is inline above and below: do NOT run commands or read files. The glossary, style "
        "reference and synopsis are given above; the pairs chunk is below, complete.\n"
        "Start your report with exactly one line: `Coverage: FIRST_ID .. LAST_ID (N rows)`, the first and last `>>` "
        "ids you judged and how many `>>` rows there were. Judge every `>>` row.")
    parts.append(f"=== Pairs chunk {pairs.name} ===\n" + pairs.read_text(encoding="utf-8"))
    return "\n\n".join(parts)


def run(d, nn):
    pairs = d / f"pairs_{nn}.txt"
    with open(d / f"log_{nn}.txt", "w", encoding="utf-8") as log:
        r = subprocess.run(["codex", "exec", "-s", "read-only", "--skip-git-repo-check", "-o",
                            str(d / f"report_{nn}.md"), "-"], input=prompt(pairs), text=True, encoding="utf-8",
                           stdout=log, stderr=subprocess.STDOUT, cwd=ROOT)
    return nn, r.returncode


def check(d):
    bad = 0
    for pairs in sorted(d.glob("pairs_*.txt")):
        nn = pairs.stem.split("_")[1]
        first, last, n = span(pairs)
        rep = d / f"report_{nn}.md"
        text = rep.read_text(encoding="utf-8") if rep.exists() else ""
        m = re.search(r"Coverage:\s*`?(\S+)\s*\.\.\s*(\S+?)`?\s*\((\d+) rows\)", text)
        ok = bool(m) and (m.group(1), m.group(2), int(m.group(3))) == (first, last, n)
        verdict = re.search(r"(Approved|Needs fixes)", text.split("### Assessment")[-1]) if text else None
        print(f"{nn} {'ok  ' if ok else 'FAIL'} want {first}..{last} ({n}) got "
              f"{m.group(0) if m else 'no coverage line'} | {verdict.group(1) if verdict else '-'}")
        bad += not ok
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("nn", nargs="*")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    d = Path(a.dir)
    if a.check:
        return check(d)
    nns = a.nn or sorted(p.stem.split("_")[1] for p in d.glob("pairs_*.txt"))
    with ThreadPoolExecutor(a.jobs) as ex:
        for nn, rc in ex.map(lambda nn: run(d, nn), nns):
            print(nn, "rc", rc, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
