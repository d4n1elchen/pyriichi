# Technical Debt

This document tracks unresolved review findings that should be addressed in future fixes.

## P2: Unit tests often exercise multiple modules at once

- Location: `tests/test_scoring.py`, `tests/test_yaku.py`, and `tests/test_rule_*.py`
- Impact: Many nominal unit tests instantiate multiple major subsystems, such as `Hand`, `YakuChecker`, `ScoreCalculator`, `TileSet`, and `RuleEngine`. This makes failures harder to localize and encourages broad fixture setup for narrow behavior.
- Suggested fix: Keep direct subsystem tests narrow, and move cross-module behavior into integration or engine-level test files with explicit naming.

## P3: Some assertions are smoke checks rather than rule checks

- Location: `tests/`
- Impact: Assertions such as `result is not None`, `dora_count >= 0`, or score deltas only checking direction can pass while important rule details are wrong.
- Suggested fix: Tighten assertions when touching each test area, especially for scoring and action-resolution behavior.

## P2: Integration test is random and flaky

- Location: `tests/test_integration.py`
- Impact: `test_game_flow_with_meld` uses a shuffled live round, discards, then assumes the same `current_player` can discard again. If the first discard creates interrupt actions, the player has no available discard action and the test fails nondeterministically.
- Suggested fix: Make the test deterministic by constructing hands/wall state directly, or update the flow to resolve or pass interrupts before expecting the next discard.

## Test runner command clarity

- Location: project documentation and developer setup.
- Impact: `pytest` and `python` may not be available on `PATH` unless the virtual environment is activated. In this workspace, `.venv/bin/python -m pytest --collect-only -q` collects the suite successfully.
- Suggested fix: Document the canonical local test command after dependency installation, such as `.venv/bin/python -m pytest`, or require contributors to activate the virtual environment before running test commands.
