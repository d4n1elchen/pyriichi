# PyRiichi Requirements

This document keeps project-level requirements that are not specific riichi rules. Rule requirements are split into focused files under `rules/`.

## System Overview

PyRiichi is a Japanese riichi mahjong game engine. It provides tile and hand modeling, rule adjudication, yaku detection, scoring, round flow, configurable rulesets, and simple AI players.

## Rule Requirement Documents

- [Rules Overview](rules/README.md)
- [Tile and Hand Rules](rules/tile-and-hand.md)
- [Game Flow and Call Rules](rules/game-flow.md)
- [Yaku Rules](rules/yaku.md)
- [Scoring Rules](rules/scoring.md)
- [Round and Game State Rules](rules/round-state.md)
- [Implementation Audit](rules/implementation-audit.md)

## AI Players, Optional Feature

### Basic AI

- Simple discard strategy.
- Basic tenpai detection.
- Basic winning-hand detection.

### Advanced AI

- Tile-efficiency calculation.
- Defensive strategy.
- Offensive strategy.
- Riichi decision.
- Call decision.

## Non-Functional Requirements

### Performance Requirements

- Hand detection response time < 100 ms.
- Yaku detection response time < 500 ms.
- Support continuous multi-round games.

### Maintainability

- Clear code structure.
- Complete documentation.
- Unit test coverage > 80%.
- Rule behavior should be covered by focused tests near the subsystem that implements it.

### Extensibility

- Modular design.
- Easy to add new yaku.
- Easy to modify rules through `RulesetConfig`.
- New rule terms must follow [GLOSSARY.md](GLOSSARY.md).

### Testability

- All core features have corresponding tests.
- Test cases cover edge cases.
- Ruleset variants should have direct tests for enabled and disabled behavior.

## Technical Implementation Requirements

### Data Structures

- Use enums or constants to represent tile types, actions, phases, yaku, and ruleset variants.
- Use lists or sets to manage hands, melds, discards, waits, and winning decompositions.
- Use dictionaries or structured objects to manage game state, pending actions, and score deltas.

### Algorithms

- Winning-hand detection may use recursion, backtracking, or equivalent search.
- Yaku detection should use explicit rule matching.
- Tenpai detection should enumerate possible winning tile transformations.

### Error Handling

- Validate input actions.
- Reject illegal actions with clear exceptions or failure results.
- Keep error messages understandable for developers using the engine.

## Testing Requirements

### Unit Tests

- Tile set operation tests.
- Hand operation tests.
- Yaku detection tests.
- Score calculation tests.
- Ruleset configuration tests.

### Integration Tests

- Complete game flow tests.
- Special-case tests, such as ryuukyoku and yakuman.
- Multi-module tests for hand, yaku, scoring, and rule engine interactions.

### Boundary Tests

- Extreme case handling.
- Invalid input handling.
- Round-end and wall-exhaustion behavior.
- Multiple winner and ruleset-variant behavior.
