"""Action execution tests for RuleEngine."""

import pytest

from pyriichi.hand import Hand
from pyriichi.rules import GameAction, GamePhase, RyuukyokuType
from pyriichi.tiles import Suit, Tile
from pyriichi.utils import parse_tiles
from tests.helpers import RuleEngineTestMixin, no_response_hand


class TestActionExecution(RuleEngineTestMixin):
    def test_pon_action_claims_last_discard(self):
        """Test pon action claims last discard and changes turn."""
        self._init_game()
        tile_to_discard = Tile(Suit.MANZU, 3)

        self.engine._hands[0] = Hand(parse_tiles("1356789m1234p123s"))
        # 33m 567p 89p 456s 789s
        self.engine._hands[1] = Hand(parse_tiles("33m56789p456789s"))
        self.engine._hands[2] = no_response_hand()
        self.engine._hands[3] = no_response_hand()

        self.engine._current_player = 0
        discard_before = len(self.engine.get_discards(0))

        discard_result = self.engine.execute_action(
            0, GameAction.DISCARD, tile=tile_to_discard
        )
        assert discard_result.discarded is True
        assert self.engine.get_last_discard() == tile_to_discard
        assert self.engine.get_last_discard_player() == 0
        actions = self.engine.get_available_actions(1)
        assert GameAction.PON in actions

        pon_result = self.engine.execute_action(1, GameAction.PON)

        assert pon_result.called_action == GameAction.PON
        assert pon_result.meld is not None
        assert tile_to_discard in pon_result.meld.tiles
        assert len(self.engine.get_hand(1).melds) == 1
        assert len(self.engine.get_discards(0)) == discard_before
        assert self.engine.get_last_discard() is None
        assert self.engine.get_last_discard_player() is None
        assert self.engine.get_current_player() == 1
        actions_after = self.engine.get_available_actions(1)
        assert GameAction.DRAW not in actions_after

    def test_chi_action_uses_sequence_and_resets_turn(self):
        """Test chi action uses specified sequence and resets turn."""
        self._init_game()
        tile_to_discard = Tile(Suit.MANZU, 4)

        self.engine._hands[0] = Hand(parse_tiles("4789m12345p12345s"))
        # 23m 56m 678p 9p 678s 9s 5s
        self.engine._hands[1] = Hand(parse_tiles("2356m6789p56789s"))
        # 11m 11p 112345678s
        self.engine._hands[2] = Hand(parse_tiles("11m11p12345678s"))

        self.engine._current_player = 0
        self.engine.execute_action(0, GameAction.DISCARD, tile=tile_to_discard)

        actions_player1 = self.engine.get_available_actions(1)
        assert GameAction.CHI in actions_player1
        actions_player2 = self.engine.get_available_actions(2)
        assert GameAction.CHI not in actions_player2

        sequences = self.engine.get_available_chi_sequences(1)
        assert sequences

        target_sequence = None
        for seq in sequences:
            ranks = sorted(tile.rank for tile in seq)
            if ranks == [2, 3]:
                target_sequence = seq
                break

        assert target_sequence is not None

        chi_result = self.engine.execute_action(
            1, GameAction.CHI, sequence=target_sequence
        )

        assert chi_result.called_action == GameAction.CHI
        assert chi_result.called_tile == tile_to_discard
        assert chi_result.meld is not None
        assert len(self.engine.get_hand(1).melds) == 1
        assert self.engine.get_last_discard() is None
        assert self.engine.get_last_discard_player() is None
        assert self.engine.get_current_player() == 1
        actions_after_chi = self.engine.get_available_actions(1)
        assert GameAction.DRAW not in actions_after_chi

    def test_execute_action_draw_no_tile_set(self):
        """Test Draw when tile set is not initialized"""
        self._init_game()
        hand = self.engine.get_hand(0)
        self.engine.execute_action(0, GameAction.DISCARD, tile=hand.tiles[0])
        current_player = self.engine.get_current_player()

        self.engine._tile_set = None

        # Ensure hand is not full
        hand = self.engine.get_hand(current_player)
        if hand.total_tile_count() >= 14:
            hand.tiles.pop()

        with pytest.raises(ValueError, match="牌組未初始化"):
            self.engine._handle_draw(current_player)

    def test_execute_action_discard_no_tile(self):
        """Test Discard without specifying tile"""
        self._init_game()
        current_player = self.engine.get_current_player()
        with pytest.raises(ValueError):
            self.engine.execute_action(current_player, GameAction.DISCARD, tile=None)

    def test_execute_action_discard_no_tile_set(self):
        """Test Discard when tile set is not initialized"""
        self._init_game()
        current_player = self.engine.get_current_player()
        hand = self.engine.get_hand(current_player)
        self.engine._tile_set = None
        with pytest.raises(ValueError, match="牌組未初始化"):
            self.engine.execute_action(
                current_player, GameAction.DISCARD, tile=hand.tiles[0]
            )

    def test_execute_action_discard_last_tile(self):
        """Test discard last tile (houtei)"""
        self._init_game()
        current_player = self.engine.get_current_player()
        hand = self.engine.get_hand(current_player)

        # Simulate wall exhausted
        assert self.engine._tile_set is not None
        self.engine._tile_set._tiles = []

        result = self.engine.execute_action(
            current_player, GameAction.DISCARD, tile=hand.tiles[0]
        )
        assert result.is_last_tile is True

    def test_execute_action_draw_last_tile(self):
        """Test draw last tile (haitei)"""
        self._init_game()
        current_player = self.engine.get_current_player()

        # Ensure hand has one less tile to allow draw
        hand = self.engine.get_hand(current_player)
        hand._tiles.pop()

        assert self.engine._tile_set is not None
        self.engine._tile_set._tiles = [Tile(Suit.MANZU, 1)]

        assert self.engine._tile_set is not None
        self.engine._tile_set._tiles = [Tile(Suit.MANZU, 1)]

        # Directly call internal _handle_draw to test logic, as DRAW action is removed
        result = self.engine._handle_draw(current_player)
        assert result.is_last_tile is True

    def test_execute_action_discard_history(self):
        """Test discard history recording"""
        self._init_game()
        current_player = self.engine.get_current_player()
        hand = self.engine.get_hand(current_player)
        assert hand.tiles is not None
        self.engine.execute_action(
            current_player, GameAction.DISCARD, tile=hand.tiles[0]
        )
        assert len(self.engine._discard_history) > 0

    def test_execute_action_discard_history_limit(self):
        """Test discard history keeps only last 4"""
        self._init_game()
        # dealer has 14 tiles at start, discard one first
        current_player = self.engine.get_current_player()
        hand = self.engine.get_hand(current_player)
        assert self._has_action(current_player, GameAction.DISCARD)
        self.engine.execute_action(
            current_player, GameAction.DISCARD, tile=hand.tiles[0]
        )
        for _ in range(10):
            current_player = self.engine.get_current_player()
        for _ in range(10):
            current_player = self.engine.get_current_player()
            # DRAW is automatic, so check DISCARD directly
            hand = self.engine.get_hand(current_player)
            # Ensure there are tiles to discard
            if not hand.tiles:
                self.engine._handle_draw(current_player)

            # If just drawn, hand count should be 14. After discard 13.
            # Next player will automatically draw.

            # Here we force discard
            if self._has_action(current_player, GameAction.DISCARD):
                self.engine.execute_action(
                    current_player, GameAction.DISCARD, tile=hand.tiles[0]
                )
            else:
                # If cannot discard (e.g. no tiles), manually draw one
                # Ensure hand is not full
                if hand.total_tile_count() < 14:
                    self.engine._handle_draw(current_player)

                if self._has_action(current_player, GameAction.DISCARD):
                    self.engine.execute_action(
                        current_player, GameAction.DISCARD, tile=hand.tiles[0]
                    )

        assert len(self.engine._discard_history) <= 4

    def test_execute_action_draw_no_tile_drawn(self):
        """Test Draw when no tiles left"""
        self._init_game()
        current_player = self.engine.get_current_player()

        # Exhaust wall to trigger draw() returning None
        assert self.engine._tile_set is not None
        hand = self.engine.get_hand(current_player)
        assert hand.tiles is not None
        self.engine.execute_action(
            current_player, GameAction.DISCARD, tile=hand.tiles[0]
        )
        while self.engine._tile_set._tiles:
            self.engine._tile_set.draw()
        current_player = self.engine.get_current_player()
        while self.engine._tile_set._tiles:
            self.engine._tile_set.draw()
        current_player = self.engine.get_current_player()

        # Ensure hand is not full (less than 14)
        hand = self.engine.get_hand(current_player)
        while hand.total_tile_count() >= 14:
            hand._tiles.pop()

        # Directly call _handle_draw
        result = self.engine._handle_draw(current_player)
        assert result.ryuukyoku is not None
        assert result.ryuukyoku.ryuukyoku is True
        assert result.ryuukyoku.ryuukyoku_type == RyuukyokuType.EXHAUSTIVE_DRAW
        # _handle_draw sets phase
        assert self.engine._phase == GamePhase.RYUUKYOKU

    def test_execute_action_discard_is_last_tile(self):
        """Test check for discarding the last tile"""
        self._init_game()
        current_player = self.engine.get_current_player()
        hand = self.engine.get_hand(current_player)
        assert hand.tiles
        assert hand.total_tile_count() == 14
        self.engine.execute_action(
            current_player, GameAction.DISCARD, tile=hand.tiles[0]
        )

        # Simulate wall has only one tile left
        assert self.engine._tile_set is not None
        self.engine._tile_set._tiles = [Tile(Suit.MANZU, 1)]
