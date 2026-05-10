# Technical Debt

This document tracks unresolved review findings that should be addressed in future fixes.

## P2: Multi-ron and pao tests still use heavy private setup

- Location: `tests/test_rule_multiple_ron.py` and `tests/test_rule_pao.py`
- Impact: These tests are now in focused files, but they still build full hands and mutate private engine state to reach the target scenario.
- Suggested fix: Add scenario helpers for prepared ron, multi-ron, and pao states so each test states only the rule variant it is checking.
