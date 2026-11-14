# Fonts

Every font or glyph sheet the build reads ends up inside the released patch, so its licence must allow that. One row
per file; a font with no known licence doesn't go into a release.

| File | Source (URL, version) | Licence | Redistributable in a patch | Used for | Changes made |
|---|---|---|---|---|---|
| fonts/vwf_en.png, fonts/vwf_en.tsv | Lato Bold (https://github.com/google/fonts/tree/main/ofl/lato, Lato-Bold.ttf, fetched 2026-11-15) rendered at 13 px by `tools/vwf_font.py` | SIL OFL 1.1 (Reserved Font Name "Lato") | yes, as rendered bitmap glyphs; credit Łukasz Dziedzic / Lato in the release README; the patch must not call the font "Lato" | dialogue and menu VWF (`tools/vwf.py`) | rasterised to 16 grey levels, 1 px gap after each glyph; no outline edits |

The TTF itself is not in the repo (download it to re-render: `python -X utf8 tools/vwf_font.py render Lato-Bold.ttf`);
the committed PNG is what the build reads. Japanese glyphs stay the game's own font.
