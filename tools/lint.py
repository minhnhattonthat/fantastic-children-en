"""lint.py: check every translated row (`en` set) against its measured budget (docs/re/text.md §Box widths).

    python -X utf8 tools/lint.py            # exit 1 on any error; warnings don't fail
    from lint import budget, lint_row        # budget(row) -> (px, codes, source)

Budgets (ink width, vwf.ink_width, and pair codes, vwf.encode_pairs):
  - choice answer (a page of a choice-list message, docs/re/choices.tsv): 9 cells, 72 px, 9 codes;
  - dialogue page: 21 codes; 192 px when every message showing it opens the bottom box, else 168 px (top box with
    portrait; also the default for messages docs/re/msg_boxes.tsv hasn't seen yet);
  - battle line (sys_battle.tsv): shown through the page copy in the bottom box: 21 codes, 192 px, with every
    {argN} counted as NAME_PX (an 8-cell name field), or NUM_PX where the Japanese uses it as a number;
  - other system string: the cell region its caller gives it (docs/re/sys_regions.tsv: cells x 8 px, codes <= cells);
    item/card descriptions (sys_items.tsv) not measured yet take the 28-cell info box; anything else unmeasured
    is a warning.
A dialogue page (not a choice answer) may hold " / ": each part is one more line, measured on its own.
Also: every character encodable, the same {argN} tokens as the Japanese, {endflag} kept, leading/trailing blanks
kept.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import vwf  # noqa: E402
from script_tsv import ENDFLAG, load  # noqa: E402
from tbl import Table  # noqa: E402

PAGE_CODES = 21
LINE_SEP = " / "    # = insert.LINE_SEP: a dialogue page's English may run onto extra lines (extra pages)
MAX_EXTRA = 2       # extra lines per page; more means the English is padded, not translated
NAME_PX = 64
NUM_PX = 24         # a number argument (damage, hits, times, HP, round): up to 3 game digits, 8 px each
NUM_ARG = re.compile(r"\{arg(\d)\}(?=ダメージ|ヒット|回|かいふく)|(?<=ラウンド)\{arg(\d)\}")
INFO_CELLS = 28
AREA_CELLS = 15     # area names (sys_menu s09C81E-s09CD48) share the file slot's area field (s09CD5A: 15 cells)
AREA_IDS = ("s09C81E", "s09CD48")


def is_area_name(r):
    return r["id"][0] == "s" and AREA_IDS[0] <= r["id"] <= AREA_IDS[1]
BLANKS = " 　"


def _table(path):
    out = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines()[1:]:
            if line:
                f = line.split("\t")
                out[f[0]] = f[1:]
    return out


BOXES = _table(ROOT / "docs" / "re" / "msg_boxes.tsv")
REGIONS = _table(ROOT / "docs" / "re" / "sys_regions.tsv")
CHOICES = _table(ROOT / "docs" / "re" / "choices.tsv")   # choice-list message ids (tools/events.py --choices)
CHOICE_CELLS = 9    # answers sit in a 2-column grid: cursor col 2 / 12, text col 3 / 13 (top box; bottom +2)


def budget(r):
    """(max ink px, max codes, where the limit comes from) or None when unmeasured."""
    if r["id"][0] == "p":
        msgs = [m.split(".")[0][1:] for m in r["ref"].split(",")]
        if any(m in CHOICES for m in msgs):
            return CHOICE_CELLS * 8, CHOICE_CELLS, f"choice answer, {CHOICE_CELLS} cells"
        boxes = {BOXES.get(m, ["top"])[0] for m in msgs}
        return (vwf.BOTTOM_PX if boxes == {"bottom"} else vwf.TOP_PX), PAGE_CODES, "box " + "/".join(sorted(boxes))
    if r["id"] in REGIONS:
        cells = int(REGIONS[r["id"]][0])
        return cells * 8, cells, f"region {cells} cells ({REGIONS[r['id']][3]})"
    if is_area_name(r):
        return AREA_CELLS * 8, AREA_CELLS, f"area name, file slot {AREA_CELLS} cells"
    if r["file"] == "sys_battle.tsv":
        return vwf.BOTTOM_PX, PAGE_CODES, "battle line, bottom box"
    if r["file"] == "sys_items.tsv":
        return INFO_CELLS * 8, INFO_CELLS, "info box (group default)"
    return None


def _measure(en, jp=""):
    """Ink px and codes of one line; {argN} = NAME_PX, or NUM_PX where the Japanese uses it as a number."""
    text = en[:-len(ENDFLAG)] if en.endswith(ENDFLAG) else en
    nums = {a or b for a, b in NUM_ARG.findall(jp)}
    args = re.findall(r"\{arg(\d)\}", text)
    px = vwf.ink_width(re.sub(r"\{arg\d\}", "", text)) + sum(NUM_PX if a in nums else NAME_PX for a in args)
    return px, len(vwf.encode_pairs(text))


def lint_row(r, en_tbl):
    errs, warns = [], []
    en, jp = r["en"], r["jp"]
    pi = vwf.pair_index()
    for tok in vwf._tokens(en[:-len(ENDFLAG)] if en.endswith(ENDFLAG) else en):
        if tok not in pi and tok not in en_tbl.enc and not re.fullmatch(r"\{arg\d\}", tok):
            errs.append(f"can't encode {tok!r}")
    if sorted(re.findall(r"\{arg\d\}", en)) != sorted(re.findall(r"\{arg\d\}", jp)):
        errs.append("argument tokens differ from the Japanese")
    if jp.endswith(ENDFLAG) != en.endswith(ENDFLAG):
        errs.append("{endflag} must match the Japanese")
    if (jp[:1] in BLANKS) != (en[:1] in BLANKS) or (jp.replace(ENDFLAG, "")[-1:] in BLANKS) != (en.replace(ENDFLAG, "")[-1:] in BLANKS):
        errs.append("leading/trailing blank differs from the Japanese")
    if errs:
        return errs, warns
    b = budget(r)
    lines = en.split(LINE_SEP)
    if len(lines) > 1:
        if r["id"][0] != "p" or (b and b[2].startswith("choice")):
            return [f"{LINE_SEP!r} (extra line) only in dialogue pages"], warns
        if len(lines) > MAX_EXTRA + 1:
            errs.append(f"{len(lines) - 1} extra lines > {MAX_EXTRA}")
        if any(not ln.strip() for ln in lines):
            errs.append("empty line")
    for ln in lines:
        px, codes = _measure(ln, jp)
        if b is None:
            warns.append(f"no measured budget yet ({px} px, {codes} codes)")
        else:
            if px > b[0]:
                errs.append(f"{px} px > {b[0]} ({b[2]}): {ln!r}")
            if codes > b[1]:
                errs.append(f"{codes} codes > {b[1]} ({b[2]}): {ln!r}")
    return errs, warns


def box_groups(all_rows):
    """Errors for box groups whose line-count parity changed. The box holds 2 lines; the Japanese pads a group of
    odd length with a blank page so the next group (a new speaker) opens a fresh box. Extra lines (" / ") in a group
    that a blank page follows must add up to an even number. -> [(first page id of the group, message, message)]."""
    msgs = {}
    for r in all_rows:
        if r["id"][0] != "p":
            continue
        for ref in r["ref"].split(","):
            m, n = ref[1:].split(".")
            msgs.setdefault(int(m), []).append((int(n), r))
    out = []
    for m, pages in sorted(msgs.items()):
        pages.sort(key=lambda p: p[0])
        extra, first = 0, None
        for _, r in pages:
            if not r["jp"].strip(BLANKS):
                if first is not None and extra % 2:
                    out.append((first["id"], f"m{m}", f"box group adds {extra} lines (odd) before a blank page: "
                                "add or remove one ' / ' so the next speaker starts a fresh box"))
                extra, first = 0, None
                continue
            first = first or r
            extra += r["en"].count(LINE_SEP)
    return out


def main():
    en_tbl = Table.load(ROOT / "tbl" / "en.tbl")
    allrows = list(load().values())
    rows = [r for r in allrows if r["en"]]
    nerr = nwarn = 0
    for rid, m, e in box_groups(allrows):
        print(f"ERROR {rid} ({m}): {e}")
        nerr += 1
    for r in rows:
        errs, warns = lint_row(r, en_tbl)
        for e in errs:
            print(f"ERROR {r['file']} {r['id']}: {e}: {r['en']}")
        for w in warns:
            print(f"warn  {r['file']} {r['id']}: {w}")
        nerr += len(errs)
        nwarn += len(warns)
    print(f"lint: {len(rows)} translated rows, {nerr} errors, {nwarn} warnings")
    return 1 if nerr else 0


if __name__ == "__main__":
    sys.exit(main())
