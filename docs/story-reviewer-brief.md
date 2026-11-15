# Story reviewer brief - Fantastic Children (GBA)

You read one chapter of a JP->English fan translation straight through, in story order, the way a player
meets it. Per-batch reviewers already judged single lines with +-2 lines of context; your job is what they can't see.
Read-only: no edits, no git, no subagents. Return the report as your final message; the controller saves it.

## Inputs (inline in the prompt)
- Chapter: every translated page of the chapter in message order (the game's message ids run roughly in story order;
  area NPC chatter, item pickups and battle lines sit between story scenes), `>> id | ref | speaker | JP` / `EN`.
  `ref` is `mMESSAGE.PAGE`; a new message starts a new scene or speech. " / " in EN is a line break inside the box.
  Read ALL of it before judging.
- `docs/synopsis.md` (plot, who is who, late reveals), `docs/style-reference.md` (voice per character),
  `glossary.md` (rulings at the top: names, terms, decisions).

## Hard limits (do not ask for what can't fit)
- Each box line holds about 23-27 characters (168 px top box, 192 px bottom box). Choice answers are 9 characters
  (D8). Item/info strings are one line. Suggest wording of similar length.
- Pagination is NOT yours to judge: a row may carry 1, 2, 3 or more " / " lines and sentences run across rows on
  purpose. The box shows 2 lines, then continues the same message in a fresh box; the layout was reflowed by a tool
  and every box was checked in the emulator. Never report line counts, "exceeds the page limit", or where a sentence
  breaks between rows. Read the rows of one message as one continuous text and judge only what it says.
- Debug/test messages (イベントテスト, ヌルイベント, character lists, "Added 2005...") are the game's leftover debug
  text: don't judge them.

## Judge, across the whole chapter
- Continuity: each line follows from the one before; setups, callbacks and references back are kept; who knows what
  stays coherent; nothing gives a later reveal away early.
- Voice: each character sounds like the same person all chapter and matches their style-reference row: speech quirks,
  register, how they address others. Name the line where a voice drifts or goes neutral.
- Emotion: anger, fear, grief and comedy beats are as strong as the Japanese; a running gag keeps its punchline.
- Accuracy only where a line breaks one of the above; single-line accuracy was reviewed already.

## Report
Start with exactly one line: `Coverage: FIRST_ID .. LAST_ID (N rows)` (the first and last `>>` ids and the count).
### Issues
#### Critical (continuity break, reveal given away, wrong speaker)
#### Important (voice drift or flattened, emotional beat lost, setup or callback dropped, joke dead)
#### Minor (deferred to the polish pass)
Each: `id - JP gist - problem - suggested EN`.
### Assessment
`ok` (no Critical/Important) | `issue` - one sentence why. The controller writes this word into the chapter's verdict.
