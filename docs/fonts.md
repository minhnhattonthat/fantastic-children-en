# Fonts

Every font or glyph sheet the build reads ends up inside the released patch, so its licence must allow that. One row
per file; a font with no known licence doesn't go into a release.

| File | Source (URL, version) | Licence | Redistributable in a patch | Used for | Changes made |
|---|---|---|---|---|---|
| fonts/vwf_en.png, fonts/vwf_en.tsv | Lato Bold (https://github.com/google/fonts/tree/main/ofl/lato, Lato-Bold.ttf, fetched 2026-11-15) rendered at 13 px by `tools/vwf_font.py` | SIL OFL 1.1 (Reserved Font Name "Lato") | yes, as rendered bitmap glyphs; credit Łukasz Dziedzic / Lato in the release README; the patch must not call the font "Lato" | dialogue and menu VWF (`tools/vwf.py`) | rasterised to 16 grey levels, 1 px gap after each glyph; no outline edits |
| gfx/title_0..3.png (logo only) | Bebas Neue Regular (https://github.com/google/fonts/tree/main/ofl/bebasneue, BebasNeue-Regular.ttf, fetched 2026-11-15) rendered by `tools/title_logo.py` | SIL OFL 1.1 | yes, as a rendered picture; credit Dharma Type / Bebas Neue in the release README | title logo "FANTASTIC CHILDREN" (G1) | cap 22 px, hard-edged, 3 px tracking, gradient fill + outlines added |
| gfx/devlogo.png | Lato Black (https://github.com/google/fonts/tree/main/ofl/lato, Lato-Black.ttf, fetched 2026-11-15) rendered by `tools/devlogo_gfx.py` | SIL OFL 1.1 (RFN "Lato") | yes, as a rendered picture; same credit as the VWF row | boot developer logo "INTI CREATES" (G3) | cap 12 px, sheared 0.22 (italic), 13-step palette ramp, 1 px shadow |
| gfx/staff_00..17.png | Oswald (variable, Bold instance; https://github.com/google/fonts/tree/main/ofl/oswald, Oswald[wght].ttf, fetched 2026-11-15) rendered by `tools/staff_gfx.py` | SIL OFL 1.1 | yes, as a rendered picture; credit Vernon Adams / Oswald in the release README | staff roll credits (G5) | capitals squeezed to 7x12 px in 8x16 cells, 16 grey levels, 1 px shadow |
| gfx/title_0..3.png (copyright lines) | the game's own 8×8 font (ROM 0x40000, G6) | the game's | n/a (already in the ROM) | title copyright (G2) | R redrawn (G6's reads as B), © drawn by hand |

The TTF itself is not in the repo (download it to re-render: `python -X utf8 tools/vwf_font.py render Lato-Bold.ttf`);
the committed PNG is what the build reads. Japanese glyphs stay the game's own font.
