# Rule Requirements

This directory contains the riichi-rule-specific requirements for PyRiichi. Project-level, AI, quality, and testing requirements remain in [../REQUIREMENTS.md](../REQUIREMENTS.md).

## Files

- [Tile and Hand Rules](tile-and-hand.md): tile set, tile notation, hand operations, tenpai, and winning shapes.
- [Game Flow and Call Rules](game-flow.md): turn flow, action priority, furiten, kan timing, abortive draws, and chombo.
- [Yaku Rules](yaku.md): standard yaku, yakuman, optional yaku variants, and yaku combination rules.
- [Scoring Rules](scoring.md): fu, han, limits, payments, honba, kyoutaku, noten bappu, and pao.
- [Round and Game State Rules](round-state.md): round winds, seat winds, renchan, game end, tobi, west round extension, and agari yame.
- [Implementation Audit](implementation-audit.md): current code status against these requirements.

## Scope

Rules in this directory describe common modern Japanese riichi mahjong behavior, with ruleset-dependent variants called out explicitly. When implementation behavior intentionally differs from these requirements, the variant should be represented in `RulesetConfig` and documented here.
