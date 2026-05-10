"""Multiple ron decision tests for RuleEngine."""

from pyriichi.hand import Hand
from pyriichi.rules import GameAction
from pyriichi.tiles import Suit, Tile
from pyriichi.utils import parse_tiles
from tests.helpers import (
    RuleEngineTestMixin,
    no_response_hand,
    set_non_matching_scoring_dora,
)


def _score_deltas(initial_scores, current_scores):
    return [current - initial for current, initial in zip(current_scores, initial_scores)]


class TestMultipleRon(RuleEngineTestMixin):
    def test_multiple_ron_decision(self):
        """Test multiple ron decisions (One ron, One Pass)"""
        self._init_game()

        # Enable double_ron
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True

        # Set Player 1 tenpai (machi 5p)
        # 123m 456s 789p 11z + 46p (machi 5p for 456p)
        self.engine.get_hand(1)._tiles = parse_tiles("123m456s789p11z46p")
        self.engine.get_hand(1)._melds = []

        # Set Player 2 tenpai (machi 5p)
        # 123m 456s 789p 22z + 46p (machi 5p for 456p)
        self.engine.get_hand(2)._tiles = parse_tiles("123m456s789p22z46p")
        self.engine.get_hand(2)._melds = []

        # Player 0 discards 5p
        discard_tile = Tile(Suit.PINZU, 5)
        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # Check interrupts
        interrupts = self.engine._check_interrupts(discard_tile, discarded_player=0)

        # Ensure Player 1 and Player 2 can both ron
        assert 1 in interrupts
        assert GameAction.RON in interrupts[1]
        assert 2 in interrupts
        assert GameAction.RON in interrupts[2]

        # Set waiting for actions
        self.engine._waiting_for_actions = interrupts
        self.engine._incoming_actions = {}
        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # Player 1 chooses RON
        self.engine.execute_action(1, GameAction.RON)

        # Player 2 chooses PASS
        result = self.engine.execute_action(2, GameAction.PASS)

        # Verify result
        # Only Player 1 should win
        assert result.success
        assert len(result.winners) == 1
        assert result.winners[0] == 1

        # Verify Player 2 furiten (Missed ron)
        assert self.engine._furiten_temp[2]

    def test_head_bump_only_shimocha_wins(self):
        """Test head_bump: shimocha and kamicha can ron, only shimocha wins."""
        self._init_game()

        assert self.engine._game_state.ruleset.head_bump_only

        discard_tile = Tile(Suit.MANZU, 1)
        self.engine._hands[1] = Hand(parse_tiles("23456789m12344p"))
        self.engine._hands[3] = Hand(parse_tiles("23456789m12344p"))
        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        winners = self.engine.check_multiple_ron(discard_tile, 0)

        assert winners == [1]

    def test_head_bump_only_toimen_blocked(self):
        """Test head_bump: toimen can ron but blocked."""
        self._init_game()

        discard_tile = Tile(Suit.MANZU, 1)
        self.engine._hands[2] = Hand(parse_tiles("23456789m12344p"))
        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        winners = self.engine.check_multiple_ron(discard_tile, 0)

        assert winners == [2]

    def test_head_bump_only_kamicha_blocked(self):
        """Test head_bump: kamicha can ron but blocked."""
        self._init_game()

        discard_tile = Tile(Suit.MANZU, 1)
        self.engine._hands[3] = Hand(parse_tiles("23456789m12344p"))
        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        winners = self.engine.check_multiple_ron(discard_tile, 0)

        assert winners == [3]

    def test_double_ron_both_win(self):
        """Test double_ron: Two players win simultaneously."""
        self._init_game()
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True

        discard_tile = Tile(Suit.MANZU, 1)
        self.engine._hands[1] = Hand(parse_tiles("23456789m12344p"))
        self.engine._hands[2] = Hand(parse_tiles("23456789m12344p"))
        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        winners = self.engine.check_multiple_ron(discard_tile, 0)

        assert winners == [1, 2]

    def test_double_ron_score_calculation(self):
        """Test double_ron: Verify deal-in player pays both."""
        self._init_game()
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True

        discard_tile = Tile(Suit.PINZU, 4)
        hand_tiles = parse_tiles("234567m23456p88s")
        self.engine._hands[1] = Hand(hand_tiles)
        self.engine._hands[2] = Hand(hand_tiles)
        self.engine._current_player = 0
        self.engine._is_first_turn_after_deal = False
        set_non_matching_scoring_dora(self.engine)

        initial_scores = self.engine._game_state.scores.copy()
        self.engine._hands[0]._tiles.append(discard_tile)
        self.engine._waiting_for_actions = {0: self.engine._calculate_turn_actions(0)}
        self.engine.execute_action(0, GameAction.DISCARD, discard_tile)
        self.engine.execute_action(1, GameAction.RON, tile=discard_tile)
        result = self.engine.execute_action(2, GameAction.RON, tile=discard_tile)

        assert result.success
        assert len(result.winners) == 2
        score_deltas = _score_deltas(initial_scores, self.engine._game_state.scores)
        assert score_deltas[1] > 0
        assert score_deltas[2] == score_deltas[1]
        assert score_deltas[0] == -(score_deltas[1] + score_deltas[2])

    def test_double_ron_uses_score_result_settlement(self):
        """Test double_ron uses score_result settlement."""
        self._init_game()
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True
        self.engine._game_state._honba = 1
        self.engine._game_state.add_riichi_stick()

        discard_tile = Tile(Suit.PINZU, 4)
        hand_tiles = parse_tiles("234567m23456p88s")
        self.engine._hands[1] = Hand(hand_tiles)
        self.engine._hands[2] = Hand(hand_tiles)
        self.engine._current_player = 0
        self.engine._is_first_turn_after_deal = False
        set_non_matching_scoring_dora(self.engine)

        initial_scores = self.engine._game_state.scores.copy()
        self.engine._hands[0]._tiles.append(discard_tile)
        self.engine._waiting_for_actions = {0: self.engine._calculate_turn_actions(0)}
        self.engine.execute_action(0, GameAction.DISCARD, discard_tile)
        self.engine.execute_action(1, GameAction.RON, tile=discard_tile)
        result = self.engine.execute_action(2, GameAction.RON, tile=discard_tile)

        assert result.success
        assert sorted(result.winners) == [1, 2]
        assert self.engine._game_state.riichi_sticks == 0
        score_deltas = _score_deltas(initial_scores, self.engine._game_state.scores)
        assert score_deltas[1] > score_deltas[2] > 0
        assert score_deltas[1] - score_deltas[2] == 1000
        assert sum(score_deltas) == 1000

    def test_double_ron_dealer_renchan(self):
        """Test double_ron: dealer win leads to renchan."""
        self._init_game()
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True
        self.engine._game_state._dealer = 0
        self.engine._game_state._round_number = 1
        self.engine._game_state._honba = 0

        discard_tile = Tile(Suit.PINZU, 5)
        hand_str = "233445678m2345p"
        self.engine._hands[0] = Hand(parse_tiles(hand_str))
        self.engine._hands[2] = Hand(parse_tiles(hand_str))
        self.engine._hands[3] = no_response_hand()
        self.engine._current_player = 1
        self.engine._hands[1]._tiles.append(discard_tile)
        self.engine._waiting_for_actions = {1: self.engine._calculate_turn_actions(1)}
        self.engine.execute_action(1, GameAction.DISCARD, discard_tile)

        self.engine.execute_action(0, GameAction.RON, tile=discard_tile)
        result = self.engine.execute_action(2, GameAction.RON, tile=discard_tile)

        assert result.success
        assert sorted(result.winners) == [0, 2]

    def test_triple_ron_enabled_all_win(self):
        """Test triple_ron enabled: All three players win."""
        self._init_game()
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True
        self.engine._game_state.ruleset.allow_triple_ron = True
        self.engine._is_first_turn_after_deal = False

        discard_tile = Tile(Suit.PINZU, 5)
        hand_str = "233445678m2345p"
        self.engine._hands[1] = Hand(parse_tiles(hand_str))
        self.engine._hands[2] = Hand(parse_tiles(hand_str))
        self.engine._hands[3] = Hand(parse_tiles(hand_str))
        set_non_matching_scoring_dora(self.engine)

        initial_scores = self.engine._game_state.scores.copy()
        self.engine._current_player = 0
        self.engine._hands[0]._tiles.append(discard_tile)
        self.engine._waiting_for_actions = {0: self.engine._calculate_turn_actions(0)}
        self.engine.execute_action(0, GameAction.DISCARD, discard_tile)
        self.engine.execute_action(1, GameAction.RON, tile=discard_tile)
        self.engine.execute_action(2, GameAction.RON, tile=discard_tile)
        result = self.engine.execute_action(3, GameAction.RON, tile=discard_tile)

        assert result.success
        assert sorted(result.winners) == [1, 2, 3]
        score_deltas = _score_deltas(initial_scores, self.engine._game_state.scores)
        assert score_deltas[1] > 0
        assert score_deltas[2] == score_deltas[1]
        assert score_deltas[3] == score_deltas[1]
        assert score_deltas[0] == -sum(score_deltas[1:])

    def test_double_ron_with_furiten(self):
        """Test double_ron with furiten: One player furiten, only other player wins."""
        self._init_game()
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True

        discard_tile = Tile(Suit.PINZU, 5)
        hand_str = "233445678m2345p"
        self.engine._hands[1] = Hand(parse_tiles(hand_str))
        self.engine._hands[2] = Hand(parse_tiles(hand_str))
        self.engine._hands[2]._discards.append(discard_tile)
        self.engine._current_player = 0
        self.engine._hands[0]._tiles.append(discard_tile)
        self.engine._waiting_for_actions = {0: self.engine._calculate_turn_actions(0)}
        self.engine.execute_action(0, GameAction.DISCARD, discard_tile)

        result = self.engine.execute_action(1, GameAction.RON, tile=discard_tile)

        assert result.success
        assert result.winners == [1]

    def test_double_ron_priority_order(self):
        """Test double_ron: Verify player order."""
        self._init_game()
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True

        discard_tile = Tile(Suit.PINZU, 5)
        hand_str = "233445678m2345p"
        self.engine._hands[2] = Hand(parse_tiles(hand_str))
        self.engine._hands[3] = Hand(parse_tiles(hand_str))
        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        winners = self.engine.check_multiple_ron(discard_tile, 0)

        assert winners == [2, 3]
