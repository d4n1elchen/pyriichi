# Technical Debt

This document tracks unresolved review findings that should be addressed in future fixes.

## P2: Rule tests still mix engine behavior with subsystem setup

- Location: `tests/test_rule_action_execution.py` and `tests/test_rule_ryuukyoku.py`
- Impact: The rule tests are now split by topic, but several tests still set up `Hand`, `TileSet`, score state, and private `RuleEngine` fields in the same assertion path. Failures in these tests can still come from hand parsing, action resolution, scoring, or yaku detection rather than the rule being tested.
- Suggested fix: When touching each area, extract focused helpers and keep the rule tests centered on engine state transitions and settlement side effects.

## P2: Multi-ron and pao tests still use heavy private setup

- Location: `tests/test_rule_multiple_ron.py` and `tests/test_rule_pao.py`
- Impact: These tests are now in focused files, but they still build full hands and mutate private engine state to reach the target scenario.
- Suggested fix: Add scenario helpers for prepared ron, multi-ron, and pao states so each test states only the rule variant it is checking.
