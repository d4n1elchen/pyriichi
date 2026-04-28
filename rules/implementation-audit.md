# Implementation Audit

This audit compares the current codebase against the rule requirements in this directory. Status values:

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
| Winning-hand detection | Partial | Standard, Chiitoitsu, and Kokushi Musou exist in `Hand`; `RuleEngine.check_win()` now allows special hands without standard combinations. Known decomposition issues remain for four identical concealed tiles. |
| Tenpai and machi listing | Met | Implemented, including decomposition paths where four identical concealed tiles can be used as a triplet plus a leftover tile. |
| Action priority | Met | `_resolve_decisions()` prioritizes ron, then pon/kan, then chi. |
| Multiple ron rules | Partial | Head Bump, Double Ron, Triple Ron, and Sancha Ron are represented, but multiple-ron score settlement is simplified. |
| Furiten | Partial | Genbutsu and temp furiten exist; riichi furiten storage exists but is not set when a riichi player passes ron. |
| Riichi action rules | Partial | Closed hand and tenpai-after-discard checks exist; 1000-point payment exists; remaining-wall requirement is not implemented. |
| Ippatsu | Partial | Ippatsu tracking exists, but first-turn and interruption behavior needs broader verification. |
| Kan and rinshan flow | Partial | Kan, closed kan, rinshan draw, Chankan, and Suukan Sanra exist; dora indicator timing is simplified through indicator count. |
| Abortive draws | Partial | Suufon Renda, Kyuushu Kyuuhai, Suucha Riichi, Suukan Sanra, and Sancha Ron exist; dealer-continuation behavior is incomplete. |
| Yaku coverage | Partial | Most listed yaku exist, but several standard rule details do not match requirements. |
| Open-hand reductions | Met | Chanta, Junchan, Sanshoku Doujun, Ittsu, Honitsu, and Chinitsu apply open-hand han reductions. |
| Yaku combination filtering | Partial | Pinfu now combines with Iipeikou and Ryanpeikou, and yakuman results exclude non-yakuman yaku. Chiitoitsu combination handling is still too narrow. |
| Scoring calculations | Partial | Fu, han, limits, payment rounding, honba, kyoutaku, Kiriage Mangan, Noten Bappu, and Pao have support, with important bugs noted below. |
| Payment context | Mismatch | `ScoreCalculator.calculate()` computes payments before `payment_to` and `payment_from` are set, so dealer/non-dealer payment branches can be wrong. |
| Pinfu tsumo fu | Mismatch | `calculate_fu()` returns 30 fu for Pinfu tsumo; requirement says Pinfu tsumo is 20 fu. |
| Nagashi Mangan | Partial | One path scores Nagashi Mangan as mangan-like payments; `handle_ryuukyoku()` still applies a simplified +3000/-1000 transfer. |
| Renchan and round progression | Partial | Dealer win renchan exists, but exhaustive-draw dealer tenpai continuation is not implemented in `end_round()`. |
| Game-end conditions | Partial | Tobi, west round extension, and Agari Yame exist; end-round flow needs integration coverage. |
| Chombo | Missing | Config exists, but no complete violation detection and penalty flow was found. |

## Detailed Findings

### Initial Dealer Deal

- Requirement: the current dealer receives 14 tiles.
- Status: fixed.
- Code: `TileSet.deal()` accepts a dealer index and gives that player the extra tile. `RuleEngine.deal()` passes `GameState.dealer`.

### Kokushi Through Rule Engine

- Requirement: Kokushi Musou is a supported winning shape.
- Status: fixed.
- Code: `Hand.is_winning_hand()` supports Kokushi, and `RuleEngine.check_win()` now lets special hands without standard decompositions continue to `YakuChecker`.

### Four Identical Concealed Tiles

- Requirement: standard winning-hand detection should find legal decompositions.
- Status: fixed.
- Code: concealed hand decomposition now removes three identical tiles as a triplet and leaves any fourth copy available for other meld paths.

### Open-Hand Han Reductions

- Requirement: Sanshoku Doujun and Ittsu are 2 han closed and 1 han open; Honitsu is 3/2; Chinitsu is 6/5.
- Status: fixed.
- Code: `check_sanshoku_doujun()`, `check_ittsu()`, `check_honitsu()`, and `check_chinitsu()` now use `hand.is_concealed` to apply open-hand han reductions.

### Pinfu and Sequence Yaku

- Requirement: Pinfu can combine with Iipeikou and Ryanpeikou.
- Status: fixed.
- Code: `_filter_conflicting_yaku()` no longer removes Pinfu when Iipeikou or Ryanpeikou exists.

### Yakuman and Non-Yakuman Yaku

- Requirement: yakuman do not score with non-yakuman yaku.
- Status: fixed.
- Code: `YakuChecker.check_all()` returns only yakuman results once any yakuman is present.

### Chiitoitsu Combination Handling

- Requirement: Chiitoitsu can combine with compatible composition yaku.
- Code: the Chiitoitsu branch only adds Riichi, Double Riichi, and Ippatsu.
- Impact: compatible yaku such as Tanyao, Honitsu, Chinitsu, Honroutou, Menzen Tsumo, and dora-related han are not fully represented through yaku results.
- Suggested fix: evaluate compatible composition yaku for Chiitoitsu using tile composition, while still excluding standard-shape yaku.

### Payment Context

- Requirement: payment calculation must use the actual winner and payer.
- Code: `ScoreCalculator.calculate()` calls `calculate_payments()` before `RuleEngine.check_win()` sets `payment_to` and `payment_from`.
- Impact: non-dealer ron and tsumo payment branches can be calculated as if player 0 is the winner.
- Suggested fix: pass `payment_to` and `payment_from` into scoring before payment calculation, or defer payment calculation until after those fields are set.

### Pinfu Tsumo Fu

- Requirement: Pinfu tsumo is 20 fu.
- Code: `ScoreCalculator.calculate_fu()` returns 30 fu for Pinfu tsumo.
- Impact: Pinfu tsumo is over-scored.
- Suggested fix: return 20 fu for Pinfu tsumo and 30 fu for closed Pinfu ron.

### Nagashi Mangan Settlement

- Requirement: Nagashi Mangan is scored as mangan.
- Code: `end_round()` uses dealer/non-dealer mangan-like payments, but `handle_ryuukyoku()` applies a simplified +3000/-1000 transfer.
- Impact: behavior depends on which ryuukyoku path is used.
- Suggested fix: use one Nagashi Mangan settlement path and score it as mangan.

### Renchan on Exhaustive Draw

- Requirement: Exhaustive Draw causes renchan when the dealer is tenpai; otherwise the dealer rotates.
- Code: `end_round()` sets `dealer_won = False` for ryuukyoku and rotates the dealer unconditionally.
- Impact: dealer tenpai at Exhaustive Draw does not cause renchan.
- Suggested fix: determine dealer tenpai during exhaustive draw and pass that into dealer advancement.

### Riichi Furiten

- Requirement: passing ron after riichi creates permanent furiten.
- Code: passing a ron opportunity sets temp furiten, but `_furiten_permanent` is not set for riichi players.
- Impact: riichi furiten does not persist as required.
- Suggested fix: when a riichi player passes ron, set `_furiten_permanent[player] = True`.

### Pao Tracking

- Requirement: Pao responsibility is triggered when the final qualifying call confirms Daisangen or Daisuushi.
- Code: Pao payment support exists, but automatic responsibility tracking was not found; tests manually set `_pao_daisangen`.
- Impact: responsibility payment will not trigger naturally during normal play.
- Suggested fix: update call handling to detect when a call confirms Daisangen or Daisuushi and record the responsible player.

### Chombo

- Requirement: false win, invalid riichi, and penalties are handled.
- Code: `RulesetConfig` has `chombo_penalty_enabled`, but no complete chombo flow was found.
- Impact: violations are mostly rejected as invalid actions rather than handled as chombo penalties.
- Suggested fix: add explicit violation detection and penalty settlement.
