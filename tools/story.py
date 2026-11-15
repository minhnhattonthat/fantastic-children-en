"""Story pass (Phase 9): one chapter file per message range, reviewed whole by codex, verdicts for qa_gate.

    python -X utf8 tools/story.py chapters               work/qa/story/chapters/chNN.txt (+ qa_gate init)
    python -X utf8 tools/story.py review [chNN ...] [--jobs 4]   codex -> work/qa/story/reports/chNN.md
    python -X utf8 tools/story.py check                  coverage line + Assessment of every report
    python -X utf8 tools/story.py verdicts [--tag T]     reports -> work/qa/story/verdicts/<T>chNN.tsv (ok|issue)

Chapters are message-id ranges (CHAPTERS); the game's ids run roughly in story order. The prompt inlines
docs/story-reviewer-brief.md + glossary.md + docs/style-reference.md + docs/synopsis.md + the chapter (no tool reads,
so nothing gets cut), sent on stdin to `codex exec -s read-only -`.
After a text fix: `chapters` again (re-hashes; a changed chapter loses its verdict), `review` it, `verdicts --tag fN_`.
"""
import argparse
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from script_tsv import load  # noqa: E402

STORY = ROOT / "work/qa/story"
DOCS = ["docs/story-reviewer-brief.md", "glossary.md", "docs/style-reference.md", "docs/synopsis.md"]
# (first message, last message) per chapter
CHAPTERS = [(0, 99), (100, 199), (200, 299), (300, 399), (400, 499), (500, 599), (600, 699), (700, 799),
            (800, 899), (900, 999), (1000, 1099), (1100, 1199), (1200, 1399), (1400, 1599)]


def gate_script():
    out = subprocess.run([sys.executable, str(ROOT / "tools/skill.py")], capture_output=True, text=True).stdout
    return Path(out.strip()) / "scripts/qa_gate.py"


def mnum(r):
    m = re.match(r"m(\d+)\.", r["ref"])
    return int(m.group(1)) if m else None


def chapters():
    rs = [r for r in load().values() if r["file"].startswith("msg_")]
    out = STORY / "chapters"
    out.mkdir(parents=True, exist_ok=True)
    for n, (lo, hi) in enumerate(CHAPTERS, 1):
        lines, speaker, cur = [], "", None
        for r in rs:
            m = mnum(r)
            if m is None or not lo <= m <= hi:
                continue
            if m != cur:
                cur, speaker = m, "-"
            sm = re.match(r"^([^「」\s]{1,12})「", r["jp"])
            if sm:
                speaker = sm.group(1)
            if not r["jp"].strip():
                continue
            lines.append(f">> {r['id']} | {r['ref']} | {speaker} | {r['jp']}\n   EN: {r['en']}")
        (out / f"ch{n:02d}.txt").write_text(
            f"# Chapter {n:02d}: messages {lo}-{hi}\n\n" + "\n".join(lines) + "\n", encoding="utf-8")
        print(f"ch{n:02d}: messages {lo}-{hi}, {len(lines)} rows")
    return subprocess.run([sys.executable, "-X", "utf8", str(gate_script()), "init", str(STORY / "manifest.tsv"),
                           str(out), "--glob", "*.txt"]).returncode


def span(path):
    ids = re.findall(r"^>> (\S+)", path.read_text(encoding="utf-8"), re.M)
    return ids[0], ids[-1], len(ids)


def prompt(path):
    parts = [f"=== {d} ===\n" + (ROOT / d).read_text(encoding="utf-8") for d in DOCS]
    parts.append("=== Instructions for this run ===\nEverything you need is inline: do NOT run commands or read "
                 "files. Start with the Coverage line, judge the whole chapter, end with the Assessment section.")
    parts.append(f"=== Chapter {path.stem} ===\n" + path.read_text(encoding="utf-8"))
    return "\n\n".join(parts)


def run(ch):
    path = STORY / "chapters" / f"{ch}.txt"
    rep = STORY / "reports"
    rep.mkdir(parents=True, exist_ok=True)
    with open(rep / f"log_{ch}.txt", "w", encoding="utf-8") as log:
        r = subprocess.run(["codex", "exec", "-s", "read-only", "--skip-git-repo-check", "-o", str(rep / f"{ch}.md"),
                            "-"], input=prompt(path), text=True, encoding="utf-8", stdout=log,
                           stderr=subprocess.STDOUT, cwd=ROOT)
    return ch, r.returncode


def assessment(text):
    tail = text.split("### Assessment")[-1] if "### Assessment" in text else ""
    m = re.search(r"`?(ok|issue)`?\s*[-:\u2014]?\s*(.*)", tail, re.I | re.S)
    return (m.group(1).lower(), " ".join(m.group(2).split())[:300]) if m else (None, "")


def check():
    bad = 0
    for path in sorted((STORY / "chapters").glob("ch*.txt")):
        first, last, n = span(path)
        rep = STORY / "reports" / f"{path.stem}.md"
        text = rep.read_text(encoding="utf-8") if rep.exists() else ""
        m = re.search(r"Coverage:\s*`?(\S+)\s*\.\.\s*(\S+?)`?\s*\((\d+) rows\)", text)
        ok = bool(m) and (m.group(1), m.group(2)) == (first, last)
        v, note = assessment(text)
        print(f"{path.stem} {'ok  ' if ok and v else 'FAIL'} want {first}..{last} ({n}) got "
              f"{m.group(0) if m else 'no coverage line'} | {v or '-'} {note[:120]}")
        bad += not (ok and v)
    return 1 if bad else 0


def verdicts(tag, only):
    vd = STORY / "verdicts"
    vd.mkdir(parents=True, exist_ok=True)
    for rep in sorted((STORY / "reports").glob("ch*.md")):
        if only and rep.stem not in only:
            continue
        v, note = assessment(rep.read_text(encoding="utf-8"))
        if v:
            (vd / f"{tag}{rep.stem}.tsv").write_text(f"{rep.stem}\t{v}\t{note}\n", encoding="utf-8")
            print(rep.stem, v)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["chapters", "review", "check", "verdicts"])
    ap.add_argument("ch", nargs="*")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    if a.cmd == "chapters":
        return chapters()
    if a.cmd == "check":
        return check()
    if a.cmd == "verdicts":
        return verdicts(a.tag, set(a.ch))
    chs = a.ch or sorted(p.stem for p in (STORY / "chapters").glob("ch*.txt"))
    with ThreadPoolExecutor(a.jobs) as ex:
        for ch, rc in ex.map(run, chs):
            print(ch, "rc", rc, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
