"""
Unit tests for RuleEngine
"""

import pytest

from pyriichi.game_state import Wind
from pyriichi.hand import Hand, Meld, MeldType
from pyriichi.rules import (
    GameAction,
    GamePhase,
    RuleEngine,
)
from pyriichi.tiles import Suit, Tile, TileSet
from pyriichi.utils import parse_tiles
from pyriichi.yaku import Yaku
from tests.helpers import (
    RuleEngineTestMixin,
    set_non_matching_scoring_dora,
)


class TestRuleEngine(RuleEngineTestMixin):
    """Rule Engine Tests"""

    def test_start_game(self):
        """Test start game"""
        self.engine.start_game()
        assert self.engine.get_phase() == GamePhase.INIT

    def test_start_round(self):
        """Test start round"""
        self.engine.start_game()
        self.engine.start_round()
        assert self.engine.get_phase() == GamePhase.DEALING

    def test_deal(self):
        """Test deal"""
        self.engine.start_game()
        self.engine.start_round()
        hands = self.engine.deal()

        assert len(hands) == 4
        # dealer should have 14 tiles, others 13
        assert len(hands[0]) == 14
        assert len(hands[1]) == 13
        assert len(hands[2]) == 13
        assert len(hands[3]) == 13

        assert self.engine.get_phase() == GamePhase.PLAYING

    def test_deal_uses_current_dealer(self):
        """Test deal uses current dealer."""
        self.engine.start_game()
        self.engine.game_state.set_dealer(2)
        self.engine.start_round()
        hands = self.engine.deal()

        assert len(hands) == 4
        assert len(hands[0]) == 13
        assert len(hands[1]) == 13
        assert len(hands[2]) == 14
        assert len(hands[3]) == 13
        assert self.engine.get_current_player() == 2
        assert self.engine.get_available_actions(2)
        assert not self.engine.get_available_actions(0)

    def test_check_win_allows_kokushi_musou_ron(self):
        """Test check_win allows kokushi_musou ron."""
        self._init_game()
        winning_tile = Tile(Suit.HONORS, 1)
        self.engine._hands[1] = Hand(parse_tiles("19m19p19s22z3z4z5z6z7z"))
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 0
        self.engine._is_first_turn_after_deal = False

        result = self.engine.check_win(1, winning_tile)

        assert result is not None
        assert result.win
        assert any(yaku.yaku == Yaku.KOKUSHI_MUSOU for yaku in result.yaku)

    def test_check_win_allows_kokushi_musou_tsumo(self):
        """Test check_win allows kokushi_musou tsumo."""
        self._init_game()
        winning_tile = Tile(Suit.HONORS, 7)
        self.engine._hands[1] = Hand(parse_tiles("19m19p19s1z2z3z4z5z6z77z"))
        self.engine._last_drawn_tile = (1, winning_tile)
        self.engine._is_first_turn_after_deal = False

        result = self.engine.check_win(1, winning_tile)

        assert result is not None
        assert result.win
        assert any(yaku.yaku == Yaku.KOKUSHI_MUSOU for yaku in result.yaku)

    def test_check_win_uses_non_dealer_payment_context(self):
        """Test check_win uses non-dealer payment context."""
        self._init_game()
        winning_tile = Tile(Suit.SOUZU, 5)
        hand = Hand(parse_tiles("123m456m789m123p5s"))
        hand.set_riichi(True)
        self.engine._hands[1] = hand
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 0
        self.engine._is_first_turn_after_deal = False
        set_non_matching_scoring_dora(self.engine)

        result = self.engine.check_win(1, winning_tile)

        assert result is not None
        assert result.score_result.payment_to == 1
        assert result.score_result.payment_from == 0
        assert result.score_result.total_points == 5200


    def test_hand_total_tile_count_includes_melds(self):
        """Total tile count should include melded tiles."""
        # 11m 123m 456p 77s 8s 99s
        tiles = parse_tiles("11123m456p77899s")

        hand = Hand(tiles)
        assert hand.total_tile_count() == 13

        meld = hand.pon(Tile(Suit.MANZU, 1))
        assert meld is not None
        assert len(hand.tiles) == 11
        assert hand.total_tile_count() == 14

    def test_get_hand_invalid_player(self):
        """Test get_hand invalid player error"""
        self._init_game()
        # Test invalid player index
        with pytest.raises(ValueError, match="玩家位置必須在"):
            self.engine.get_hand(-1)

        with pytest.raises(ValueError, match="玩家位置必須在"):
            self.engine.get_hand(4)

    def test_get_discards_invalid_player(self):
        """Test get_discards invalid player error"""
        self._init_game()
        # Test invalid player index
        with pytest.raises(ValueError, match="玩家位置必須在"):
            self.engine.get_discards(-1)

        with pytest.raises(ValueError, match="玩家位置必須在"):
            self.engine.get_discards(4)

    def test_deal_wrong_phase(self):
        """Test deal in wrong phase"""
        self.engine.start_game()
        # Not in dealing phase
        self.engine._phase = GamePhase.PLAYING
        with pytest.raises(ValueError, match="只能在發牌階段發牌"):
            self.engine.deal()

    def test_deal_no_tile_set(self):
        self.engine.start_game()
        self.engine.start_round()
        # Manually initialize hands because deal() was not called
        self.engine._hands = [Hand([]) for _ in range(4)]
        self.engine._tile_set = None
        # Directly call _handle_draw
        # Ensure hand is not full
        hand = self.engine.get_hand(0)
        if hand.total_tile_count() >= 14:
            hand.tiles.pop()

        # Error message might be "Tile set not initialized" or similar, loose check here
        with pytest.raises(ValueError):
            self.engine._handle_draw(0)






