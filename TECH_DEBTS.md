# Technical Debt

This document tracks unresolved review findings that should be addressed in future fixes.

## P3: Dora tests bundle separate cases into one mutable test

- Location: `tests/test_rule_dora.py`
- Impact: `test_count_dora_one` checks normal dora, ura_dora after riichi, and red_dora by mutating the same engine and hand setup in sequence. A failure in the middle can hide which dora path regressed.
- Suggested fix: Split normal dora, ura_dora, and red_dora into separate focused tests, with a helper for setting dora and ura_dora indicators.
