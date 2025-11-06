"""
工具函數

提供便利函數用於牌的解析和格式化。
"""

from typing import List
from pyriichi.tiles import Tile, Suit, create_tile


def parse_tiles(tile_string: str) -> List[Tile]:
    """
    從字符串解析牌（例如："1m2m3m4p5p6p"）

    Args:
        tile_string: 牌字符串

    Returns:
        牌列表

    Example:
        >>> parse_tiles("1m2m3m4p5p6p")
        [Tile(MANZU, 1), Tile(MANZU, 2), Tile(MANZU, 3), ...]
        >>> parse_tiles("[5p]6p7p")  # 紅寶牌用 [ ] 括號包裹
        [Tile(PINZU, 5, red=True), Tile(PINZU, 6), Tile(PINZU, 7)]
    """
    tiles = []
    i = 0
    while i < len(tile_string):
        # 檢查是否為紅寶牌（用 [ ] 括號包裹）
        if tile_string[i] == "[":
            # 解析括號內的牌
            i += 1  # 跳過 [
            if i < len(tile_string) and tile_string[i].isdigit():
                rank = int(tile_string[i])
                i += 1
                if i < len(tile_string):
                    suit = tile_string[i]
                    i += 1
                    # 檢查是否有 ]
                    if i < len(tile_string) and tile_string[i] == "]":
                        tiles.append(create_tile(suit, rank, is_red=True))
                        i += 1  # 跳過 ]
                    else:
                        # 沒有 ]，按普通牌處理
                        tiles.append(create_tile(suit, rank, is_red=False))
        elif tile_string[i].isdigit():
            rank = int(tile_string[i])
            i += 1
            if i < len(tile_string):
                suit = tile_string[i]
                # 檢查是否為舊格式的紅寶牌（用 ] 標記，向後兼容）
                is_red = False
                if i + 1 < len(tile_string) and tile_string[i + 1] == "]":
                    is_red = True
                    i += 1
                tiles.append(create_tile(suit, rank, is_red))
                i += 1
        else:
            i += 1
    return tiles


def format_tiles(tiles: List[Tile]) -> str:
    """
    將牌列表格式化為字符串

    Args:
        tiles: 牌列表

    Returns:
        格式化後的字符串

    Example:
        >>> format_tiles([Tile(Suit.MANZU, 1), Tile(Suit.PINZU, 5)])
        "1m5p"
    """
    return "".join(str(tile) for tile in tiles)


def is_winning_hand(tiles: List[Tile], winning_tile: Tile) -> bool:
    """
    快速檢查是否和牌（便利函數）

    Args:
        tiles: 手牌列表（13 張）
        winning_tile: 和牌牌

    Returns:
        是否和牌
    """
    from pyriichi.hand import Hand

    hand = Hand(tiles)
    return hand.is_winning_hand(winning_tile)
