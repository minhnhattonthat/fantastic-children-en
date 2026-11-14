"""Translation batches (docs/translator-brief.md): split untranslated text, check translator output, merge it back.

    python -X utf8 tools/batches.py split [--size 3500]         work/tl/bNNN.tsv + build/terms_bNNN.txt
    python -X utf8 tools/batches.py check bNNN [...]            a batch's work/tl/bNNN.out.tsv; prints OK or problems
    python -X utf8 tools/batches.py check                       all English in script/ (glossary rules)
    python -X utf8 tools/batches.py merge bNNN ... [--overwrite]   check, then write the English into script/
    python -X utf8 tools/batches.py fit "text" [--px 168]       width per line (" / " = extra line)

Adapted from the skill's assets/batches.py for this repo's TSV script (tools/script_tsv.py). Widths, encodability,
{argN}/{endflag}, blanks and box groups come from tools/lint.py, so the batch check and the build lint agree.
Batch TSV: id, ref, form, limit, JP. form: dlg | dlg+break (a blank line follows: the box group ends there) |
choice | sys. Output: work/tl/bNNN.out.tsv, id<TAB>English, every id once, same order.
"""
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import lint  # noqa: E402
import vwf  # noqa: E402
from script_tsv import SCRIPT, load, read_tsv as read_script, write_tsv  # noqa: E402
from tbl import Table  # noqa: E402

TL = ROOT / "work/tl"
GLOSSARY = ROOT / "glossary.md"
MAX_ENTRIES = 150
NAME = r"[ァ-ヶー]+"
# per glossary.md: honorifics kept, hyphenated, after a katakana name
HONORIFICS = [("さん", "-san"), ("くん", "-kun"), ("ちゃん", "-chan"), ("様", "-sama"), ("さま", "-sama"),
              ("先生", "-sensei"), ("せんせい", "-sensei")]


def blank(jp):
    return not jp.strip(lint.BLANKS)


def kind(char):
    if "぀" <= char <= "ゟ":
        return "hiragana"
    if "゠" <= char <= "ヿ":
        return "katakana"
    if "一" <= char <= "鿿" or char == "々":
        return "kanji"
    return "other"


def has_term(jp, term):
    """term occurs as a whole kana or kanji run: ミン isn't in タイミング, くも isn't in ぼくも."""
    for m in re.finditer(re.escape(term), jp):
        a, b = m.start(), m.end()
        if (a == 0 or kind(jp[a - 1]) != kind(term[0]) or kind(term[0]) == "kanji") and \
           (b == len(jp) or kind(jp[b]) != kind(term[-1]) or kind(term[-1]) == "kanji"):
            return True
    return False


def glossary():
    """[(JP forms, EN forms, avoid forms)] from glossary.md's | JP | EN | max | notes | Avoid | tables."""
    rows = []
    for line in GLOSSARY.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) >= 2 and cells[0] not in ("JP", "") and not set(cells[0]) <= set("-: "):
            avoid = [x.strip() for x in cells[4].split(",") if x.strip()] if len(cells) > 4 else []
            rows.append(([x.strip() for x in cells[0].split("/")], [x.strip() for x in cells[1].split("/")], avoid))
    return rows


def form_of(r, nxt):
    if r["id"][0] == "s":
        return "sys"
    b = lint.budget(r)
    if b and b[2].startswith("choice"):
        return "choice"
    return "dlg+break" if nxt is not None and blank(nxt["jp"]) else "dlg"


def limit_label(r):
    b = lint.budget(r)
    return f"{b[0]}px" if b else "?"


def ordered():
    """Rows in script order (files, then file order)."""
    out = []
    for p in sorted(SCRIPT.glob("*.tsv")):
        rows = read_script(p)
        for r in rows:
            r["file"] = p.name
        out += rows
    return out


def problems(r, en, terms, en_tbl):
    if not en.strip():
        return ["empty English"]
    out = []
    if re.search(r"\\u[0-9a-fA-F]{4}|\\n|\t", en):
        out.append("escape sequence or tab in the English")
    errs, _ = lint.lint_row(dict(r, en=en), en_tbl)
    out += errs
    if re.search(r"\{arg\d\}(st|nd|rd|th)\b", en):
        out.append('ordinal suffix after an argument (write "No. {arg0}")')
    if re.search(r"\b(a|an|A|An)\s+\{arg\d\}", en):
        out.append("a/an right before an argument")
    jp = r["jp"]
    for jps, ens, avoid in terms:
        if any(has_term(jp, j) for j in jps) and not any(e.lower() in en.lower() for e in ens):
            out.append(f"glossary: {jps[0]} -> {ens[0]}")
        out += [f"glossary Avoid: {a}" for a in avoid if re.search(rf"\b{re.escape(a)}\b", en)]
    for jp_form, en_form in HONORIFICS:
        if re.search(NAME + re.escape(jp_form), jp) and en_form not in en:
            out.append(f"honorific {jp_form} after a name needs {en_form}")
    return out


def batch_rows(path):
    return [line.split("\t") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def existing():
    return sorted(TL.glob("b[0-9][0-9][0-9].tsv"))


def split(size):
    """Whole messages stay together. Numbers on from the last batch; ids already batched are left out."""
    TL.mkdir(parents=True, exist_ok=True)
    (ROOT / "build").mkdir(exist_ok=True)
    taken = {r[0] for p in existing() for r in batch_rows(p)}
    n = max((int(p.stem[1:]) for p in existing()), default=0)
    rows = ordered()
    groups, seen = {}, set()
    for i, r in enumerate(rows):
        nxt = rows[i + 1] if i + 1 < len(rows) and rows[i + 1]["file"] == r["file"] else None
        r["form"] = form_of(r, nxt)
        if blank(r["jp"]) or r["en"] or r["id"] in taken or r["id"] in seen:
            continue
        seen.add(r["id"])
        key = (r["file"], r["ref"].split(",")[0].split(".")[0] if r["id"][0] == "p" else i // 60)
        groups.setdefault(key, []).append(r)
    batches, cur, chars = [], [], 0
    prev_file = None
    for (f, _), group in groups.items():
        c = sum(len(e["jp"]) for e in group)
        if cur and (chars + c > size or len(cur) + len(group) > MAX_ENTRIES or (f != prev_file and f.startswith("sys") != prev_file.startswith("sys"))):
            batches.append(cur)
            cur, chars = [], 0
        cur += group
        chars += c
        prev_file = f
    if cur:
        batches.append(cur)
    terms = glossary()
    for batch in batches:
        n += 1
        name = f"b{n:03d}"
        path = TL / f"{name}.tsv"
        if path.exists():
            sys.exit(f"{path} already exists")
        out = [f"{e['id']}\t{e['ref']}\t{e['form']}\t{limit_label(e)}\t{e['jp']}" for e in batch]
        path.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
        jps = "\n".join(e["jp"] for e in batch)
        used = [(j, ens[0]) for jpl, ens, _ in terms for j in jpl if has_term(jps, j)]
        (ROOT / f"build/terms_{name}.txt").write_text("".join(f"{j}\t{e}\n" for j, e in used)
                                                      or "(no glossary terms in this batch)\n", encoding="utf-8",
                                                      newline="\n")
        print(f"{name}: {len(batch)} rows, {sum(len(e['jp']) for e in batch)} JP chars")
    print(f"{len(batches)} new batches in {TL}, {len(taken)} ids already batched")


def check_batch(batch, rows_by_id, terms, en_tbl):
    want = [r[0] for r in batch_rows(TL / f"{batch}.tsv")]
    out = TL / f"{batch}.out.tsv"
    if not out.exists():
        return [f"{out} missing"], {}
    rows = [(r[0], "\t".join(r[1:])) for r in batch_rows(out)]
    bad = []
    got = [r[0] for r in rows]
    if got != want:
        dup = sorted(i for i, c in Counter(got).items() if c > 1)
        bad.append(f"ids differ: missing {sorted(set(want) - set(got))[:8]} extra {sorted(set(got) - set(want))[:8]} "
                   f"duplicate {dup[:8]} (order must match too)")
    for rid, en in rows:
        if rid in rows_by_id:
            bad += [f"{rid}: {p}: {en!r}" for p in problems(rows_by_id[rid], en, terms, en_tbl)]
    new = dict(rows)
    overlay = [dict(r, en=new.get(r["id"], r["en"])) for r in rows_by_id.values()]
    bad += [f"{rid} ({m}): {e}" for rid, m, e in lint.box_groups(overlay) if rid in new]
    return bad, new


def merge(new, overwrite):
    """Refuses to replace different English unless told to, before anything is written."""
    by_file = {}
    for p in sorted(SCRIPT.glob("*.tsv")):
        by_file[p] = read_script(p)
    if not overwrite:
        for rows in by_file.values():
            for r in rows:
                if r["id"] in new and r["en"] and r["en"] != new[r["id"]]:
                    sys.exit(f"{r['id']} would lose {r['en']!r}: pass --overwrite if that is meant")
    changed = 0
    for p, rows in by_file.items():
        touched = False
        for r in rows:
            if r["id"] in new and r["en"] != new[r["id"]]:
                r["en"] = new[r["id"]]
                touched = True
                changed += 1
        if touched:
            write_tsv(p, rows)
    print(f"merged: {changed} entries changed")


def fit(text, px):
    for ln in text.split(lint.LINE_SEP):
        w = vwf.ink_width(ln)
        print(f"{w:4d} px {len(vwf.encode_pairs(ln)):3d} codes {'OVER ' if w > px else 'ok   '}{ln!r}")


def main(argv):
    if not argv:
        sys.exit(__doc__)
    cmd, args = argv[0], argv[1:]
    if cmd == "split":
        return split(int(args[args.index("--size") + 1]) if "--size" in args else 3500)
    if cmd == "fit":
        px = int(args[args.index("--px") + 1]) if "--px" in args else vwf.TOP_PX
        return fit(args[0], px)
    overwrite = "--overwrite" in args
    names = [a for a in args if a != "--overwrite"]
    rows_by_id, terms, en_tbl = load(), glossary(), Table.load(ROOT / "tbl" / "en.tbl")
    if cmd == "check" and not names:
        bad = [f"{i}: {p}: {r['en']!r}" for i, r in rows_by_id.items() if r["en"]
               for p in problems(r, r["en"], terms, en_tbl)]
        print(f"{len(rows_by_id)} rows, {len(bad)} problems")
        print("\n".join(bad[:200]))
        return 1 if bad else 0
    if cmd not in ("check", "merge") or not names:
        sys.exit(__doc__)
    new, failed = {}, 0
    for batch in names:
        bad, rows = check_batch(batch, rows_by_id, terms, en_tbl)
        new.update(rows)
        failed += bool(bad)
        print(f"{batch}: " + ("OK" if not bad else f"{len(bad)} problems"))
        for line in bad:
            print("  " + line)
    if failed:
        return 1
    if cmd == "merge":
        merge(new, overwrite)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
