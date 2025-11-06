"""
遊戲狀態管理 - GameState implementation

管理局數、風、點數等遊戲狀態。
"""

from enum import Enum
from typing import List, Optional
from pyriichi.rules_config import RulesetConfig


class Wind(Enum):
    """風"""

    EAST = "e"  # 東
    SOUTH = "s"  # 南
    WEST = "w"  # 西
    NORTH = "n"  # 北


class GameState:
    """遊戲狀態管理器"""

    def __init__(
        self,
        initial_scores: Optional[List[int]] = None,
        num_players: int = 4,
        ruleset: Optional[RulesetConfig] = None,
    ):
        """
        初始化遊戲狀態

        Args:
            initial_scores: 初始點數列表（默認每人 25000）
            num_players: 玩家數量
            ruleset: 規則配置（默認使用標準競技規則）
        """
        if initial_scores is None:
            initial_scores = [25000] * num_players

        self._scores = initial_scores.copy()
        self._round_wind = Wind.EAST
        self._round_number = 1
        self._dealer = 0
        self._honba = 0
        self._riichi_sticks = 0
        self._num_players = num_players
        self._ruleset = ruleset if ruleset is not None else RulesetConfig.standard()

    @property
    def round_wind(self) -> Wind:
        """當前局風"""
        return self._round_wind

    @property
    def round_number(self) -> int:
        """當前局數（1-4）"""
        return self._round_number

    @property
    def player_winds(self) -> List[Wind]:
        """每個玩家的自風"""
        winds = [Wind.EAST, Wind.SOUTH, Wind.WEST, Wind.NORTH]
        return [winds[(i - self._dealer) % self._num_players] for i in range(self._num_players)]

    @property
    def dealer(self) -> int:
        """當前莊家位置（0-3）"""
        return self._dealer

    @property
    def honba(self) -> int:
        """本場數"""
        return self._honba

    @property
    def riichi_sticks(self) -> int:
        """供託棒數"""
        return self._riichi_sticks

    @property
    def scores(self) -> List[int]:
        """每個玩家的點數"""
        return self._scores.copy()

    def set_round(self, round_wind: Wind, round_number: int) -> None:
        """設置局數"""
        self._round_wind = round_wind
        self._round_number = round_number

    def set_dealer(self, dealer: int) -> None:
        """設置莊家"""
        if not (0 <= dealer < self._num_players):
            raise ValueError(f"莊家位置必須在 0-{self._num_players-1} 之間")
        self._dealer = dealer

    def add_honba(self, count: int = 1) -> None:
        """增加本場數"""
        self._honba += count

    def reset_honba(self) -> None:
        """重置本場數"""
        self._honba = 0

    def add_riichi_stick(self) -> None:
        """增加供託棒"""
        self._riichi_sticks += 1

    def clear_riichi_sticks(self) -> None:
        """清除供託棒"""
        self._riichi_sticks = 0

    @property
    def ruleset(self) -> RulesetConfig:
        """規則配置"""
        return self._ruleset

    def update_score(self, player: int, points: int) -> None:
        """更新玩家點數"""
        if not (0 <= player < self._num_players):
            raise ValueError(f"玩家位置必須在 0-{self._num_players-1} 之間")
        self._scores[player] += points

    def transfer_points(self, from_player: int, to_player: int, points: int) -> None:
        """轉移點數"""
        self.update_score(from_player, -points)
        self.update_score(to_player, points)

    def next_round(self) -> bool:
        """
        進入下一局

        Returns:
            是否還有下一局（遊戲是否結束）
        """
        self._round_number += 1

        # 如果完成了 4 局，進入下一風
        if self._round_number > 4:
            if self._round_wind == Wind.EAST:
                self._round_wind = Wind.SOUTH
                self._round_number = 1
            elif self._round_wind == Wind.SOUTH:
                # 遊戲結束
                return False

        return True

    def next_dealer(self, dealer_won: bool) -> None:
        """
        下一局莊家

        Args:
            dealer_won: 莊家是否獲勝
        """
        if not dealer_won:
            self._dealer = (self._dealer + 1) % self._num_players
            self.reset_honba()
        else:
            self.add_honba()
