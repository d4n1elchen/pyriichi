# PyRiichi API Summary

This document provides a quick reference for the PyRiichi API.

## Core Classes

### 1. Tile System

#### `Tile`
Single mahjong tile.
- `suit`: tile suit.
- `rank`: tile rank, 1-9.
- `is_red_dora`: whether the tile is Red Dora.
- `is_honor`: whether the tile is an honor tile.
- `is_terminal`: whether the tile is a terminal tile.
- `is_simple`: whether the tile is a simple tile.

#### `TileSet`
Tile set manager.
- `shuffle()`: shuffle tiles.
- `deal(num_players=4)`: deal starting hands.
- `draw()`: draw a tile.
- `draw_rinshan()`: draw a rinshan tile.
- `get_dora_indicators(count=None)`: get dora indicators.
- `get_ura_dora_indicators(count=None)`: get Ura Dora indicators.
- `get_dora(indicator)`: get the dora tile from an indicator.

### 2. Hand Management

#### `Hand`
Hand manager.
- `add_tile(tile)`: add a drawn tile.
- `discard(tile)`: discard a tile.
- `can_chi(tile, from_player)`: check whether chi is possible.
- `chi(tile, sequence)`: perform chi.
- `can_pon(tile)`: check whether pon is possible.
- `pon(tile)`: perform pon.
- `can_kan(tile=None)`: check whether kan is possible.
- `kan(tile)`: perform kan.
- `is_tenpai()`: check whether the hand is tenpai.
- `get_machi_tiles()`: get machi tiles.
- `is_winning_hand(winning_tile)`: check whether the hand is winning.
- `get_winning_combinations(winning_tile, is_tsumo=False)`: get winning combinations.

#### `Meld`
Meld, including open triplets, open sequences, open kans, and closed kans.
- `type`: meld type.
- `tiles`: tile list.
- `called_tile`: called tile.
- `is_open`: whether the meld is open.

### 3. Game State

#### `GameState`
Game state manager.
- `round_wind`: current round_wind.
- `round_number`: current Round Number.
- `dealer`: dealer position.
- `seat_winds`: Seat Wind for each player.
- `honba`: honba count.
- `riichi_sticks`: Riichi Stick count.
- `scores`: player score list.
- `set_round(wind, number)`: set the round.
- `set_dealer(dealer)`: set the dealer.
- `next_round(dealer_won=False)`: advance to the next round.
- `update_score(player, points)`: update a player's score.

### 4. Rule Engine

#### `RuleEngine`
Game rule engine.
- `start_game()`: start a new game.
- `start_round()`: start a new round.
- `deal()`: deal tiles.
- `get_current_player()`: get the current player.
- `get_phase()`: get the game phase.
- `get_available_actions(player)`: get the player's available actions.
- `execute_action(player, action, tile=None, **kwargs)`: execute an action.
- `check_win(player, winning_tile, is_tsumo=False, **kwargs)`: check a win.
- `check_ryuukyoku()`: check ryuukyoku.
- `get_hand(player)`: get a player's hand.
- `get_discards(player)`: get a player's discards.
- `get_game_state()`: get the game state.
- `waiting_for_actions`: property containing players currently waiting for responses and their available actions.

#### `ActionResult`
Action execution result.
- `success`: whether the action succeeded.
- `phase`: current game phase.
- `drawn_tile`: drawn tile, for draw actions.
- `discarded`: whether a discard was executed.
- `winners`: winning player list.
- `win_results`: detailed win results.
- `ryuukyoku`: ryuukyoku result, when the round ended in a draw.
- `waiting_for`: players waiting for responses and their actions, `Dict[int, List[GameAction]]`.
- `message`: optional result message.

#### `GameAction` Enum
Game action types.
- `DRAW`: draw a tile, usually automatic except in special cases.
- `DISCARD`: discard a tile.
- `CHI`: chi.
- `PON`: pon.
- `KAN`: kan.
- `DECLARE_ANKAN`: declare closed kan.
- `DECLARE_RIICHI`: declare riichi.
- `DECLARE_KYUUSHU_KYUUHAI`: declare Kyuushu Kyuuhai.
- `WIN`: win.
- `TSUMO`: tsumo.
- `RON`: ron.
- `PASS`: pass on a call or ron opportunity.

#### `GamePhase` Enum
Game phases.
- `INIT`: initialization.
- `DEALING`: dealing.
- `PLAYING`: playing.
- `WINNING`: winning.
- `DRAW`: drawn round.
- `ENDED`: ended.

### 5. Yaku Detection

#### `YakuChecker`
Yaku detector.
- `check_all(hand, winning_tile, winning_combination, game_state, is_tsumo=False, is_ippatsu=False, is_first_turn=False, is_last_tile=False, player_position=0, is_rinshan=False)`: check all yaku.
- `check_riichi(hand, game_state, is_ippatsu=False)`: check Riichi and Ippatsu.
- `check_tanyao(hand, winning_combination)`: check Tanyao.
- `check_pinfu(hand, winning_combination)`: check Pinfu.
- `check_chiitoitsu(hand)`: check Chiitoitsu.
- `check_chanta(hand, winning_combination)`: check Chanta.
- Other yaku check methods.

#### `YakuResult`
Yaku detection result.
- `yaku`: yaku enum value.
- `han`: han value.
- `is_yakuman`: whether the yaku is yakuman.

### 6. Score Calculation

#### `ScoreCalculator`
Score calculator.
- `calculate(hand, winning_tile, winning_combination, yaku_results, dora_count, game_state, is_tsumo, player_position=0)`: calculate score.
- `calculate_fu(hand, winning_tile, winning_combination, yaku_results, game_state, is_tsumo, player_position=0)`: calculate fu.
- `calculate_han(yaku_results, dora_count)`: calculate han.

#### `ScoreResult`
Score calculation result.
- `han`: han value.
- `fu`: fu value.
- `base_points`: base points.
- `total_points`: total points.
- `payment_from`: paying player position.
- `payment_to`: receiving player position.
- `is_yakuman`: whether the hand is yakuman.
- `yakuman_count`: yakuman multiplier.
- `is_tsumo`: whether the win is tsumo.
- `dealer_payment`: dealer payment for tsumo.
- `non_dealer_payment`: non-dealer payment for tsumo.
- `honba_bonus`: honba bonus.
- `riichi_sticks_bonus`: kyoutaku distribution.
- `pao_player`: responsible player for pao, when applicable.
- `pao_payment`: pao payment amount.

### 7. AI Player System

#### `BasePlayer`
Player base class, abstract base class.
- `decide_action(game_state, player_index, hand, available_actions, public_info=None)`: decide the next action.

#### `RandomPlayer`
Random-action AI.
- Strategy: randomly choose legal actions, prioritizing wins.

#### `SimplePlayer`
Simple heuristic AI.
- Strategy: prioritize win, then riichi, then discard honors or terminals.

#### `DefensivePlayer`
Defensive AI.
- Strategy: when another player has declared riichi, prioritize genbutsu; otherwise use `SimplePlayer` behavior.

#### `PublicInfo`
Public game information.
- `discards`: discards for each player.
- `melds`: melds for each player.
- `riichi_players`: list of players who declared riichi.

## Utility Functions

### `parse_tiles(tile_string)`
Parse tiles from a string.
```python
tiles = parse_tiles("1m2m3m4p5p6p")
```

### `format_tiles(tiles)`
Format a tile list as a string.
```python
s = format_tiles([Tile(Suit.MANZU, 1), Tile(Suit.PINZU, 5)])
```

### `is_winning_hand(tiles, winning_tile)`
Quickly check whether the hand is winning.
```python
if is_winning_hand(tiles, winning_tile):
    print("Win!")
```

## Usage Example

```python
from pyriichi.rules import RuleEngine, GameAction, GamePhase
from pyriichi.player import RandomPlayer

# Initialize the game and players.
engine = RuleEngine(num_players=4)
players = [RandomPlayer(f"Player {i}") for i in range(4)]

engine.start_game()
engine.start_round()
engine.deal()

# Main game loop.
while engine.get_phase() == GamePhase.PLAYING:
    current_player_idx = engine.get_current_player()
    player = players[current_player_idx]

    # Get available actions.
    actions = engine.get_available_actions(current_player_idx)
    if not actions:
        break

    # Let the AI decide an action.
    action, tile = player.decide_action(
        engine.game_state,
        current_player_idx,
        engine.get_hand(current_player_idx),
        actions,
    )

    # Execute the action.
    engine.execute_action(current_player_idx, action, tile)
```

## Detailed Documentation

For complete API documentation, see `API_DESIGN.md`.
