"""Win-context tests for RuleEngine."""

from pyriichi.hand import Hand, Meld, MeldType
from pyriichi.rules import GamePhase
from pyriichi.tiles import Suit, Tile
from pyriichi.utils import parse_tiles
from pyriichi.yaku import Yaku
from tests.helpers import (
    RuleEngineTestMixin,
    set_non_matching_scoring_dora,
)


class TestWinContext(RuleEngineTestMixin):
    def test_check_chankan(self):
        """Test chankan check"""
        self._init_game()
        self.engine._is_first_turn_after_deal = False
        set_non_matching_scoring_dora(self.engine)

        # Set Player 0 can chankan (machi 6p, tanyao)
        # hand: 234m 567m 234p 66p 78p (machi 6p/9p)
        test_tiles = parse_tiles("234567m2346678p")
        self.engine._hands[0] = Hand(test_tiles)

        # Check chankan
        kan_tile = Tile(Suit.PINZU, 6)

        # check_win needs pending_kan_tile to set payer
        # Assume Player 1 open_kan 6p
        self.engine._pending_kan_tile = (1, kan_tile)

        result = self.engine.check_win(0, kan_tile, is_chankan=True)
        assert result is not None
        assert result.win is True
        assert result.chankan is True
        assert {y.yaku for y in result.yaku} == {Yaku.CHANKAN, Yaku.TANYAO}
        assert result.score_result.payment_from == 1

    def test_false_tsumo_applies_chombo(self):
        """Test false tsumo applies chombo."""
        self._init_game()
        player = 1
        self.engine._game_state.set_dealer(0)
        self.engine._hands[player] = Hand(parse_tiles("124578m1245p78s1z"))
        tile = Tile(Suit.HONORS, 1)
        self.engine._hands[player].add_tile(tile)
        initial_scores = self.engine._game_state.scores.copy()

        result = self.engine._handle_tsumo(player, tile=tile)

        assert result.chombo is True
        assert result.chombo_player == player
        assert self.engine.get_phase() == GamePhase.RYUUKYOKU
        assert self.engine._game_state.scores[player] == initial_scores[player] - 8000
        assert self.engine._game_state.scores[0] == initial_scores[0] + 4000

    def test_false_ron_applies_chombo(self):
        """Test false ron applies chombo."""
        self._init_game()
        player = 1
        self.engine._game_state.set_dealer(0)
        winning_tile = Tile(Suit.PINZU, 4)
        self.engine._hands[player] = Hand(parse_tiles("124578m1245p78s1z"))
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 0
        initial_scores = self.engine._game_state.scores.copy()

        result = self.engine._handle_ron(player)

        assert result.chombo is True
        assert result.chombo_player == player
        assert self.engine.get_phase() == GamePhase.RYUUKYOKU
        assert self.engine._game_state.scores[player] == initial_scores[player] - 8000
        assert self.engine._game_state.scores[0] == initial_scores[0] + 4000

    def test_check_win_rinshan(self):
        """Test rinshan win check"""
        self._init_game()
        self.engine._is_first_turn_after_deal = False
        set_non_matching_scoring_dora(self.engine)
        # Set a hand that can win on rinshan
        # Create a winning hand
        # hand: 123m 456m 789m 123p 4p (rinshan tile 4p)
        self.engine._hands[0] = Hand(parse_tiles("123456789m12344p"))
        self.engine._current_player = 0

        # Check rinshan win
        rinshan_tile = Tile(Suit.PINZU, 4)
        result = self.engine.check_win(0, rinshan_tile, is_rinshan=True)
        assert result is not None
        assert result.win is True
        assert result.rinshan is True
        assert {y.yaku for y in result.yaku} == {
            Yaku.MENZEN_TSUMO,
            Yaku.RINSHAN,
            Yaku.ITTSU,
        }
        assert result.score_result.is_tsumo is True

    def test_check_win_tsumo_sets_is_tsumo(self):
        """Test Tumo sets score_result.is_tsumo to True"""
        self._init_game()
        self.engine._is_first_turn_after_deal = False
        set_non_matching_scoring_dora(self.engine)
        player = self.engine.get_current_player()
        winning_tile = Tile(Suit.PINZU, 4)
        # Concealed hand: 123m 456m 789m 123p + 4p
        self.engine._hands[player] = Hand(parse_tiles("123456789m12344p"))
        # Simulate just drawn winning tile
        self.engine._last_drawn_tile = (player, winning_tile)
        result = self.engine.check_win(player, winning_tile)
        assert result is not None
        assert {y.yaku for y in result.yaku} == {Yaku.MENZEN_TSUMO, Yaku.ITTSU}
        assert result.score_result.is_tsumo is True
        assert result.score_result.payment_from == 0

    def test_check_win_ron_when_turn_passes(self):
        """Test ron after other player discards is not mistaken for tsumo"""
        self._init_game()
        discarder = 0
        winner = (discarder + 1) % self.engine.get_num_players()
        winning_tile = Tile(Suit.PINZU, 4)
        self.engine._is_first_turn_after_deal = False
        set_non_matching_scoring_dora(self.engine)
        self.engine._hands[winner] = Hand(parse_tiles("123456789m1234p"))
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = discarder
        # Simulate turn passed to next player (actually ron state)
        self.engine._current_player = winner
        self.engine._last_drawn_tile = None
        result = self.engine.check_win(winner, winning_tile)
        assert result is not None
        assert {y.yaku for y in result.yaku} == {Yaku.ITTSU}
        assert result.score_result.is_tsumo is False
        assert result.score_result.payment_from == discarder

    def test_check_win_no_combinations(self):
        """Test check_win with no winning combinations"""
        self._init_game()
        # Create a non-winning hand
        # 123m 456m 78m 123p 45p
        test_tiles = parse_tiles("12345678m12345p")
        test_hand = Hand(test_tiles)
        self.engine._hands[0] = test_hand

        # Check win (Should return None because no winning combinations)
        winning_tile = Tile(Suit.MANZU, 9)
        result = self.engine.check_win(0, winning_tile)
        assert result is None

    def test_check_win_no_yaku(self):
        """Test No yaku"""
        self._init_game()
        # 234m 567m 789m 2p 4p 22s
        tiles = parse_tiles("234567789m24p22s")

        hand = Hand(tiles)
        # Set hand to not concealed
        hand._melds.append(Meld(MeldType.PON_MELD, parse_tiles("1s1s1s")))
        # Set last discard to 3p, test ron
        winning_tile = Tile(Suit.PINZU, 3)
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1

        self.engine._last_discarded_player = 1

        # Set hand to player 0
        self.engine._hands[0] = hand
        self.engine._current_player = 2

        # Check win (Not concealed and no other yaku, should return None)
        result = self.engine.check_win(0, winning_tile)
        assert result is None
