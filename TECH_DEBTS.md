# Technical Debt

This document tracks unresolved review findings that should be addressed in future fixes.

## P1: Rule-engine unit tests need deterministic dora setup

- Location: `tests/test_rules.py`
- Impact: Several tests depend on shuffled `TileSet` dora indicators or clear `_dora_indicators` to `[]`. The production rules now require the initial dora indicator to exist and count it, so these tests can fail with accidental dora or with `ValueError` from missing indicators.
- Suggested fix: Add a small deterministic test helper, such as `set_dora_indicators(engine, indicators)` or `set_no_dora_for_hand(engine, hand_tiles)`, and update score-sensitive rule tests to use explicit non-matching indicators.

## P1: Double ron score tests are coupled to incidental dora

- Location: `tests/test_rules.py`
- Impact: Double ron tests assert fixed point deltas while using live shuffled dora indicators. If an indicator makes a winning tile dora, the expected score changes even though the double ron behavior is otherwise correct.
- Suggested fix: Fix dora determinism first, then update double ron expected scores only if they still fail.

## P2: Riichi noten fixture may now be tenpai

- Location: `tests/test_rules.py`
- Impact: `test_riichi_requires_discard_and_tenpai` expects one fixture to be noten, but current hand-search behavior appears to find a legal tenpai shape after the discard.
- Suggested fix: Replace the fixture with a clearly noten hand before changing riichi logic.

## P2: Integration test is random and flaky

- Location: `tests/test_integration.py:184-197`
- Impact: `test_game_flow_with_meld` uses a shuffled live round, discards, then assumes the same `current_player` can discard again. If the first discard creates interrupt actions, the player has no available discard action and the test fails nondeterministically.
- Suggested fix: Make the test deterministic by constructing hands/wall state directly, or update the flow to resolve or pass interrupts before expecting the next discard.

## Test runner command clarity

- Location: project documentation and developer setup.
- Impact: `pytest` and `python` may not be available on `PATH` unless the virtual environment is activated. In this workspace, `.venv/bin/python -m pytest --collect-only -q` collects the suite successfully.
- Suggested fix: Document the canonical local test command after dependency installation, such as `.venv/bin/python -m pytest`, or require contributors to activate the virtual environment before running test commands.
