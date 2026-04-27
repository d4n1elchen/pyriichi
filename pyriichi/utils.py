"""
Utility functions

Provides convenience functions for tile parsing and formatting.
"""

from typing import List

from pyriichi.tiles import Suit, Tile


def parse_tiles(tile_string: str) -> List[Tile]:
    """
    Parse tiles from string (e.g., "1m2m3m4p5p6p").

    Args:
        tile_string (str): Tile string.

    Returns:
        List[Tile]: List of tiles.

    Example:
        >>> parse_tiles("1m2m3m4p5p6p")
        [Tile(MANZU, 1), Tile(MANZU, 2), Tile(MANZU, 3), ...]
        >>> parse_tiles("r5p6p7p")  # red_dora uses 'r' prefix (Standard format)
        [Tile(PINZU, 5, red=True), Tile(PINZU, 6), Tile(PINZU, 7)]
    """
    tiles = []
    buffer = []  # List to store (rank, is_red)
    i = 0
    suit_map = {"m": Suit.MANZU, "p": Suit.PINZU, "s": Suit.SOUZU, "z": Suit.HONORS}

    while i < len(tile_string):
        char = tile_string[i]

        if char == "r":
            if i + 1 < len(tile_string) and tile_string[i + 1].isdigit():
                rank = int(tile_string[i + 1])
                buffer.append((rank, True))
                i += 2
                continue
            else:
                i += 1
                continue

        if char.isdigit():
            rank = int(char)
            buffer.append((rank, False))
            i += 1
            continue

        if char in suit_map:
            suit = suit_map[char]
            for rank, is_red in buffer:
                tiles.append(Tile(suit, rank, is_red))
            buffer = []
            i += 1
            continue

        # Ignore other characters
        i += 1

    return tiles


def format_tiles(tiles: List[Tile]) -> str:
    """
    Format tile list to string.

    Args:
        tiles (List[Tile]): List of tiles.

    Returns:
        str: Formatted string.

    Example:
        >>> format_tiles([Tile(Suit.MANZU, 1), Tile(Suit.PINZU, 5)])
        "1m5p"
    """
    return "".join(str(tile) for tile in tiles)


def is_winning_hand(tiles: List[Tile], winning_tile: Tile) -> bool:
    """
    Quick check if hand is winning (Convenience function).

    Args:
        tiles (List[Tile]): hand tiles (13 tiles).
        winning_tile (Tile): Winning tile.

    Returns:
        bool: Whether it is a winning hand.
    """
    from pyriichi.hand import Hand

    hand = Hand(tiles)
    return hand.is_winning_hand(winning_tile)
