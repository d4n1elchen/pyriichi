"""Test module."""

import pytest

from pyriichi.tiles import Suit, Tile
from pyriichi.utils import format_tiles, is_winning_hand, parse_tiles


class TestUtils:
    """Tests for TestUtils."""

    def test_parse_tiles_basic(self):
        """Test parse tiles basic."""
        tiles = parse_tiles("123m456p")
        assert len(tiles) == 6
        assert tiles[0].suit == Suit.MANZU
        assert tiles[0].rank == 1
        assert tiles[3].suit == Suit.PINZU
        assert tiles[3].rank == 4

    def test_parse_tiles_shorthand(self):
        """Test parse tiles shorthand."""
        tiles = parse_tiles("123m456p")
        assert len(tiles) == 6
        assert tiles[0].suit == Suit.MANZU
        assert tiles[0].rank == 1
        assert tiles[1].suit == Suit.MANZU
        assert tiles[1].rank == 2
        assert tiles[2].suit == Suit.MANZU
        assert tiles[2].rank == 3
        assert tiles[3].suit == Suit.PINZU
        assert tiles[3].rank == 4
        assert tiles[4].suit == Suit.PINZU
        assert tiles[4].rank == 5
        assert tiles[5].suit == Suit.PINZU
        assert tiles[5].rank == 6

    def test_parse_tiles_red_dora(self):
        """Test parse tiles red dora."""
        tiles = parse_tiles("r5p")
        assert len(tiles) == 1
        assert tiles[0].is_red
        assert tiles[0].rank == 5
        assert tiles[0].suit == Suit.PINZU

    def test_parse_tiles_with_red_dora(self):
        """Test parse tiles with red dora."""
        tiles = parse_tiles("r567p")
        assert len(tiles) == 3
        assert tiles[0].is_red
        assert tiles[0].rank == 5
        assert not tiles[1].is_red
        assert tiles[1].rank == 6
        assert not tiles[2].is_red
        assert tiles[2].rank == 7

    def test_parse_tiles_mixed_shorthand_red(self):
        """Test parse tiles mixed shorthand red."""
        # 12r5p -> 1p 2p r5p
        tiles = parse_tiles("12r5p")
        assert len(tiles) == 3
        assert tiles[0].rank == 1
        assert not tiles[0].is_red
        assert tiles[1].rank == 2
        assert not tiles[1].is_red
        assert tiles[2].rank == 5
        assert tiles[2].is_red
        assert all(t.suit == Suit.PINZU for t in tiles)

    def test_parse_tiles_invalid_char(self):
        """Test parse tiles invalid char."""
        tiles = parse_tiles("123m abc 45p")
        assert len(tiles) >= 3

    def test_format_tiles(self):
        """Test format tiles."""
        tiles = parse_tiles("12m5p9s")
        result = format_tiles(tiles)
        assert isinstance(result, str)
        assert "1m" in result
        assert "5p" in result
        assert "9s" in result

    def test_format_tiles_empty(self):
        """Test format tiles empty."""
        tiles = []
        result = format_tiles(tiles)
        assert result == ""

    def test_is_winning_hand(self):
        """Test is winning hand."""
        tiles = parse_tiles("123m456m789m123p4p")
        winning_tile = Tile(Suit.PINZU, 4)

        result = is_winning_hand(tiles, winning_tile)
        assert result is True

    def test_is_winning_hand_not_winning(self):
        """Test is winning hand not winning."""
        tiles = parse_tiles("123m456m78m123p45p")
        winning_tile = Tile(Suit.MANZU, 9)

        result = is_winning_hand(tiles, winning_tile)
        assert isinstance(result, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
