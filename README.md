# PyRiichi - Python Riichi Mahjong Engine

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A full-featured Python Japanese riichi mahjong game engine with rule implementation, yaku detection, score calculation, and game-flow management.

## Features

- 🎴 **Complete tile system** - Supports the standard 136-tile mahjong set, including Red Dora and dora calculation.
- 🎯 **Winning-hand detection** - Accurate winning-hand detection for standard and special shapes.
- 🏆 **Yaku system** - Implements standard yaku such as Riichi, Tanyao, Pinfu, and yakuman.
- 💰 **Score calculation** - Accurate fu, han, and point calculation following Japanese riichi mahjong rules.
- 🎮 **Game engine** - Complete game-flow control, including chi, pon, kan, riichi, and related operations.
- 📊 **State management** - Round Number, winds, honba, kyoutaku, and other game-state management.
- 🤖 **AI players** - Built-in AI strategies: random, simple heuristic, and defensive, with automatic game support.
- ⚙️ **Ruleset configuration** - Supports standard competitive rules and custom rulesets.
- 🔧 **Easy integration** - Clear API design for integration into other applications.

## Project Info

- **Project status**: Development Status :: 3 - Alpha
- **Keywords**: mahjong, riichi, japanese, game, engine
- **Homepage**: <https://github.com/d4n1elchen/pyriichi>
- **Documentation**: <https://github.com/d4n1elchen/pyriichi#readme>
- **Issues**: <https://github.com/d4n1elchen/pyriichi/issues>
- **Source**: <https://github.com/d4n1elchen/pyriichi>

## Installation

```bash
pip install pyriichi
```

Or install from source:

```bash
git clone https://github.com/d4n1elchen/pyriichi.git
cd pyriichi
pip install -e .
```

## Quick Start

### Basic Usage

```python
from pyriichi.rules import RuleEngine, GameAction, GamePhase
from pyriichi.player import RandomPlayer

# Initialize the game and players.
engine = RuleEngine(num_players=4)
players = [RandomPlayer(f"Player {i}") for i in range(4)]

engine.start_game()
engine.start_round()
engine.deal()

print(f"Game started. Current phase: {engine.get_phase()}")

# Main game loop.
while engine.get_phase() == GamePhase.PLAYING:
    current_player_idx = engine.get_current_player()
    player = players[current_player_idx]

    # Get available actions.
    actions = engine.get_available_actions(current_player_idx)
    if not actions:
        break

    # Check whether there are pending interrupt actions such as calls or ron.
    if engine.waiting_for_actions:
        for pid, p_actions in engine.waiting_for_actions.items():
            # Handle interrupt logic here.
            pass
        continue

    # Let the AI decide an action.
    action, tile = player.decide_action(
        engine.game_state,
        current_player_idx,
        engine.get_hand(current_player_idx),
        actions,
    )

    print(f"Player {current_player_idx} executes: {action.name}" + (f" {tile}" if tile else ""))

    # Execute the action.
    result = engine.execute_action(current_player_idx, action, tile)

    # Check the result.
    if result.winners:
        print("Win!")
        break
```

### Tile Representation and Operations

#### String Notation

PyRiichi uses compact string notation for mahjong tiles, making input and display convenient.

**Basic format**: `number + suit letter`

- **Manzu**: use `m`.
  - `1m` = one manzu, `2m` = two manzu, ..., `9m` = nine manzu.

- **Pinzu**: use `p`.
  - `1p` = one pinzu, `2p` = two pinzu, ..., `9p` = nine pinzu.

- **Souzu**: use `s`.
  - `1s` = one souzu, `2s` = two souzu, ..., `9s` = nine souzu.

- **Honors**: use `z`.
  - `1z` = east, `2z` = south, `3z` = west, `4z` = north.
  - `5z` = haku, `6z` = hatsu, `7z` = chun.

**Red Dora notation**: use the `r` prefix.
- `r5p` = red five pinzu.
- `r5s` = red five souzu.
- `r5m` = red five manzu.

**Note**: This is the standard format widely used in the Japanese mahjong community. Input and output both use the `r5p` style.

**Examples**:
```python
from pyriichi import Tile, Suit, TileSet, parse_tiles, format_tiles

# Create one tile.
tile = Tile(Suit.MANZU, 1)
print(tile)  # Output: 1m

# Parse tiles from a string.
tiles = parse_tiles("1m2m3m4p5p6p7s8s9s")
print(format_tiles(tiles))  # Output: 1m2m3m4p5p6p7s8s9s

# Parse tiles with Red Dora, using the standard r5p format.
red_dora_tiles = parse_tiles("r5p6p7p")
print(format_tiles(red_dora_tiles))  # Output: r5p6p7p

# Parse honors.
honor_tiles = parse_tiles("1z2z3z5z6z7z")
print(format_tiles(honor_tiles))  # Output: 1z2z3z5z6z7z

# Create and shuffle a tile set.
tile_set = TileSet()
tile_set.shuffle()
hands = tile_set.deal()  # Deal to 4 players.
```

**Notes**:
- Strings may contain spaces or other characters; `parse_tiles()` skips invalid characters automatically.
- Multiple tiles can be written continuously, such as `"1m2m3m"` for three manzu tiles.
- Use `format_tiles()` to convert a tile list back to string notation.
- **Red Dora format**: use the standard `r5p` format with an `r` prefix. Input and output are consistent and support round-trip conversion.

### Game Flow Control

```python
from pyriichi import RuleEngine, GameAction

engine = RuleEngine()
engine.start_game()
engine.start_round()
engine.deal()

# Draw.
current_player = engine.get_current_player()
result = engine.execute_action(current_player, GameAction.DRAW)
if result.drawn_tile is not None:
    print(f"Drew: {result.drawn_tile}")

# Discard.
hand = engine.get_hand(current_player)
if hand.tiles:
    discard_tile = hand.tiles[0]
    engine.execute_action(current_player, GameAction.DISCARD, tile=discard_tile)

# Check win.
winning_result = engine.check_win(current_player, winning_tile)
if winning_result:
    print(f"Win! Han: {winning_result.han}, fu: {winning_result.fu}")
    print(f"Score: {winning_result.points}")
```

### Hand Operations

```python
from pyriichi import Hand, parse_tiles

# Create a hand.
tiles = parse_tiles("1m2m3m4p5p6p7s8s9s1z2z3z4z")
hand = Hand(tiles)

# Draw.
from pyriichi import Tile, Suit
new_tile = Tile(Suit.MANZU, 5)
hand.add_tile(new_tile)

# Discard.
hand.discard(new_tile)

# Check tenpai.
if hand.is_tenpai():
    machi_tiles = hand.get_machi_tiles()
    print(f"Machi tiles: {machi_tiles}")

# Check winning hand.
winning_tile = Tile(Suit.MANZU, 1)
if hand.is_winning_hand(winning_tile):
    combinations = hand.get_winning_combinations(winning_tile)
    print(f"Number of winning combinations: {len(combinations)}")
    if combinations:
        # get_winning_combinations returns List[List[Combination]].
        winning_combination = combinations[0]
        print("First winning combination:", winning_combination)
```

### Calls

```python
from pyriichi import Hand, Tile, Suit

hand = Hand([...])  # Hand tiles.

# Check pon.
tile = Tile(Suit.PINZU, 5)
if hand.can_pon(tile):
    meld = hand.pon(tile)
    print(f"Pon: {meld}")

# Check chi, which can only be called from kamicha.
if hand.can_chi(tile, from_player=0):  # 0 means kamicha.
    sequences = hand.can_chi(tile, from_player=0)
    if sequences:
        meld = hand.chi(tile, sequences[0])
        print(f"Chi: {meld}")
```

### Yaku Detection

```python
from pyriichi import YakuChecker, Hand, GameState, parse_tiles
from pyriichi.tiles import Tile, Suit

yaku_checker = YakuChecker()

# Create a winning hand.
tiles = parse_tiles("1m2m3m4p5p6p7s8s9s2m3m4m5p")
hand = Hand(tiles)
winning_tile = Tile(Suit.PINZU, 5)

# Get winning combinations. Convert the first combination to a list when needed.
winning_combinations = hand.get_winning_combinations(winning_tile)
if winning_combinations:
    winning_combination = list(winning_combinations[0])

    game_state = GameState(num_players=4)

    # Check all yaku.
    yaku_results = yaku_checker.check_all(
        hand=hand,
        winning_tile=winning_tile,
        winning_combination=winning_combination,
        game_state=game_state,
        is_tsumo=True,
        player_position=0,
    )

    for result in yaku_results:
        print(f"{result.yaku.en}: {result.han} han")

# Check a specific yaku.
riichi_results = yaku_checker.check_riichi(hand, game_state, is_ippatsu=True)
for result in riichi_results:
    print(f"{result.yaku.en}: {result.han} han")
```

### Score Calculation

```python
from pyriichi import ScoreCalculator, YakuChecker, Hand, GameState, parse_tiles
from pyriichi.tiles import Tile, Suit

score_calculator = ScoreCalculator()
yaku_checker = YakuChecker()

# Create a winning hand.
tiles = parse_tiles("1m2m3m4p5p6p7s8s9s2m3m4m5p")
hand = Hand(tiles)
winning_tile = Tile(Suit.PINZU, 5)

# Get winning combinations. Convert the first combination to a list when needed.
winning_combinations = hand.get_winning_combinations(winning_tile)
if winning_combinations:
    winning_combination = winning_combinations[0]

    game_state = GameState(num_players=4)

    # Check yaku first.
    yaku_results = yaku_checker.check_all(
        hand=hand,
        winning_tile=winning_tile,
        winning_combination=winning_combination,
        game_state=game_state,
        is_tsumo=True,
        player_position=0,
    )

    dora_count = 0
    is_tsumo = True

    # Calculate score.
    score_result = score_calculator.calculate(
        hand=hand,
        winning_tile=winning_tile,
        winning_combination=winning_combination,
        yaku_results=yaku_results,
        dora_count=dora_count,
        game_state=game_state,
        is_tsumo=is_tsumo,
        player_position=0,
    )

    print(f"Han: {score_result.han}")
    print(f"Fu: {score_result.fu}")
    print(f"Base points: {score_result.base_points}")
    print(f"Total points: {score_result.total_points}")
    print(f"Yakuman: {score_result.is_yakuman}")
    print(f"Tsumo: {score_result.is_tsumo}")
```

### Game State Management

```python
from pyriichi import GameState, Wind

# Create a game state with the default standard competitive rules.
game_state = GameState(num_players=4)

# Set the round.
game_state.set_round(Wind.EAST, 1)  # East 1.
game_state.set_dealer(0)  # Player 0 is dealer.

# Query state.
print(f"Current round: {game_state.round_wind} {game_state.round_number}")
print(f"Dealer: Player {game_state.dealer}")
print(f"Honba: {game_state.honba}")
print(f"Riichi sticks: {game_state.riichi_sticks}")

# Update score.
game_state.update_score(0, 1000)  # Player 0 gains 1000 points.
print(f"Player scores: {game_state.scores}")

# Advance to the next round.
game_state.next_round()
```

### Ruleset Configuration

PyRiichi supports standard competitive rules and custom ruleset configuration.

```python
from pyriichi import GameState, RulesetConfig
from pyriichi.rules_config import RenhouPolicy

# 1. Use the default standard competitive rules.
game_state = GameState(num_players=4)
# game_state.ruleset is already RulesetConfig.standard().

# 2. Custom ruleset configuration.
custom_ruleset = RulesetConfig(
    renhou_policy=RenhouPolicy.YAKUMAN,  # Renhou is yakuman.
    pinfu_require_ryanmen=False,  # Pinfu does not require ryanmen.
    chanta_enabled=True,
    chanta_closed_han=2,  # Chanta closed: 2 han.
    chanta_open_han=1,  # Chanta open: 1 han.
    junchan_closed_han=3,  # Junchan closed: 3 han.
    junchan_open_han=2,  # Junchan open: 2 han.
    suuankou_tanki_double=False,  # Suuankou Tanki is single yakuman.
    pure_chuuren_poutou_double=False,  # Pure Chuuren Poutou is single yakuman.
)
game_state_custom = GameState(num_players=4, ruleset=custom_ruleset)

# Ruleset configuration affects yaku detection.
print(f"Renhou policy: {game_state.ruleset.renhou_policy.value}")  # Standard: "two_han".
print(f"Pinfu requires ryanmen: {game_state.ruleset.pinfu_require_ryanmen}")  # Standard: True.
```

**Standard competitive rule characteristics**:
- Renhou is 2 han, not yakuman.
- Pinfu must be ryanmen.
- Chanta: closed 2 han, open 1 han.
- Junchan: closed 3 han, open 2 han.
- Suuankou Tanki is double yakuman, 26 han.
- Four Returns is disabled.

### Complete Game Example

```python
from pyriichi import RuleEngine, GameAction, GamePhase

# Initialize the game.
engine = RuleEngine(num_players=4)
engine.start_game()
engine.start_round()
engine.deal()

# Main game loop.
max_turns = 100  # Prevent infinite loops.
turn_count = 0

while engine.get_phase() == GamePhase.PLAYING and turn_count < max_turns:
    turn_count += 1
    current_player = engine.get_current_player()

    # Draw.
    result = engine.execute_action(current_player, GameAction.DRAW)
    if result.draw:
        # Ryuukyoku.
        print("Ryuukyoku")
        break

    hand = engine.get_hand(current_player)
    drawn_tile = result.drawn_tile

    # Check win by tsumo.
    if drawn_tile:
        win_result = engine.check_win(current_player, drawn_tile)
        if win_result:
            print(f"Player {current_player} wins by tsumo!")
            print(f"Han: {win_result.han}, fu: {win_result.fu}")
            print(f"Score: {win_result.points}")
            break

    # Check whether riichi can be declared.
    if GameAction.DECLARE_RIICHI in engine.get_available_actions(current_player):
        # Add player riichi decision logic here.
        # For example: if hand.is_tenpai() and player_decision():
        pass

    # Discard, using a simple strategy: discard the first tile.
    if hand.tiles:
        discard_tile = hand.tiles[0]
        engine.execute_action(current_player, GameAction.DISCARD, tile=discard_tile)
        print(f"Player {current_player} discards: {discard_tile}")

print("Game ended")
```

## Core API

### Main Classes

- **`RuleEngine`** - Game rule engine that manages the full game flow.
- **`Hand`** - Hand manager that handles hand operations and detection.
- **`TileSet`** - Tile set manager that handles dealing and shuffling.
- **`GameState`** - Game state manager for rounds, scores, and related state.
- **`YakuChecker`** - Yaku detector that checks all yaku.
- **`ScoreCalculator`** - Score calculator for fu, han, and points.
- **`RulesetConfig`** - Ruleset configuration class for standard competitive rules and custom rules.
- **`BasePlayer`** - Base class for AI players.

### AI Players

PyRiichi includes several built-in AI strategies for testing or play.

- **`RandomPlayer`**: completely random actions, useful for fuzz testing.
- **`SimplePlayer`**: simple heuristic strategy: prioritize win, then riichi, then discard honors.
- **`DefensivePlayer`**: defensive AI that prioritizes genbutsu when another player has declared riichi.

```python
from pyriichi.player import SimplePlayer, DefensivePlayer

# Create players with different strategies.
p1 = SimplePlayer("Attacker")
p2 = DefensivePlayer("Defender")
```

### Main Enums

- **`GameAction`** - Game action types, such as draw, discard, chi, and pon.
- **`GamePhase`** - Game phases, such as initialization, dealing, playing, and ended.
- **`Suit`** - Suits: manzu, pinzu, souzu, honors.
- **`Wind`** - Winds: east, south, west, north.
- **`MeldType`** - Meld types: chi, pon, kan, closed kan.

### Utility Functions

- **`parse_tiles(tile_string)`** - Parse tiles from a string.
- **`format_tiles(tiles)`** - Format a tile list as a string.
- **`is_winning_hand(tiles, winning_tile)`** - Quickly check whether the tiles form a winning hand.

## Complete Feature List

### Implemented Features

- ✅ Tile set system, standard 136 tiles.
- ✅ Basic hand operations: draw and discard.
- ✅ Game flow control: dealing and turn management.
- ✅ Game state management: Round Number, winds, and scores.
- ✅ Winning-hand detection algorithm for standard and special shapes.
- ✅ Tenpai detection.
- ✅ Chi, pon, and kan operations.
- ✅ Yaku detection system, including all standard yaku and yakuman.
- ✅ Score calculation system: fu, han, and points.
- ✅ Ryuukyoku handling, including Kyuushu Kyuuhai.
- ✅ Ruleset configuration system for standard competitive rules and custom rules.
- ✅ Basic API structure.

### Notes

- `get_winning_combinations()` returns `List[List[Combination]]` and can be used directly:
  ```python
  combinations = hand.get_winning_combinations(winning_tile)
  if combinations:
      winning_combination = combinations[0]
  ```

## Documentation

- [API quick reference](API_SUMMARY.md) - Quick API reference guide.
- [Requirements](REQUIREMENTS.md) - Project-level requirements and links to rule requirements.
- [Rule requirements](rules/README.md) - Split riichi rule requirements and implementation audit.
- [Glossary](GLOSSARY.md) - Canonical code, Japanese, English, and Traditional Chinese terms.
- [Development plan](DEVELOPMENT_PLAN.md) - Development plan and timeline.

## Examples

See the `examples/` directory for more complete examples:

- `basic_usage.py` - Basic usage example.

## System Requirements

- Python 3.8 to 3.12, officially supported versions.
- Core features have no external dependencies.

## Development and Testing

- Install project dependencies in a virtual environment.
- Install the full development toolchain: `pip install ".[dev]"`.
  - Includes pytest>=7.0.0, pytest-cov>=4.0.0, black>=23.0.0, flake8>=6.0.0, and mypy>=1.0.0.
- Install only test tools: `pip install ".[test]"`.
  - Includes pytest>=7.0.0 and pytest-cov>=4.0.0.

## Contributing

Issues and pull requests are welcome. Use the `dev` and `test` extras to help maintain test quality.

## License

This project is licensed under the MIT License. See `LICENSE` for details.

## Related Resources

- [Riichi mahjong rules](https://en.wikipedia.org/wiki/Japanese_Mahjong)
- [List of yaku](https://en.wikipedia.org/wiki/Japanese_Mahjong_yaku)

---

**Note**: This project is under active development, and some features may not be fully implemented yet. See the development plan for details.
