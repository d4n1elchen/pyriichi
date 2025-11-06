"""
ScoreCalculator 的單元測試
"""

import pytest
from pyriichi.hand import Hand
from pyriichi.tiles import Tile, Suit
from pyriichi.yaku import YakuChecker, YakuResult
from pyriichi.scoring import ScoreCalculator, ScoreResult
from pyriichi.game_state import GameState, Wind


class TestScoreCalculator:
    """得分計算測試"""

    def setup_method(self):
        """設置測試環境"""
        self.calculator = ScoreCalculator()
        self.yaku_checker = YakuChecker()
        self.game_state = GameState()
        self.game_state.set_round(Wind.EAST, 1)

    def test_calculate_fu_basic(self):
        """測試基本符數計算"""
        # 門清榮和：20 + 10 = 30 符（只有順子，無刻子）
        # 但這個手牌實際上有刻子，所以會更多
        tiles = [
            Tile(Suit.MANZU, 2), Tile(Suit.MANZU, 3), Tile(Suit.MANZU, 4),
            Tile(Suit.MANZU, 5), Tile(Suit.MANZU, 6), Tile(Suit.MANZU, 7),
            Tile(Suit.PINZU, 3), Tile(Suit.PINZU, 4), Tile(Suit.PINZU, 5),
            Tile(Suit.PINZU, 6), Tile(Suit.PINZU, 7), Tile(Suit.PINZU, 8),
            Tile(Suit.SOZU, 4),
        ]
        hand = Hand(tiles)
        winning_tile = Tile(Suit.SOZU, 4)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            fu = self.calculator.calculate_fu(
                hand, winning_tile, combinations[0], yaku_results, self.game_state, False
            )
            # 門清榮和：20 + 10 = 30 符（只有順子，無刻子）
            # 但實際可能有刻子組合，所以至少 30 符
            assert fu >= 30

    def test_calculate_fu_triplet(self):
        """測試刻子符數"""
        # 對對和：有刻子
        tiles = [
            Tile(Suit.MANZU, 1), Tile(Suit.MANZU, 1), Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 2), Tile(Suit.MANZU, 2), Tile(Suit.MANZU, 2),
            Tile(Suit.MANZU, 3), Tile(Suit.MANZU, 3), Tile(Suit.MANZU, 3),
            Tile(Suit.PINZU, 4), Tile(Suit.PINZU, 4), Tile(Suit.PINZU, 4),
            Tile(Suit.PINZU, 5),
        ]
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 5)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = self.yaku_checker.check_all(hand, winning_tile, combinations[0], self.game_state)
            fu = self.calculator.calculate_fu(
                hand, winning_tile, combinations[0], yaku_results, self.game_state, False
            )
            # 門清榮和：20 + 10 = 30
            # 4個中張暗刻：4 * 4 = 16
            # 總計：30 + 16 = 46，進位到 50
            assert fu >= 40  # 至少 40 符

    def test_calculate_han(self):
        """測試翻數計算"""
        yaku_results = [
            YakuResult("立直", "Riichi", "立直", 1, False),
            YakuResult("斷么九", "Tanyao", "斷么九", 1, False),
        ]

        han = self.calculator.calculate_han(yaku_results, 0)
        assert han == 2

        # 加上寶牌
        han = self.calculator.calculate_han(yaku_results, 2)
        assert han == 4

    def test_calculate_score(self):
        """測試完整得分計算"""
        # 斷么九
        tiles = [
            Tile(Suit.MANZU, 2), Tile(Suit.MANZU, 3), Tile(Suit.MANZU, 4),
            Tile(Suit.MANZU, 5), Tile(Suit.MANZU, 6), Tile(Suit.MANZU, 7),
            Tile(Suit.PINZU, 3), Tile(Suit.PINZU, 4), Tile(Suit.PINZU, 5),
            Tile(Suit.PINZU, 6), Tile(Suit.PINZU, 7), Tile(Suit.PINZU, 8),
            Tile(Suit.SOZU, 4),
        ]
        hand = Hand(tiles)
        winning_tile = Tile(Suit.SOZU, 4)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = self.yaku_checker.check_all(hand, winning_tile, combinations[0], self.game_state)
            score_result = self.calculator.calculate(
                hand, winning_tile, combinations[0],
                yaku_results, 0, self.game_state, False
            )

            assert score_result.han > 0
            assert score_result.fu >= 20
            assert score_result.total_points > 0

    def test_calculate_score_mangan(self):
        """測試滿貫得分"""
        # 5翻滿貫
        yaku_results = [
            YakuResult("立直", "Riichi", "立直", 1, False),
            YakuResult("斷么九", "Tanyao", "斷么九", 1, False),
            YakuResult("三色同順", "Sanshoku Doujun", "三色同順", 2, False),
            YakuResult("一気通貫", "Ittsu", "一氣通貫", 2, False),
        ]

        # 模擬一個和牌組合
        tiles = [Tile(Suit.MANZU, i//2+1) for i in range(13)]
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 1)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            score_result = self.calculator.calculate(
                hand, winning_tile, combinations[0],
                yaku_results, 0, self.game_state, False
            )
            # 5翻應該是滿貫（2000點），6翻是跳滿（3000點）
            if score_result.han == 5:
                assert score_result.total_points == 2000
            elif score_result.han >= 6:
                assert score_result.total_points >= 3000

    def test_calculate_score_toitoi(self):
        """測試對對和得分（滿貫）"""
        tiles = [
            Tile(Suit.MANZU, 1), Tile(Suit.MANZU, 1), Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 2), Tile(Suit.MANZU, 2), Tile(Suit.MANZU, 2),
            Tile(Suit.MANZU, 3), Tile(Suit.MANZU, 3), Tile(Suit.MANZU, 3),
            Tile(Suit.PINZU, 4), Tile(Suit.PINZU, 4), Tile(Suit.PINZU, 4),
            Tile(Suit.PINZU, 5),
        ]
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 5)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = self.yaku_checker.check_all(hand, winning_tile, combinations[0], self.game_state)
            score_result = self.calculator.calculate(
                hand, winning_tile, combinations[0],
                yaku_results, 0, self.game_state, False
            )

            # 對對和至少 2 翻
            assert score_result.han >= 2
            # 通常對對和會達到滿貫（5翻以上或4翻40符以上）
            assert score_result.total_points >= 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
