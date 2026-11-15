# Fantastic Children English translation

Unofficial English fan translation of **Fantastic Children** (Game Boy Advance, Bandai, 2005): the source text and
tools that build the patch.

**Just want to play?** Download the patch from [Releases](../../releases) and follow its README. This repository holds
no game data you can play; you need your own dump of the Japanese game.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a savestate
helps most.

## Base ROM

| | |
|---|---|
| No-Intro name | Fantastic Children (Japan) |
| Size | 8,388,608 bytes |
| CRC32 | FEFE25BE |
| MD5 | 43265d5f7709133927133a331b55c61b |
| SHA-1 | 8af0853249f6f4da90ac1044c387e067ef85972a |

The patched ROM's hashes are in the README inside each release zip. Tested in Mesen 2.2.1 (GBA core, official BIOS);
start from a cold boot, not from a savestate made on the Japanese version.

## Translation status

| Part | Status |
|---|---|
| Dialogue / story (4,133 pages) | Translated |
| Menus, items, cards, battle lines, area names | Translated |
| Title logo, copyright line, boot logo | Redrawn in English |
| Staff roll | Redrawn in English (staff-name readings are best guesses from kanji: corrections welcome) |
| Name entry | None in this game |
| "SAVING...", pause card faces | Already English in the original |

Known issues: none known; see [Issues](../../issues).

## What's here

| Path | What it is |
|---|---|
| `script/` | Every text block: original Japanese and English. Translation fixes go here. |
| `glossary.md` | Binding names, terms and style rules. |
| `tools/` | Python build chain: extract, insert, lint, release. |
| `tests/` | unittest suite (ROM-dependent tests skip when the ROM is absent). |
| `docs/re/` | Reverse-engineering notes. |
| `docs/decisions.md`, `docs/status.md` | Rulings with their reasons; current progress and open bugs. |
| `docs/fonts.md` | Fonts used and their licences. |
| `AGENTS.md` | Instructions for coding agents (`CLAUDE.md` points to it). |
| `.codex/agents/`, `.opencode/agents/` | Subagent types (translator, reviewer, visual QA, playtester, graphics) for Codex and opencode; Claude Code gets them from the plugin. |

## Build your own patched ROM

Needs Python 3.12+ (`pip install keystone-engine pillow`) and your own dump of the Japanese game.

```sh
git clone https://github.com/minhnhattonthat/fantastic-children-en
cd fantastic-children-en
# copy your dump to: rom/Fantastic Children (Japan).gba
#   (8388608 bytes, SHA-1 8af0853249f6f4da90ac1044c387e067ef85972a; the build refuses any other dump, see rom.sha1)
python -X utf8 build.py                                # -> build/fantastic_children_en.gba
python -X utf8 tools/check.py                          # tests + text lint
```

## Credits

Fonts rendered into the patch (SIL Open Font License 1.1): Lato by Łukasz Dziedzic (dialogue, boot logo), Bebas Neue
by Dharma Type (title logo), Oswald by Vernon Adams (staff roll). Details in `docs/fonts.md`.

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

## Licence

Tools and English translation: MIT. The original Japanese text in `script/` is Bandai's and is included only so
the translation can be checked against it. Fantastic Children is (c) Nippon Animation / Bandai; this project is not
affiliated with them. Do not share patched ROMs.

The translation was made with extensive AI assistance (Claude by Anthropic, with review passes by OpenAI Codex).
Corrections are very welcome.
