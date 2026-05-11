# Technical Debt

This document tracks unresolved review findings that should be addressed in future fixes.

## Manual Rule Audit Findings

Last updated: 2026-05-11.

### Implementation Gaps

| Priority | Item | Status |
|----------|------|--------|
| P1 | Double-yakuman yaku are scored as single yakuman when they are the only yakuman result. | Open |
| P1 | Junchan rejects valid triplet/kan shapes. | Open |
| P2 | Kan Dora delayed reveal timing for daiminkan and added kan is not distinctly modeled. | Open |
| P2 | Double wind pair behavior is documented as ruleset-dependent but has no config. | Open |
| P2 | Red Dora are documented as enabled/disabled behavior but are always included in the standard tile set. | Open |
| P2 | Pao is documented as ruleset-supported behavior but has no config. | Open |
| P3 | Optional at/below-zero Tobi is documented but has no config or implementation. | Open |
| P3 | Invalid riichi timing differs between docs and implementation. | Open |

### Test Gaps

| Priority | Item | Status |
|----------|------|--------|
| P2 | Add exact standard tile-set composition tests. | Open |
| P2 | Add dealer-start/current-player test after initial deal. | Open |
| P2 | Add valid-shape no-yaku rejection test. | Open |
| P2 | Add dora-only no-yaku rejection test. | Open |
| P2 | Add direct Haneman limit test. | Open |
| P2 | Add custom Chanta/Junchan han config tests. | Open |
| P2 | Add natural Sancha Ron action-flow test. | Open |
| P3 | Add targeted furiten ron chombo/rejection test. | Open |
| P3 | Tighten conditional yaku tests into direct assertions where practical. | Open |
