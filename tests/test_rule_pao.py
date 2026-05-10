"""Pao tests for RuleEngine."""

from pyriichi.hand import Hand, Meld, MeldType
from pyriichi.tiles import Suit, Tile
from pyriichi.utils import parse_tiles
from pyriichi.yaku import Yaku
from tests.helpers import RuleEngineTestMixin


def _score_deltas(initial_scores, current_scores):
    return [current - initial for current, initial in zip(current_scores, initial_scores)]


class TestRulePao(RuleEngineTestMixin):
    def test_pao_daisangen_tsumo(self):
        """Test pao: daisangen tsumo, pao player pays all."""
        self._init_game()

        self.engine._hands[0] = Hand(parse_tiles("11199m"))
        meld_haku = Meld(MeldType.PON_MELD, [Tile(Suit.HONORS, 5)] * 3, 1)
        meld_hatsu = Meld(MeldType.PON_MELD, [Tile(Suit.HONORS, 6)] * 3, 2)
        meld_chun = Meld(MeldType.PON_MELD, [Tile(Suit.HONORS, 7)] * 3, 3)
        self.engine._hands[0]._melds = [meld_haku, meld_hatsu, meld_chun]
        self.engine._pao_daisangen[0] = 3

        winning_tile = Tile(Suit.MANZU, 1)
        self.engine._current_player = 0
        self.engine._last_drawn_tile = (0, winning_tile)
        initial_scores = self.engine._game_state.scores.copy()

        result = self.engine.check_win(0, winning_tile)
        assert result is not None
        assert result.win
        assert any(y.yaku == Yaku.DAISANGEN for y in result.yaku)

        self.engine.apply_win_score(result)
        self.engine.end_round([0])

        score_deltas = _score_deltas(initial_scores, self.engine._game_state.scores)
        assert score_deltas[0] > 0
        assert score_deltas[3] == -score_deltas[0]
        assert score_deltas[1] == 0
        assert score_deltas[2] == 0

    def test_pao_daisangen_tracks_final_dragon_call(self):
        """Test pao_daisangen tracks final dragon call."""
        self._init_game()
        player = 0
        responsible_player = 3
        called_tile = Tile(Suit.HONORS, 7)
        hand = Hand(parse_tiles("77z123m456p789s1m"))
        hand._melds = [
            Meld(
                MeldType.PON_MELD,
                [Tile(Suit.HONORS, 5)] * 3,
                called_tile=Tile(Suit.HONORS, 5),
            ),
            Meld(
                MeldType.PON_MELD,
                [Tile(Suit.HONORS, 6)] * 3,
                called_tile=Tile(Suit.HONORS, 6),
            ),
        ]
        self.engine._hands[player] = hand
        self.engine._hands[responsible_player]._discards = [called_tile]
        self.engine._last_discarded_tile = called_tile
        self.engine._last_discarded_player = responsible_player

        self.engine._handle_pon(player)

        assert self.engine._pao_daisangen[player] == responsible_player

    def test_pao_daisuushi_tracks_final_wind_call(self):
        """Test pao_daisuushi tracks final wind call."""
        self._init_game()
        player = 0
        responsible_player = 2
        called_tile = Tile(Suit.HONORS, 4)
        hand = Hand(parse_tiles("44z123m456p789s1m"))
        hand._melds = [
            Meld(
                MeldType.PON_MELD,
                [Tile(Suit.HONORS, 1)] * 3,
                called_tile=Tile(Suit.HONORS, 1),
            ),
            Meld(
                MeldType.PON_MELD,
                [Tile(Suit.HONORS, 2)] * 3,
                called_tile=Tile(Suit.HONORS, 2),
            ),
            Meld(
                MeldType.PON_MELD,
                [Tile(Suit.HONORS, 3)] * 3,
                called_tile=Tile(Suit.HONORS, 3),
            ),
        ]
        self.engine._hands[player] = hand
        self.engine._hands[responsible_player]._discards = [called_tile]
        self.engine._last_discarded_tile = called_tile
        self.engine._last_discarded_player = responsible_player

        self.engine._handle_pon(player)

        assert self.engine._pao_daisuushi[player] == responsible_player

    def test_pao_daisangen_ron_pao_player(self):
        """Test pao: daisangen ron pao player."""
        self._init_game()

        self.engine._hands[0] = Hand(parse_tiles("1199m"))
        meld_haku = Meld(MeldType.PON_MELD, [Tile(Suit.HONORS, 5)] * 3, 1)
        meld_hatsu = Meld(MeldType.PON_MELD, [Tile(Suit.HONORS, 6)] * 3, 2)
        meld_chun = Meld(MeldType.PON_MELD, [Tile(Suit.HONORS, 7)] * 3, 3)
        self.engine._hands[0]._melds = [meld_haku, meld_hatsu, meld_chun]
        self.engine._pao_daisangen[0] = 3

        winning_tile = Tile(Suit.MANZU, 1)
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 3
        self.engine._current_player = 0
        initial_scores = self.engine._game_state.scores.copy()

        result = self.engine.check_win(0, winning_tile)
        self.engine.apply_win_score(result)
        self.engine.end_round([0])

        score_deltas = _score_deltas(initial_scores, self.engine._game_state.scores)
        assert score_deltas[0] > 0
        assert score_deltas[3] == -score_deltas[0]
        assert score_deltas[1] == 0
        assert score_deltas[2] == 0

    def test_pao_daisangen_ron_other(self):
        """Test pao: daisangen ron other."""
        self._init_game()

        self.engine._hands[0] = Hand(parse_tiles("1199m"))
        meld_haku = Meld(MeldType.PON_MELD, [Tile(Suit.HONORS, 5)] * 3, 1)
        meld_hatsu = Meld(MeldType.PON_MELD, [Tile(Suit.HONORS, 6)] * 3, 2)
        meld_chun = Meld(MeldType.PON_MELD, [Tile(Suit.HONORS, 7)] * 3, 3)
        self.engine._hands[0]._melds = [meld_haku, meld_hatsu, meld_chun]
        self.engine._pao_daisangen[0] = 3

        winning_tile = Tile(Suit.MANZU, 1)
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0
        initial_scores = self.engine._game_state.scores.copy()

        result = self.engine.check_win(0, winning_tile)
        self.engine.apply_win_score(result)
        self.engine.end_round([0])

        score_deltas = _score_deltas(initial_scores, self.engine._game_state.scores)
        assert score_deltas[0] > 0
        assert score_deltas[1] == score_deltas[3]
        assert score_deltas[1] < 0
        assert score_deltas[0] == -(score_deltas[1] + score_deltas[3])
        assert score_deltas[2] == 0
