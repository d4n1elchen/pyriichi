"""Furiten tests for RuleEngine."""

from pyriichi.hand import Hand
from pyriichi.rules import GameAction
from pyriichi.tiles import Suit, Tile
from pyriichi.utils import parse_tiles
from tests.helpers import RuleEngineTestMixin, set_ron_context, set_tsumo_context


class TestFuriten(RuleEngineTestMixin):
    def test_furiten_discards_cannot_ron(self):
        """Test furiten (Discards): Cannot ron if winning tile is in discards"""
        self._init_game()

        discard_tile = Tile(Suit.PINZU, 3)
        hand = set_ron_context(self.engine, 0, 1, "123456789m1233p", discard_tile)
        hand._discards.append(discard_tile)

        # Check furiten status
        assert self.engine.check_furiten_discards(0) is True
        assert self.engine.is_furiten(0) is True

        # Try ron, should fail
        result = self.engine.check_win(0, discard_tile)
        assert result is None or result.win is False

    def test_furiten_ron_declaration_applies_chombo(self):
        """Test declaring ron while furiten applies chombo."""
        self._init_game()
        discard_tile = Tile(Suit.PINZU, 3)
        hand = set_ron_context(self.engine, 0, 1, "123456789m1233p", discard_tile)
        hand._discards.append(discard_tile)
        self.engine._waiting_for_actions = {0: [GameAction.RON, GameAction.PASS]}

        result = self.engine.execute_action(0, GameAction.RON)

        assert result.chombo is True
        assert result.chombo_player == 0

    def test_furiten_discards_can_tsumo(self):
        """Test furiten (Discards): Can tsumo even if furiten"""
        self._init_game()

        discard_tile = Tile(Suit.PINZU, 3)
        hand = set_tsumo_context(self.engine, 0, "123456789m1233p", discard_tile)
        hand._discards.append(discard_tile)

        # Check furiten status (13 tiles, should be furiten)
        assert self.engine.check_furiten_discards(0) is True

        # tsumo requires 14 tiles in hand
        hand.add_tile(discard_tile)

        # tsumo should succeed
        result = self.engine.check_win(0, discard_tile)
        assert result is not None
        assert result.win is True

    def test_furiten_temp_same_turn_cannot_ron(self):
        """Test temp_furiten (Same Turn): Cannot ron if passed winning tile in same turn"""
        self._init_game()

        winning_tile = Tile(Suit.PINZU, 4)
        set_ron_context(self.engine, 0, 1, "123456789m1234p", winning_tile)
        self.engine._furiten_temp[0] = True
        self.engine._furiten_temp_round[0] = self.engine._turn_count

        # Check furiten status
        assert self.engine.check_furiten_temp(0) is True
        assert self.engine.is_furiten(0) is True

        result = self.engine.check_win(0, winning_tile)
        assert result is None or result.win is False

    def test_furiten_temp_next_turn_can_ron(self):
        """Test temp_furiten: Can ron in next turn"""
        self._init_game()

        winning_tile = Tile(Suit.PINZU, 4)
        set_ron_context(self.engine, 0, 1, "123456789m1234p", winning_tile)
        self.engine._furiten_temp[0] = True
        self.engine._furiten_temp_round[0] = 0
        self.engine._turn_count = 2  # 2 turns passed

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

        winning_tile = Tile(Suit.PINZU, 4)
        hand = set_ron_context(self.engine, 0, 1, "123456789m1234p", winning_tile)
        hand.set_riichi(True)
        self.engine._furiten_permanent[0] = True

        # Check furiten status
        assert self.engine.check_furiten_riichi(0) is True
        assert self.engine.is_furiten(0) is True

        result = self.engine.check_win(0, winning_tile)
        assert result is None or result.win is False

    def test_passing_ron_after_riichi_sets_permanent_furiten(self):
        """Test passing ron after riichi sets permanent furiten."""
        self._init_game()
        player = 0
        winning_tile = Tile(Suit.PINZU, 4)
        hand = set_ron_context(self.engine, player, 1, "123456789m1234p", winning_tile)
        hand.set_riichi(True)
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

        winning_tile = Tile(Suit.PINZU, 4)
        hand = set_tsumo_context(self.engine, 0, "123456789m12344p", winning_tile)
        hand.set_riichi(True)
        self.engine._furiten_permanent[0] = True

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

        winning_tile = Tile(Suit.PINZU, 5)
        hand = set_ron_context(self.engine, 0, 1, "123456789m4455p", winning_tile)
        hand._discards.append(Tile(Suit.PINZU, 4))

        # Check furiten status after discarding one of the winning tiles.
        assert self.engine.check_furiten_discards(0) is True

        # Even if the discarded is 5p, the other winning tile, ron is blocked.
        result = self.engine.check_win(0, winning_tile)
        assert result is None or result.win is False
