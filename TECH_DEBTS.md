# Technical Debt

This document tracks unresolved review findings that should be addressed in future fixes.

## P3: Integration tests overlap unit coverage and contain conditional smoke flows

- Location: `tests/test_integration.py`
- Impact: Several integration tests repeat hand, yaku, and scoring assertions already covered by dedicated unit tests. Some game-flow tests branch on whatever actions are available after a live deal, which can make them assert only that the engine did not crash rather than a deterministic rule outcome.
- Suggested fix: Keep a small number of deterministic end-to-end smoke tests, remove or relocate duplicated hand/yaku/scoring cases, and replace live-deal conditional flows with fixed scenarios when the expected behavior matters.

## P3: Dora tests bundle separate cases into one mutable test

- Location: `tests/test_rule_dora.py`
- Impact: `test_count_dora_one` checks normal dora, ura_dora after riichi, and red_dora by mutating the same engine and hand setup in sequence. A failure in the middle can hide which dora path regressed.
- Suggested fix: Split normal dora, ura_dora, and red_dora into separate focused tests, with a helper for setting dora and ura_dora indicators.
