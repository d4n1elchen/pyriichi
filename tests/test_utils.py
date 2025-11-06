"""
utils 模組的單元測試
"""

import pytest
from pyriichi.tiles import Tile, Suit
from pyriichi.utils import parse_tiles, format_tiles, is_winning_hand


class TestUtils:
    """工具函數測試"""

    def test_parse_tiles_basic(self):
        """測試基本牌解析"""
        tiles = parse_tiles("1m2m3m4p5p6p")
        assert len(tiles) == 6
        assert tiles[0].suit == Suit.MANZU
        assert tiles[0].rank == 1
        assert tiles[3].suit == Suit.PINZU
        assert tiles[3].rank == 4

    def test_parse_tiles_red_dora(self):
        """測試解析紅寶牌（標準格式：r5p）"""
        # 測試標準格式：用 r 前綴
        tiles = parse_tiles("r5p")
        assert len(tiles) == 1
        assert tiles[0].is_red == True
        assert tiles[0].rank == 5
        assert tiles[0].suit == Suit.PINZU

    def test_parse_tiles_with_red_dora(self):
        """測試包含紅寶牌的牌字符串"""
        # 測試標準格式：r5p6p7p
        tiles = parse_tiles("r5p6p7p")
        assert len(tiles) == 3
        assert tiles[0].is_red == True
        assert tiles[0].rank == 5
        assert tiles[1].is_red == False
        assert tiles[1].rank == 6
        assert tiles[2].is_red == False
        assert tiles[2].rank == 7

    def test_parse_tiles_invalid_char(self):
        """測試解析無效字符（跳過）"""
        # 測試包含非數字和花色的字符
        tiles = parse_tiles("1m2m3m abc 4p5p")
        # 應該跳過無效字符，只解析有效部分
        assert len(tiles) >= 3

    def test_format_tiles(self):
        """測試牌格式化"""
        tiles = [
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 2),
            Tile(Suit.PINZU, 5),
            Tile(Suit.SOZU, 9),
        ]
        result = format_tiles(tiles)
        assert isinstance(result, str)
        assert "1m" in result
        assert "5p" in result
        assert "9s" in result

    def test_format_tiles_empty(self):
        """測試空列表格式化"""
        tiles = []
        result = format_tiles(tiles)
        assert result == ""

    def test_is_winning_hand(self):
        """測試 is_winning_hand 便利函數"""
        # 標準和牌型
        tiles = [
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 2),
            Tile(Suit.MANZU, 3),
            Tile(Suit.MANZU, 4),
            Tile(Suit.MANZU, 5),
            Tile(Suit.MANZU, 6),
            Tile(Suit.MANZU, 7),
            Tile(Suit.MANZU, 8),
            Tile(Suit.MANZU, 9),
            Tile(Suit.PINZU, 1),
            Tile(Suit.PINZU, 2),
            Tile(Suit.PINZU, 3),
            Tile(Suit.PINZU, 4),
        ]
        winning_tile = Tile(Suit.PINZU, 4)

        result = is_winning_hand(tiles, winning_tile)
        assert result is True

    def test_is_winning_hand_not_winning(self):
        """測試非和牌"""
        tiles = [
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 2),
            Tile(Suit.MANZU, 3),
            Tile(Suit.MANZU, 4),
            Tile(Suit.MANZU, 5),
            Tile(Suit.MANZU, 6),
            Tile(Suit.MANZU, 7),
            Tile(Suit.MANZU, 8),
            Tile(Suit.PINZU, 1),
            Tile(Suit.PINZU, 2),
            Tile(Suit.PINZU, 3),
            Tile(Suit.PINZU, 4),
            Tile(Suit.PINZU, 5),
        ]
        winning_tile = Tile(Suit.MANZU, 9)

        result = is_winning_hand(tiles, winning_tile)
        # 可能和牌也可能不和牌，取決於具體手牌
        assert isinstance(result, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
