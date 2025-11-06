"""
牌組系統 - Tile and TileSet implementation

提供牌的表示、牌組管理和發牌功能。
"""

from enum import Enum
from typing import List, Optional
import random


class Suit(Enum):
    """花色"""

    MANZU = "m"  # 萬子
    PINZU = "p"  # 筒子
    SOZU = "s"  # 條子
    JIHAI = "z"  # 字牌


class Tile:
    """單張麻將牌"""

    def __init__(self, suit: Suit, rank: int, is_red: bool = False):
        """
        初始化一張牌

        Args:
            suit: 花色
            rank: 數字（1-9 對數牌，1-7 對字牌）
            is_red: 是否為紅寶牌（默認 False）

        Raises:
            ValueError: 如果 rank 超出範圍
        """
        if suit == Suit.JIHAI:
            if not (1 <= rank <= 7):
                raise ValueError(f"字牌 rank 必須在 1-7 之間，得到 {rank}")
        else:
            if not (1 <= rank <= 9):
                raise ValueError(f"數牌 rank 必須在 1-9 之間，得到 {rank}")

        self._suit = suit
        self._rank = rank
        self._is_red = is_red

    @property
    def suit(self) -> Suit:
        """獲取花色"""
        return self._suit

    @property
    def rank(self) -> int:
        """獲取數字"""
        return self._rank

    @property
    def is_red(self) -> bool:
        """是否為紅寶牌"""
        return self._is_red

    @property
    def is_honor(self) -> bool:
        """是否為字牌"""
        return self._suit == Suit.JIHAI

    @property
    def is_terminal(self) -> bool:
        """是否為老頭牌（1 或 9）"""
        if self._suit == Suit.JIHAI:
            return False
        return self._rank == 1 or self._rank == 9

    @property
    def is_simple(self) -> bool:
        """是否為中張牌（2-8）"""
        if self._suit == Suit.JIHAI:
            return False
        return 2 <= self._rank <= 8

    def __eq__(self, other) -> bool:
        """比較兩張牌是否相同（不考慮紅寶牌）"""
        if not isinstance(other, Tile):
            return False
        return self._suit == other._suit and self._rank == other._rank

    def __hash__(self) -> int:
        """哈希值，用於集合和字典"""
        return hash((self._suit, self._rank))

    def __lt__(self, other) -> bool:
        """排序：先按花色，再按數字"""
        if not isinstance(other, Tile):
            return NotImplemented
        if self._suit.value != other._suit.value:
            return self._suit.value < other._suit.value
        return self._rank < other._rank

    def __str__(self) -> str:
        """字符串表示（例如：1m, 5p, r5m 表示紅寶牌）"""
        suit_map = {
            Suit.MANZU: "m",
            Suit.PINZU: "p",
            Suit.SOZU: "s",
            Suit.JIHAI: "z",
        }
        if self._is_red:
            return f"r{self._rank}{suit_map[self._suit]}"
        return f"{self._rank}{suit_map[self._suit]}"

    def __repr__(self) -> str:
        """對象表示"""
        return f"Tile({self._suit.name}, {self._rank}, red={self._is_red})"


def create_tile(suit: str, rank: int, is_red: bool = False) -> Tile:
    """
    創建一張牌（便捷函數）

    Args:
        suit: 花色字符串 ("m", "p", "s", "z")
        rank: 數字
        is_red: 是否為紅寶牌

    Returns:
        Tile 對象

    Raises:
        ValueError: 如果 suit 無效
    """
    suit_map = {
        "m": Suit.MANZU,
        "p": Suit.PINZU,
        "s": Suit.SOZU,
        "z": Suit.JIHAI,
    }
    if suit not in suit_map:
        raise ValueError(f"無效的花色: {suit}")
    return Tile(suit_map[suit], rank, is_red)


class TileSet:
    """牌組管理器"""

    def __init__(self, tiles: Optional[List[Tile]] = None):
        """
        初始化牌組

        Args:
            tiles: 初始牌列表（如果為 None，則創建標準 136 張牌）
        """
        if tiles is None:
            tiles = self._create_standard_set()
        self._tiles = tiles.copy()
        self._wall = []
        self._dora_indicators = []

    @staticmethod
    def _create_standard_set() -> List[Tile]:
        """創建標準 136 張牌"""
        tiles = []
        # 數牌：萬、筒、條各 36 張（1-9 各 4 張）
        for suit in [Suit.MANZU, Suit.PINZU, Suit.SOZU]:
            for rank in range(1, 10):
                for _ in range(4):
                    tiles.append(Tile(suit, rank))

        # 字牌：風牌 16 張（東南西北各 4 張），三元牌 12 張（白發中各 4 張）
        for rank in range(1, 8):
            for _ in range(4):
                tiles.append(Tile(Suit.JIHAI, rank))

        return tiles

    def shuffle(self) -> None:
        """洗牌"""
        random.shuffle(self._tiles)
        # 初始化王牌區（最後 14 張）
        self._wall = self._tiles[-14:]
        self._tiles = self._tiles[:-14]
        # 設置寶牌指示牌（王牌區倒數第 5 張開始）
        self._dora_indicators = [self._wall[4]]  # 表寶牌
        # 裡寶牌在立直時才顯示

    def deal(self, num_players: int = 4) -> List[List[Tile]]:
        """
        發牌

        Args:
            num_players: 玩家數量（默認 4）

        Returns:
            每個玩家的手牌列表（13 張），莊家為 14 張
        """
        hands = [[] for _ in range(num_players)]

        # 每人發 13 張
        for i in range(13):
            for player in range(num_players):
                if self._tiles:
                    hands[player].append(self._tiles.pop(0))

        # 莊家多發 1 張（第 14 張）
        if self._tiles:
            hands[0].append(self._tiles.pop(0))

        # 排序每人的手牌
        for hand in hands:
            hand.sort()

        return hands

    def draw(self) -> Optional[Tile]:
        """
        從牌山頂端摸一張牌

        Returns:
            摸到的牌，如果牌山為空則返回 None
        """
        if not self._tiles:
            return None
        return self._tiles.pop(0)

    def draw_wall_tile(self) -> Optional[Tile]:
        """
        從王牌區摸一張牌（用於槓後摸牌）

        Returns:
            摸到的牌，如果王牌區為空則返回 None
        """
        if not self._wall:
            return None
        return self._wall.pop(0)

    @property
    def remaining(self) -> int:
        """剩餘牌數"""
        return len(self._tiles)

    @property
    def wall_remaining(self) -> int:
        """王牌區剩餘牌數"""
        return len(self._wall)

    def is_exhausted(self) -> bool:
        """檢查牌山是否耗盡"""
        return len(self._tiles) == 0

    def get_dora_indicator(self, index: int = 0) -> Optional[Tile]:
        """
        獲取寶牌指示牌

        Args:
            index: 指示牌索引（0 為表寶牌，1+ 為裡寶牌）

        Returns:
            指示牌，如果不存在則返回 None
        """
        if index < len(self._dora_indicators):
            return self._dora_indicators[index]
        # 裡寶牌在王牌區倒數第 2 張開始
        if index == 1 and len(self._wall) >= 2:
            return self._wall[-2]
        return None

    def get_dora(self, indicator: Tile) -> Tile:
        """
        根據指示牌獲取寶牌

        Args:
            indicator: 指示牌

        Returns:
            對應的寶牌
        """
        if indicator.suit == Suit.JIHAI:
            # 字牌：東→南→西→北→白→發→中→東
            if indicator.rank == 4:  # 北
                return Tile(Suit.JIHAI, 1)  # 東
            elif indicator.rank == 5:  # 白
                return Tile(Suit.JIHAI, 6)  # 發
            elif indicator.rank == 6:  # 發
                return Tile(Suit.JIHAI, 7)  # 中
            elif indicator.rank == 7:  # 中
                return Tile(Suit.JIHAI, 1)  # 東
            else:
                return Tile(Suit.JIHAI, indicator.rank + 1)
        else:
            # 數牌：1-8→+1，9→1
            if indicator.rank == 9:
                return Tile(indicator.suit, 1)
            else:
                return Tile(indicator.suit, indicator.rank + 1)
