# Glossary - Fantastic Children (GBA)

Binding for every translator and reviewer. Agents propose additions in reports (`NEW TERM: jp -> en`); only the
controller edits this file. `tools/batches.py check` enforces the EN column for every JP term in a line.

## Rulings (asked of the user once; options and reasons in docs/decisions.md)
- Honorifics: kept, hyphenated (Helga-chan, Tohma-kun, Borabora-sama); 先生 after a name -> "-sensei". Family words
  for one's own family are English (とうちゃん "Dad", かあちゃん "Mom"). Name order: Western (D1).
- Romanisation: the anime's English names (Wikipedia list of characters, Bandai/Animax), else Hepburn without
  macrons (D2). Credits: English (D3).
- Register: plain, lively modern English for kids' adventure dialogue; each character keeps a voice (below).
  Sound effects: plain words with their punctuation ("Hah!", "Whoa!", "Kee kee!").
- Abbreviations: none. Full names and terms; if a line is too long, use an extra line (" / ") before cutting (D4).

## Style rules
- Speaker prefix: `トーマ「...` -> `Tohma: ...`. The closing 」 is dropped; no quote marks around speech.
  Continuation lines that start with blanks in the Japanese start with one space in English (lint checks it).
- Punctuation map: ・・・ / … -> "..." ; ！！ -> "!!" ; ！？ -> "?!" ; 「」 around a name or item -> "..." double quotes;
  『』 -> '...' single quotes (or double quotes inside narration) ; ー stretches -> repeated letters ("Waaah!").
- ♪ stays (encodable). No other non-ASCII except what tbl/en.tbl encodes (… — ‘ ’ “ ” é × ♪).
- Numbers stay digits as in the Japanese ("10" items). No ordinal suffix after a {argN}.
- Voices:
  - Tohma (オレ, ～ぜ, ～だぜ, ～じゃねぇか): brash, cocky 11-year-old island boy; contractions, "gonna", "ain't" sparingly,
    exclamations. Kind under the bluster.
  - Helga (わたし, short sentences): quiet, guarded, few words; no slang. Warms up slowly.
  - Chitto (ボク, ～です/～だよ): gentle, earnest, polite small boy; slightly formal ("Um, Tohma... I think...").
  - Children of Befort (Soran, Agi, Soreto, Hesma, Hasmodai, Tarlant, Mel): calm, adult, solemn; no slang.
  - Dumas: cold, grand, menacing.  Tohma's Dad (Papin Kenpo master): loud, gruff, joking. Mom: warm, scolding.

## Characters
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| トーマ | Tohma | | hero, 11, Papin Island; reincarnation of Seth | Toma, Thomas |
| ヘルガ | Helga | | runaway orphan girl; reincarnation of Tina | |
| チット | Chitto | | Helga's friend from the orphanage | Chit |
| ティナ | Tina | | princess of Greecia | |
| セス | Seth | | Tohma's past life | Sess |
| ソラン | Soran | | leader of the Children of Befort | |
| デュマ | Dumas | | | Duma, Damien |
| アギ | Agi | | Befort child | |
| ソレト | Soreto | | Befort child | |
| ヒースマ | Hesma | | Befort child | Heathma |
| ハスモダイ | Hasmodai | | Befort child | |
| タルラント | Tarlant | | Befort child | |
| メル | Mel | | Befort child | |
| ゲルタ | Gherta | | Gherta Hawksbee | Gerta |
| ゲオルカ | Georca | | | |
| タイタス | Titas | | king of Greecia | Titus |
| ゴトー | Goto | | | |
| レダ | Reda | | | |
| エンマ | Enma | | | |
| セラフィーヌ | Seraphine | | | Serafine |
| クリスティーナ | Christina | | | Cristina |
| アメデオ | Amedeo | | monkey ("キキッ" -> "Kee kee!") | |
| ボラボラ | Borabora | | ボラボラ様 -> Borabora-sama | |
| ワンダ | Wanda | | | |
| ラウロ | Lauro | | | |
| リリア | Lilia | | | |
| アーノン | Arnon | | | |
| アカバ | Akaba | | | |
| ハザマ | Hazama | | | |

## Places
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| パパン島 | Papin Island | | パパン alone -> Papin | Papan, Papen |
| パパン拳法 | Papin Kenpo | | Tohma's family martial art | |
| チカオ | Chikao | | チカオ島 Chikao Island | |
| 児童学園 | Children's Academy | | the orphanage (チカオ児童学園 Chikao Children's Academy) | |
| ナツナ島 | Natsuna Island | | | |
| コックリ島 | Kokkuri Island | | | |
| クリル島 | Kuril Island | | | |
| クレルモン | Clermont | | | |
| リョウヨウ施設 | sanatorium | | 療養施設 | |
| ギリシア | Greecia | | the lost planet | Greece, Girishia |
| ベフォール | Befort | | ベフォールの子供たち -> the Children of Befort | Beforl |
| ヴェガ | Vega | | 宇宙船ヴェガ -> the spaceship Vega | |
| ゲドリング | Gedling | | | |
| ストーングランド | Stone Grand | | | |
| タナトルーム | Thanato Room | | | |
| 宝物庫 | treasury | | | |

## Items / skills / terms
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| オエセル | Orsel | | life force | Oesel |
| アウトゾーン | Autozone | | machine that returns souls from the Zone | Out Zone |
| ゾーン | Zone | | land of the dead | |
| ゲド機関 | the GED | | ゲド alone -> GED | Ged Engine |
| 記憶のレコード | Memory Record | | | |
| レコードのカケラ | Record Shard | | plural "Record Shards"; "10 Record Shards" | Record Fragment |
| カケラ | shard | | when it means a Record Shard | |
| フラグメント | Fragment | | | |
| バトルアイテム | Battle Item | | バトルアイテムＳＰ -> Battle Item SP | |
| パンチ | Punch | | | |
| キック | Kick | | | |
| チョップ | Chop | | | |
| ガード | Guard | | | |
| アクションバー | Action Bar | | | |
| サポートフレンド | Support Friend | | | |
| サポートエディット | Support Edit | | | |
| バトルエディット | Battle Edit | | | |
| ワンダーアタック | Wonder Attack | | | |
| ターンストップ | Turn Stop | | | |
| デコードクリスタル | Decode Crystal | | Ｒ/Ｇ/Ｂ/Ｙ -> R/G/B/Y | |
| クリスタルキー | Crystal Key | | | |
| パスカード | Pass Card | | | |
| セキュリティカード | Security Card | | | |
| データディスク | Data Disc | | | Data Disk |
| ポックリの実 | Pokkuri Fruit | | 大きなポックリの実 Big Pokkuri Fruit | |
| フォグボート | Fog Boat | | | |
| ヒコウテイ | flying boat | | 飛行艇 | |
| トークバトル | Talk Battle | | | |
| リアルタイムバトル | Real-Time Battle | | | |
| ラウンド | Round | | | |

## Decisions from earlier batches
- (none yet)
