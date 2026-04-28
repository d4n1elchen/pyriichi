"""Test module."""

import pytest
from pyriichi.tiles import Tile, Suit, TileSet, create_tile


class TestTile:
    """Tests for TestTile."""

    def test_tile_creation(self):
        """Test tile creation."""
        tile = Tile(Suit.MANZU, 1)
        assert tile.suit == Suit.MANZU
        assert tile.rank == 1

    def test_tile_creation_invalid_rank_honors(self):
        """Test tile creation invalid rank honors."""
        with pytest.raises(ValueError, match="字牌 rank 必須在 1-7 之間"):
            Tile(Suit.HONORS, 0)

        with pytest.raises(ValueError, match="字牌 rank 必須在 1-7 之間"):
            Tile(Suit.HONORS, 8)

    def test_tile_creation_invalid_rank_number(self):
        """Test tile creation invalid rank number."""
        with pytest.raises(ValueError, match="數牌 rank 必須在 1-9 之間"):
            Tile(Suit.MANZU, 0)

        with pytest.raises(ValueError, match="數牌 rank 必須在 1-9 之間"):
            Tile(Suit.MANZU, 10)

    def test_tile_red_dora(self):
        """Test tile red_dora."""
        tile = Tile(Suit.PINZU, 5, is_red_dora=True)
        assert tile.is_red_dora == True

    def test_tile_properties(self):
        """Test tile properties."""
        tile = Tile(Suit.MANZU, 1)
        assert tile.is_terminal == True
        assert tile.is_simple == False
        assert tile.is_honor == False

        tile = Tile(Suit.MANZU, 5)
        assert tile.is_terminal == False
        assert tile.is_simple == True

        tile = Tile(Suit.HONORS, 1)
        assert tile.is_honor == True
        assert tile.is_terminal == False
        assert tile.is_simple == False

    def test_tile_eq(self):
        """Test tile eq."""
        tile1 = Tile(Suit.MANZU, 1)
        tile2 = Tile(Suit.MANZU, 1)
        tile3 = Tile(Suit.MANZU, 2)

        assert tile1 == tile2
        assert tile1 != tile3

        assert tile1 != "1m"
        assert tile1 != None

    def test_tile_hash(self):
        """Test tile hash."""
        tile1 = Tile(Suit.MANZU, 1)
        tile2 = Tile(Suit.MANZU, 1)
        tile3 = Tile(Suit.MANZU, 2)

        assert hash(tile1) == hash(tile2)
        assert hash(tile1) != hash(tile3)

        tile_set = {tile1, tile2, tile3}
        assert len(tile_set) == 2

    def test_tile_lt(self):
        """Test tile lt."""
        tile1 = Tile(Suit.MANZU, 1)
        tile2 = Tile(Suit.MANZU, 2)
        tile3 = Tile(Suit.PINZU, 1)

        assert tile1 < tile2
        assert tile1 < tile3

        result = tile1.__lt__("1m")
        assert result is NotImplemented

    def test_tile_str_red_dora(self):
        """Test tile str red_dora."""
        tile = Tile(Suit.PINZU, 5, is_red_dora=True)
        tile_str = str(tile)
        assert tile_str == "r5p"
        assert tile_str.startswith("r")
        assert "5" in tile_str
        assert "p" in tile_str

    def test_tile_repr(self):
        """Test tile repr."""
        tile = Tile(Suit.MANZU, 1, is_red_dora=False)
        repr_str = repr(tile)
        assert "Tile" in repr_str
        assert "MANZU" in repr_str
        assert "1" in repr_str

    def test_create_tile_invalid_suit(self):
        """Test create tile invalid suit."""
        with pytest.raises(ValueError, match="無效的花色"):
            create_tile("x", 1)


class TestTileSet:
    """Tests for TestTileSet."""

    def test_tileset_creation(self):
        """Test tileset creation."""
        tile_set = TileSet()
        assert tile_set is not None

    def test_tileset_shuffle(self):
        """Test tileset shuffle."""
        tile_set = TileSet()
        tiles_before = tile_set._tiles.copy()
        tile_set.shuffle()
        assert len(tile_set._tiles) == len(tiles_before) - 14

    def test_tileset_deal(self):
        """Test tileset deal."""
        tile_set = TileSet()
        hands = tile_set.deal(num_players=4)
        assert len(hands) == 4
        assert len(hands[0]) == 14
        for i in range(1, 4):
            assert len(hands[i]) == 13

    def test_tileset_draw(self):
        """Test tileset draw."""
        tile_set = TileSet()
        tile_set.shuffle()
        initial_count = len(tile_set._tiles)
        tile = tile_set.draw()
        assert tile is not None
        assert len(tile_set._tiles) == initial_count - 1

    def test_tileset_draw_empty(self):
        """Test tileset draw empty."""
        tile_set = TileSet()
        tile_set.shuffle()
        while tile_set._tiles:
            tile_set.draw()
        tile = tile_set.draw()
        assert tile is None

    def test_tileset_draw_rinshan_tile(self):
        """Test tileset draw rinshan tile."""
        tile_set = TileSet()
        tile_set.shuffle()
        if tile_set._rinshan_tiles:
            tile = tile_set.draw_rinshan()
            assert tile is not None

        while tile_set._rinshan_tiles:
            tile_set.draw_rinshan()
        tile = tile_set.draw_rinshan()
        assert tile is None

    def test_tileset_remaining(self):
        """Test tileset remaining."""
        tile_set = TileSet()
        tile_set.shuffle()
        initial_remaining = tile_set.remaining
        assert initial_remaining > 0

        tile_set.draw()
        assert tile_set.remaining == initial_remaining - 1

    def test_tileset_is_exhausted(self):
        """Test tileset is exhausted."""
        tile_set = TileSet()
        tile_set.shuffle()
        assert not tile_set.is_exhausted()

        while tile_set._tiles:
            tile_set.draw()
        assert tile_set.is_exhausted()

    def test_tileset_get_dora_indicator(self):
        """Test tileset get dora indicator."""
        tile_set = TileSet()
        tile_set.shuffle()

        indicators = tile_set.get_dora_indicators()
        assert indicators is not None
        assert len(indicators) == 1

        ura_indicators = tile_set.get_ura_dora_indicators()
        assert ura_indicators is not None
        assert len(ura_indicators) == 1

    def test_tileset_get_dora(self):
        """Test tileset get dora."""
        tile_set = TileSet()

        indicator_north = Tile(Suit.HONORS, 4)
        dora = tile_set.get_dora(indicator_north)
        assert dora.suit == Suit.HONORS
        assert dora.rank == 1

        indicator_haku = Tile(Suit.HONORS, 5)
        dora = tile_set.get_dora(indicator_haku)
        assert dora.suit == Suit.HONORS
        assert dora.rank == 6

        indicator_hatsu = Tile(Suit.HONORS, 6)
        dora = tile_set.get_dora(indicator_hatsu)
        assert dora.suit == Suit.HONORS
        assert dora.rank == 7

        indicator_chun = Tile(Suit.HONORS, 7)
        dora = tile_set.get_dora(indicator_chun)
        assert dora.suit == Suit.HONORS
        assert dora.rank == 1

        indicator_9 = Tile(Suit.MANZU, 9)
        dora = tile_set.get_dora(indicator_9)
        assert dora.suit == Suit.MANZU
        assert dora.rank == 1

        indicator_5 = Tile(Suit.MANZU, 5)
        dora = tile_set.get_dora(indicator_5)
        assert dora.suit == Suit.MANZU
        assert dora.rank == 6

    def test_create_tile(self):
        """Test create tile."""
        tile = create_tile("m", 1)
        assert tile.suit == Suit.MANZU
        assert tile.rank == 1

        tile = create_tile("p", 5, is_red_dora=True)
        assert tile.suit == Suit.PINZU
        assert tile.rank == 5
        assert tile.is_red_dora == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
