"""
得分計算系統 - ScoreCalculator implementation

提供符數、翻數和點數計算功能。
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass
from pyriichi.hand import Hand, CombinationType, Combination
from pyriichi.tiles import Tile, Suit
from pyriichi.game_state import GameState, Wind
from pyriichi.yaku import YakuResult, Yaku, WaitingType


@dataclass
class ScoreResult:
    """得分計算結果"""

    han: int  # 翻數
    fu: int  # 符數
    base_points: int  # 基本點
    total_points: int  # 總點數（自摸時為每人支付，榮和時為總支付）
    payment_from: int  # 支付者位置（榮和時）
    payment_to: int  # 獲得者位置
    is_yakuman: bool  # 是否役滿
    yakuman_count: int  # 役滿倍數
    is_tsumo: bool = False  # 是否自摸
    dealer_payment: int = 0  # 莊家支付（自摸時）
    non_dealer_payment: int = 0  # 閒家支付（自摸時）
    honba_bonus: int = 0  # 本場獎勵
    riichi_sticks_bonus: int = 0  # 供託分配
    kiriage_mangan_enabled: bool = False  # 是否啟用切上滿貫

    def __post_init__(self):
        """計算最終得分"""
        if self.is_yakuman:
            self.total_points = 8000 * self.yakuman_count
        elif self.han >= 13:
            self.total_points = 8000  # 役滿
        elif self.han >= 11:
            self.total_points = 6000  # 三倍滿
        elif self.han >= 8:
            self.total_points = 4000  # 倍滿
        elif self.han >= 6:
            self.total_points = 3000  # 跳滿
        elif self.han >= 5 or (self.han == 4 and self.fu >= 40):
            self.total_points = 2000  # 滿貫
        elif self.kiriage_mangan_enabled and ((self.han == 4 and self.fu == 30) or (self.han == 3 and self.fu == 60)):
            # 切上滿貫：30符4翻 或60符3翻 計為滿貫
            self.total_points = 2000  # 滿貫
        else:
            # 基本點計算
            base = self.fu * (2 ** (self.han + 2))
            self.base_points = base
            self.total_points = (base + 9) // 10 * 10  # 進位到 10

    def calculate_payments(self, game_state: GameState) -> None:
        """
        計算支付方式

        自摸支付：
        - 莊家自摸：每個閒家支付 base_payment + honba，總共獲得 3 * (base_payment + honba)
        - 閒家自摸：莊家支付 2 * (base_payment + honba)，其他閒家支付 base_payment + honba，總共獲得 2 * (base_payment + honba) + (base_payment + honba) * 2

        榮和支付：
        - 支付者支付全部 total_points（包含本場）

        本場獎勵：
        - 每個本場 +300 點（自摸時每人支付，榮和時放銃者支付）

        供託分配：
        - 所有供託棒給和牌者
        """
        # 計算本場獎勵
        self.honba_bonus = game_state.honba * 300

        # 計算供託分配
        self.riichi_sticks_bonus = game_state.riichi_sticks * 1000

        # 基本點數（不含本場和供託）
        base_payment = self.total_points

        if self.is_tsumo:
            # 自摸支付
            # 每人需要支付：base_payment + honba_bonus
            payment_per_person = base_payment + self.honba_bonus

            if self.payment_to == game_state.dealer:
                # 莊家自摸：每個閒家支付 payment_per_person
                self.dealer_payment = payment_per_person  # 每個閒家支付
                self.non_dealer_payment = 0
                self.total_points = payment_per_person * 3 + self.riichi_sticks_bonus  # 3個閒家支付 + 供託
            else:
                # 閒家自摸：莊家支付 2 * payment_per_person，其他閒家支付 payment_per_person
                self.dealer_payment = 2 * payment_per_person
                self.non_dealer_payment = payment_per_person
                # 計算總支付（莊家1個 + 閒家2個）+ 供託
                self.total_points = self.dealer_payment + self.non_dealer_payment * 2 + self.riichi_sticks_bonus
        else:
            # 榮和支付：放銃者支付全部（包含本場和供託）
            self.dealer_payment = 0
            self.non_dealer_payment = 0
            # total_points 已經是全部支付，加上本場和供託
            self.total_points = base_payment + self.honba_bonus + self.riichi_sticks_bonus


class ScoreCalculator:
    """得分計算器"""

    @staticmethod
    def _group_combinations(winning_combination: Optional[List[Combination]]) -> dict:
        groups = {
            CombinationType.PAIR: [],
            CombinationType.SEQUENCE: [],
            CombinationType.TRIPLET: [],
            CombinationType.KAN: [],
        }
        if not winning_combination:
            return groups

        for combination in winning_combination:
            if combination is None:
                continue
            groups.setdefault(combination.type, []).append(combination)

        return groups

    @staticmethod
    def _extract_pair(winning_combination: Optional[List[Combination]]) -> Optional[Combination]:
        if not winning_combination:
            return None
        for combination in winning_combination:
            if combination.type == CombinationType.PAIR:
                return combination
        return None

    def calculate(
        self,
        hand: Hand,
        winning_tile: Tile,
        winning_combination: List,
        yaku_results: List[YakuResult],
        dora_count: int,
        game_state: GameState,
        is_tsumo: bool,
        player_position: int = 0,
    ) -> ScoreResult:
        """
        計算得分

        Args:
            hand: 手牌
            winning_tile: 和牌牌
            winning_combination: 和牌組合
            yaku_results: 役種列表
            dora_count: 寶牌數量
            game_state: 遊戲狀態
            is_tsumo: 是否自摸
            player_position: 玩家位置（用於計算自風對子符數）

        Returns:
            得分計算結果
        """
        # 計算符數（需要傳入 yaku_results 來判斷是否為平和）
        fu = self.calculate_fu(
            hand, winning_tile, winning_combination, yaku_results, game_state, is_tsumo, player_position
        )

        # 計算翻數
        han = self.calculate_han(yaku_results, dora_count)

        # 檢查是否役滿
        is_yakuman = any(r.is_yakuman for r in yaku_results)
        yakuman_count = sum(bool(r.is_yakuman) for r in yaku_results)

        # 創建結果對象
        result = ScoreResult(
            han=han,
            fu=fu,
            base_points=0,
            total_points=0,
            payment_from=0,
            payment_to=0,
            is_yakuman=is_yakuman,
            yakuman_count=yakuman_count,
            is_tsumo=is_tsumo,
            kiriage_mangan_enabled=game_state.ruleset.kiriage_mangan,
        )

        # 計算支付方式（在 RuleEngine 中會根據本場和供託進一步調整）
        # 這裡先計算基本支付
        result.calculate_payments(game_state)

        return result

    def calculate_fu(
        self,
        hand: Hand,
        winning_tile: Tile,
        winning_combination: List,
        yaku_results: List[YakuResult],
        game_state: GameState,
        is_tsumo: bool,
        player_position: int = 0,
    ) -> int:
        """
        計算符數

        Args:
            hand: 手牌
            winning_tile: 和牌牌
            winning_combination: 和牌組合
            yaku_results: 役種列表
            game_state: 遊戲狀態
            is_tsumo: 是否自摸
            player_position: 玩家位置（用於計算自風對子符數）

        Returns:
            符數
        """
        if any(r.yaku == Yaku.CHIITOITSU for r in yaku_results):
            return 25  # 七對子固定 25 符

        if any(r.yaku == Yaku.PINFU for r in yaku_results):
            return 30 if is_tsumo else 20  # 平和固定 30 符（自摸）或 20 符（榮和）

        fu = 20  # 基本符

        # 副底符
        if hand.is_concealed and not is_tsumo:
            fu += 10  # 門清榮和
        elif is_tsumo:
            fu += 2  # 自摸

        # 面子符
        for combination in winning_combination:
            if combination.type in [
                CombinationType.PAIR,
                CombinationType.SEQUENCE,
            ]:
                continue

            tile = combination.tiles[0]

            if combination.type == CombinationType.TRIPLET:
                fu += 8 if tile.is_terminal or tile.is_honor else 4
            elif combination.type == CombinationType.KAN:
                fu += 32 if tile.is_terminal or tile.is_honor else 16

            # TODO: 明刻/槓子符數計算

        if pair_combination := self._extract_pair(winning_combination):
            pair_tile = pair_combination.tiles[0]

            # 役牌對子 +2 符
            if pair_tile.suit == Suit.JIHAI:
                # 三元牌
                if pair_tile.rank in [5, 6, 7]:  # 白、發、中
                    fu += 2
                # 場風
                round_wind_tile = game_state.round_wind.tile
                if round_wind_tile == pair_tile:
                    fu += 2
                # 自風
                player_winds = game_state.player_winds
                if player_position < len(player_winds):
                    player_wind_tile = player_winds[player_position].tile
                    if player_wind_tile == pair_tile:
                        fu += 2

        # 聽牌符
        waiting_type = self._determine_waiting_type(winning_tile, winning_combination)
        if waiting_type in {WaitingType.TANKI, WaitingType.PENCHAN, WaitingType.KANCHAN}:  # 單騎、邊張、嵌張
            fu += 2
        # 兩面聽和雙碰聽不增加符數

        # 進位到 10
        return ((fu + 9) // 10) * 10

    def _determine_waiting_type(self, winning_tile: Tile, winning_combination: List) -> WaitingType:
        """
        判斷聽牌類型

        Args:
            winning_tile: 和牌牌
            winning_combination: 和牌組合

        Returns:
            聽牌類型：'ryanmen'（兩面）、'penchan'（邊張）、'kanchan'（嵌張）、'tanki'（單騎）、'shabo'（雙碰）
        """
        if not winning_combination:
            return WaitingType.RYANMEN  # 默認為兩面聽

        pair_combination = self._extract_pair(winning_combination)
        if pair_combination and any(tile == winning_tile for tile in pair_combination.tiles):
            return WaitingType.TANKI

        for combination in winning_combination:
            if combination.type != CombinationType.SEQUENCE:
                continue

            if winning_tile not in combination.tiles:
                continue

            tiles = sorted(combination.tiles)
            try:
                index = tiles.index(winning_tile)
            except ValueError:
                index = next(
                    (
                        i
                        for i, tile in enumerate(tiles)
                        if tile.suit == winning_tile.suit and tile.rank == winning_tile.rank
                    ),
                    -1,
                )
                if index == -1:
                    continue

            if index == 1:
                return WaitingType.KANCHAN

            first_rank = tiles[0].rank
            last_rank = tiles[-1].rank
            if index in {0, 2}:
                if first_rank == 1 or last_rank == 9:
                    return WaitingType.PENCHAN
                return WaitingType.RYANMEN

        return WaitingType.RYANMEN

    def calculate_han(self, yaku_results: List[YakuResult], dora_count: int) -> int:
        """
        計算翻數

        Args:
            yaku_results: 役種列表
            dora_count: 寶牌數量

        Returns:
            翻數
        """
        han = sum(r.han for r in yaku_results)
        han += dora_count
        return han
