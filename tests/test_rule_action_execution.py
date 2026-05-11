"""Action execution tests for RuleEngine."""

import pytest

from pyriichi.hand import Hand
from pyriichi.rules import ActionResult, GameAction
from pyriichi.tiles import Suit, Tile
from pyriichi.utils import parse_tiles
from tests.helpers import RuleEngineTestMixin, no_response_hand, set_non_matching_scoring_dora


class TestActionExecution(RuleEngineTestMixin):
    def test_response_priority_ron_beats_pon(self):
        """Test response priority: ron beats pon."""
        self._init_game()
        set_non_matching_scoring_dora(self.engine)
        discard_tile = Tile(Suit.PINZU, 4)

        self.engine._is_first_turn_after_deal = False
        self.engine._hands[1] = Hand(parse_tiles("123456789m1234p"))
        self.engine._hands[2] = Hand(parse_tiles("44p123456789m12s"))
        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0
        self.engine._incoming_actions = {
            1: (GameAction.RON, discard_tile, {}),
            2: (GameAction.PON, discard_tile, {}),
        }

        result = self.engine._resolve_decisions()

        assert result.success
        assert result.winners == [1]
        assert result.called_action is None
        assert len(self.engine.get_hand(2).melds) == 0

    def test_response_priority_pon_beats_chi(self):
        """Test response priority: pon beats chi."""
        self._init_game()
        discard_tile = Tile(Suit.MANZU, 4)

        self.engine._hands[0]._discards.append(discard_tile)
        self.engine._hands[1] = Hand(parse_tiles("23m56789p456789s"))
        self.engine._hands[2] = Hand(parse_tiles("44m56789p456789s"))
        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0
        self.engine._incoming_actions = {
            1: (GameAction.CHI, discard_tile, {}),
            2: (GameAction.PON, discard_tile, {}),
        }

        result = self.engine._resolve_decisions()

        assert result.called_action == GameAction.PON
        assert result.called_tile == discard_tile
        assert self.engine.get_current_player() == 2
        assert len(self.engine.get_hand(2).melds) == 1
        assert len(self.engine.get_hand(1).melds) == 0

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
        self.engine._hands[2] = no_response_hand()
        self.engine._hands[3] = no_response_hand()

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
        """Test discard history keeps only last 4."""
        self._init_game()
        discards = [Tile(Suit.MANZU, rank) for rank in range(1, 6)]

        for tile in discards:
            self.engine._apply_discard_effects(0, tile, ActionResult())

        assert self.engine._discard_history == [(0, tile) for tile in discards[-4:]]
