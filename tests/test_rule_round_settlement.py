"""Round settlement tests for RuleEngine."""

from pyriichi.game_state import Wind
from pyriichi.hand import Hand
from pyriichi.rules import GamePhase
from pyriichi.tiles import Suit, Tile
from pyriichi.utils import parse_tiles
from tests.helpers import (
    RuleEngineTestMixin,
    set_non_matching_scoring_dora,
    set_ron_context,
    set_tsumo_context,
)


TENPAI_HAND = "123456789m1234p"
NOTEN_HAND = "124578m1245p78s1z"


def _set_tenpai_players(engine, tenpai_players):
    tenpai_players = set(tenpai_players)
    for player in range(engine.get_num_players()):
        hand_str = TENPAI_HAND if player in tenpai_players else NOTEN_HAND
        engine._hands[player] = Hand(parse_tiles(hand_str))


def _end_exhaustive_draw(engine, tenpai_players):
    _set_tenpai_players(engine, tenpai_players)
    initial_scores = engine._game_state.scores.copy()
    engine._tile_set._tiles = []
    engine.end_round(None)
    return initial_scores


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

        initial_scores = _end_exhaustive_draw(self.engine, [0])

        assert self.engine._game_state.scores[0] == initial_scores[0] + 3000
        for i in range(1, 4):
            assert self.engine._game_state.scores[i] == initial_scores[i] - 1000

    def test_noten_bappu_two_tenpai(self):
        """Test noten_bappu: Two tenpai (+1500 / -1500)"""
        self._init_game()

        initial_scores = _end_exhaustive_draw(self.engine, [0, 1])

        assert self.engine._game_state.scores[0] == initial_scores[0] + 1500
        assert self.engine._game_state.scores[1] == initial_scores[1] + 1500
        assert self.engine._game_state.scores[2] == initial_scores[2] - 1500
        assert self.engine._game_state.scores[3] == initial_scores[3] - 1500

    def test_noten_bappu_three_tenpai(self):
        """Test noten_bappu: Three tenpai (+1000 / -3000)"""
        self._init_game()

        initial_scores = _end_exhaustive_draw(self.engine, [0, 1, 2])

        assert self.engine._game_state.scores[0] == initial_scores[0] + 1000
        assert self.engine._game_state.scores[1] == initial_scores[1] + 1000
        assert self.engine._game_state.scores[2] == initial_scores[2] + 1000
        assert self.engine._game_state.scores[3] == initial_scores[3] - 3000

    def test_noten_bappu_all_tenpai(self):
        """Test noten_bappu: All tenpai (0)"""
        self._init_game()

        initial_scores = _end_exhaustive_draw(self.engine, [0, 1, 2, 3])

        for i in range(4):
            assert self.engine._game_state.scores[i] == initial_scores[i]

    def test_noten_bappu_no_tenpai(self):
        """Test noten_bappu: No tenpai (0)"""
        self._init_game()

        initial_scores = _end_exhaustive_draw(self.engine, [])

        for i in range(4):
            assert self.engine._game_state.scores[i] == initial_scores[i]

    def test_exhaustive_draw_dealer_tenpai_renchan(self):
        """Test exhaustive_draw dealer tenpai renchan."""
        self._init_game()
        self.engine._game_state.set_dealer(0)
        self.engine._game_state.set_round(Wind.EAST, 1)
        self.engine._game_state._honba = 0
        _set_tenpai_players(self.engine, [0])
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
        _set_tenpai_players(self.engine, [1])
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
        set_non_matching_scoring_dora(self.engine)
        winning_tile = Tile(Suit.PINZU, 4)
        set_ron_context(self.engine, 0, 1, TENPAI_HAND, winning_tile)

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
        self.engine._game_state._scores[1] = 1000
        set_non_matching_scoring_dora(self.engine)
        winning_tile = Tile(Suit.PINZU, 4)
        set_tsumo_context(self.engine, 0, "123456789m12344p", winning_tile)

        result = self.engine.check_win(0, winning_tile)

        assert result is not None
        assert result.score_result.is_tsumo is True
        self.engine.apply_win_score(result)
        assert self.engine._game_state.scores[1] < 0

        self.engine.end_round([0])
        assert self.engine.get_phase() == GamePhase.ENDED

    def test_tobi_noten_bappu(self):
        """Test tobi (Bankruptcy): noten_bappu causes score < 0"""
        self._init_game()
        self.engine._game_state.ruleset.tobi_enabled = True

        # Set Player 1 score very low
        self.engine._game_state._scores[1] = 500

        _set_tenpai_players(self.engine, [0])
        self.engine._tile_set._tiles = []
        self.engine.end_round(None)

        assert self.engine._game_state.scores[1] == -500

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
