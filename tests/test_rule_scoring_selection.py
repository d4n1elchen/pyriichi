"""Scoring interpretation tests for RuleEngine."""

from pyriichi.hand import Hand
from pyriichi.rules import RuleEngine
from pyriichi.tiles import Suit, Tile
from pyriichi.utils import parse_tiles
from pyriichi.yaku import Yaku


class TestHighScoringMethod:
    def test_ambiguous_hand_pinfu_vs_triplet(self):
        # 111222333m.
        # 111 222 333 (Triplet).
        # 123 123 123 (Sequence).
        # This is a classic case!

        tiles = parse_tiles("111m222m333m678p55s")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 1)  # Win on 1m

        combinations = hand.get_winning_combinations(winning_tile, is_tsumo=True)

        assert len(combinations) >= 2, "Should have at least 2 interpretations"

        engine = RuleEngine()
        engine.start_game()
        engine.start_round()
        engine.deal()

        # Simulate game state
        engine._hands[0] = hand

        # Set last drawn tile to simulate tsumo
        engine._last_drawn_tile = (0, winning_tile)

        # Disable tenhou/chihou/renhou
        engine._is_first_turn_after_deal = False

        # Calculate score
        result = engine.check_win(0, winning_tile)

        assert result is not None

        assert any(y.yaku == Yaku.SANANKOU for y in result.yaku)
