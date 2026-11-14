# Visual-QA reviewer brief - Fantastic Children (GBA)

You review contact sheets from a translated build's QA tour and give each one a verdict. Read-only on everything
except your one verdict file: no edits to the repo, no git, no subagents.

## Inputs (in your dispatch)
- A chunk file: one `id<TAB>path` line per sheet. Read every sheet in it; none may be skipped.
- Your verdict file: `work/qa/verdicts/<chunk>.tsv` (with `codex exec -s read-only` the controller saves your
  final answer there instead: then print the verdict lines as your final answer).
- Optional: the original ROM's sheets (`work/qa/tour_jp/`, same ids) and `glossary.md`.

## How to look
- Read each sheet whole first. Where text is small, zoom into it with
  `python -X utf8 $SKILL/scripts/sheet.py SHEET.png --crop x,y,w,h --zoom 3 --out <scratch>.png` and read that.
- When something looks wrong, open the same id from `tour_jp/` (`sheet.py EN.png --compare JP.png`). If the
  original shows the same thing, it is the game's own behaviour: `ok`, with a note.
- Zoom into every Yes/No prompt, selection box, menu row and speech bubble: a few pixels of misalignment don't show
  at sheet scale. To measure one: `python -X utf8 $SKILL/scripts/inkbox.py SHOT.png x,y,w,h`.

## Judge
An `issue` is any of:
- Japanese still visible;
- text overflowing a box, clipped by a frame, or running off screen;
- text off-centre where the original centres it: an option in its selection box or cursor brackets, a label, a bubble;
- garbage tiles, wrong or missing glyphs, a strike or stray pixels across letters;
- broken line breaks: a word split mid-line, a one-word line (or one or two short words) that could have joined
  its neighbour, a name or term ("Old Paints", "+Control Pad", "10 damage") split across lines;
- an empty box where text belongs;
- a name that differs from `glossary.md`.

Standing non-bugs, `ok` (the controller adds the game's own below):
- text still typing out, a box mid-fade or mid-scroll, a cursor caught mid-blink;
- a map or scene still loading after a warp;
- anything identical in the original's sheet.
- Warp artefacts (the debug warp, not the game): battle and NPC scripts play in area 62 (a plain indoor room), not where
  the NPC stands; a battle backdrop garbled in area 16; story flags out of order, so a scene can show a line that
  doesn't follow from the one before; characters standing in odd places.
- A sentence that runs on into the next box. The dialogue box holds 2 lines and clears; a long English sentence
  needs 3+ lines, and the Japanese itself breaks ~190 boxes mid-sentence. Every message's box breaks were laid out
  by `tools/reflow.py` (sentence ends at box ends wherever the page count allows), so a box ending mid-sentence is
  `ok` unless it leaves a fragment line as above.
- Choice answers are left-aligned after a ▶ cursor in a 2-column grid (as in the original), not centred.
- The pause menu labels, card faces (Punch, Kick ...), GAME OVER and "SAVING... Do not turn the power OFF" are the
  original's own English graphics.
- `debug_viewer` and test events (ev_0017, ev_0031 スイッチイベント8 ...) are leftover debug scripts: judge only text.
- Dialogue font: one proportional English font (Lato), names in a blue/coloured label over the top box are the game's.
- Forced scenes (text coverage, `tools/debug/force.gba.txt`): `force_NN` replays one test event in a plain room
  and swaps in message after message, so the lines follow no story order and all show in the same box, with the
  room shown between messages. `forceput_NN` draws system strings (file menu, area names, item/card descriptions,
  battle lines) three at a time in the pause screen's info rows, out of their own screen: judge the text itself
  (Japanese, garbage, glyphs, clipping at the right edge, names). In those rows an argument code ({arg0}: a name or
  number the battle code fills in) is not filled in and may show as one odd glyph or a gap: not an issue.

## Verdicts
Write your verdict file once you have read every sheet, one line per id in the chunk:
`id<TAB>ok|issue<TAB>what and where` (for an issue: which tile, which text, what is wrong).
Then return a short summary: counts, and the issues one per line.
