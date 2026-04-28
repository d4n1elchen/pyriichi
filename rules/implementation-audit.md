# Implementation Audit

This audit compares the current codebase against the rule requirements in this directory.
Fixed findings are intentionally removed from this document so it stays focused on unresolved work.

Status values:

- **Partial**: the code has support, but behavior is incomplete, simplified, or has a known edge-case issue.
- **Missing**: no implementation was found.
- **Mismatch**: implementation contradicts the requirement.

## Summary

| Area | Status | Suggested fix |
|------|--------|---------------|
| Chombo | Missing | Add an explicit chombo result and mangan-level penalty flow for false win and invalid riichi when enabled by `RulesetConfig`. |
| Dora indicator count | Mismatch | Count the initial dora indicator plus one additional indicator per kan when scoring dora and ura dora. |
| Abortive draw settlement | Partial | Apply a consistent round-settlement path for abortive draws, including dealer continuation and honba handling. |
| Open Tanyao configuration | Partial | Add a ruleset option for Open Tanyao and reject open Tanyao when the option is disabled. |

## Detailed Findings

### Chombo

- Requirement: false win, invalid riichi, and penalties are handled when the ruleset enables chombo penalties.
- Code: `RulesetConfig` has `chombo_penalty_enabled`, but invalid wins and invalid riichi are mostly rejected as invalid actions.
- Impact: callers cannot distinguish ordinary invalid actions from chombo, and score penalties are not applied.
- Suggested fix: add an explicit chombo result, apply mangan-level penalty payments, and end the hand in ryuukyoku/chombo state.

### Dora Indicator Count

- Requirement: the first dora indicator is always active, and each kan reveals one additional dora indicator.
- Code: `_count_dora()` passes `_kan_count` into `get_dora_indicators()` and `get_ura_dora_indicators()`, so zero kan means zero visible indicators and one kan means only the initial indicator.
- Impact: hands can be under-scored by missing initial dora and kan dora.
- Suggested fix: use `1 + _kan_count` for dora and ura-dora indicator count, capped by the available indicators.

### Abortive Draw Settlement

- Requirement: abortive draws end the hand and update round state according to the active continuation rule.
- Code: `handle_ryuukyoku()` reports abortive draw types but does not share the same dealer/honba progression path as `end_round()`.
- Impact: direct abortive-draw handling can leave dealer, honba, and round number stale.
- Suggested fix: add a shared ryuukyoku settlement helper and call it from abortive-draw handlers.

### Open Tanyao Configuration

- Requirement: Open Tanyao is ruleset-dependent.
- Code: `check_tanyao()` always allows open hands and `RulesetConfig` has no Open Tanyao option.
- Impact: rulesets that disable Open Tanyao cannot be represented.
- Suggested fix: add `open_tanyao_enabled` to `RulesetConfig` and apply it in Tanyao checking.
