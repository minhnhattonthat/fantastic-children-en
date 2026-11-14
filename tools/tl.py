"""Controller helpers for translating batches by hand (Phase 6).

    python -X utf8 tools/tl.py show bNNN      compact view: id ref flags JP; a row whose JP repeats an earlier row
                                             (this batch or a translated one) is listed as "= id" and needs no English
    python -X utf8 tools/tl.py fill bNNN      merges work/tl/bNNN.out.tsv and the hand-written bNNN.part.tsv,
                                             bNNN.part2.tsv... (partial; later files win), fills the repeated rows,
                                             writes bNNN.out.tsv in input order, runs tools/batches.py check bNNN
    python -X utf8 tools/tl.py fix rNN       fixes to translated rows: from work/tl/rNN.out.tsv (id<TAB>EN) writes
                                             the rNN.tsv batch rows, runs the check; then `batches.py merge rNN --overwrite`

flags: # = dlg+break (a blank line follows), W = 192 px bottom box (else 168 px top box), c = choice (72 px), s = sys.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TL = ROOT / "work" / "tl"


def rows(b):
    out = []
    for ln in (TL / f"{b}.tsv").read_text(encoding="utf-8").splitlines():
        i, ref, form, limit, jp = ln.split("\t")
        out.append((i, ref, form, limit, jp))
    return out


def known():
    """JP -> English from every other batch's output (first seen wins)."""
    m = {}
    for f in sorted(TL.glob("b*.out.tsv")):
        src = {r[0]: r[4] for r in rows(f.name.split(".")[0])}
        for ln in f.read_text(encoding="utf-8").splitlines():
            i, en = ln.split("\t", 1)
            if i in src:
                m.setdefault(src[i], en)
    return m


def flags(form, limit):
    if form == "choice":
        return "c"
    if form == "sys":
        return "s" + limit
    return ("#" if form.endswith("+break") else "") + ("W" if limit == "192px" else "")


def show(b):
    seen, prior = {}, known()
    for i, ref, form, limit, jp in rows(b):
        if jp in seen:
            print(f"{i} = {seen[jp]}")
            continue
        seen[jp] = i
        mark = " (done)" if jp in prior else ""
        print(f"{i}\t{ref}\t{flags(form, limit)}\t{jp}{mark}")


def fill(b):
    p = TL / f"{b}.out.tsv"
    d = {}
    # the out file, then the hand-written parts bNNN.part.tsv, bNNN.part2.tsv... (later ones win)
    parts = sorted(TL.glob(f"{b}.part*.tsv"), key=lambda f: (len(f.name), f.name))
    hand = {}
    for f in ([p] if p.exists() else []) + parts:
        for ln in f.read_text(encoding="utf-8").splitlines():
            if "\t" in ln:
                i, en = ln.split("\t", 1)
                d[i] = en
                if f != p:
                    hand[i] = en
    rs = rows(b)
    byjp = {}
    for i, _, _, _, jp in rs:   # hand-written lines first, so a fix reaches every repeat of its Japanese
        if i in hand:
            byjp[jp] = hand[i]
    for i, _, _, _, jp in rs:
        if i in d:
            byjp.setdefault(jp, d[i])
    for i, _, _, _, jp in rs:
        if i not in hand and jp in byjp:
            d[i] = byjp[jp]
    prior = known()
    missing = []
    for i, _, _, _, jp in rs:
        if i not in d:
            if jp in byjp:
                d[i] = byjp[jp]
            elif jp in prior:
                d[i] = prior[jp]
            else:
                missing.append(i)
    if missing:
        print("missing:", " ".join(missing))
    p.write_text("".join(f"{i}\t{d[i]}\n" for i, *_ in rs if i in d), encoding="utf-8", newline="\n")
    r = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "tools" / "batches.py"), "check", b],
                       capture_output=True, text=True, encoding="utf-8")
    print((r.stdout + r.stderr).strip())
    return r.returncode or bool(missing)


def fix(b):
    """rNN.out.tsv (id<TAB>EN, hand-written fixes of translated rows) -> rNN.tsv batch rows, then batches.py check."""
    sys.path.insert(0, str(ROOT / "tools"))
    import batches
    ids = [ln.split("\t", 1)[0] for ln in (TL / f"{b}.out.tsv").read_text(encoding="utf-8").splitlines() if "\t" in ln]
    allr = batches.ordered()
    pos = {r["id"]: k for k, r in enumerate(allr)}
    out = []
    for i in ids:
        k = pos[i]
        r = allr[k]
        nxt = allr[k + 1] if k + 1 < len(allr) and allr[k + 1]["file"] == r["file"] else None
        out.append("\t".join([i, r["ref"], batches.form_of(r, nxt), batches.limit_label(r), r["jp"]]) + "\n")
    (TL / f"{b}.tsv").write_text("".join(out), encoding="utf-8", newline="\n")
    r = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "tools" / "batches.py"), "check", b],
                       capture_output=True, text=True, encoding="utf-8")
    print((r.stdout + r.stderr).strip())
    return r.returncode


if __name__ == "__main__":
    cmd, b = sys.argv[1], sys.argv[2]
    sys.exit({"show": show, "fill": fill, "fix": fix}[cmd](b))
