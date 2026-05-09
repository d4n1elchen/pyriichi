# Technical Debt

This document tracks unresolved review findings that should be addressed in future fixes.

## P2: Rule tests still mix engine behavior with subsystem behavior

- Location: `tests/test_rule_winning_scoring.py`, `tests/test_rule_action_execution.py`, and `tests/test_rule_ryuukyoku.py`
- Impact: The rule tests are now split by topic, but several tests still set up `Hand`, `TileSet`, score state, private `RuleEngine` fields, and scoring/yaku expectations in the same assertion path. Failures in these tests can still come from hand parsing, action resolution, scoring, or yaku detection rather than the rule being tested.
- Suggested fix: When touching each area, move narrow scoring/yaku expectations into subsystem tests and keep the rule tests focused on engine state transitions and settlement side effects.

## P2: Winning and scoring rule assertions are still loose

- Location: `tests/test_rule_winning_scoring.py`
- Impact: Some tests assert `dora_count >= 0`, only check score-change direction, or depend on broad `result is not None` checks before the actual rule assertion. These can pass while the exact han, fu, winner list, or payment distribution is wrong.
- Suggested fix: Replace smoke checks with exact expected dora counts, winner lists, score deltas, and yaku/score fields. Start with `test_count_dora_one` and `test_triple_ron_enabled_all_win`.

## Test runner command clarity

- Location: project documentation and developer setup.
- Impact: `pytest` and `python` may not be available on `PATH` unless the virtual environment is activated. In this workspace, `.venv/bin/python -m pytest --collect-only -q` collects the suite successfully.
- Suggested fix: Document the canonical local test command after dependency installation, such as `.venv/bin/python -m pytest`, or require contributors to activate the virtual environment before running test commands.
