"""Furiten tests for RuleEngine."""

from pyriichi.hand import Hand
from pyriichi.rules import GameAction
from pyriichi.tiles import Suit, Tile
from pyriichi.utils import parse_tiles
from tests.helpers import RuleEngineTestMixin


class TestFuriten(RuleEngineTestMixin):
    def test_furiten_discards_cannot_ron(self):
        """Test furiten (Discards): Cannot ron if winning tile is in discards"""
        self._init_game()

        # Set Player 0 tenpai (machi 3p)
        # hand: 123m 456m 789m 12p 33p (machi 3p)
        tiles = parse_tiles("123456789m1233p")
        self.engine._hands[0] = Hand(tiles)

        # Player 0 discarded 3p before (now in discards)
        discard_tile = Tile(Suit.PINZU, 3)
        self.engine._hands[0]._discards.append(discard_tile)

        # Other player discards 3p
        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0
        self.engine._last_drawn_tile = None

        # Check furiten status
        assert self.engine.check_furiten_discards(0) is True
        assert self.engine.is_furiten(0) is True

        # Try ron, should fail
        result = self.engine.check_win(0, discard_tile)
        assert result is None or result.win is False

    def test_furiten_discards_can_tsumo(self):
        """Test furiten (Discards): Can tsumo even if furiten"""
        self._init_game()

        # Set Player 0 tenpai (machi 3p)
        # hand: 123m 456m 789m 12p 33p (13 tiles, machi 3p)
        tiles = parse_tiles("123456789m1233p")
        self.engine._hands[0] = Hand(tiles)

        # Player 0 discarded 3p before
        discard_tile = Tile(Suit.PINZU, 3)
        self.engine._hands[0]._discards.append(discard_tile)

        # Check furiten status (13 tiles, should be furiten)
        assert self.engine.check_furiten_discards(0) is True

        # Simulate tsumo 3p
        self.engine._current_player = 0
        self.engine._last_drawn_tile = (0, discard_tile)
        self.engine._last_discarded_tile = None

        # tsumo requires 14 tiles in hand
        self.engine._hands[0].add_tile(discard_tile)

        # tsumo should succeed
        result = self.engine.check_win(0, discard_tile)
        assert result is not None
        assert result.win is True

    def test_furiten_temp_same_turn_cannot_ron(self):
        """Test temp_furiten (Same Turn): Cannot ron if passed winning tile in same turn"""
        self._init_game()

        # Set Player 0 tenpai (machi 4p)
        # hand: 123m 456m 789m 123p 4p
        tiles = parse_tiles("123456789m1234p")
        self.engine._hands[0] = Hand(tiles)

        winning_tile = Tile(Suit.PINZU, 4)

        # Set temp_furiten status (Player 0 passed ron in current turn)
        self.engine._furiten_temp[0] = True
        self.engine._furiten_temp_round[0] = self.engine._turn_count

        # Other player discards 4p
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0
        self.engine._last_drawn_tile = None

        # Check furiten status
        assert self.engine.check_furiten_temp(0) is True
        assert self.engine.is_furiten(0) is True

        result = self.engine.check_win(0, winning_tile)
        assert result is None or result.win is False

    def test_furiten_temp_next_turn_can_ron(self):
        """Test temp_furiten: Can ron in next turn"""
        self._init_game()

        # Set Player 0 tenpai (machi 4p)
        tiles = parse_tiles("123456789m1234p")
        self.engine._hands[0] = Hand(tiles)

        winning_tile = Tile(Suit.PINZU, 4)

        # Set temp_furiten status (Previous turn)
        self.engine._furiten_temp[0] = True
        self.engine._furiten_temp_round[0] = 0
        self.engine._turn_count = 2  # 2 turns passed

        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0
        self.engine._last_drawn_tile = None

        # Check furiten status (Should not be temp_furiten)
        assert self.engine.check_furiten_temp(0) is False
        assert self.engine.is_furiten(0) is False

        # Try ron, should succeed
        result = self.engine.check_win(0, winning_tile)
        assert result is not None
        assert result.win is True

    def test_furiten_riichi_permanent(self):
        """Test riichi furiten: Permanent furiten after passing ron in riichi"""
        self._init_game()

        # Set Player 0 riichi and tenpai (machi 4p)
        tiles = parse_tiles("123456789m1234p")
        self.engine._hands[0] = Hand(tiles)
        self.engine._hands[0].set_riichi(True)

        winning_tile = Tile(Suit.PINZU, 4)

        # Set riichi furiten status (Player 0 passed ron after riichi)
        self.engine._furiten_permanent[0] = True

        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0
        self.engine._last_drawn_tile = None

        # Check furiten status
        assert self.engine.check_furiten_riichi(0) is True
        assert self.engine.is_furiten(0) is True

        result = self.engine.check_win(0, winning_tile)
        assert result is None or result.win is False

    def test_passing_ron_after_riichi_sets_permanent_furiten(self):
        """Test passing ron after riichi sets permanent furiten."""
        self._init_game()
        player = 0
        self.engine._hands[player] = Hand(parse_tiles("123456789m1234p"))
        self.engine._hands[player].set_riichi(True)
        self.engine._last_discarded_tile = Tile(Suit.PINZU, 4)
        self.engine._last_discarded_player = 1
        self.engine._waiting_for_actions = {
            player: [GameAction.RON, GameAction.PASS],
            2: [GameAction.PASS],
        }

        self.engine.execute_action(player, GameAction.PASS)

        assert self.engine.check_furiten_temp(player) is True
        assert self.engine.check_furiten_riichi(player) is True
        assert self.engine.is_furiten(player) is True

    def test_furiten_riichi_can_tsumo(self):
        """Test riichi furiten: Can tsumo even if permanent furiten"""
        self._init_game()

        # Set Player 0 riichi and tenpai (machi 4p)
        tiles = parse_tiles("123456789m12344p")
        self.engine._hands[0] = Hand(tiles)
        self.engine._hands[0].set_riichi(True)

        winning_tile = Tile(Suit.PINZU, 4)

        # Set riichi furiten status
        self.engine._furiten_permanent[0] = True

        # Simulate tsumo 4p
        self.engine._current_player = 0
        self.engine._last_drawn_tile = (0, winning_tile)
        self.engine._last_discarded_tile = None

        # Check furiten status (Still furiten)
        assert self.engine.check_furiten_riichi(0) is True

        # tsumo should succeed
        result = self.engine.check_win(0, winning_tile)
        assert result is not None
        assert result.win is True

    def test_furiten_not_tenpai_returns_false(self):
        """Test furiten check returns False if not tenpai"""
        self._init_game()

        # Set Player 0 noten
        tiles = parse_tiles("123456789m12345p")
        self.engine._hands[0] = Hand(tiles)

        # Check furiten status (noten is not furiten)
        assert self.engine.check_furiten_discards(0) is False
        assert self.engine.is_furiten(0) is False

    def test_furiten_multiple_machi_tiles(self):
        """Test furiten with multiple machi tiles."""
        self._init_game()

        # Set Player 0 multi-machi (machi 4p 5p)
        # hand: 123m 456m 789m 44p 55p (Shanpon machi 4p 5p)
        tiles = parse_tiles("123456789m4455p")
        self.engine._hands[0] = Hand(tiles)

        # Player 0 discarded 4p before (one of the machi tiles).
        self.engine._hands[0]._discards.append(Tile(Suit.PINZU, 4))

        # Check furiten status after discarding one of the winning tiles.
        assert self.engine.check_furiten_discards(0) is True

        # Even if the discarded is 5p, the other winning tile, ron is blocked.
        winning_tile = Tile(Suit.PINZU, 5)
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0
        self.engine._last_drawn_tile = None

        result = self.engine.check_win(0, winning_tile)
        assert result is None or result.win is False
