"""qa_sheets.py: visual-QA contact sheets from a warp tour (tools/debug/warp_all.py --pages N).

    python -X utf8 tools/qa_sheets.py OUT [OUT2 ..] [--qa DIR] [--per 20] [--changed 0.01]

Per scene (report.tsv order): warp.png then page_NN.png, keeping only frames that differ from the last kept one by
more than --changed (the mash pages through the text; a still area shows once), and dropping a frame whose box text
the next frame only adds to (a page still typing; warp.lua shoots before each press, so the complete page follows).
Tiles go into OUT/qa/sheet_NNN.png
at full size, 4 columns, --per tiles a sheet, never splitting a scene across sheets unless it alone fills one.
OUT/qa/index.tsv: sheet<TAB>scene<TAB>tiles, in reading order (left to right, top to bottom).
Then: qa_gate.py init work/qa/manifest.tsv OUT/qa --build build/fantastic_children_en.gba --glob "sheet_*.png".
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SCRIPTS  # noqa: E402

sys.path.insert(0, SCRIPTS)
import sheet  # noqa: E402


def _dark(px):
    return px[0] + px[1] + px[2] < 90


def partial_of(a, b):
    """True when b only adds ink to a's text box: a is the same page still typing. The box rows are the rows that
    are mostly dark in a; outside them sprites animate, so they don't count."""
    w, h, pa, ra = a
    _, _, pb, rb = b
    rows = [y for y in range(h) if sum(_dark(ra[y][x * pa:x * pa + 3]) for x in range(w)) > w * 0.6]
    if not rows:
        return False
    added = gone = 0
    for y in rows:
        for x in range(w):
            pxa, pxb = ra[y][x * pa:x * pa + 3], rb[y][x * pb:x * pb + 3]
            if pxa != pxb:
                if _dark(pxa):
                    added += 1
                else:
                    gone += 1   # ink gone or changed: a new page, unless it is only the typing cursor (a few px)
    return added > 0 and gone <= GONE_MAX and added > 4 * gone


GONE_MAX = 24   # the typing cursor glyph left at the end of a partly typed line


def frames(d, changed):
    """Partly typed pages go first, against the raw next frame: a dedup first would drop the complete page when it
    adds only a few glyphs to the partial (under --changed) and keep the partial."""
    paths = [d / "warp.png"] + sorted(d.glob("page_*.png"))
    imgs = [sheet.read_png(p) for p in paths if p.exists()]
    imgs = [a for a, b in zip(imgs, imgs[1:] + [None]) if b is None or not partial_of(a, b)]
    kept = []
    for img in imgs:
        if not kept or sheet.diff(kept[-1], img) > changed:
            kept.append(img)
    return kept


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", type=Path, nargs="+", help="warp_all.py run dirs (scenes in each one's report.tsv order)")
    ap.add_argument("--qa", type=Path, help="sheet dir (default OUT/qa of the first run dir)")
    ap.add_argument("--per", type=int, default=20)
    ap.add_argument("--changed", type=float, default=0.01)
    a = ap.parse_args()
    qa = a.qa or a.out[0] / "qa"
    qa.mkdir(parents=True, exist_ok=True)
    for old in qa.glob("sheet_*.png"):
        old.unlink()
    scenes = [o / ln.split("\t")[0] for o in a.out
              for ln in (o / "report.tsv").read_text(encoding="utf-8").splitlines()[1:] if ln]
    index, page, names, n = [], [], [], 1

    def flush():
        nonlocal page, names, n
        if page:
            name = f"sheet_{n:03d}.png"
            sheet.sheet(page, 4, qa / name)
            index.extend(f"{name}\t{s}\t{k}" for s, k in names)
            page, names, n = [], [], n + 1

    for sd in scenes:
        s = sd.name
        imgs = frames(sd, a.changed)
        if not imgs:
            continue
        if page and len(page) + len(imgs) > a.per:
            flush()
        while len(imgs) > a.per:
            page, names = imgs[:a.per], [(s, a.per)]
            flush()
            imgs = imgs[a.per:]
        page += imgs
        names.append((s, len(imgs)))
    flush()
    (qa / "index.tsv").write_text("sheet\tscene\ttiles\n" + "\n".join(index) + "\n", encoding="utf-8")
    print(f"{n - 1} sheets, {len(scenes)} scenes -> {qa}")


if __name__ == "__main__":
    main()
