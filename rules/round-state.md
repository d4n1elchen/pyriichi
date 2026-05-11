# Round and Game State Rules

## Round Management

- East round: East 1, East 2, East 3, East 4.
- South round: South 1, South 2, South 3, South 4.
- West round extension is ruleset-dependent.
- round_wind is the wind of the current round.
- seat_wind is each player's seat wind: east, south, west, or north.

## Player State

- Initial score is 25000 points unless configured otherwise.
- Track riichi state.
- Track fully concealed state.
- Track open meld state.
- Track discards and called discards.

## Game State

- Current turn player.
- Current dealer.
- Honba count.
- Kyoutaku count.
- Remaining live wall tiles.
- Ryuukyoku state.
- Ruleset configuration.

## Renchan and Counters

- Dealer win causes renchan and increments honba.
- Exhaustive Draw causes renchan when the dealer is tenpai; otherwise the dealer rotates.
- Abortive draw dealer-continuation behavior is ruleset-dependent.
- Kyoutaku carries forward until the next winning hand.

## Game-End Conditions

- Normal end: complete the scheduled rounds, such as ending after South 4.
- Tobi: any player's score drops below 0.
- West round extension: if nobody reaches the target score, usually 30000, after South 4, extend into the west round.
- Agari Yame: when the last-round dealer wins while in first place, they may choose to end the game.
