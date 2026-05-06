# Implementation Audit

This audit compares the current codebase against the rule requirements in this directory.
Met items are kept in the summary for context. Detailed findings are limited to unresolved work.

Status values:

- **Met**: the requirement appears implemented in code.
- **Partial**: the code has support, but behavior is incomplete, simplified, or has a known edge-case issue.
- **Missing**: no implementation was found.
- **Mismatch**: implementation contradicts the requirement.

## Summary

| Area | Status | Notes |
|------|--------|-------|
| Tile set and compact notation | Met | `Tile`, `TileSet`, `parse_tiles`, and `format_tiles` cover the standard tile set and Red Dora notation. |
| Initial deal | Met | `TileSet.deal()` is dealer-aware, and `RuleEngine.deal()` passes `GameState.dealer`. |
| Hand operations | Met | Draw, discard, chi, pon, kan, and closed kan exist. |
| Winning-hand detection | Met | Standard, Chiitoitsu, and Kokushi Musou are accepted by `Hand` and `RuleEngine.check_win()`. |
| Tenpai and machi listing | Met | Includes decomposition paths where four identical concealed tiles can be used as a triplet plus a leftover tile. |
| Action priority | Met | `_resolve_decisions()` prioritizes ron, then pon/kan, then chi. |
| Multiple ron rules | Met | Head Bump, Double Ron, Triple Ron, and Sancha Ron are represented, and multiple-ron scoring uses `ScoreResult` settlement. |
| Furiten | Met | Genbutsu, temp furiten, and permanent riichi furiten are implemented. |
| Riichi action rules | Met | Closed hand, tenpai-after-discard, Riichi Stick payment, and remaining-wall requirement are implemented. |
| Ippatsu | Met | Ippatsu is tracked after riichi and interrupted by calls or kan according to ruleset configuration. |
| Kan and rinshan flow | Met | Kan, closed kan, rinshan draw, Chankan, Suukan Sanra, and kan dora indicator counts are implemented. |
| Abortive draws | Met | Suufon Renda, Kyuushu Kyuuhai, Suucha Riichi, Suukan Sanra, and Sancha Ron exist, with shared ryuukyoku settlement for dealer continuation and honba handling. |
| Yaku coverage | Met | Listed standard yaku exist, including ruleset-configurable Open Tanyao. |
| Open-hand reductions | Met | Chanta, Junchan, Sanshoku Doujun, Ittsu, Honitsu, and Chinitsu apply open-hand han reductions. |
| Yaku combination filtering | Met | Pinfu combines with Iipeikou and Ryanpeikou, yakuman results exclude non-yakuman yaku, and Chiitoitsu includes compatible yaku. |
| Scoring calculations | Met | Fu, han, limits, payment rounding, honba, kyoutaku, Kiriage Mangan, Noten Bappu, Pao, and dora counting are implemented. |
| Payment context | Met | `ScoreCalculator.calculate()` receives payment context before calculating payment branches. |
| Pinfu tsumo fu | Met | `calculate_fu()` returns 20 fu for Pinfu tsumo and 30 fu for closed Pinfu ron. |
| Nagashi Mangan | Met | Exhaustive-draw paths score Nagashi Mangan with mangan payments. |
| Renchan and round progression | Met | Dealer win and exhaustive-draw dealer tenpai renchan are implemented in `end_round()`. |
| Game-end conditions | Met | Tobi, west round extension, and Agari Yame are implemented. |
| Chombo | Met | False win and invalid riichi produce explicit Chombo results and mangan-level penalties when enabled by `RulesetConfig`. |
| Abortive draw settlement | Met | Abortive draws now use shared ryuukyoku settlement, with configurable dealer continuation and honba incrementing. |

## Detailed Findings

No unresolved findings remain in this audit.
