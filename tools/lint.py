"""lint.py: check every translated row (`en` set) against its measured budget (docs/re/text.md §Box widths).

    python -X utf8 tools/lint.py            # exit 1 on any error; warnings don't fail
    from lint import budget, lint_row        # budget(row) -> (px, codes, source)

Budgets (ink width, vwf.ink_width, and pair codes, vwf.encode_pairs):
  - dialogue page: 21 codes; 192 px when every message showing it opens the bottom box, else 168 px (top box with
    portrait; also the default for messages docs/re/msg_boxes.tsv hasn't seen yet);
  - battle line (sys_battle.tsv): shown through the page copy in the bottom box: 21 codes, 192 px, with every
    {argN} counted as NAME_PX (an 8-cell name field);
  - other system string: the cell region its caller gives it (docs/re/sys_regions.tsv: cells x 8 px, codes <= cells);
    item/card descriptions (sys_items.tsv) not measured yet take the 28-cell info box; anything else unmeasured
    is a warning.
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
NAME_PX = 64
INFO_CELLS = 28
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


def budget(r):
    """(max ink px, max codes, where the limit comes from) or None when unmeasured."""
    if r["id"][0] == "p":
        msgs = [m.split(".")[0][1:] for m in r["ref"].split(",")]
        boxes = {BOXES.get(m, ["top"])[0] for m in msgs}
        return (vwf.BOTTOM_PX if boxes == {"bottom"} else vwf.TOP_PX), PAGE_CODES, "box " + "/".join(sorted(boxes))
    if r["id"] in REGIONS:
        cells = int(REGIONS[r["id"]][0])
        return cells * 8, cells, f"region {cells} cells ({REGIONS[r['id']][3]})"
    if r["file"] == "sys_battle.tsv":
        return vwf.BOTTOM_PX, PAGE_CODES, "battle line, bottom box"
    if r["file"] == "sys_items.tsv":
        return INFO_CELLS * 8, INFO_CELLS, "info box (group default)"
    return None


def _measure(en):
    text = en[:-len(ENDFLAG)] if en.endswith(ENDFLAG) else en
    px = vwf.ink_width(re.sub(r"\{arg\d\}", "", text)) + NAME_PX * len(re.findall(r"\{arg\d\}", text))
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
    px, codes = _measure(en)
    b = budget(r)
    if b is None:
        warns.append(f"no measured budget yet ({px} px, {codes} codes)")
    else:
        if px > b[0]:
            errs.append(f"{px} px > {b[0]} ({b[2]})")
        if codes > b[1]:
            errs.append(f"{codes} codes > {b[1]} ({b[2]})")
    return errs, warns


def main():
    en_tbl = Table.load(ROOT / "tbl" / "en.tbl")
    rows = [r for r in load().values() if r["en"]]
    nerr = nwarn = 0
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
