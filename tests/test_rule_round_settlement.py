"""Round settlement tests for RuleEngine."""

from pyriichi.game_state import Wind
from pyriichi.hand import Hand
from pyriichi.rules import GamePhase
from pyriichi.tiles import Suit, Tile
from pyriichi.utils import parse_tiles
from tests.helpers import RuleEngineTestMixin, set_non_matching_scoring_dora


class TestRoundSettlement(RuleEngineTestMixin):
    def test_end_round_with_winner(self):
        """Test end round (with winner)"""
        self._init_game()

        # Set to South 4 Round
        self.engine._game_state.set_round(Wind.SOUTH, 4)
        self.engine._game_state._dealer = 3  # Player 3 is dealer

        # Set player score >= 30000 (Return point), otherwise will go into West round
        self.engine._game_state._scores[0] = 30000

        # Test with winner (Player 0 wins, non-dealer)
        winner = 0
        self.engine.end_round([winner])

        # Should end game (GamePhase.ENDED)
        assert self.engine._phase == GamePhase.ENDED

    def test_noten_bappu_one_tenpai(self):
        """Test noten_bappu: One tenpai (+3000 / -1000)"""
        self._init_game()

        # Set Player 0 tenpai
        # 123m 456m 789m 123p 4p
        self.engine._hands[0] = Hand(parse_tiles("123456789m1234p"))

        # Set other players noten
        # 12m 45m 78m 12p 45p 78s 1z
        noten_hand = Hand(parse_tiles("124578m1245p78s1z"))
        for i in range(1, 4):
            self.engine._hands[i] = noten_hand

        # Record initial scores
        initial_scores = self.engine._game_state.scores.copy()

        # Simulate ryuukyoku (exhaustive_draw)
        self.engine._tile_set._tiles = []
        # Ensure check_ryuukyoku returns EXHAUSTED
        # Note: check_ryuukyoku relies on _tile_set.is_exhausted()

        # Directly call end_round(None)
        # Expect end_round to detect ryuukyoku and calculate penalty
        self.engine.end_round(None)

        # Verify score changes
        # Player 0: +3000
        assert self.engine._game_state.scores[0] == initial_scores[0] + 3000
        # Other players: -1000
        for i in range(1, 4):
            assert self.engine._game_state.scores[i] == initial_scores[i] - 1000

    def test_noten_bappu_two_tenpai(self):
        """Test noten_bappu: Two tenpai (+1500 / -1500)"""
        self._init_game()

        # Set Player 0, 1 tenpai
        tenpai_hand = Hand(parse_tiles("123456789m1234p"))
        self.engine._hands[0] = tenpai_hand
        self.engine._hands[1] = tenpai_hand

        # Set Player 2, 3 noten
        noten_hand = Hand(parse_tiles("124578m1245p78s1z"))
        self.engine._hands[2] = noten_hand
        self.engine._hands[3] = noten_hand

        initial_scores = self.engine._game_state.scores.copy()

        self.engine._tile_set._tiles = []
        self.engine.end_round(None)

        assert self.engine._game_state.scores[0] == initial_scores[0] + 1500
        assert self.engine._game_state.scores[1] == initial_scores[1] + 1500
        assert self.engine._game_state.scores[2] == initial_scores[2] - 1500
        assert self.engine._game_state.scores[3] == initial_scores[3] - 1500

    def test_noten_bappu_three_tenpai(self):
        """Test noten_bappu: Three tenpai (+1000 / -3000)"""
        self._init_game()

        # Set Player 0, 1, 2 tenpai
        tenpai_hand = Hand(parse_tiles("123456789m1234p"))
        self.engine._hands[0] = tenpai_hand
        self.engine._hands[1] = tenpai_hand
        self.engine._hands[2] = tenpai_hand

        # Set Player 3 noten
        noten_hand = Hand(parse_tiles("124578m1245p78s1z"))
        self.engine._hands[3] = noten_hand

        initial_scores = self.engine._game_state.scores.copy()

        self.engine._tile_set._tiles = []
        self.engine.end_round(None)

        assert self.engine._game_state.scores[0] == initial_scores[0] + 1000
        assert self.engine._game_state.scores[1] == initial_scores[1] + 1000
        assert self.engine._game_state.scores[2] == initial_scores[2] + 1000
        assert self.engine._game_state.scores[3] == initial_scores[3] - 3000

    def test_noten_bappu_all_tenpai(self):
        """Test noten_bappu: All tenpai (0)"""
        self._init_game()

        # Set all players tenpai
        tenpai_hand = Hand(parse_tiles("123456789m1234p"))
        for i in range(4):
            self.engine._hands[i] = tenpai_hand

        initial_scores = self.engine._game_state.scores.copy()

        self.engine._tile_set._tiles = []
        self.engine.end_round(None)

        for i in range(4):
            assert self.engine._game_state.scores[i] == initial_scores[i]

    def test_noten_bappu_no_tenpai(self):
        """Test noten_bappu: No tenpai (0)"""
        self._init_game()

        # Set all players noten
        noten_hand = Hand(parse_tiles("124578m1245p78s1z"))
        for i in range(4):
            self.engine._hands[i] = noten_hand

        initial_scores = self.engine._game_state.scores.copy()

        self.engine._tile_set._tiles = []
        self.engine.end_round(None)

        for i in range(4):
            assert self.engine._game_state.scores[i] == initial_scores[i]

    def test_exhaustive_draw_dealer_tenpai_renchan(self):
        """Test exhaustive_draw dealer tenpai renchan."""
        self._init_game()
        self.engine._game_state.set_dealer(0)
        self.engine._game_state.set_round(Wind.EAST, 1)
        self.engine._game_state._honba = 0
        self.engine._hands[0] = Hand(parse_tiles("123456789m1234p"))
        noten_hand = Hand(parse_tiles("124578m1245p78s1z"))
        for i in range(1, 4):
            self.engine._hands[i] = noten_hand
        self.engine._tile_set._tiles = []

        self.engine.end_round(None)

        assert self.engine._game_state.dealer == 0
        assert self.engine._game_state.round_wind == Wind.EAST
        assert self.engine._game_state.round_number == 1
        assert self.engine._game_state.honba == 1

    def test_exhaustive_draw_dealer_noten_rotates(self):
        """Test exhaustive_draw dealer noten rotates."""
        self._init_game()
        self.engine._game_state.set_dealer(0)
        self.engine._game_state.set_round(Wind.EAST, 1)
        self.engine._hands[0] = Hand(parse_tiles("124578m1245p78s1z"))
        self.engine._hands[1] = Hand(parse_tiles("123456789m1234p"))
        for i in range(2, 4):
            self.engine._hands[i] = Hand(parse_tiles("124578m1245p78s1z"))
        self.engine._tile_set._tiles = []

        self.engine.end_round(None)

        assert self.engine._game_state.dealer == 1
        assert self.engine._game_state.round_wind == Wind.EAST
        assert self.engine._game_state.round_number == 2
        assert self.engine._game_state.honba == 1

    def test_tobi_ron(self):
        """Test tobi (Bankruptcy): ron causes score < 0"""
        self._init_game()
        self.engine._game_state.ruleset.tobi_enabled = True
        self.engine._game_state._scores[1] = 1000
        self.engine._hands[0] = Hand(parse_tiles("123456789m1234p"))
        set_non_matching_scoring_dora(self.engine)
        winning_tile = Tile(Suit.PINZU, 4)
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0
        self.engine._is_first_turn_after_deal = False

        result = self.engine.check_win(0, winning_tile)

        assert result is not None
        assert result.score_result.payment_from == 1
        self.engine.apply_win_score(result)
        assert self.engine._game_state.scores[1] < 0

        self.engine.end_round([0])

        assert self.engine.get_phase() == GamePhase.ENDED

    def test_tobi_tsumo(self):
        """Test tobi (Bankruptcy): tsumo causes score < 0"""
        self._init_game()
        self.engine._game_state.ruleset.tobi_enabled = True

        # Set Player 1, 2, 3 score very low
        self.engine._game_state._scores[1] = 1000

        # Player 0 tsumo, everyone pays 1000
        self.engine._game_state.update_score(1, -2000)  # Assume big hand
        self.engine._game_state.update_score(0, 6000)

        assert self.engine._game_state.scores[1] < 0

        self.engine.end_round([0])
        assert self.engine.get_phase() == GamePhase.ENDED

    def test_tobi_noten_bappu(self):
        """Test tobi (Bankruptcy): noten_bappu causes score < 0"""
        self._init_game()
        self.engine._game_state.ruleset.tobi_enabled = True

        # Set Player 1 score very low
        self.engine._game_state._scores[1] = 500

        # Set Player 0 tenpai, others noten
        tenpai_hand = Hand(parse_tiles("123456789m1234p"))
        noten_hand = Hand(parse_tiles("124578m1245p78s1z"))

        self.engine._hands[0] = tenpai_hand
        for i in range(1, 4):
            self.engine._hands[i] = noten_hand

        # Simulate ryuukyoku
        self.engine._tile_set._tiles = []
        self.engine.end_round(None)

        # Player 1 pays 1000, becomes -500
        assert self.engine._game_state.scores[1] == -500

        # Verify game ended
        assert self.engine.get_phase() == GamePhase.ENDED

    def test_tobi_disabled(self):
        """Test tobi Disabled"""
        self._init_game()
        self.engine._game_state.ruleset.tobi_enabled = False

        # Set Player 1 score negative
        self.engine._game_state.scores[1] = -1000

        # End round
        self.engine.end_round([0])

        # Verify game not ended (Next round or next wind)
        # Assuming not last round
        assert self.engine.get_phase() != GamePhase.ENDED
