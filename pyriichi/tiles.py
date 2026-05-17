"""
Tile System - Tile and TileSet implementation

Provides tile representation, wall management, and dealing behavior.
"""

import itertools
import random
from typing import Dict, List, Optional

from pyriichi.enum_utils import TranslatableEnum
from pyriichi.errors import TileError


class Suit(TranslatableEnum):
    """Tile suit."""

    MANZU = ("manzu", "萬子", "萬子", "Characters")
    PINZU = ("pinzu", "筒子", "筒子", "Circles")
    SOUZU = ("souzu", "索子", "索子", "Bamboo")
    HONORS = ("honors", "字牌", "字牌", "Honor Tiles")


class Tile:
    """Single mahjong tile."""

    _NUMERAL_MAP: Dict[str, Dict[int, str]] = {
        "zh": {
            1: "一",
            2: "二",
            3: "三",
            4: "四",
            5: "五",
            6: "六",
            7: "七",
            8: "八",
            9: "九",
        },
        "ja": {
            1: "一",
            2: "二",
            3: "三",
            4: "四",
            5: "五",
            6: "六",
            7: "七",
            8: "八",
            9: "九",
        },
        "en": {1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9"},
    }

    _SUIT_SUFFIX_MAP: Dict[str, Dict[Suit, str]] = {
        "zh": {Suit.MANZU: "萬", Suit.PINZU: "筒", Suit.SOUZU: "索"},
        "ja": {Suit.MANZU: "萬", Suit.PINZU: "筒", Suit.SOUZU: "索"},
        "en": {Suit.MANZU: "Man", Suit.PINZU: "Pin", Suit.SOUZU: "Sou"},
    }

    _HONOR_NAME_MAP: Dict[str, Dict[int, str]] = {
        "zh": {1: "東", 2: "南", 3: "西", 4: "北", 5: "白", 6: "發", 7: "中"},
        "ja": {1: "東", 2: "南", 3: "西", 4: "北", 5: "白", 6: "発", 7: "中"},
        "en": {
            1: "East",
            2: "South",
            3: "West",
            4: "North",
            5: "White",
            6: "Green",
            7: "Red",
        },
    }

    _RED_DORA_PREFIX_MAP: Dict[str, str] = {"zh": "赤", "ja": "赤", "en": "Red "}

    def __init__(self, suit: Suit, rank: int, is_red_dora: bool = False):
        """
        Initialize a tile.

        Args:
            suit (Suit): Tile suit.
            rank (int): Rank, 1-9 for number tiles or 1-7 for honors.
            is_red_dora (bool): Whether this is a Red Dora tile.

        Raises:
            ValueError: If rank is out of range.
        """
        if suit == Suit.HONORS:
            if not (1 <= rank <= 7):
                raise TileError("honor_rank_out_of_range", {"rank": rank})
        elif not (1 <= rank <= 9):
            raise TileError("number_rank_out_of_range", {"rank": rank})

        self._suit = suit
        self._rank = rank
        self._is_red_dora = is_red_dora

    @property
    def suit(self) -> Suit:
        return self._suit

    @property
    def rank(self) -> int:
        return self._rank

    @property
    def is_red_dora(self) -> bool:
        return self._is_red_dora

    @property
    def is_honor(self) -> bool:
        return self._suit == Suit.HONORS

    @property
    def is_terminal(self) -> bool:
        return False if self._suit == Suit.HONORS else self._rank in [1, 9]

    @property
    def is_simple(self) -> bool:
        return False if self._suit == Suit.HONORS else 2 <= self._rank <= 8

    def __eq__(self, other) -> bool:
        """
        Compare two tiles by suit and rank, ignoring red_dora status.

        Args:
            other (Any): Object to compare.

        Returns:
            bool: True if suit and rank are equal.
        """
        if not isinstance(other, Tile):
            return False
        return self._suit == other._suit and self._rank == other._rank

    def __hash__(self) -> int:
        return hash((self._suit, self._rank))

    def __lt__(self, other) -> bool:
        if not isinstance(other, Tile):
            return NotImplemented
        suit_order = {
            Suit.MANZU: 0,
            Suit.PINZU: 1,
            Suit.SOUZU: 2,
            Suit.HONORS: 3,
        }
        if self._suit != other._suit:
            return suit_order[self._suit] < suit_order[other._suit]
        return self._rank < other._rank

    def __str__(self) -> str:
        """
        Get the compact tile notation, such as 1m, 5p, or r5m for red_dora.

        Returns:
            str: Compact tile notation.
        """
        suit_map = {
            Suit.MANZU: "m",
            Suit.PINZU: "p",
            Suit.SOUZU: "s",
            Suit.HONORS: "z",
        }
        if self._is_red_dora:
            return f"r{self._rank}{suit_map[self._suit]}"
        return f"{self._rank}{suit_map[self._suit]}"

    def __repr__(self) -> str:
        return f"Tile({self._suit.name}, {self._rank}, red_dora={self._is_red_dora})"

    @property
    def is_yaochuu(self) -> bool:
        """
        Check whether this tile is yaochuu: a 1, 9, or honor tile.

        Returns:
            bool: True if this tile is yaochuu.
        """
        if self._suit == Suit.HONORS:
            return True
        return self._rank == 1 or self._rank == 9

    def _format_name(self, locale: str) -> str:
        if locale not in {"zh", "ja", "en"}:
            raise TileError("unsupported_locale", {"locale": locale})

        prefix = self._RED_DORA_PREFIX_MAP[locale] if self._is_red_dora else ""

        if self._suit == Suit.HONORS:
            return f"{prefix}{self._HONOR_NAME_MAP[locale][self._rank]}"

        numeral = self._NUMERAL_MAP[locale][self._rank]
        suffix = self._SUIT_SUFFIX_MAP[locale][self._suit]

        if locale == "en":
            return f"{prefix}{numeral} {suffix}".strip()

        return f"{prefix}{numeral}{suffix}"

    def get_name(self, locale: str = "zh") -> str:
        """
        Get the localized tile name.

        Args:
            locale (str): Locale code ("zh", "ja", "en").

        Returns:
            str: Localized name.
        """
        return self._format_name(locale)


def create_tile(suit: str, rank: int, is_red_dora: bool = False) -> Tile:
    """
    Create a tile from compact suit notation.

    Args:
        suit (str): Suit notation ("m", "p", "s", "z").
        rank (int): Tile rank.
        is_red_dora (bool): Whether this is a Red Dora tile.

    Returns:
        Tile: Created tile.

    Raises:
        ValueError: If suit is invalid.
    """
    suit_map = {
        "m": Suit.MANZU,
        "p": Suit.PINZU,
        "s": Suit.SOUZU,
        "z": Suit.HONORS,
    }
    if suit not in suit_map:
        raise TileError("invalid_suit", {"suit": suit})
    return Tile(suit_map[suit], rank, is_red_dora)


class TileSet:
    """Tile wall manager."""

    def __init__(self, tiles: Optional[List[Tile]] = None):
        """
        Initialize the tile set.

        Args:
            tiles (Optional[List[Tile]]): Initial tiles, or None to create a standard 136-tile set.
        """
        if tiles is None:
            tiles = self._create_standard_set()
        self._tiles = tiles.copy()
        self._wall = []
        self._dora_indicators = []

    @staticmethod
    def _create_standard_set() -> List[Tile]:
        tiles = []
        # Number tiles: manzu, pinzu, and souzu each have 36 tiles.
        for suit in [Suit.MANZU, Suit.PINZU, Suit.SOUZU]:
            for rank in range(1, 10):
                if rank == 5:
                    tiles.extend(Tile(suit, rank) for _ in range(3))
                    tiles.append(Tile(suit, rank, is_red_dora=True))
                else:
                    tiles.extend(Tile(suit, rank) for _ in range(4))
        # honors: 16 wind tiles and 12 haku/hatsu/chun tiles.
        tiles.extend(
            Tile(Suit.HONORS, rank)
            for rank, _ in itertools.product(range(1, 8), range(4))
        )
        return tiles

    def shuffle(self) -> None:
        random.shuffle(self._tiles)
        # Initialize the dead wall from the last 14 tiles.
        self._wall = self._tiles[-14:]
        self._tiles = self._tiles[:-14]

        self._rinshan_tiles = self._wall[:4]

        self._dora_indicators = self._wall[4:9]

        self._ura_dora_indicators = self._wall[9:14]

    def deal(self, num_players: int = 4, dealer: int = 0) -> List[List[Tile]]:
        """
        Deal initial hands.

        Args:
            num_players (int): Number of players, defaulting to 4.
            dealer (int): Dealer player index.

        Returns:
            List[List[Tile]]: Hands for each player; dealer has 14 tiles and others have 13.

        Raises:
            ValueError: If dealer is out of range.
        """
        if not (0 <= dealer < num_players):
            raise TileError(
                "dealer_position_out_of_range", {"max_player": num_players - 1}
            )

        hands = [[] for _ in range(num_players)]

        for _, player in itertools.product(range(13), range(num_players)):
            if self._tiles:
                hands[player].append(self._tiles.pop(0))

        # Dealer receives the 14th tile.
        if self._tiles:
            hands[dealer].append(self._tiles.pop(0))

        for hand in hands:
            hand.sort()

        return hands

    def draw(self) -> Optional[Tile]:
        """
        Draw one tile from the live wall.

        Returns:
            Optional[Tile]: Drawn tile, or None if the wall is empty.
        """
        return self._tiles.pop(0) if self._tiles else None

    def draw_rinshan(self) -> Optional[Tile]:
        """
        Draw one rinshan tile after kan.

        Returns:
            Optional[Tile]: Drawn tile, or None if no rinshan tiles remain.
        """
        return self._rinshan_tiles.pop(0) if self._rinshan_tiles else None

    @property
    def remaining(self) -> int:
        return len(self._tiles)

    @property
    def wall_remaining(self) -> int:
        return len(self._wall)

    def is_exhausted(self) -> bool:
        return len(self._tiles) == 0

    def get_dora_indicators(self, count: Optional[int] = None) -> List[Tile]:
        """
        Get revealed dora indicators.

        Args:
            count (Optional[int]): Number of indicators, inferred from rinshan tiles if None.

        Returns:
            List[Tile]: Dora indicator tiles.

        Raises:
            ValueError: If there are not enough indicators.
        """
        if count is None:
            count = 5 - len(self._rinshan_tiles)
        if count > len(self._dora_indicators):
            raise TileError(
                "dora_indicators_insufficient",
                {"count": count, "actual": len(self._dora_indicators)},
            )
        return self._dora_indicators[:count]

    def get_ura_dora_indicators(self, count: Optional[int] = None) -> List[Tile]:
        """
        Get Ura Dora indicators.

        Args:
            count (Optional[int]): Number of indicators, inferred from rinshan tiles if None.

        Returns:
            List[Tile]: Ura_dora indicator tiles.

        Raises:
            ValueError: If there are not enough indicators.
        """
        if count is None:
            count = 5 - len(self._rinshan_tiles)
        if count > len(self._ura_dora_indicators):
            raise TileError(
                "ura_dora_indicators_insufficient",
                {"count": count, "actual": len(self._ura_dora_indicators)},
            )
        return self._ura_dora_indicators[:count]

    def get_dora(self, indicator: Tile) -> Tile:
        """
        Get the dora tile corresponding to an indicator.

        Args:
            indicator (Tile): Dora indicator.

        Returns:
            Tile: Matching dora tile.
        """
        if indicator.suit == Suit.HONORS:
            # Honors: east -> south -> west -> north -> haku -> hatsu -> chun -> east.
            if indicator.rank == 4:  # north
                return Tile(Suit.HONORS, 1)  # east
            elif indicator.rank == 5:  # haku
                return Tile(Suit.HONORS, 6)  # hatsu
            elif indicator.rank == 6:  # hatsu
                return Tile(Suit.HONORS, 7)  # chun
            elif indicator.rank == 7:  # chun
                return Tile(Suit.HONORS, 1)  # east
            else:
                return Tile(Suit.HONORS, indicator.rank + 1)
        else:
            # Number tiles: 1-8 advance by one, 9 wraps to 1.
            if indicator.rank == 9:
                return Tile(indicator.suit, 1)
            else:
                return Tile(indicator.suit, indicator.rank + 1)
