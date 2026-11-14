# Decisions

The user's rulings on scope, style and trade-offs, newest last. Read before asking the user anything; if a later
decision replaces one, mark the old one "replaced by D<n>" instead of deleting it. Binding term spellings live in
`glossary.md`; this file holds the why.

All of D1-D7 came from the owner's standing answers injected into the one-shot run brief (Orca coordinator), 2026-11-14.

| # | Date | Question | Options offered | Decision and reason |
|---|---|---|---|---|
| D1 | 2026-11-14 | Honorifics and name order | keep (-san), drop; JP or Western order | Keep honorifics; Western name order (given name first). Owner's standing answer. |
| D2 | 2026-11-14 | Romanization source for names | official art, earlier patch, Hepburn | Official English names where they exist (Bandai Entertainment's English anime release), else an earlier fan patch, else Hepburn without macrons. |
| D3 | 2026-11-14 | Credits | stay Japanese, translate | English. |
| D4 | 2026-11-14 | Abbreviations | engine work first (default), abbreviate | Skill default: full names and terms, engine work before shortening; abbreviate only as a flagged last resort. |
| D5 | 2026-11-14 | Graphics text left in Japanese | none (default), list | Translate all graphics text (titles, menus, banners, cards); leave the original Japanese logo only if it has no official English version. |
| D6 | 2026-11-14 | Specs and plans | need approval, pre-approved | Pre-approved: keep going through every checkpoint, report at the end. Never `gh release create`, never change repo visibility; the run ends at a built and verified release zip. |
| D7 | 2026-11-14 | Existing saves / savestates | user's saves, none | None provided; build the debug tool as usual. |
| D8 | 2026-11-15 | Destination answers in the 72 px choice grid ("Natsuna Island" is ~90 px) | widen the grid (engine), drop "Island", abbreviate | Agent default under D6 (pre-approved): drop " Island" in choice answers only ("Natsuna", "Chikao", "Papin"), as a map menu would; not an abbreviation, and the 2-column grid is the game's layout. `batches.py` accepts it for choice rows only. Same for 宇宙船ヴェガ: "Vega" in a choice answer ("Spaceship Vega" ~100 px; reviewers flagged it, kept under this ruling). Revisit if the owner objects. |
| D9 | 2026-11-15 | Area names in the file slot's 15-cell (120 px) field ("Chikao Children's Academy Punishment Room" ~250 px) | widen the field (engine), short site-first names, abbreviate | Agent default under D6: short names that keep the site and drop the island when a site is named ("Academy Lockup", "Gedling Shaft", "Papin Cove", "Vega Quarters 1"); no abbreviations. `lint.py` gives s09C81E-s09CD48 15 cells; `batches.py` accepts the short forms for those rows only. Phase 7: measured with a filled slot (original ROM, `work/qa/p7/del`): text_put n=15 at x=17, but only cols 17-29 are on screen (the original clips 「ここは どこだ|ろうか」), so the lint budget is 13 cells / 104 px for s09C81E-s09CF8A and 19 names were shortened again (Temple Hall, Academy Den, Vega Cabins 1-3, Gedling Site 1/2...; "...Where am I..."). Revisit if the owner objects. |
| D10 | 2026-11-15 | Battle names (s09F8FE-s09F9DA) fill `{argN}` in battle lines, which the lint counts at 64 px; "Robot Soldier" (86), "GED Soldier" (75), "Scarecrow" (67) overran it | count names at their real max width (≈50 battle lines then overflow 192 px), shorten the 3 names | Agent default under D6: the names table is held to 64 px by a lint rule; ロボット兵 Robot, ゲド機関兵 GED Goon, カカシ Strawman (dialogue keeps Robot Soldier / GED Soldier). Revisit if the owner objects. |
