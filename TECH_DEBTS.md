# Technical Debt

This document tracks unresolved review findings that should be addressed in future fixes.

## P2: Rule coverage gaps remain after the health audit

- Location: `tests/test_yaku.py`, `tests/test_rule_riichi.py`, `tests/test_rule_action_execution.py`, `tests/test_rule_pao.py`, `tests/test_rule_round_settlement.py`, and `tests/test_scoring.py`
- Impact: The suite covers most rules, but several documented rules are either untested or only weakly tested: disabled or alternate ruleset flags, direct response-priority conflicts, riichi stick payment, kyoutaku carry, Daisuushi pao settlement, and tobi through normal win settlement.
- Suggested fix: Add focused tests for each missing rule branch before refactoring the related implementation. Replace broad smoke assertions with exact expected yaku, fu, han, payment, or state changes.

## P2: Rule docs have stale or underspecified edge cases

- Location: `rules/`, `README.md`, and `DEVELOPMENT_PLAN.md`
- Impact: `DEVELOPMENT_PLAN.md` claims Four Returns is implemented even though it is not in the canonical yaku list or `Yaku` enum. It also describes Nagashi Mangan differently from the canonical rule docs. The rule docs also omit current details for Kyuushu Kyuuhai restrictions, higher-scoring decomposition selection, closed-kan tile selection, pao trigger conditions, and ruleset flag mappings.
- Suggested fix: Align stale non-canonical docs with `rules/`, add a ruleset-variant table, and document implemented edge behavior that should be kept.

## P2: Win-context and furiten tests duplicate hand-built win contexts

- Location: `tests/test_rule_win_context.py` and `tests/test_rule_furiten.py`
- Impact: These tests repeatedly prepare the same ron, tsumo, chankan, and furiten states by mutating `_hands`, `_last_drawn_tile`, `_last_discarded_tile`, `_last_discarded_player`, `_current_player`, and furiten flags inline. That makes the tests longer than the behavior being asserted and makes failures hard to attribute to the rule under test.
- Suggested fix: Add focused scenario helpers for prepared ron, prepared tsumo, chankan, riichi furiten, temp_furiten, and discard furiten states. Keep each test body centered on the one rule outcome it is asserting.

## P2: Round-settlement tests mix settlement rules with manual score simulation

- Location: `tests/test_rule_round_settlement.py`
- Impact: The noten_bappu and exhaustive_draw tests repeat tenpai/noten hand setup and wall exhaustion inline. The tobi tests also mutate scores directly to simulate ron or tsumo payment, so they do not verify the win-settlement path that would normally create those score changes.
- Suggested fix: Extract helpers for tenpai/noten player sets, exhaustive_draw setup, and score deltas. Then decide whether tobi tests should remain direct `end_round` state tests or be moved to a win-settlement scenario that reaches bankruptcy through normal scoring.

## P2: Riichi interrupt tests are heavy action-flow fixtures

- Location: `tests/test_rule_riichi.py`
- Impact: The ippatsu interruption tests repeat riichi state setup, manufactured discard/call hands, and manual pass loops. These tests exercise action resolution, call availability, and riichi interruption all at once, so a failure may not point to the riichi rule itself.
- Suggested fix: Extract helpers for active ippatsu state, prepared discard calls, and draining pass actions. Keep one end-to-end action-flow test, and make the rest assert the riichi interruption behavior through narrower scenarios.

## P2: Kan tests still carry dense private setup and mixed concerns

- Location: `tests/test_rule_kan.py`
- Impact: Rinshan, chankan, suukan_sanra, open_kan, and closed_kan selection scenarios each build large engine states inline with `_hands`, `_tile_set`, `_waiting_for_actions`, `_kan_count`, and `_last_discarded_tile`. `TestClosedKanSelection` also constructs a one-player `RuleEngine` and edits `TileSet` internals directly, making it more of a fixture-construction test than a rule assertion.
- Suggested fix: Add scenario helpers for open_kan, closed_kan, rinshan, chankan, and exhausted-wall kan states. Consider moving closed_kan selection into a smaller hand/engine helper test or giving it a deterministic engine fixture.

## P3: Integration tests overlap unit coverage and contain conditional smoke flows

- Location: `tests/test_integration.py`
- Impact: Several integration tests repeat hand, yaku, and scoring assertions already covered by dedicated unit tests. Some game-flow tests branch on whatever actions are available after a live deal, which can make them assert only that the engine did not crash rather than a deterministic rule outcome.
- Suggested fix: Keep a small number of deterministic end-to-end smoke tests, remove or relocate duplicated hand/yaku/scoring cases, and replace live-deal conditional flows with fixed scenarios when the expected behavior matters.

## P3: Dora tests bundle separate cases into one mutable test

- Location: `tests/test_rule_dora.py`
- Impact: `test_count_dora_one` checks normal dora, ura_dora after riichi, and red_dora by mutating the same engine and hand setup in sequence. A failure in the middle can hide which dora path regressed.
- Suggested fix: Split normal dora, ura_dora, and red_dora into separate focused tests, with a helper for setting dora and ura_dora indicators.
