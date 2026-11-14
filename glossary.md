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
  - Chitto (ボク, ～です/～だよ): prickly with strangers (calls Tohma "airhead", "Are you stupid?!"), soft and polite with Helga (docs/style-reference.md).
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
| ゲド機関 | the GED / GED Soldier / GED Goon | | ゲド alone -> GED; ゲド機関兵 in dialogue -> GED Soldier; as a battle name ({argN} filler, 64 px) -> GED Goon | Ged Engine |
| ロボット兵 | Robot Soldier / Robot | | battle name ({argN} filler, 64 px) -> Robot | |
| カカシ | Scarecrow / Strawman | | battle name ({argN} filler, 64 px) -> Strawman | |
| 記憶のレコード | Memory Record | | | |
| レコードのカケラ | Record Shard | | plural "Record Shards"; "10 Record Shards" | Record Fragment |
| カケラ | shard | | when it means a Record Shard | |
| フラグメント | Fragment | | | |
| バトルアイテム | Battle Item | | バトルアイテムＳＰ -> Battle Item SP | |
| パンチ | Punch | | | |
| キック | Kick | | | |
| チョップ | Chop | | | |
| ガード | Guard / blocked | | battle log 〜の攻撃をガード -> "{arg0} blocked {arg1}!" ("guarded X" reads as protecting X) | |
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
| 回帰の旅 | Journey of Return | | Helga's past-life journey | |
| 伝書 | Scroll | | Battle Item tiers: 伝書 Scroll, 神技書 Divine Scroll, 秘伝書 Secret Scroll | |
| 神技書 | Divine Scroll | | | |
| 秘伝書 | Secret Scroll | | | |
| 転生装置 | reincarnation device | | 72 px choice answer "Device" (D8: a choice may use the form's last word) | rebirth device |
| 前世 | past life / past-life / past lives | | 前世の記憶 -> past-life memories | |
| 魂 | soul | | | |
| カイジョ | unseal | | レッドクリスタルをカイジョ -> unseal the Red Crystal | |
| コノエ | Royal Guard / guard | | コノエ兵 -> Royal Guard; "guard" when it is the role | |
| 霊道 | Spirit Road | | | |
| レッドクリスタル | Red Crystal | | | |

## More names and places (from batches b001-b012)
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| ケトプラック島 | Ketoprak Island | | | |
| アカバ海 | Akaba Sea | | | |
| ラウロしょとう | Lauro Islands | | | |
| オーラント島 | Orant Island | | in Spain (スペイン) | |
| ジム | Jim | | sailor who loved Seraphine | |
| アーノン | Arnon | | Christina's pupil | |
| ピロシカ | Piroshika | | a pale-blue flower/dye | |
| 院長 | Director | | head of the Children's Academy | Principal |
| 職員 | Staff | | speaker label | |

## Decisions from earlier batches
- 施設 for the orphanage -> "the home" (児童学園 stays "Children's Academy").
- Choice answers naming an island drop " Island" ("Natsuna", "Chikao", "Papin"): decisions.md D8.
- Speaker labels: とうちゃん "Dad", かあちゃん "Mom", 少年/少女 "Boy"/"Girl" until the game names them.
- ～様 after a name -> "-sama" (Tina-sama, Seth-sama, Titas-sama, Reda-sama); ～せんせい -> "-sensei".
- Tutorial tips: "+Control Pad", "A Button"/"A"; Support Friend gains read "The Support Friend "X"" / "joined you!".
- Battle lines (sys_battle): one line each, no " / "; a two-row line keeps the verb in the shared row ("and used it!",
  "and threw it!"). Battle-log style may drop "the" before an item. Name/number args: `tools/lint.py` NUM_PX.
- Item/card descriptions (sys_items): title row `Scroll "Punch 10" Straight Punch 1` (no colon), `SP "Pepper" ...`.

## Battle items and moves (from batches b024-b029)
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| 奥義書 | Master Scroll | | 4th Battle Item tier | |
| 占い道具 | Fortune Kit | | SP item | Fortune Tools |
| ブッ殺しバチのシガイ | Dead Killer Bee / dead bee | | SP item; battle line "the dead bee" | |
| ヘビのヌケガラ | Shed Snakeskin / Snakeskin | | SP item; battle line "Snakeskin" | |
| コショウ | Pepper | | | |
| さびたクギ | Rusty Nail | | | |
| コケむした花壇 | Mossy Flowerbed / Flowerbed | | battle line "Flowerbed" | |
| くちた画材 | Old Paints | | | Rotted Art Supplies |
| せいぎょカイロ | Control Chip | | | Control Circuit |
| デュマの涙 | Dumas's Tear | | | |
| 銀色の球体 | Silver Sphere | | | |
| 古い地図 | Old Map | | | |
| 裏口のカギ | Back Door Key | | | |
| さびたカギ | Rusty Key | | | |
| 正拳 | Straight Punch / Flurry | | 正拳連打 Flurry; 奥義パパン拳 Papin Fist | |
| 手刀 | Knife Hand / Combo / hand chop | | 手刀連撃 Combo; 奥義パパン掌 Papin Palm; in dialogue "hand chop" | |
| 確り | Front Kick / Spin Kick | | kanji table reads 蹴 as 確 here; 回し確り Spin Kick; 奥義パパン脚 Papin Leg | |
| ターンストップ | Turn Stop | | ＳＰかいふく SP Heal | |
| ショウヒレコード | Record | | support card cost: "Uses N Records" | |
| 闘魔 | Touma | | Tohma's dark battle form (pun on his name) | |
