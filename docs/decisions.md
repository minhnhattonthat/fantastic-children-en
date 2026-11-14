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
| D8 | 2026-11-15 | Destination answers in the 72 px choice grid ("Natsuna Island" is ~90 px) | widen the grid (engine), drop "Island", abbreviate | Agent default under D6 (pre-approved): drop " Island" in choice answers only ("Natsuna", "Chikao", "Papin"), as a map menu would; not an abbreviation, and the 2-column grid is the game's layout. `batches.py` accepts it for choice rows only. Revisit if the owner objects. |
