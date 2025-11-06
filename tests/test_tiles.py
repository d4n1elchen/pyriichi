"""
Tile 和 TileSet 的單元測試
"""

import pytest
from pyriichi.tiles import Tile, Suit, TileSet, create_tile


class TestTile:
    """Tile 類測試"""

    def test_tile_creation(self):
        """測試牌的基本創建"""
        tile = Tile(Suit.MANZU, 1)
        assert tile.suit == Suit.MANZU
        assert tile.rank == 1

    def test_tile_creation_invalid_rank_jihai(self):
        """測試字牌無效 rank 錯誤"""
        # 字牌 rank 必須在 1-7 之間
        with pytest.raises(ValueError, match="字牌 rank 必須在 1-7 之間"):
            Tile(Suit.JIHAI, 0)  # 無效 rank

        with pytest.raises(ValueError, match="字牌 rank 必須在 1-7 之間"):
            Tile(Suit.JIHAI, 8)  # 無效 rank

    def test_tile_creation_invalid_rank_number(self):
        """測試數牌無效 rank 錯誤"""
        # 數牌 rank 必須在 1-9 之間
        with pytest.raises(ValueError, match="數牌 rank 必須在 1-9 之間"):
            Tile(Suit.MANZU, 0)  # 無效 rank

        with pytest.raises(ValueError, match="數牌 rank 必須在 1-9 之間"):
            Tile(Suit.MANZU, 10)  # 無效 rank

    def test_tile_red_dora(self):
        """測試紅寶牌"""
        tile = Tile(Suit.PINZU, 5, is_red=True)
        assert tile.is_red == True

    def test_tile_properties(self):
        """測試牌的屬性"""
        tile = Tile(Suit.MANZU, 1)
        assert tile.is_terminal == True
        assert tile.is_simple == False
        assert tile.is_honor == False

        tile = Tile(Suit.MANZU, 5)
        assert tile.is_terminal == False
        assert tile.is_simple == True

        tile = Tile(Suit.JIHAI, 1)
        assert tile.is_honor == True
        assert tile.is_terminal == False
        # 字牌 is_simple 應該返回 False
        assert tile.is_simple == False

    def test_tile_eq(self):
        """測試牌的相等性比較"""
        tile1 = Tile(Suit.MANZU, 1)
        tile2 = Tile(Suit.MANZU, 1)
        tile3 = Tile(Suit.MANZU, 2)

        assert tile1 == tile2
        assert tile1 != tile3

        # 測試與非 Tile 對象比較
        assert tile1 != "1m"
        assert tile1 != None

    def test_tile_hash(self):
        """測試牌的哈希值"""
        tile1 = Tile(Suit.MANZU, 1)
        tile2 = Tile(Suit.MANZU, 1)
        tile3 = Tile(Suit.MANZU, 2)

        # 相同牌應該有相同哈希值
        assert hash(tile1) == hash(tile2)
        # 不同牌應該有不同的哈希值（通常）
        assert hash(tile1) != hash(tile3)

        # 可以放入集合
        tile_set = {tile1, tile2, tile3}
        assert len(tile_set) == 2  # tile1 和 tile2 相同

    def test_tile_lt(self):
        """測試牌的排序"""
        tile1 = Tile(Suit.MANZU, 1)
        tile2 = Tile(Suit.MANZU, 2)
        tile3 = Tile(Suit.PINZU, 1)

        assert tile1 < tile2
        assert tile1 < tile3  # 萬子 < 筒子

        # 測試與非 Tile 對象比較
        result = tile1.__lt__("1m")
        assert result is NotImplemented

    def test_tile_str_red_dora(self):
        """測試牌的字符串表示（標準格式：r5p）"""
        tile = Tile(Suit.PINZU, 5, is_red=True)
        tile_str = str(tile)
        # 紅寶牌應該用 r 前綴（標準格式）
        assert tile_str == "r5p"
        assert tile_str.startswith("r")
        assert "5" in tile_str
        assert "p" in tile_str

    def test_tile_repr(self):
        """測試牌的對象表示"""
        tile = Tile(Suit.MANZU, 1, is_red=False)
        repr_str = repr(tile)
        assert "Tile" in repr_str
        assert "MANZU" in repr_str
        assert "1" in repr_str

    def test_create_tile_invalid_suit(self):
        """測試 create_tile 無效花色錯誤"""
        with pytest.raises(ValueError, match="無效的花色"):
            create_tile("x", 1)  # 無效花色


class TestTileSet:
    """TileSet 類測試"""

    def test_tileset_creation(self):
        """測試牌組創建"""
        tile_set = TileSet()
        assert tile_set is not None

    def test_tileset_shuffle(self):
        """測試洗牌"""
        tile_set = TileSet()
        tiles_before = tile_set._tiles.copy()
        tile_set.shuffle()
        # 洗牌後順序應該不同（高概率）
        # 注意：由於隨機性，這裡只檢查是否執行
        # 洗牌後會移除王牌區（14張），所以 _tiles 會減少
        assert len(tile_set._tiles) == len(tiles_before) - 14

    def test_tileset_deal(self):
        """測試發牌"""
        tile_set = TileSet()
        hands = tile_set.deal(num_players=4)
        assert len(hands) == 4
        # 莊家應該有 14 張，其他玩家 13 張
        assert len(hands[0]) == 14
        for i in range(1, 4):
            assert len(hands[i]) == 13

    def test_tileset_draw(self):
        """測試摸牌"""
        tile_set = TileSet()
        tile_set.shuffle()  # 先洗牌（需要先洗牌才能摸牌）
        initial_count = len(tile_set._tiles)
        tile = tile_set.draw()
        assert tile is not None
        assert len(tile_set._tiles) == initial_count - 1

    def test_tileset_draw_empty(self):
        """測試從空牌組摸牌"""
        tile_set = TileSet()
        tile_set.shuffle()
        # 耗盡所有牌
        while tile_set._tiles:
            tile_set.draw()
        # 現在應該返回 None
        tile = tile_set.draw()
        assert tile is None

    def test_tileset_draw_wall_tile(self):
        """測試從王牌區摸牌"""
        tile_set = TileSet()
        tile_set.shuffle()
        # 從王牌區摸牌
        if tile_set._wall:
            tile = tile_set.draw_wall_tile()
            assert tile is not None

        # 耗盡王牌區
        while tile_set._wall:
            tile_set.draw_wall_tile()
        # 現在應該返回 None
        tile = tile_set.draw_wall_tile()
        assert tile is None

    def test_tileset_remaining(self):
        """測試剩餘牌數"""
        tile_set = TileSet()
        tile_set.shuffle()
        initial_remaining = tile_set.remaining
        assert initial_remaining > 0

        tile_set.draw()
        assert tile_set.remaining == initial_remaining - 1

    def test_tileset_wall_remaining(self):
        """測試王牌區剩餘牌數"""
        tile_set = TileSet()
        tile_set.shuffle()
        wall_remaining = tile_set.wall_remaining
        assert wall_remaining == 14  # 王牌區應該有 14 張牌

        if tile_set._wall:
            tile_set.draw_wall_tile()
            assert tile_set.wall_remaining == wall_remaining - 1

    def test_tileset_is_exhausted(self):
        """測試牌組是否耗盡"""
        tile_set = TileSet()
        tile_set.shuffle()
        assert not tile_set.is_exhausted()

        # 耗盡所有牌
        while tile_set._tiles:
            tile_set.draw()
        assert tile_set.is_exhausted()

    def test_tileset_get_dora_indicator(self):
        """測試獲取寶牌指示牌"""
        tile_set = TileSet()
        tile_set.shuffle()

        # 獲取表寶牌（index=0）
        indicator0 = tile_set.get_dora_indicator(0)
        assert indicator0 is not None

        # 獲取裡寶牌（index=1，如果可用）
        indicator1 = tile_set.get_dora_indicator(1)
        # 如果王牌區不足 2 張，應該返回 None
        # 否則返回裡寶牌指示牌

        # 測試無效 index
        indicator_invalid = tile_set.get_dora_indicator(2)
        assert indicator_invalid is None

    def test_tileset_get_dora(self):
        """測試根據指示牌獲取寶牌"""
        tile_set = TileSet()

        # 測試字牌寶牌
        # 北（4）→ 東（1）
        indicator_north = Tile(Suit.JIHAI, 4)
        dora = tile_set.get_dora(indicator_north)
        assert dora.suit == Suit.JIHAI
        assert dora.rank == 1

        # 白（5）→ 發（6）
        indicator_white = Tile(Suit.JIHAI, 5)
        dora = tile_set.get_dora(indicator_white)
        assert dora.suit == Suit.JIHAI
        assert dora.rank == 6

        # 發（6）→ 中（7）
        indicator_green = Tile(Suit.JIHAI, 6)
        dora = tile_set.get_dora(indicator_green)
        assert dora.suit == Suit.JIHAI
        assert dora.rank == 7

        # 中（7）→ 東（1）
        indicator_red = Tile(Suit.JIHAI, 7)
        dora = tile_set.get_dora(indicator_red)
        assert dora.suit == Suit.JIHAI
        assert dora.rank == 1

        # 測試數牌寶牌
        # 9 → 1
        indicator_9 = Tile(Suit.MANZU, 9)
        dora = tile_set.get_dora(indicator_9)
        assert dora.suit == Suit.MANZU
        assert dora.rank == 1

        # 1-8 → +1
        indicator_5 = Tile(Suit.MANZU, 5)
        dora = tile_set.get_dora(indicator_5)
        assert dora.suit == Suit.MANZU
        assert dora.rank == 6

    def test_create_tile(self):
        """測試 create_tile 便利函數"""
        tile = create_tile("m", 1)
        assert tile.suit == Suit.MANZU
        assert tile.rank == 1

        tile = create_tile("p", 5, is_red=True)
        assert tile.suit == Suit.PINZU
        assert tile.rank == 5
        assert tile.is_red == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
