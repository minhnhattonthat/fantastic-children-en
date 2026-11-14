# Translator brief - Fantastic Children (GBA, Bandai 2005)

You translate part of the Japanese script of *Fantastic Children* into English for a fan patch. It is an adventure
game with "Talk Battles", based on the 2004 anime: Tohma, a brash 11-year-old from Papin Island, helps the runaway
orphans Helga and Chitto, while the ageless Children of Befort search for the reincarnated princess Tina.
Work only on the batches named in your dispatch, one at a time in the order given, each to a passing check before the
next. Do all translation yourself; do not dispatch subagents. Edit nothing but your own output files.

## Read first
1. `glossary.md` - rulings, style rules, character voices, and the binding term table.
2. `docs/style-reference.md` if it exists - approved example pairs. Match this voice.
3. `build/terms_<batch>.txt` - the glossary rows found in this batch (the check enforces them).
4. `docs/synopsis.md` - who is who and the late reveals. Don't give a reveal away early.

## Input: `work/tl/<batch>.tsv`
`id<TAB>ref<TAB>form<TAB>limit<TAB>Japanese`.
- Each row is ONE LINE of a text box (a "page"). `ref` = `m<message>.<line>`: rows of one message are consecutive and
  make up one conversation; translate them as a whole and spread the English over its lines naturally.
  A row may belong to several messages (`m300.0,m302.1`): the same line reused, translate it once.
- The box shows 2 lines, then waits for a key and shows the next 2. The Japanese uses blank lines (not in the batch)
  to make a new speaker start a fresh box: `form` = `dlg+break` means a blank line follows this row.
- `limit` = ink width in pixels of the box: 192px (bottom box) or 168px (top box with portrait); about 6.5 px per
  character, so roughly 29 / 25 characters. `choice` rows are answers in a 2-column menu: 72px (about 10 characters)
  and must stay one line. `sys` rows are menu, item, help and battle strings; their limit comes from the screen region.
- If the English needs more room than the Japanese lines, a dialogue row may continue onto extra lines: write ` / `
  (space slash space) where the next line starts, at most 2 per row. Rules: (1) each line must fit the limit on its
  own; (2) within one box group (the rows up to a `dlg+break` row), the extra lines must add up to an EVEN number, so
  the next speaker still opens a fresh box - e.g. add one ` / ` in two rows of the group, or two in one row. Prefer
  fitting into the existing lines; use extra lines rather than cutting meaning.
- Speaker lines: `トーマ「ハァッ！` -> `Tohma: Hah!`. Lines starting with blanks (continuation under the name) start with
  one space in English. A row that begins or ends with a blank must do so in English too.
- `{arg0}`..`{arg3}` are names/numbers the game inserts; keep each exactly. `{endflag}` stays at the very end.
- Rows `ヌルイベント`, `イベントテスト0`, `カイワテスト1`, `バトルカイシ`... are debug event names: translate plainly
  ("Null Event", "Event Test 0", "Dialogue Test 1", "Battle Start").

## Output: `work/tl/<batch>.out.tsv`, written with your file-write tool (not a shell heredoc)
`id<TAB>English`, every input id exactly once, same order, no header. ASCII plus the few characters the font has
(… ♪ é × ‘ ’ “ ” —); prefer plain `...` and straight quotes. No tabs inside the English, no Japanese or fullwidth
characters, no `\n`, no `\uXXXX`.

## Validate
`python -X utf8 tools/batches.py check <batch>` from the repo root; fix every reported id until it prints OK.
To try a line: `python -X utf8 tools/batches.py fit "Tohma: Hah! / second line" --px 168`.

## Style
- Faithful: keep the information and order of ideas; adapt idiom, not meaning. Don't add or drop details. Adapt jokes
  and wordplay so they still land (no translator notes).
- Keep the speaker audible (voices in `glossary.md`): Tohma's オレ/ぜ/じゃねぇか is cocky and rough ("Heh, not bad...",
  "Can't run from my Papin Kenpo!"); Chitto's ボク/です is soft and polite; Helga is terse; the Children of Befort are
  solemn adults. A line any character could have said is a mistake.
- Names and terms exactly as in the glossary; honorifics kept and hyphenated (Helga-chan). Never abbreviate to fit.
- Sound effects and shouts: natural English ("Hah!", "Hyaaah!", "Kee kee!"), not romaji.
- Game prompts in second person, imperative and short ("Use the +Control Pad to move left and right").
- Punctuation: ・・・ -> `...`; ！！ -> `!!`; ！？ -> `?!`; 「item」 -> "item"; 『』 -> single quotes.

## Consistency
Never edit `glossary.md`. For a recurring name or term not in it, pick a form, use it consistently, and report it.

## Report (reply with only this)
Per batch: file written and entry count; then any lines `NEW TERM: jp -> en`, `UNSURE: id - note`, `LONG: id - note`.
