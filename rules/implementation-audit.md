# Implementation and Test Coverage Audit

This audit compares the current codebase against the rule requirements in this directory and the current test suite. It keeps met areas in the summary for context, then calls out documentation mismatches, implemented-but-underdocumented behavior, and test coverage gaps.

Last audit run: 2026-05-10.

Verification command:

```bash
.venv/bin/python -m pytest --cov=pyriichi --cov-report=term-missing
```

Latest full-suite result: 342 tests passed. The latest coverage audit measured total source line coverage at 88%.

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
| Kan and rinshan flow | Met | Partial | Open kan, closed kan, rinshan, chankan, fourth-kan ryuukyoku, and fourth-kan win exceptions are covered. The tests still depend on dense private setup. |
| Abortive and exhaustive draws | Met | Met | Suufon Renda, Kyuushu Kyuuhai, Suucha Riichi, Suukan Sanra, Sancha Ron, Exhaustive Draw, dealer continuation variants, and Nagashi Mangan are covered. |
| Yaku coverage | Met | Met | Listed yaku and yakuman have direct tests, including the currently supported yaku ruleset variants. |
| Yaku combination filtering | Met | Partial | Major exclusions and allowed combinations are covered, but some tests use conditional assertions that can pass without verifying the yaku if decomposition fails. |
| Fu and limit scoring | Met | Partial | Set fu, pair fu, wait fu, Chiitoitsu, Pinfu tsumo/ron, limits, payment rounding, Kiriage Mangan, and basic payments are covered. Some tests still assert broad smoke values rather than exact rule-table results. |
| Dora and Ura Dora | Met | Partial | Visible dora, kan dora count, Ura Dora after riichi, and Red Dora are covered. Normal dora, Ura Dora, and Red Dora should be split into separate focused tests. |
| Noten Bappu | Met | Met | One, two, three, all, and no tenpai payment splits are covered. |
| Honba and Kyoutaku | Met | Met | Honba, riichi-stick settlement, double-ron split behavior, and kyoutaku carry into a later single win are covered. |
| Pao | Met | Met | Daisangen and Daisuushi tracking and pao settlement are covered. |
| Round progression and game end | Met | Partial | Dealer win renchan, exhaustive-draw renchan/rotation, tobi, west extension, and Agari Yame are covered. Tobi tests mostly mutate scores directly rather than reaching bankruptcy through normal win settlement. |
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
| Suucha Riichi applies a 300-point transfer from dealer to each non-dealer before settlement. | `RuleEngine.handle_ryuukyoku()` special-cases `RyuukyokuType.SUUCHA_RIICHI`. | Not documented in `rules/game-flow.md`, `rules/scoring.md`, or `rules/round-state.md`. | Do not keep as default standard behavior unless this is intended as a local rule. Standard four-riichi abortive draw should not have this 300-point dealer payment. Prefer removing it or adding a ruleset flag and documenting it as a local variant. |
| Kyuushu Kyuuhai requires the declaring player's first turn, no player melds including closed kan, no prior discard by the declaring player, and at least nine unique yaochuu. | `_check_kyuushu_kyuuhai()` in `RuleEngine`. | `rules/game-flow.md` lists only first turn, nine unique yaochuu, and no calls. | Keep. These are useful precision guards and should be documented in `rules/game-flow.md`. |
| Engine chooses the highest-scoring winning interpretation for ambiguous hands. | `tests/test_rule_scoring_selection.py` covers an ambiguous hand selecting the higher-scoring result. | Not explicitly documented in `rules/scoring.md` or `rules/tile-and-hand.md`. | Keep. This is expected scoring behavior when a hand has multiple decompositions; document it in scoring rules. |
| Closed-kan action can choose which quad to declare when multiple quads are present. | `tests/test_rule_kan.py::TestClosedKanSelection`. | `rules/tile-and-hand.md` says closed kan exists, but does not specify multiple-quad selection. | Keep. It is important API/UI behavior; document that explicit tile selection is supported when multiple closed kans are legal. |
| Discard history keeps only the last four entries. | `_discard_history` is capped in discard handling and tested in `tests/test_rule_action_execution.py`. | Not in rule docs. | Keep as an internal implementation detail for Suufon Renda detection. It does not need rule documentation unless public debugging/state APIs expose it. |
| `ScoreResult.total_points` may hold unrounded base points before `calculate_payments()`. | Kiriage Mangan tests construct `ScoreResult` directly and observe `1920` when Kiriage Mangan is disabled. | Rule docs describe final payment rounding, not internal `ScoreResult` lifecycle. | Keep internally, but clarify API docs or consider renaming if `ScoreResult` is treated as public API. |

## Stale or Conflicting Documentation

| Item | Location | Issue | Recommendation |
|------|----------|-------|----------------|
| Four Returns | `README.md` and `DEVELOPMENT_PLAN.md` | README says Four Returns is disabled; DEVELOPMENT_PLAN says Four Returns is implemented. It is not listed in canonical `rules/yaku.md`, and no `Yaku` enum entry exists. | Treat this as stale non-canonical documentation. Remove the implemented claim from DEVELOPMENT_PLAN and keep Four Returns out of the canonical rule list unless a real local-yakuman feature is added. |
| Nagashi Mangan condition | `rules/game-flow.md` and `DEVELOPMENT_PLAN.md` | Canonical rules say every discard is yaochuu and none are called. DEVELOPMENT_PLAN says it requires tenpai and all winning tiles to be terminals/honors. | Keep the canonical rule-doc version and update/remove the stale DEVELOPMENT_PLAN claim. |
| Ruleset-dependent behavior | `rules/*.md` | Several rules are marked ruleset-dependent without listing current default, supported alternatives, and config flag names. | Add a ruleset-variant table that maps docs to `RulesetConfig` fields. |
| Pao trigger details | `rules/scoring.md` | Payment split is documented, but final-call responsibility assignment is not. | Document Daisangen and Daisuushi responsibility trigger conditions. |

## Test Coverage Gaps to Add

Priority order for new tests:

1. Tobi through normal win settlement, not only direct score mutation.
2. Exact scoring table assertions where tests currently use broad `> 0`, `>= 30`, or similar smoke assertions.
3. Replace conditional yaku assertions such as `if combinations:` with explicit setup assertions so decomposition regressions fail loudly.

## Current Health Assessment

The rules engine has broad implementation and test coverage for modern riichi mahjong. The biggest remaining risks are not whole missing rule categories; they are optional ruleset branches, exact settlement paths, and documentation drift around edge rules. The test suite is strong enough to protect the core engine, but several tests still verify outcomes indirectly through large private fixtures or broad smoke assertions.
