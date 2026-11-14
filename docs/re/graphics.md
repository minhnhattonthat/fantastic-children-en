# Graphics text survey

Screens seen so far (tour of the original ROM: boot, intro, title, file select, opening cutscene, stage 1).
Status: **tour part done for the opening; static sweep not done yet** (Phase 1 remainder, see `docs/status.md`).

| # | Screen | Element | Kind | Source guess | Plan |
|---|---|---|---|---|---|
| G1 | Title | Logo ファンタジックチルドレン (with small "FANTASTIC CHILDREN" above) | BG tiles | compressed graphics block (not located yet) | Redraw as an English logo (D5: the anime had an official English title logo) |
| G2 | Title | Copyright line "© なかむらたかし／日本アニメーション・FC製作委員会 2004 / © BANDAI 2005" | BG tiles | with the title graphics | Redraw in English: "© Takashi Nakamura / Nippon Animation, FC Production Committee 2004" |
| G3 | Boot | Developer logo インディ・クリエイツ | BG tiles | boot graphics | Company logo in katakana; redraw as romanized name (check the company's own romanization) |
| G4 | Intro / cutscenes | Book pages with pseudo-handwriting | BG tiles | IWRAM decompressor stream `0x189BD4-0x1F38E3` | Not Japanese (scribbles); no change |

Already English in the original: BANDAI and GAME BOY logos, PUSH START BUTTON, START GAME / DELETE GAME, NEW GAME
slots, HUD name plate (TOMA), HUD counters.

Font-drawn (text work, not graphics): intro and cutscene captions, the file-select help line
"ゲームを 最初からはじめます。 / A:決定 B:もどる" (8×16 dialogue font; source string not yet matched to the message
table — check in the marker build).

## Still to survey
- Static sweep: render all 170 LZ77 blocks (`tools/gbacomp.py scan`), the IWRAM-decompressed cutscene stream and the
  raw graphics regions as gba4/gba8 sheets with an offset index, and list every Japanese cell.
- Screens beyond stage 1 via the Phase 2 debug tool: pause/menu screens, stage title cards, boss/battle banners
  ("talk battle" exists per the debug event names), game over, ending, staff roll.
