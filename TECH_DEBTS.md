# Technical Debt

This document tracks unresolved review findings that should be addressed in future fixes.

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
