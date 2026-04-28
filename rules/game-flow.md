# Game Flow and Call Rules

## Basic Flow

1. Deal 13 tiles to each player and 14 tiles to the current dealer.
2. The current player draws or starts with a 14-tile dealer hand.
3. The current player discards one tile or declares a legal win or kan.
4. Other players may respond to a discard with ron, pon, kan, chi, or pass.
5. The highest-priority response is resolved.
6. The next turn proceeds from the player who took the action.
7. The round ends on win, ryuukyoku, abortive draw, or game-end condition.

## Response Priority

- Ron has priority over calls.
- Pon and kan have priority over chi.
- Chi is only available to shimocha.
- When multiple players may ron the same discard, resolve according to the active multi-win rule:
  - Head Bump.
  - Double Ron.
  - Triple Ron.
  - Sancha Ron abortive draw when Triple Ron is disabled.

## Riichi Action Rules

- Riichi requires a closed hand.
- Riichi requires tenpai after the declaration discard.
- The player must pay one Riichi Stick.
- The declaration must meet the ruleset's remaining-wall requirement.
- After riichi, the player must discard the drawn tile unless a legal closed kan is allowed.
- After riichi, closed kan is legal only when it does not change machi tiles.

## Ippatsu Interruption

- Ippatsu is available after riichi until the player wins or the first uninterrupted turn passes.
- Chi, pon, kan, or closed kan interrupts Ippatsu when the ruleset enables that behavior.

## Furiten

- Genbutsu furiten: a player cannot ron on a tile if any of their own previous discards is one of their machi tiles.
- Temp Furiten: after a player passes on a winning tile, they cannot ron during the same turn cycle.
- Riichi furiten: after declaring riichi, passing on a winning tile creates permanent furiten; the player may still win by tsumo.

## Kan and Dora Timing

- Closed kan reveals a kan dora indicator immediately.
- Daiminkan and added kan reveal the kan dora indicator after the discard, or after Rinshan when applicable.
- A kan draw uses a rinshan tile from the dead wall.
- Chankan may apply to added kan.
- Suukan Sanra is checked after the fourth kan unless a valid win on the fourth kan prevents the abortive draw.

## Ryuukyoku and Abortive Draws

- Exhaustive Draw: live wall is exhausted.
- Nagashi Mangan: special draw score when all of a player's discards are yaochuu and none are called.
- Suufon Renda: all first discards are the same wind.
- Kyuushu Kyuuhai: a player has at least nine unique yaochuu tiles on their first turn and no calls have occurred.
- Suucha Riichi: all four players declare riichi.
- Suukan Sanra: four kans are declared without a qualifying win.
- Sancha Ron: three players ron the same discard when Triple Ron is disabled.

## Chombo Handling

- False win: declaring a win while not tenpai, declaring ron while furiten, and similar violations.
- Invalid riichi: declaring riichi while not tenpai, discovered at ryuukyoku.
- Penalty behavior is ruleset-dependent; common handling is a mangan-level penalty or only rejecting the illegal action.
