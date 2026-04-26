# Mahjong Terminology

This document tracks Japanese riichi mahjong terms used in the pyriichi codebase.
`Code` is the short identifier-style form used in code and developer-facing APIs. `English` is the game/UI display form.

## Translation Guidelines

Use these conventions when adding new terms:

- Start from the canonical Japanese riichi term, then choose one code form, one English display form, and one Traditional Chinese display form.
- Preserve the table shape: `Code | 日本語 | English | 中文 | Notes`.
- `Code` values are developer-facing identifiers. Use lowercase `snake_case`, and make sure every `Code` value is unique across the file.
- `English` values are game/UI display labels. Prefer wording used by English riichi games when it is clear and player-facing, for example `All Simples`, `Full Flush`, `Prevalent Wind`, `Exhaustive Draw`, and `Discard River`.
- Keep standard riichi UI calls as romaji: `Chi`, `Pon`, `Kan`, `Riichi`, `Ron`, and `Tsumo`.
- Keep standard scoring and bonus terms as romaji: `Mangan`, `Haneman`, `Baiman`, `Sanbaiman`, `Yakuman`, `Dora`, `Red Dora`, and `Ura Dora`.
- Use Traditional Chinese consistently in the `中文` column.
- Pick one translation. Do not list alternatives in a cell or add notes like "also common" unless the note explains a real code distinction.
- Split terms by context when the same Japanese surface form has different meanings. For example, `draw` and `tsumo` may both use `ツモ`, but they represent different UI/game concepts.
- Do not add speculative terms. Before adding a new glossary entry, search the codebase and docs for the Japanese, Chinese, and existing code/API names. If a term is not used and has no clear source, leave it out.
- Remove stale glossary-only terms instead of quarantining them indefinitely.

## Tile Groups (牌種)

| Code | 日本語 | English | 中文 | Notes |
|------|--------|---------|------|-------|
| manzu | 萬子 | Characters | 萬子 | Character suit. |
| pinzu | 筒子 | Circles | 筒子 | Circle suit. |
| souzu | 索子 | Bamboo | 索子 | Bamboo suit. |
| honors | 字牌 | Honor Tiles | 字牌 | Winds and dragons. |

## Winds (風牌)

| Code | 日本語 | English | 中文 | Notes |
|------|--------|---------|------|-------|
| east | 東 | East | 東 | East wind. |
| south | 南 | South | 南 | South wind. |
| west | 西 | West | 西 | West wind. |
| north | 北 | North | 北 | North wind. |
| round_wind | 場風 | Prevalent Wind | 場風 | Wind of the current round. |
| seat_wind | 自風 | Seat Wind | 自風 | Wind of a player seat. |

## Dragon Tiles (三元牌)

| Code | 日本語 | English | 中文 | Notes |
|------|--------|---------|------|-------|
| white | 白 | White | 白 | White dragon. |
| green | 発 | Green | 發 | Green dragon. |
| red | 中 | Red | 中 | Red dragon. |

## Calls and Turn Actions (鳴き・動作)

| Code | 日本語 | English | 中文 | Notes |
|------|--------|---------|------|-------|
| draw | ツモ | Draw | 摸牌 | Drawing a tile. |
| discard | 打牌 | Discard | 打牌 | The action of discarding a tile. |
| chi | チー | Chi | 吃 | Call a sequence from the previous player. |
| pon | ポン | Pon | 碰 | Call a triplet. |
| kan | カン | Kan | 槓 | Declare a kan. |
| declare_riichi | リーチ | Riichi | 立直 | Button/action form used in games. |
| ron | ロン | Ron | 榮和 | Win on another player's discard. |
| tsumo | ツモ | Tsumo | 自摸 | Self-draw win. |
| pass | パス | Pass | 過 | Decline a call or win opportunity. |

## Game State (局面)

| Code | 日本語 | English | 中文 | Notes |
|------|--------|---------|------|-------|
| round_number | 局 | Round Number | 局數 | East 1, East 2, etc. |
| dealer | 親 | Dealer | 莊家 | Dealer/east player. |
| honba | 本場 | Honba | 本場 | Counter for repeat/dealer-continuation bonus sticks. |
| kyoutaku | 供託 | Deposit | 供託 | Points/sticks placed on the table. |
| riichi_stick | 立直棒 | Riichi Stick | 立直棒 | The 1000-point stick paid on riichi declaration. |

## Yaku (役)

| Code | 日本語 | English | 中文 | Notes |
|------|--------|---------|------|-------|
| riichi | 立直 | Riichi | 立直 | Yaku name. |
| double_riichi | ダブルリーチ | Double Riichi | 雙立直 | Yaku name. |
| ippatsu | 一発 | Ippatsu | 一發 | |
| menzen_tsumo | 門前清自摸和 | Fully Concealed Tsumo | 門前清自摸和 | Closed self-draw yaku. |
| pinfu | 平和 | Pinfu | 平和 | |
| tanyao | 断么九 | All Simples | 斷么九 | |
| iipeikou | 一盃口 | Pure Double Sequence | 一盃口 | |
| ryanpeikou | 二盃口 | Twice Pure Double Sequence | 二盃口 | |
| toitoi | 対々和 | All Triplets | 對對和 | |
| sanankou | 三暗刻 | Three Concealed Triplets | 三暗刻 | |
| sankantsu | 三槓子 | Three Kans | 三槓子 | |
| sanshoku_doujun | 三色同順 | Mixed Triple Sequence | 三色同順 | |
| sanshoku_doukou | 三色同刻 | Mixed Triple Triplets | 三色同刻 | |
| ittsu | 一気通貫 | Pure Straight | 一氣通貫 | |
| honitsu | 混一色 | Half Flush | 混一色 | |
| chinitsu | 清一色 | Full Flush | 清一色 | |
| junchan | 純全帯么九 | Terminal in Each Set | 純全帶么九 | |
| chanta | 混全帯么九 | Outside Hand | 混全帶么九 | |
| honroutou | 混老頭 | All Terminals and Honors | 混老頭 | |
| shousangen | 小三元 | Little Three Dragons | 小三元 | |
| daisangen | 大三元 | Big Three Dragons | 大三元 | |
| suuankou | 四暗刻 | Four Concealed Triplets | 四暗刻 | |
| suuankou_tanki | 四暗刻単騎 | Four Concealed Triplets Single Wait | 四暗刻單騎 | |
| suukantsu | 四槓子 | Four Kans | 四槓子 | |
| shousuushi | 小四喜 | Little Four Winds | 小四喜 | |
| daisuushi | 大四喜 | Big Four Winds | 大四喜 | |
| chinroutou | 清老頭 | All Terminals | 清老頭 | |
| tsuuiisou | 字一色 | All Honors | 字一色 | |
| ryuuiisou | 緑一色 | All Green | 綠一色 | |
| chuuren_poutou | 九蓮宝燈 | Nine Gates | 九蓮寶燈 | |
| pure_chuuren_poutou | 純正九蓮宝燈 | Pure Nine Gates | 純正九蓮寶燈 | |
| kokushi_musou | 国士無双 | Thirteen Orphans | 國士無雙 | |
| kokushi_musou_juusanmen | 国士無双十三面 | Thirteen-Sided Thirteen Orphans | 國士無雙十三面 | |
| tenhou | 天和 | Heavenly Hand | 天和 | |
| chihou | 地和 | Earthly Hand | 地和 | |
| renhou | 人和 | Hand of Man | 人和 | |
| haitei | 海底摸月 | Under the Sea | 海底摸月 | Win by self-draw on the last wall tile. |
| houtei | 河底撈魚 | Under the River | 河底撈魚 | Win by ron on the last discard. |
| rinshan | 嶺上開花 | After a Kan | 嶺上開花 | |
| chankan | 槍槓 | Robbing a Kan | 搶槓 | |
| chiitoitsu | 七対子 | Seven Pairs | 七對子 | |
| nagashi_mangan | 流し満貫 | Nagashi Mangan | 流局滿貫 | Special win/score event. |

## Wait Shapes (待ち)

| Code | 日本語 | English | 中文 | Notes |
|------|--------|---------|------|-------|
| ryanmen | 両面 | Two-Sided Wait | 兩面 | |
| penchan | 辺張 | Edge Wait | 邊張 | |
| kanchan | 嵌張 | Closed Wait | 嵌張 | |
| tanki | 単騎 | Single Wait | 單騎 | |
| shabo | シャボ | Pair-Pair Wait | 雙碰 | |
| machi | 待ち | Wait | 聽牌形 | Generic wait shape. |

## Scoring Limits (点数)

| Code | 日本語 | English | 中文 | Notes |
|------|--------|---------|------|-------|
| han | 翻 | Han | 翻 | Han value. |
| fu | 符 | Fu | 符 | Fu value. |
| mangan | 満貫 | Mangan | 滿貫 | |
| haneman | 跳満 | Haneman | 跳滿 | |
| baiman | 倍満 | Baiman | 倍滿 | |
| sanbaiman | 三倍満 | Sanbaiman | 三倍滿 | |
| yakuman | 役満 | Yakuman | 役滿 | |

## Dora and Bonus Indicators (ドラ)

| Code | 日本語 | English | 中文 | Notes |
|------|--------|---------|------|-------|
| dora | ドラ | Dora | 寶牌 | Bonus tile. |
| red_dora | 赤ドラ | Red Dora | 赤寶牌 | Red five bonus tile. |
| ura_dora | 裏ドラ | Ura Dora | 裏寶牌 | Hidden dora revealed after riichi wins. |

## Defensive and Hand-State Concepts (守備・手牌状態)

| Code | 日本語 | English | 中文 | Notes |
|------|--------|---------|------|-------|
| furiten | 振聴 | Furiten | 振聽 | Cannot ron due to discard/win-pass constraints. |
| temp_furiten | 一時振聴 | Temporary Furiten | 暫時振聽 | Temporary furiten after passing a ron opportunity. |
| tenpai | 聴牌 | Tenpai | 聽牌 | One tile from winning. |
| shanten | 向聴 | Shanten | 向聽 | Distance from tenpai. |
| discarded | 捨て牌 | Discarded Tile | 捨牌 | The tile after it has been discarded. |
| genbutsu | 現物 | Safe Tile | 現物 | Tile known safe against a player because they discarded it. |
| betaori | ベタオリ | Full Fold | 棄和防守 | Full defense/folding. |
| wall | 壁 | Wall | 壁 | Tile-wall safety concept. |
| river | 河 | Discard River | 牌河 | Discard river. |
| ryuukyoku | 流局 | Exhaustive Draw | 流局 | Drawn hand. |
