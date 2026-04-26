# Technical Debt

This document tracks review findings that should be addressed in future fixes.

## P1: Payments are calculated before winner/loser are set

- Location: `pyriichi/scoring.py:259-273`
- Impact: `ScoreCalculator.calculate` creates a `ScoreResult` with `payment_from=0` and `payment_to=0`, then immediately calls `calculate_payments`. `RuleEngine` sets the real winner and payer only after the calculation, so non-dealer wins can be scored using dealer payment branches.
- Suggested fix: Pass `payment_to` and `payment_from` into score calculation before `calculate_payments`, or defer payment calculation until after `RuleEngine` has populated those fields.

## P1: Kokushi is rejected by the game engine

- Location: `pyriichi/rules.py:1355-1358`
- Impact: `Hand.is_winning_hand` can accept Kokushi Musou, but `RuleEngine.check_win` returns `None` when `get_winning_combinations` is empty. Since Kokushi has no standard 4-meld-1-pair decomposition, it never reaches `YakuChecker`.
- Suggested fix: Allow special hands with empty standard combinations to continue through yaku checking, similarly to Chiitoitsu handling.

## P1: Four identical concealed tiles block legal decompositions

- Location: `pyriichi/hand.py:670-682`
- Impact: The standard hand search treats a concealed count of four as a kan and removes all four tiles. In an undeclared hand, four identical tiles must also be searchable as a triplet plus one remaining tile. For example, `1111m23m234p234s55z` winning `3m` should be valid, but currently reports no win.
- Suggested fix: When count is four in concealed decomposition, try removing three tiles as a triplet as well as any declared-kan path where appropriate.

## P2: Pinfu is incorrectly removed when Iipeikou/Ryanpeikou exists

- Location: `pyriichi/yaku.py:451-455`
- Impact: Pinfu can legally combine with Iipeikou and Ryanpeikou, but the conflict filter removes Pinfu whenever either sequence yaku appears. This undercounts valid sequence hands by one han.
- Suggested fix: Remove this conflict rule. Keep only real exclusions, such as Iipeikou being superseded by Ryanpeikou.

## P2: Open-hand han reductions are missing for common yaku

- Location: `pyriichi/yaku.py:812-940`
- Impact: Sanshoku Doujun, Ittsu, Chinitsu, and Honitsu return fixed closed-hand han values even when `hand.is_concealed` is false. Open hands are over-scored.
- Suggested fix: Apply open-hand reductions according to the active ruleset or standard defaults:
  - Sanshoku Doujun: closed 2, open 1
  - Ittsu: closed 2, open 1
  - Honitsu: closed 3, open 2
  - Chinitsu: closed 6, open 5

## P2: Integration test is random and flaky

- Location: `tests/test_integration.py:184-197`
- Impact: `test_game_flow_with_meld` uses a shuffled live round, discards, then assumes the same `current_player` can discard again. If the first discard creates interrupt actions, the player has no available discard action and the test fails nondeterministically.
- Suggested fix: Make the test deterministic by constructing hands/wall state directly, or update the flow to resolve/pass interrupts before expecting the next discard.

## Test runner import issue

- Location: test environment
- Impact: Running `pytest -q` from the repo root via the standalone pytest entrypoint failed collection with `ModuleNotFoundError: pyriichi`, while `PYTHONPATH=/Users/daniel/Code/pyriichi pytest -q` and `python -m pytest -q` reached the suite.
- Suggested fix: Add a pytest configuration or editable-install developer setup instructions so local test commands resolve the package consistently.
