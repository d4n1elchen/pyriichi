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
| Kan and rinshan flow | Partial | Kan, closed kan, rinshan draw, Chankan, and Suukan Sanra exist; dora indicator count is still incorrect during scoring. |
| Abortive draws | Partial | Suufon Renda, Kyuushu Kyuuhai, Suucha Riichi, Suukan Sanra, and Sancha Ron exist; shared settlement is still incomplete. |
| Yaku coverage | Partial | Most listed yaku exist; Open Tanyao cannot yet be configured. |
| Open-hand reductions | Met | Chanta, Junchan, Sanshoku Doujun, Ittsu, Honitsu, and Chinitsu apply open-hand han reductions. |
| Yaku combination filtering | Met | Pinfu combines with Iipeikou and Ryanpeikou, yakuman results exclude non-yakuman yaku, and Chiitoitsu includes compatible yaku. |
| Scoring calculations | Partial | Fu, han, limits, payment rounding, honba, kyoutaku, Kiriage Mangan, Noten Bappu, and Pao have support; dora indicator count remains wrong. |
| Payment context | Met | `ScoreCalculator.calculate()` receives payment context before calculating payment branches. |
| Pinfu tsumo fu | Met | `calculate_fu()` returns 20 fu for Pinfu tsumo and 30 fu for closed Pinfu ron. |
| Nagashi Mangan | Met | Exhaustive-draw paths score Nagashi Mangan with mangan payments. |
| Renchan and round progression | Met | Dealer win and exhaustive-draw dealer tenpai renchan are implemented in `end_round()`. |
| Game-end conditions | Met | Tobi, west round extension, and Agari Yame are implemented. |
| Chombo | Met | False win and invalid riichi produce explicit Chombo results and mangan-level penalties when enabled by `RulesetConfig`. |
| Dora indicator count | Mismatch | Count the initial dora indicator plus one additional indicator per kan when scoring dora and ura dora. |
| Abortive draw settlement | Partial | Apply a consistent round-settlement path for abortive draws, including dealer continuation and honba handling. |
| Open Tanyao configuration | Partial | Add a ruleset option for Open Tanyao and reject open Tanyao when the option is disabled. |

## Detailed Findings

### Dora Indicator Count

- Requirement: the first dora indicator is always active, and each kan reveals one additional dora indicator.
- Code: `_count_dora()` passes `_kan_count` into `get_dora_indicators()` and `get_ura_dora_indicators()`, so zero kan means zero visible indicators and one kan means only the initial indicator.
- Impact: hands can be under-scored by missing initial dora and kan dora.
- Suggested fix: use `1 + _kan_count` for dora and ura-dora indicator count, capped by the available indicators.

### Abortive Draw Settlement

- Requirement: abortive draws end the hand and update round state according to the active continuation rule.
- Code: `handle_ryuukyoku()` reports abortive draw types but does not share the same dealer/honba progression path as `end_round()`.
- Impact: direct abortive-draw handling can leave dealer, honba, and round number stale.
- Suggested fix: add a shared ryuukyoku settlement helper and call it from abortive-draw handlers.

### Open Tanyao Configuration

- Requirement: Open Tanyao is ruleset-dependent.
- Code: `check_tanyao()` always allows open hands and `RulesetConfig` has no Open Tanyao option.
- Impact: rulesets that disable Open Tanyao cannot be represented.
- Suggested fix: add `open_tanyao_enabled` to `RulesetConfig` and apply it in Tanyao checking.
