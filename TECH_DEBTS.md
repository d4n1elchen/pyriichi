# Technical Debt

This document tracks unresolved review findings that should be addressed in future fixes.

## P1: `tests/test_rules.py` is an oversized integration harness

- Location: `tests/test_rules.py`
- Impact: The file contains 126 tests and hundreds of direct private-state mutations, so small internal changes can break unrelated tests and obscure whether a failure is in rules, scoring, hand logic, wall setup, or action resolution.
- Suggested fix: Split the file into focused modules such as action execution, action availability, furiten, ryuukyoku, multi-ron, scoring-in-engine, and game-end tests. Move shared setup into `tests/helpers.py`.

## P2: Unit tests often exercise multiple modules at once

- Location: `tests/test_scoring.py`, `tests/test_yaku.py`, and `tests/test_rules.py`
- Impact: Many nominal unit tests instantiate multiple major subsystems, such as `Hand`, `YakuChecker`, `ScoreCalculator`, `TileSet`, and `RuleEngine`. This makes failures harder to localize and encourages broad fixture setup for narrow behavior.
- Suggested fix: Keep direct subsystem tests narrow, and move cross-module behavior into integration or engine-level test files with explicit naming.

## P2: Rule tests duplicate setup helpers

- Location: `tests/test_rules.py`
- Impact: Multiple classes define their own `setup_method()` and `_init_game()` methods, increasing drift and making changes to game setup tedious.
- Suggested fix: Extract shared helpers for engine initialization, deterministic dora setup, hand replacement, response resolution, and wall exhaustion.

## P3: Some assertions are smoke checks rather than rule checks

- Location: `tests/`
- Impact: Assertions such as `result is not None`, `dora_count >= 0`, or score deltas only checking direction can pass while important rule details are wrong.
- Suggested fix: Tighten assertions when touching each test area, especially for scoring and action-resolution behavior.

## P2: Integration test is random and flaky

- Location: `tests/test_integration.py:184-197`
- Impact: `test_game_flow_with_meld` uses a shuffled live round, discards, then assumes the same `current_player` can discard again. If the first discard creates interrupt actions, the player has no available discard action and the test fails nondeterministically.
- Suggested fix: Make the test deterministic by constructing hands/wall state directly, or update the flow to resolve or pass interrupts before expecting the next discard.

## Test runner command clarity

- Location: project documentation and developer setup.
- Impact: `pytest` and `python` may not be available on `PATH` unless the virtual environment is activated. In this workspace, `.venv/bin/python -m pytest --collect-only -q` collects the suite successfully.
- Suggested fix: Document the canonical local test command after dependency installation, such as `.venv/bin/python -m pytest`, or require contributors to activate the virtual environment before running test commands.
