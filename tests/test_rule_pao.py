"""Pao tests for RuleEngine."""

from pyriichi.hand import Hand, Meld, MeldType
from pyriichi.tiles import Suit, Tile
from pyriichi.utils import parse_tiles
from pyriichi.yaku import Yaku
from tests.helpers import RuleEngineTestMixin


def _score_deltas(initial_scores, current_scores):
    return [
        current - initial for current, initial in zip(current_scores, initial_scores)
    ]


def _honor_pon(rank):
    tile = Tile(Suit.HONORS, rank)
    return Meld(MeldType.PON_MELD, [tile] * 3, called_tile=tile)


def _set_daisangen_pao_hand(engine, player, hand_str, pao_player):
    engine._hands[player] = Hand(parse_tiles(hand_str))
    engine._hands[player]._melds = [_honor_pon(5), _honor_pon(6), _honor_pon(7)]
    engine._pao_daisangen[player] = pao_player


def _prepare_final_honor_call(
    engine, player, responsible_player, called_tile, hand_str, meld_ranks
):
    hand = Hand(parse_tiles(hand_str))
    hand._melds = [_honor_pon(rank) for rank in meld_ranks]
    engine._hands[player] = hand
    engine._hands[responsible_player]._discards = [called_tile]
    engine._last_discarded_tile = called_tile
    engine._last_discarded_player = responsible_player


def _settle_win(engine, player, winning_tile):
    result = engine.check_win(player, winning_tile)
    engine.apply_win_score(result)
    engine.end_round([player])
    return result


class TestRulePao(RuleEngineTestMixin):
    def test_pao_daisangen_tsumo(self):
        """Test pao: daisangen tsumo, pao player pays all."""
        self._init_game()

        winning_tile = Tile(Suit.MANZU, 1)
        _set_daisangen_pao_hand(self.engine, 0, "11199m", pao_player=3)
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
        _prepare_final_honor_call(
            self.engine,
            player,
            responsible_player,
            called_tile,
            "77z123m456p789s1m",
            [5, 6],
        )

        self.engine._handle_pon(player)

        assert self.engine._pao_daisangen[player] == responsible_player

    def test_pao_daisuushi_tracks_final_wind_call(self):
        """Test pao_daisuushi tracks final wind call."""
        self._init_game()
        player = 0
        responsible_player = 2
        called_tile = Tile(Suit.HONORS, 4)
        _prepare_final_honor_call(
            self.engine,
            player,
            responsible_player,
            called_tile,
            "44z123m456p789s1m",
            [1, 2, 3],
        )

        self.engine._handle_pon(player)

        assert self.engine._pao_daisuushi[player] == responsible_player

    def test_pao_daisangen_ron_pao_player(self):
        """Test pao: daisangen ron pao player."""
        self._init_game()

        winning_tile = Tile(Suit.MANZU, 1)
        _set_daisangen_pao_hand(self.engine, 0, "1199m", pao_player=3)
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 3
        self.engine._current_player = 0
        initial_scores = self.engine._game_state.scores.copy()

        _settle_win(self.engine, 0, winning_tile)

        score_deltas = _score_deltas(initial_scores, self.engine._game_state.scores)
        assert score_deltas[0] > 0
        assert score_deltas[3] == -score_deltas[0]
        assert score_deltas[1] == 0
        assert score_deltas[2] == 0

    def test_pao_daisangen_ron_other(self):
        """Test pao: daisangen ron other."""
        self._init_game()

        winning_tile = Tile(Suit.MANZU, 1)
        _set_daisangen_pao_hand(self.engine, 0, "1199m", pao_player=3)
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0
        initial_scores = self.engine._game_state.scores.copy()

        _settle_win(self.engine, 0, winning_tile)

        score_deltas = _score_deltas(initial_scores, self.engine._game_state.scores)
        assert score_deltas[0] > 0
        assert score_deltas[1] == score_deltas[3]
        assert score_deltas[1] < 0
        assert score_deltas[0] == -(score_deltas[1] + score_deltas[3])
        assert score_deltas[2] == 0
