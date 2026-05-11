# Implementation and Test Coverage Audit

This audit compares the current codebase against the rule requirements in this directory and the current test suite. It keeps met areas in the summary for context, then calls out documentation mismatches, implementation gaps, and test gaps.

Last manual audit run: 2026-05-11.

Audit method: manual traceability review from each rule document item to implementation and tests. Coverage data was not used.

## Coverage Summary

| Area | Implementation | Test Coverage | Notes |
|------|----------------|---------------|-------|
| Tile set and notation | Met | Partial | Standard tile set, Red Dora notation, sorting, draw/deal, rinshan draw, dora indicator wrapping, and compact parsing are covered. Missing exact tile-composition assertions, and Red Dora enablement wording does not match implementation. |
| Initial deal and round setup | Met | Partial | Dealer-aware deal sizes are covered. Add a direct test that the dealer is the current/waiting player after deal. |
| Hand operations | Met | Met | Draw, discard, chi, pon, open kan, closed kan, open-kan upgrade, and meld validation are covered. |
| Winning-hand detection | Met | Met | Standard hands, open meld hands, kan hands, Chiitoitsu, Kokushi Musou, thirteen-sided Kokushi, tenpai, and machi listing are covered. |
| Action availability and priority | Met | Met | Basic availability, call execution, ron-over-call priority, and pon-over-chi priority are covered. Natural Sancha Ron action availability needs a focused check. |
| Multiple ron rules | Met | Partial | Head Bump, Double Ron, Triple Ron, Sancha Ron, furiten filtering, and multi-ron settlement are covered. Natural Sancha Ron action flow is weaker than direct helper-driven tests. |
| Riichi action rules | Met | Met | Closed-hand/tenpai requirements, declaration payment, kyoutaku increment, declaration discard, declaration-discard ron rollback, remaining-wall rule, post-riichi discard lock, closed-kan wait preservation, and ippatsu interruption are covered. Invalid-riichi timing differs from the current docs. |
| Ippatsu | Met | Met | Interruption by chi, pon, kan, and closed kan is covered, including the disabled interruption ruleset variant. |
| Furiten | Met | Met | Genbutsu, temp furiten, riichi furiten, furiten tsumo, and multi-machi furiten are covered. |
| Kan and rinshan flow | Partial | Met | Open kan, closed kan, rinshan, chankan, fourth-kan ryuukyoku, and fourth-kan win exceptions are covered. Kan Dora delayed reveal timing for daiminkan and added kan is not distinctly modeled. |
| Abortive and exhaustive draws | Met | Met | Suufon Renda, Kyuushu Kyuuhai, Suucha Riichi, Suukan Sanra, Sancha Ron, Exhaustive Draw, dealer continuation variants, and Nagashi Mangan are covered. |
| Yaku coverage | Partial | Partial | Listed yaku and yakuman mostly have tests. Junchan does not accept valid triplet/kan shapes, and several yaku tests use conditional assertions. |
| Yaku combination filtering | Met | Partial | Major exclusions and allowed combinations are covered, but some tests use conditional assertions that can pass without verifying the yaku if decomposition fails. |
| Fu and limit scoring | Partial | Partial | Set fu, pair fu, wait fu, Chiitoitsu, Pinfu tsumo/ron, limits, payment rounding, Kiriage Mangan, and basic payments are covered. Single double-yakuman yaku are scored as single yakuman, shabo is not represented as a distinct machi type, Haneman lacks a direct test, and many payment tests are broad smoke assertions. |
| Dora and Ura Dora | Met | Met | Visible dora, kan dora count, Ura Dora after riichi, and Red Dora are covered in focused tests. |
| Noten Bappu | Met | Met | One, two, three, all, and no tenpai payment splits are covered. |
| Honba and Kyoutaku | Met | Met | Honba, riichi-stick settlement, double-ron split behavior, and kyoutaku carry into a later single win are covered. |
| Pao | Met | Met | Daisangen and Daisuushi tracking and pao settlement are covered. |
| Round progression and game end | Partial | Met | Dealer win renchan, exhaustive-draw renchan/rotation, tobi through normal win settlement and ryuukyoku settlement, west extension, and Agari Yame are covered. Optional at/below-zero Tobi wording has no implementation/config. |
| Chombo | Met | Partial | False ron, false tsumo, and invalid riichi chombo paths are covered. Add targeted furiten-ron chombo/rejection tests. |
| Ruleset configuration | Partial | Partial | Pinfu ryanmen, Ippatsu interruption, Renhou policy, disabled double-yakuman variants, Chanta disabled, Open Tanyao, Kiriage Mangan, and game-end variants are covered. Double-wind pair, Red Dora enablement, Pao enablement, and at/below-zero Tobi are documented as variant-like behavior but do not have config fields. |

## Implementation Gaps

| Requirement | Current State | Recommendation |
|-------------|---------------|----------------|
| Double yakuman scoring | `ScoreCalculator` counts each yakuman result as one yakuman, ignoring single yaku results worth 26 han. | Count yakuman multipliers from yaku result han values and add exact tests for Suuankou Tanki, Kokushi Musou Juusanmen, Pure Chuuren Poutou, and combined yakuman. |
| Junchan shape | `check_junchan` only recognizes all-sequence shapes. | Accept triplets and kans whose tiles are terminal-only, while still rejecting honors and non-terminal sets. Add direct tests. |
| Kan Dora timing | Kan count immediately affects dora indicator count for all kan types. | Model delayed reveal timing for daiminkan and added kan, or adjust docs if this simplified timing is intentional. |
| Double wind pair variant | Docs call the behavior ruleset-dependent; implementation always awards both round_wind and seat_wind fu. | Add a config flag or revise docs to the implemented behavior. |
| Red Dora enablement | Docs say red fives apply when enabled; standard tile set always includes one red five per suit. | Add tile-set configuration or revise docs to standardize always-on Red Dora. |
| Pao enablement | Docs say Pao applies when the ruleset supports it; implementation always supports it. | Add a config flag or revise docs to the implemented behavior. |
| Optional at/below-zero Tobi | Docs mention optional at/below-zero Tobi; implementation checks only scores below zero. | Add a config flag or revise docs to the implemented behavior. |
| Invalid riichi timing | Docs describe invalid riichi discovered at ryuukyoku; implementation rejects/applies chombo immediately. | Decide the intended behavior and align docs/tests or engine behavior. |

## Implemented but Missing or Underspecified in Rule Docs

| Behavior | Implementation Evidence | Rule Docs Status | Recommendation |
|----------|-------------------------|------------------|----------------|
| Discard history keeps only the last four entries. | `_discard_history` is capped in discard handling and tested in `tests/test_rule_action_execution.py`. | Not in rule docs. | Keep as an internal implementation detail for Suufon Renda detection. It does not need rule documentation unless public debugging/state APIs expose it. |
| `ScoreResult.total_points` may hold unrounded base points before `calculate_payments()`. | Kiriage Mangan tests construct `ScoreResult` directly and observe `1920` when Kiriage Mangan is disabled. | Rule docs describe final payment rounding, not internal `ScoreResult` lifecycle. | Keep internally, but clarify API docs or consider renaming if `ScoreResult` is treated as public API. |

## Stale or Conflicting Documentation

| Doc Item | Conflict |
|----------|----------|
| Red Dora enablement | `tile-and-hand.md` says Red Dora are represented when enabled, but the standard tile set always includes them. |
| Double wind pair | `scoring.md` says behavior is ruleset-dependent, but there is no config flag. |
| Pao | `scoring.md` says Pao applies when the ruleset supports it, but there is no config flag. |
| Tobi | `round-state.md` mentions an optional at/below-zero rule, but there is no config flag. |
| Invalid riichi | `game-flow.md` says invalid riichi is discovered at ryuukyoku, while the engine handles it immediately. |

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

The rules engine has broad implementation and test coverage for modern riichi mahjong. The biggest remaining risks are specific: double-yakuman scoring, Junchan shape recognition, Kan Dora timing semantics, and variant wording/config mismatches. The test suite should also replace remaining broad smoke assertions with exact rule assertions where possible.
