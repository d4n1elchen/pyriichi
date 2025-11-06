"""
得分計算系統 - ScoreCalculator implementation

提供符數、翻數和點數計算功能。
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass
from pyriichi.hand import Hand
from pyriichi.tiles import Tile, Suit
from pyriichi.game_state import GameState
from pyriichi.yaku import YakuResult


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
        yakuman_count = sum(1 for r in yaku_results if r.is_yakuman)

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
            game_state: 遊戲狀態
            is_tsumo: 是否自摸

        Returns:
            符數
        """
        if not winning_combination:
            # 七對子固定 25 符（實際上是無符，但這裡返回 25）
            return 25

        fu = 20  # 基本符

        # 檢查是否為平和（平和固定 20 符，無其他符）
        is_pinfu = any(r.name == "平和" for r in yaku_results) if yaku_results else False

        if is_pinfu:
            # 平和固定符數
            if is_tsumo:
                fu = 30  # 平和自摸：20符基本符 + 2符自摸符 + 8符副底符 = 30符
            else:
                fu = 30  # 平和榮和：20符基本符 + 10符門清榮和 = 30符
            # 平和固定30符，不需要進位
            return 30

        # 副底符
        if hand.is_concealed and not is_tsumo:
            fu += 10  # 門清榮和
        elif hand.is_concealed and is_tsumo:
            fu += 2  # 門清自摸
        elif not hand.is_concealed and is_tsumo:
            fu += 2  # 非門清自摸

        # 面子符
        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                tile = Tile(suit, rank)

                if meld_type == "triplet":
                    # 刻子符
                    if tile.is_terminal or tile.is_honor:
                        # 幺九刻子
                        if hand.is_concealed:
                            fu += 8  # 暗刻
                        else:
                            fu += 4  # 明刻
                    else:
                        # 中張刻子
                        if hand.is_concealed:
                            fu += 4  # 暗刻
                        else:
                            fu += 2  # 明刻

                elif meld_type == "kan":
                    # 槓子符（需要判斷是明槓還是暗槓）
                    # TODO: 需要從 Meld 中獲取是否為暗槓
                    if tile.is_terminal or tile.is_honor:
                        # 幺九槓子
                        if hand.is_concealed:
                            fu += 32  # 暗槓
                        else:
                            fu += 16  # 明槓
                    else:
                        # 中張槓子
                        if hand.is_concealed:
                            fu += 16  # 暗槓
                        else:
                            fu += 8  # 明槓

        # 雀頭符
        pair = None
        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                if meld_type == "pair":
                    pair = (suit, rank)
                    break

        if pair:
            suit, rank = pair
            pair_tile = Tile(suit, rank)

            # 役牌對子 +2 符
            if suit == Suit.JIHAI:
                # 三元牌
                if rank in [5, 6, 7]:  # 白、發、中
                    fu += 2
                # 場風
                round_wind = game_state.round_wind
                if (
                    (rank == 1 and round_wind.value == "e")
                    or (rank == 2 and round_wind.value == "s")
                    or (rank == 3 and round_wind.value == "w")
                    or (rank == 4 and round_wind.value == "n")
                ):
                    fu += 2
                # 自風
                player_winds = game_state.player_winds
                if player_position < len(player_winds):
                    player_wind = player_winds[player_position]
                    if (
                        (rank == 1 and player_wind.value == "e")
                        or (rank == 2 and player_wind.value == "s")
                        or (rank == 3 and player_wind.value == "w")
                        or (rank == 4 and player_wind.value == "n")
                    ):
                        fu += 2

        # 聽牌符
        waiting_type = self._determine_waiting_type(winning_tile, winning_combination)
        if waiting_type in ["tanki", "penchan", "kanchan"]:  # 單騎、邊張、嵌張
            fu += 2
        # 兩面聽和雙碰聽不增加符數

        # 進位到 10
        return ((fu + 9) // 10) * 10

    def _determine_waiting_type(self, winning_tile: Tile, winning_combination: List) -> str:
        """
        判斷聽牌類型

        Args:
            winning_tile: 和牌牌
            winning_combination: 和牌組合

        Returns:
            聽牌類型：'ryanmen'（兩面）、'penchan'（邊張）、'kanchan'（嵌張）、'tanki'（單騎）、'shabo'（雙碰）
        """
        if not winning_combination:
            return "ryanmen"  # 默認為兩面聽

        # 檢查是否為單騎聽（winning_tile 是對子的一部分）
        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                if meld_type == "pair":
                    if winning_tile.suit == suit and winning_tile.rank == rank:
                        return "tanki"  # 單騎聽

        # 檢查是否為順子聽（兩面、邊張、嵌張）
        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                if meld_type == "sequence":
                    # 順子的牌範圍
                    seq_ranks = [rank, rank + 1, rank + 2]
                    if winning_tile.suit == suit and winning_tile.rank in seq_ranks:
                        # 判斷聽牌位置
                        if winning_tile.rank == rank:
                            # 聽順子的第一張（邊張）
                            if rank == 1:
                                return "penchan"  # 1-2-3 聽 1（邊張）
                            return "kanchan"  # 其他情況可能是嵌張
                        elif winning_tile.rank == rank + 1:
                            # 聽順子的中間張（嵌張）
                            return "kanchan"
                        elif winning_tile.rank == rank + 2:
                            # 聽順子的最後一張（邊張）
                            if rank == 7:
                                return "penchan"  # 7-8-9 聽 9（邊張）
                            return "kanchan"  # 其他情況可能是嵌張

        # 檢查是否為雙碰聽（winning_tile 可以是兩個對子中的任一個）
        # 這需要檢查手牌結構，但這裡簡化處理
        # 如果 winning_tile 不在任何順子中，可能是雙碰聽
        in_sequence = False
        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                if meld_type == "sequence":
                    seq_ranks = [rank, rank + 1, rank + 2]
                    if winning_tile.suit == suit and winning_tile.rank in seq_ranks:
                        in_sequence = True
                        break

        if not in_sequence:
            # 可能是雙碰聽，但需要檢查是否有兩個對子
            # 簡化處理：如果不是順子聽且不是單騎聽，可能是雙碰聽
            # 但實際上需要更複雜的邏輯來判斷
            # 這裡先返回兩面聽（最常見的情況）
            return "ryanmen"

        # 默認為兩面聽
        return "ryanmen"

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
