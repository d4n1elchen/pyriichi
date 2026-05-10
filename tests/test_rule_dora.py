"""Dora-counting tests for RuleEngine."""

from pyriichi.hand import Hand
from pyriichi.tiles import Suit, Tile
from pyriichi.utils import parse_tiles
from tests.helpers import RuleEngineTestMixin, set_non_matching_scoring_dora


class TestRuleDora(RuleEngineTestMixin):
    def test_count_dora_zero(self):
        """Test zero dora count."""
        self._init_game()
        set_non_matching_scoring_dora(self.engine)
        self.engine._hands[0] = Hand(parse_tiles("1111234567999m"))

        dora_count = self.engine._count_dora(0, Tile(Suit.MANZU, 1))

        assert dora_count == 0

    def test_count_dora_one(self):
        """Test dora count."""
        self._init_game()
        test_hand = Hand(parse_tiles("1111234567999m"))
        self.engine._hands[0] = test_hand
        self.engine._tile_set._dora_indicators = [Tile(Suit.MANZU, 9)]
        self.engine._tile_set._ura_dora_indicators = [Tile(Suit.PINZU, 9)]

        dora_count = self.engine._count_dora(0, Tile(Suit.MANZU, 1))

        assert dora_count == 5

        test_hand.set_riichi(True)
        self.engine._tile_set._ura_dora_indicators = [Tile(Suit.MANZU, 9)]
        dora_count = self.engine._count_dora(0, Tile(Suit.MANZU, 1))
        assert dora_count == 10

        red_dora_tiles = parse_tiles("r5p")
        test_hand = Hand(red_dora_tiles)
        self.engine._hands[0] = test_hand
        set_non_matching_scoring_dora(self.engine)
        dora_count = self.engine._count_dora(0, Tile(Suit.PINZU, 5))
        assert dora_count == 1

    def test_count_dora_uses_initial_and_kan_indicators(self):
        """Test dora count uses initial and kan indicators."""
        self._init_game()
        self.engine._hands[0] = Hand(parse_tiles("5m5p123456789s1z"))
        self.engine._tile_set._dora_indicators = [
            Tile(Suit.MANZU, 4),
            Tile(Suit.PINZU, 4),
        ]

        self.engine._kan_count = 0
        assert self.engine._count_dora(0) == 1

        self.engine._kan_count = 1
        assert self.engine._count_dora(0) == 2

    def test_count_ura_dora_uses_initial_indicator(self):
        """Test ura_dora count uses the initial indicator."""
        self._init_game()
        self.engine._hands[0] = Hand(parse_tiles("5m123456789s123p"))
        self.engine._hands[0].set_riichi(True)
        self.engine._tile_set._dora_indicators = [Tile(Suit.PINZU, 8)]
        self.engine._tile_set._ura_dora_indicators = [Tile(Suit.MANZU, 4)]

        assert self.engine._count_dora(0) == 1
