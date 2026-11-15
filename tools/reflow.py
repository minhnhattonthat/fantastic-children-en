"""reflow.py: re-wrap box groups whose English breaks boxes mid-sentence (Phase 8 visual QA, sheet_067 and on).

    python -X utf8 tools/reflow.py stats                 # mid-sentence box ends, English vs Japanese
    python -X utf8 tools/reflow.py batch rNN [--show N] [--why]   # work/tl/rNN.tsv + rNN.out.tsv for the groups it improves
    python -X utf8 tools/reflow.py batch rNN --cursor     # only groups with a page line touching the ▼ (lint.CURSOR_GAP)
    python -X utf8 tools/reflow.py batch rNN --widows     # only groups with a one-word continuation line (widows())

The dialogue box holds 2 lines and clears; a box group (pages up to a blank Japanese page) fills boxes from its
first line. The Japanese ends most boxes on a sentence end; English with extra lines (" / ") shifts every later box
break. Per group, a DP over word breaks picks lines (each within the page budget, lint._measure) and their pages
(the same pages, 1..MAX_EXTRA+1 lines each, a page's first line keeps the Japanese page's leading blank) so that
  - box ends land on sentence ends (then clause ends) where possible,
  - no line is a stub (< lint.STUB characters) except a page that is one short line,
  - the group's line-count parity rule (lint.box_groups) still holds,
  - fewer lines win ties.
A group is rewritten only when it ends fewer boxes mid-sentence than now, and every new page passes batches.problems
(glossary terms on their page, widths, blanks). Skipped: groups with {argN}/{endflag}, choice answers, pages shared
by several messages, a second speaker inside the group, a trailing blank in the Japanese.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import batches  # noqa: E402
import lint  # noqa: E402
import vwf  # noqa: E402
from tbl import Table  # noqa: E402

BL = lint.BLANKS
SENT_EN = re.compile(r"""[.!?…~]["')”’]*$|["”’)]$""")
SENT_END = re.compile(r"""[.!?…~]["')”’]*$""")    # a closing quote alone doesn't end a sentence ('"Chop 10" obtained!')
CLAUSE_EN = re.compile(r"[,;:—-]$")
END_JP = tuple("。！？」』…・ッ）!?")
SPEAKER = re.compile(r"^[A-Z][\w'.-]*( [A-Z][\w'.-]*)?: ")
INF = float("inf")
WEAK = set("a an the of to in on at by for with from and or but my your his her its our their is are was "
           "were be i you we he she it they that this".split())


def groups(rows):
    """[(message, [rows], followed_by_blank)] over dialogue pages, in page order."""
    msgs = {}
    for r in rows:
        if r["id"][0] != "p":
            continue
        for ref in r["ref"].split(","):
            m, n = ref[1:].split(".")
            msgs.setdefault(int(m), []).append((int(n), r))
    out = []
    for m, pages in sorted(msgs.items()):
        pages.sort(key=lambda p: p[0])
        g = []
        for _, r in pages:
            if not r["jp"].strip(BL):
                if g:
                    out.append((m, g, True))
                g = []
                continue
            g.append(r)
        if g:
            out.append((m, g, False))
    return out


def lines_of(g):
    return [ln.strip() for r in g for ln in r["en"].split(lint.LINE_SEP)]


def mid_ends(lines, jp=False):
    boxes = [lines[i:i + 2] for i in range(0, len(lines), 2)][:-1]
    if jp:
        return sum(not b[-1].replace(lint.ENDFLAG, "").endswith(END_JP) for b in boxes)
    return sum(not SENT_EN.search(b[-1]) for b in boxes)


def widows(lines):
    """One-word lines that continue the previous line's sentence ("Hm... You've gotten / good...",
    '"Chop 10" / obtained!'): visual QA flags them as orphans."""
    return sum(len(ln.split()) == 1 and k and not SENT_END.search(lines[k - 1])
               for k, ln in enumerate(lines))


def skip_reason(g):
    for k, r in enumerate(g):
        if not r["en"]:
            return "untranslated"
        if "{arg" in r["en"] or lint.ENDFLAG in r["en"] or "{arg" in r["jp"]:
            return "argument/endflag"
        if "," in r["ref"]:
            return "shared page"
        b = lint.budget(r)
        if b is None or b[2].startswith("choice"):
            return "choice/unmeasured"
        if r["jp"].replace(lint.ENDFLAG, "")[-1:] in BL:
            return "trailing blank"
        if k and SPEAKER.match(r["en"]):
            return "second speaker"
    return None


def pins(g, terms):
    """[(lo, hi)] per page: word indices (over the whole group) that must stay on that page, because the page's
    Japanese has a glossary term or a name honorific and batches.problems wants its English on the same page."""
    out, base = [], 0
    for r in g:
        ws = r["en"].replace(lint.LINE_SEP, " ").split()
        joined = " ".join(ws).lower()
        starts = [sum(len(w) + 1 for w in ws[:k]) for k in range(len(ws))]
        keep = set()

        def mark(a, b):
            keep.update(k for k, s in enumerate(starts) if s < b and s + len(ws[k]) > a)
        for jps, ens, _ in terms:
            if any(batches.has_term(r["jp"], j) for j in jps):
                for e in ens:
                    a = joined.find(e.lower())
                    if a >= 0:
                        mark(a, a + len(e))
                        break
        for jp_form, en_form in batches.HONORIFICS:
            if re.search(batches.NAME + re.escape(jp_form), r["jp"]):
                a = " ".join(ws).find(en_form)
                if a >= 0:
                    mark(a, a + len(en_form))
        out.append((base + min(keep), base + max(keep)) if keep else None)
        base += len(ws)
    return out


UNITS = ["A Button", "B Button", "L Button", "R Button", "+Control Pad", "START", "SELECT"]


def glued(words, terms):
    """Word indices j where a break before words[j] splits a unit: a short double-quoted name, a multi-word
    glossary term or button name, a number and its noun."""
    out = set()
    low = [w.lower() for w in words]
    phrases = set()
    for _, ens, _ in terms:
        for e in ens:
            if " " in e:
                phrases.add(tuple(e.lower().split()))
    phrases.update(tuple(u.lower().split()) for u in UNITS if " " in u)
    for ph in phrases:
        k = len(ph)
        for a in range(len(words) - k + 1):
            if all(low[a + t].strip("\"'.,!?…:;()").startswith(ph[t].strip("\"'.,!?…:;()")) for t in range(k)):
                out.update(range(a + 1, a + k))
    for a, w in enumerate(words):
        if w.startswith(("\"", "“")) and not re.search(r"[\"”][.,!?…]*$", w[1:]):
            for b in range(a + 1, min(a + 4, len(words))):
                if re.search(r"[\"”][.,!?…]*$", words[b]):
                    out.update(range(a + 1, b + 1))
                    break
        if re.fullmatch(r"\d+", w) and a + 1 < len(words):
            out.add(a + 1)
    return out


def solve(g, parity_fixed, terms=()):
    words = " ".join(r["en"].replace(lint.LINE_SEP, " ") for r in g).split()
    n, P = len(words), len(g)
    pin = pins(g, terms)
    glue = glued(words, terms)

    def page_start_ok(q, i):
        """page q (0-based) may start at word i: its own pins at or after i, the previous page's pins before i."""
        return (pin[q] is None or i <= pin[q][0]) and (q == 0 or pin[q - 1] is None or i > pin[q - 1][1])
    px = min(lint.budget(r)[0] for r in g) - lint.CURSOR_GAP   # any line may end its page: keep the ▼ clear
    req = [r["jp"][:1] in BL for r in g]
    cap = lint.MAX_EXTRA + 1
    old_lines = lines_of(g)

    fit = {}

    def text(i, j, indent):
        return (" " if indent else "") + " ".join(words[i:j])

    def ok(i, j, indent):
        k = (i, j, indent)
        if k not in fit:
            t = text(i, j, indent)
            w, codes = lint._measure(t)
            fit[k] = w if w <= px and codes <= lint.PAGE_CODES else None
        return fit[k] is not None

    def rag(i, j, indent, L):
        """Unused width of a line that doesn't end on punctuation; a box's first line pays more (it should be the
        full one), and a line under half the box looks like a widow."""
        if j == n:
            return 0
        slack = 1 - fit[(i, j, indent)] / px
        whole = i == 0 or SENT_EN.search(words[i - 1])     # the line opens a sentence
        widow = 20 if slack > 0.6 and not (whole and SENT_EN.search(words[j - 1])) else 0
        weak = (15 if words[j - 1].lower() in WEAK else 0) + (30 if j in glue else 0)
        if SENT_EN.search(words[j - 1]):
            return widow
        if CLAUSE_EN.search(words[j - 1]):
            slack /= 3
        return (30 if L % 2 else 12) * slack + widow + weak

    def short(i, j):
        return len(" ".join(words[i:j])) < lint.STUB

    def box_cost(j):
        w = words[j - 1]
        return 0 if SENT_EN.search(w) else (10 if CLAUSE_EN.search(w) else 40)

    # state: (i words used, L lines, p pages, c lines in page, last line short) -> (cost, back)
    best = {}
    start = []
    for j in range(1, n + 1):
        if not ok(0, j, req[0]):
            break
        start.append(((j, 1, 1, 1, short(0, j)), 3 + (8 if short(0, j) else 0) + rag(0, j, req[0], 1), None,
                      (0, j, req[0])))
    frontier = {}
    for st, cost, back, ln in start:
        if cost < frontier.get(st, (INF,))[0]:
            frontier[st] = (cost, back, ln)
    best.update(frontier)
    while frontier:
        nxt = {}
        for st, (cost, _, _) in frontier.items():
            i, L, p, c, sh = st
            if i == n:
                continue
            bc = box_cost(i) if L % 2 == 0 else 0     # line L ended a box and more text follows
            opts = []
            if c < cap:
                opts.append((p, c + 1, False))
            if p < P and not (c >= 2 and sh) and page_start_ok(p, i):
                opts.append((p + 1, 1, req[p]))
            for np_, nc, indent in opts:
                for j in range(i + 1, n + 1):
                    if not ok(i, j, indent):
                        break
                    s = short(i, j)
                    ns = (j, L + 1, np_, nc, s)
                    nc_ = cost + bc + 3 + (8 if s else 0) + rag(i, j, indent, L + 1)
                    if nc_ < best.get(ns, (INF,))[0]:
                        best[ns] = nxt[ns] = (nc_, st, (i, j, indent))
        frontier = nxt
    old_L = len(old_lines)
    finals = [(v[0], st) for st, v in best.items()
              if st[0] == n and st[2] == P and not (st[3] >= 2 and st[4]) and not (st[1] > 1 and st[4])
              and (not parity_fixed or (st[1] - P) % 2 == 0)]
    if not finals:
        return None
    _, st = min(finals)
    lines = []
    while st is not None:
        _, back, ln = best[st]
        lines.append((st[2], ln))
        st = back
    lines.reverse()
    pages = [[] for _ in range(P)]
    for p, (i, j, indent) in lines:
        pages[p - 1].append(text(i, j, indent))
    del old_L
    return [lint.LINE_SEP.join(pg) for pg in pages]


def main(argv):
    rows = batches.ordered()
    gs = groups(rows)
    if argv[:1] == ["stats"]:
        e = sum(mid_ends(lines_of(g)) for _, g, _ in gs if all(r["en"] for r in g))
        j = sum(mid_ends([r["jp"].strip(BL) for r in g], jp=True) for _, g, _ in gs)
        print(f"mid-sentence box ends: EN {e}, JP {j}")
        return
    if argv[:1] != ["batch"] or len(argv) < 2:
        sys.exit(__doc__)
    name = argv[1]
    show = int(argv[argv.index("--show") + 1]) if "--show" in argv else 0
    terms = batches.glossary()
    en_tbl = Table.load(ROOT / "tbl" / "en.tbl")
    by_pos = {r["id"]: k for k, r in enumerate(rows)}
    out, skipped, worse, bad, shown = {}, {}, 0, 0, 0
    cursor_mode = "--cursor" in argv
    widow_mode = "--widows" in argv
    for m, g, blank_after in gs:
        old = lines_of(g) if all(r["en"] for r in g) else None
        if cursor_mode:
            if not old or not any("▼" in e for r in g for e in lint.lint_row(r, en_tbl)[0]):
                continue
        elif widow_mode:
            if not old or widows(old) == 0:
                continue
        elif not old or mid_ends(old) == 0:
            continue
        why = skip_reason(g)
        if why:
            skipped[why] = skipped.get(why, 0) + 1
            continue
        new = solve(g, blank_after, terms)
        if new is None:
            skipped["no solution"] = skipped.get("no solution", 0) + 1
            continue
        nl = [ln.strip() for pg in new for ln in pg.split(lint.LINE_SEP)]
        if widow_mode:
            not_better = mid_ends(nl) > mid_ends(old) or widows(nl) >= widows(old)
        else:
            not_better = mid_ends(nl) > mid_ends(old) or (mid_ends(nl) == mid_ends(old) and not cursor_mode)
        if not_better:
            worse += 1
            if "--why" in argv:
                print(f"m{m} not improved: {' | '.join(nl)}")
            continue
        probs = [p for r, en in zip(g, new) for p in batches.problems(r, en, terms, en_tbl)]
        if probs:
            bad += 1
            if "--why" in argv:
                print(f"m{m} check: {probs[0]}")
            continue
        for r, en in zip(g, new):
            if en != r["en"]:
                out[r["id"]] = en
        if shown < show:
            shown += 1
            print(f"m{m} {mid_ends(old)}->{mid_ends(nl)}\n  old: {' | '.join(old)}\n  new: {' | '.join(nl)}")
    ids = sorted(out, key=by_pos.get)
    tl = ROOT / "work" / "tl"
    with open(tl / f"{name}.tsv", "w", encoding="utf-8", newline="\n") as f:
        for rid in ids:
            k = by_pos[rid]
            r, nx = rows[k], rows[k + 1] if k + 1 < len(rows) else None
            f.write(f"{rid}\t{r['ref']}\t{batches.form_of(r, nx)}\t{batches.limit_label(r)}\t{r['jp']}\n")
    with open(tl / f"{name}.out.tsv", "w", encoding="utf-8", newline="\n") as f:
        for rid in ids:
            f.write(f"{rid}\t{out[rid]}\n")
    print(f"{name}: {len(ids)} pages rewritten; not improved {worse}; failed batch checks {bad}; skipped {skipped}")


if __name__ == "__main__":
    main(sys.argv[1:])
