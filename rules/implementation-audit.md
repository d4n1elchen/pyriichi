# Implementation and Test Coverage Audit

This audit compares the current codebase against the rule requirements in this directory and the current test suite. It keeps met areas in the summary for context, then calls out documentation mismatches, implementation gaps, and test gaps.

Last manual audit run: 2026-05-11.

Audit method: manual traceability review from each rule document item to implementation and tests. Coverage data was not used.

## Coverage Summary

| Area | Implementation | Test Coverage | Notes |
|------|----------------|---------------|-------|
| Tile set and notation | Met | Partial | Standard tile set, Red Dora notation, sorting, draw/deal, rinshan draw, dora indicator wrapping, and compact parsing are covered. Missing exact tile-composition assertions. |
| Initial deal and round setup | Met | Partial | Dealer-aware deal sizes are covered. Add a direct test that the dealer is the current/waiting player after deal. |
| Hand operations | Met | Met | Draw, discard, chi, pon, open kan, closed kan, open-kan upgrade, and meld validation are covered. |
| Winning-hand detection | Met | Met | Standard hands, open meld hands, kan hands, Chiitoitsu, Kokushi Musou, thirteen-sided Kokushi, tenpai, and machi listing are covered. |
| Action availability and priority | Met | Met | Basic availability, call execution, ron-over-call priority, and pon-over-chi priority are covered. Natural Sancha Ron action availability needs a focused check. |
| Multiple ron rules | Met | Partial | Head Bump, Double Ron, Triple Ron, Sancha Ron, furiten filtering, and multi-ron settlement are covered. Natural Sancha Ron action flow is weaker than direct helper-driven tests. |
| Riichi action rules | Met | Met | Closed-hand/tenpai requirements, declaration payment, kyoutaku increment, declaration discard, declaration-discard ron rollback, remaining-wall rule, post-riichi discard lock, closed-kan wait preservation, invalid-riichi handling, and ippatsu interruption are covered. |
| Ippatsu | Met | Met | Interruption by chi, pon, kan, and closed kan is covered, including the disabled interruption ruleset variant. |
| Furiten | Met | Met | Genbutsu, temp furiten, riichi furiten, furiten tsumo, and multi-machi furiten are covered. |
| Kan and rinshan flow | Met | Met | Open kan, closed kan, rinshan, chankan, kan dora indicator counting, fourth-kan ryuukyoku, and fourth-kan win exceptions are covered with the engine's immediate kan-dora-count convention. |
| Abortive and exhaustive draws | Met | Met | Suufon Renda, Kyuushu Kyuuhai, Suucha Riichi, Suukan Sanra, Sancha Ron, Exhaustive Draw, dealer continuation variants, and Nagashi Mangan are covered. |
| Yaku coverage | Met | Partial | Listed yaku and yakuman mostly have tests, including Junchan terminal triplet shapes. Several yaku tests still use conditional assertions. |
| Yaku combination filtering | Met | Partial | Major exclusions and allowed combinations are covered, but some tests use conditional assertions that can pass without verifying the yaku if decomposition fails. |
| Fu and limit scoring | Met | Partial | Set fu, pair fu, wait fu, Chiitoitsu, Pinfu tsumo/ron, limits, payment rounding, Kiriage Mangan, double-yakuman multipliers, and basic payments are covered. Shabo is not represented as a distinct machi type, Haneman lacks a direct test, and many payment tests are broad smoke assertions. |
| Dora and Ura Dora | Met | Met | Visible dora, kan dora count, Ura Dora after riichi, and Red Dora are covered in focused tests. |
| Noten Bappu | Met | Met | One, two, three, all, and no tenpai payment splits are covered. |
| Honba and Kyoutaku | Met | Met | Honba, riichi-stick settlement, double-ron split behavior, and kyoutaku carry into a later single win are covered. |
| Pao | Met | Met | Daisangen and Daisuushi tracking and pao settlement are covered. |
| Round progression and game end | Met | Met | Dealer win renchan, exhaustive-draw renchan/rotation, below-zero Tobi through normal win settlement and ryuukyoku settlement, west extension, and Agari Yame are covered. |
| Chombo | Met | Partial | False ron, false tsumo, and invalid riichi chombo paths are covered. Add targeted furiten-ron chombo/rejection tests. |
| Ruleset configuration | Met | Partial | Pinfu ryanmen, Ippatsu interruption, Renhou policy, disabled double-yakuman variants, Chanta disabled, Open Tanyao, Kiriage Mangan, and game-end variants are covered. Custom Chanta/Junchan han values still need direct tests. |

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

| Gap | Recommendation |
|-----|----------------|
| Tile set composition | Assert exact 136-tile composition and per-tile counts. |
| Dealer start after deal | Assert current/waiting player is the dealer after initial deal. |
| No-yaku win rejection | Add a valid-shape no-yaku hand that `check_win` rejects. |
| Dora-only no-yaku rejection | Add a dora-only hand that remains non-winning without yaku. |
| Shabo machi | Add direct shabo detection or document that only fu effect is represented. |
| Haneman | Add direct Haneman limit test. |
| Custom Chanta/Junchan han | Add tests for non-default config values. |
| Conditional yaku assertions | Replace conditional yaku tests with direct constructed-combination assertions where practical. |
| Natural Sancha Ron action flow | Add an end-to-end action-flow test for Triple Ron disabled. |
| Furiten ron chombo/rejection | Add targeted test for declaring ron while furiten. |

## Current Health Assessment

The rules engine has broad implementation and test coverage for modern riichi mahjong. The biggest remaining risks are test-quality issues: remaining broad smoke assertions, a few missing direct edge-case tests, and conditional yaku tests that can pass without proving the intended yaku.
