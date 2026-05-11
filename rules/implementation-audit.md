# Implementation and Test Coverage Audit

This audit compares the current codebase against the rule requirements in this directory and the current test suite. It keeps met areas in the summary for context, then calls out documentation mismatches, implemented-but-underdocumented behavior, and test coverage gaps.

Last audit run: 2026-05-10.

Verification command:

```bash
.venv/bin/python -m pytest --cov=pyriichi --cov-report=term-missing
```

Latest full-suite result: 334 tests passed. The latest coverage audit measured total source line coverage at 88%.

## Coverage Summary

| Area | Implementation | Test Coverage | Notes |
|------|----------------|---------------|-------|
| Tile set and notation | Met | Met | Standard 136-tile set, Red Dora notation, sorting, tile set draw/deal, rinshan draw, dora indicator wrapping, and compact parsing are covered. |
| Initial deal and round setup | Met | Met | Dealer-aware deal sizes and basic phase transitions are covered. |
| Hand operations | Met | Met | Draw, discard, chi, pon, open kan, closed kan, open-kan upgrade, and meld validation are covered. |
| Winning-hand detection | Met | Met | Standard hands, open meld hands, kan hands, Chiitoitsu, Kokushi Musou, thirteen-sided Kokushi, tenpai, and machi listing are covered. |
| Action availability and priority | Met | Met | Basic availability, call execution, ron-over-call priority, and pon-over-chi priority are covered. |
| Multiple ron rules | Met | Met | Head Bump, Double Ron, Triple Ron, Sancha Ron, furiten filtering, and multi-ron settlement are covered. |
| Riichi action rules | Met | Met | Closed-hand/tenpai requirements, declaration payment, kyoutaku increment, declaration discard, remaining-wall rule, post-riichi discard lock, closed-kan wait preservation, and ippatsu interruption are covered. |
| Ippatsu | Met | Met | Interruption by chi, pon, kan, and closed kan is covered, including the disabled interruption ruleset variant. |
| Furiten | Met | Met | Genbutsu, temp furiten, riichi furiten, furiten tsumo, and multi-machi furiten are covered. |
| Kan and rinshan flow | Met | Met | Open kan, closed kan, rinshan, chankan, fourth-kan ryuukyoku, and fourth-kan win exceptions are covered with focused helpers. |
| Abortive and exhaustive draws | Met | Met | Suufon Renda, Kyuushu Kyuuhai, Suucha Riichi, Suukan Sanra, Sancha Ron, Exhaustive Draw, dealer continuation variants, and Nagashi Mangan are covered. |
| Yaku coverage | Met | Met | Listed yaku and yakuman have direct tests, including the currently supported yaku ruleset variants. |
| Yaku combination filtering | Met | Partial | Major exclusions and allowed combinations are covered, but some tests use conditional assertions that can pass without verifying the yaku if decomposition fails. |
| Fu and limit scoring | Met | Partial | Set fu, pair fu, wait fu, Chiitoitsu, Pinfu tsumo/ron, limits, payment rounding, Kiriage Mangan, and basic payments are covered. Some tests still assert broad smoke values rather than exact rule-table results. |
| Dora and Ura Dora | Met | Met | Visible dora, kan dora count, Ura Dora after riichi, and Red Dora are covered in focused tests. |
| Noten Bappu | Met | Met | One, two, three, all, and no tenpai payment splits are covered. |
| Honba and Kyoutaku | Met | Met | Honba, riichi-stick settlement, double-ron split behavior, and kyoutaku carry into a later single win are covered. |
| Pao | Met | Met | Daisangen and Daisuushi tracking and pao settlement are covered. |
| Round progression and game end | Met | Met | Dealer win renchan, exhaustive-draw renchan/rotation, tobi through normal win settlement and ryuukyoku settlement, west extension, and Agari Yame are covered. |
| Chombo | Met | Met | False ron, false tsumo, and invalid riichi chombo paths are covered. |
| Ruleset configuration | Met | Met | Pinfu ryanmen, Ippatsu interruption, Renhou policy, disabled double-yakuman variants, Chanta disabled, Open Tanyao, Kiriage Mangan, and game-end variants are covered. |

## Source Coverage Notes

The coverage run gives useful implementation-level signal, but it does not prove rule-level correctness by itself.

| Source File | Coverage | Notes |
|-------------|----------|-------|
| `pyriichi/rules.py` | 87% | Main remaining misses are edge branches in action validation, chombo and ryuukyoku variants, pao branches, and some ruleset alternatives. |
| `pyriichi/yaku.py` | 89% | Misses line up with failed-yaku branches and optional ruleset paths. |
| `pyriichi/scoring.py` | 92% | Mostly covered, with a few payment and fu edge branches still missed. |
| `pyriichi/hand.py` | 93% | Strong coverage; remaining misses are mostly defensive and invalid-operation branches. |
| `pyriichi/player.py` | 65% | Player strategy is much less covered than the rules engine. This is separate from rules correctness but worth tracking if player behavior matters. |

## Implemented but Missing or Underspecified in Rule Docs

| Behavior | Implementation Evidence | Rule Docs Status | Recommendation |
|----------|-------------------------|------------------|----------------|
| Discard history keeps only the last four entries. | `_discard_history` is capped in discard handling and tested in `tests/test_rule_action_execution.py`. | Not in rule docs. | Keep as an internal implementation detail for Suufon Renda detection. It does not need rule documentation unless public debugging/state APIs expose it. |
| `ScoreResult.total_points` may hold unrounded base points before `calculate_payments()`. | Kiriage Mangan tests construct `ScoreResult` directly and observe `1920` when Kiriage Mangan is disabled. | Rule docs describe final payment rounding, not internal `ScoreResult` lifecycle. | Keep internally, but clarify API docs or consider renaming if `ScoreResult` is treated as public API. |

## Stale or Conflicting Documentation

No stale or conflicting rule documentation is currently known from this audit.

## Test Coverage Gaps to Add

The focused rule-coverage and test-structure gaps from this audit have been closed. Future work can still tighten broad yaku and scoring smoke assertions as the suite evolves.

## Current Health Assessment

The rules engine has broad implementation and test coverage for modern riichi mahjong. The biggest remaining risks are not whole missing rule categories; they are optional ruleset branches and a few broad yaku or scoring smoke assertions that can be tightened when those areas are next touched.
