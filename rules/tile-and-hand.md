# Tile and Hand Rules

## Tile Set

- The engine uses a standard 136-tile Japanese riichi mahjong set.
- Manzu: ranks 1-9, four copies each, 36 tiles total.
- Pinzu: ranks 1-9, four copies each, 36 tiles total.
- Souzu: ranks 1-9, four copies each, 36 tiles total.
- Honors:
  - Winds: east, south, west, north, four copies each, 16 tiles total.
  - Dragons: haku, hatsu, chun, four copies each, 12 tiles total.
- The standard tile set includes one red five in each number suit.

## Tile Representation

- Tiles must have stable suit and rank identifiers.
- Tiles must support comparison and sorting.
- Tiles must support compact string notation for display, examples, tests, and debugging.
- Red Dora notation uses the `r5m`, `r5p`, and `r5s` format.

## Tile Set Operations

- Shuffle.
- Deal initial hands.
- Draw from the live wall.
- Draw rinshan tiles from the dead wall.
- Track dora indicators and Ura Dora indicators.
- Query remaining live wall tiles.

## Initial Deal

- Each player receives 13 tiles.
- The current dealer receives 14 tiles.
- The active player at the start of the round is the current dealer.

## Hand Representation

- A hand tracks concealed tiles, melds, discards, riichi state, and the last drawn tile when needed.
- Melds include chi, pon, open kan, and closed kan.
- Closed kans do not make the hand open.

## Hand Operations

- Discard.
- Chi: claim a sequence from kamicha.
- Pon: claim a triplet.
- Kan: claim or declare a kan.
- Declare closed kan. When multiple closed kans are legal, the declaring action may specify which tile to use.
- Tenpai detection.
- Machi tile listing.
- Winning-hand detection.

## Winning Conditions

- Standard shape: four sets plus one pair.
- Special shapes: Chiitoitsu and Kokushi Musou.
- Optional special shapes may be added through explicit ruleset support.
- The winning hand must have at least one yaku.

## Tenpai Detection

- Determine whether the current hand is tenpai.
- List all machi tiles.
- Preserve correct behavior for standard hands, Chiitoitsu, and Kokushi Musou.
