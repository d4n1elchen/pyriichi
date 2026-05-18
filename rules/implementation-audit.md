# Implementation and Test Coverage Audit

This audit compares the current codebase against the rule requirements in this directory and the current test suite. It keeps met areas in the summary for context, then calls out documentation mismatches, implementation gaps, and test gaps.

Last manual audit run: 2026-05-12.

Audit method: manual traceability review from each rule document item to implementation and tests. Coverage data was not used.

## Coverage Summary

| Area | Implementation | Test Coverage | Notes |
|------|----------------|---------------|-------|
| Tile set and notation | Met | Met | Standard tile set composition, Red Dora notation, sorting, draw/deal, rinshan draw, dora indicator wrapping, and compact parsing are covered. |
| Initial deal and round setup | Met | Met | Dealer-aware deal sizes and dealer-current-player setup are covered. |
| Hand operations | Met | Met | Draw, discard, chi, pon, open kan, closed kan, open-kan upgrade, and meld validation are covered. |
| Winning-hand detection | Met | Met | Standard hands, open meld hands, kan hands, Chiitoitsu, Kokushi Musou, thirteen-sided Kokushi, tenpai, machi listing, and discard-to-tenpai hints are covered. |
| Action availability and priority | Met | Met | Basic availability, call execution, ron-over-call priority, pon-over-chi priority, and Sancha Ron action availability are covered. |
| Multiple ron rules | Met | Met | Head Bump, Double Ron, Triple Ron, Sancha Ron, furiten filtering, and multi-ron settlement are covered. |
| Riichi action rules | Met | Met | Closed-hand/tenpai requirements, declaration payment, kyoutaku increment, declaration discard, declaration-discard ron rollback, remaining-wall rule, post-riichi drawn-tile discard lock, closed-kan wait preservation, invalid-riichi handling, and ippatsu interruption are covered. |
| Ippatsu | Met | Met | Interruption by chi, pon, kan, and closed kan is covered, including the disabled interruption ruleset variant. |
| Furiten | Met | Met | Genbutsu, temp furiten, riichi furiten, furiten tsumo, and multi-machi furiten are covered. |
| Kan and rinshan flow | Met | Met | Open kan, closed kan, rinshan, chankan, kan dora indicator counting, fourth-kan ryuukyoku, and fourth-kan win exceptions are covered with the engine's immediate kan-dora-count convention. |
| Abortive and exhaustive draws | Met | Met | Suufon Renda, Kyuushu Kyuuhai, Suucha Riichi, Suukan Sanra, Sancha Ron, Exhaustive Draw, dealer continuation variants, and Nagashi Mangan are covered. |
| Yaku coverage | Met | Met | Listed yaku and yakuman have tests, including direct checks for Junchan terminal triplet shapes and representative constructed-combination assertions. |
| Yaku combination filtering | Met | Met | Major exclusions and allowed combinations are covered, with direct assertions for the audited conditional Iipeikou and Sanshoku Doujun cases. |
| Fu and limit scoring | Met | Met | Set fu, pair fu, wait fu, Chiitoitsu, Pinfu tsumo/ron, shabo machi, limits, Haneman, payment rounding, Kiriage Mangan, double-yakuman multipliers, and basic payments are covered. |
| Dora and Ura Dora | Met | Met | Visible dora, kan dora count, Ura Dora after riichi, and Red Dora are covered in focused tests. |
| Noten Bappu | Met | Met | One, two, three, all, and no tenpai payment splits are covered. |
| Honba and Kyoutaku | Met | Met | Honba, riichi-stick settlement, double-ron split behavior, and kyoutaku carry into a later single win are covered. |
| Pao | Met | Met | Daisangen and Daisuushi tracking and pao settlement are covered. |
| Round progression and game end | Met | Met | Dealer win renchan, exhaustive-draw renchan/rotation, below-zero Tobi through normal win settlement and ryuukyoku settlement, west extension, and Agari Yame are covered. |
| Chombo | Met | Met | False ron, false tsumo, furiten ron, and invalid riichi chombo paths are covered. |
| Ruleset configuration | Met | Met | Pinfu ryanmen, Ippatsu interruption, Renhou policy, disabled double-yakuman variants, Chanta disabled, custom Chanta/Junchan han values, Open Tanyao, Kiriage Mangan, and game-end variants are covered. |

## Implementation Gaps

No unresolved implementation gaps are currently known from this audit.

## Implemented but Missing or Underspecified in Rule Docs

| Behavior | Implementation Evidence | Rule Docs Status | Recommendation |
|----------|-------------------------|------------------|----------------|
| Discard history keeps only the last four entries. | `_discard_history` is capped in discard handling and tested in `tests/test_rule_action_execution.py`. | Not in rule docs. | Keep as an internal implementation detail for Suufon Renda detection. It does not need rule documentation unless public debugging/state APIs expose it. |
| `ScoreResult.total_points` may hold unrounded base points before `calculate_payments()`. | Kiriage Mangan tests construct `ScoreResult` directly and observe `1920` when Kiriage Mangan is disabled. | Rule docs describe final payment rounding, not internal `ScoreResult` lifecycle. | Keep internally, but clarify API docs or consider renaming if `ScoreResult` is treated as public API. |

## Stale or Conflicting Documentation

No stale or conflicting rule documentation is currently known from this audit.

## Test Coverage Gaps to Add

No unresolved test coverage gaps are currently known from this audit.

## Current Health Assessment

The rules engine has broad implementation and test coverage for modern riichi mahjong. This audit does not currently track unresolved implementation gaps, stale rule documentation, or specific missing test coverage.
