# Technical Debt

This document tracks unresolved review findings that should be addressed in future fixes.

## P2: Ryuukyoku edge tests still mix engine behavior with subsystem setup

- Location: `tests/test_rule_ryuukyoku.py`
- Impact: Common ryuukyoku setup now has helpers, but fourth-kan and nagashi_mangan tests still set up `Hand`, `TileSet`, score state, and private `RuleEngine` fields in the same assertion path.
- Suggested fix: Add focused helpers for fourth-kan and nagashi_mangan scenarios so each test states only the draw rule variant it is checking.

## P2: Multi-ron and pao tests still use heavy private setup

- Location: `tests/test_rule_multiple_ron.py` and `tests/test_rule_pao.py`
- Impact: These tests are now in focused files, but they still build full hands and mutate private engine state to reach the target scenario.
- Suggested fix: Add scenario helpers for prepared ron, multi-ron, and pao states so each test states only the rule variant it is checking.
