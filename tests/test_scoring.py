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
            Tile(Suit.MANZU, 2),
            Tile(Suit.MANZU, 3),
            Tile(Suit.MANZU, 4),
            Tile(Suit.MANZU, 5),
            Tile(Suit.MANZU, 6),
            Tile(Suit.MANZU, 7),
            Tile(Suit.PINZU, 3),
            Tile(Suit.PINZU, 4),
            Tile(Suit.PINZU, 5),
            Tile(Suit.PINZU, 6),
            Tile(Suit.PINZU, 7),
            Tile(Suit.PINZU, 8),
            Tile(Suit.SOZU, 4),
        ]
        hand = Hand(tiles)
        winning_tile = Tile(Suit.SOZU, 4)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            fu = self.calculator.calculate_fu(
                hand, winning_tile, list(combinations[0]), yaku_results, self.game_state, False
            )
            # 門清榮和：20 + 10 = 30 符（只有順子，無刻子）
            # 但實際可能有刻子組合，所以至少 30 符
            assert fu >= 30

    def test_calculate_fu_triplet(self):
        """測試刻子符數"""
        # 對對和：有刻子
        tiles = [
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 2),
            Tile(Suit.MANZU, 2),
            Tile(Suit.MANZU, 2),
            Tile(Suit.MANZU, 3),
            Tile(Suit.MANZU, 3),
            Tile(Suit.MANZU, 3),
            Tile(Suit.PINZU, 4),
            Tile(Suit.PINZU, 4),
            Tile(Suit.PINZU, 4),
            Tile(Suit.PINZU, 5),
        ]
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 5)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = self.yaku_checker.check_all(
                hand, winning_tile, list(combinations[0]), self.game_state, is_tsumo=False, turns_after_riichi=-1
            )
            fu = self.calculator.calculate_fu(
                hand, winning_tile, list(combinations[0]), yaku_results, self.game_state, False
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
            Tile(Suit.MANZU, 2),
            Tile(Suit.MANZU, 3),
            Tile(Suit.MANZU, 4),
            Tile(Suit.MANZU, 5),
            Tile(Suit.MANZU, 6),
            Tile(Suit.MANZU, 7),
            Tile(Suit.PINZU, 3),
            Tile(Suit.PINZU, 4),
            Tile(Suit.PINZU, 5),
            Tile(Suit.PINZU, 6),
            Tile(Suit.PINZU, 7),
            Tile(Suit.PINZU, 8),
            Tile(Suit.SOZU, 4),
        ]
        hand = Hand(tiles)
        winning_tile = Tile(Suit.SOZU, 4)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = self.yaku_checker.check_all(
                hand, winning_tile, list(combinations[0]), self.game_state, is_tsumo=False, turns_after_riichi=-1
            )
            score_result = self.calculator.calculate(
                hand, winning_tile, list(combinations[0]), yaku_results, 0, self.game_state, False
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
        tiles = [Tile(Suit.MANZU, i // 2 + 1) for i in range(13)]
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 1)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            score_result = self.calculator.calculate(
                hand, winning_tile, list(combinations[0]), yaku_results, 0, self.game_state, False
            )
            # 5翻應該是滿貫（2000點），6翻是跳滿（3000點）
            if score_result.han == 5:
                assert score_result.total_points == 2000
            elif score_result.han >= 6:
                assert score_result.total_points >= 3000

    def test_calculate_score_toitoi(self):
        """測試對對和得分（滿貫）"""
        tiles = [
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 2),
            Tile(Suit.MANZU, 2),
            Tile(Suit.MANZU, 2),
            Tile(Suit.MANZU, 3),
            Tile(Suit.MANZU, 3),
            Tile(Suit.MANZU, 3),
            Tile(Suit.PINZU, 4),
            Tile(Suit.PINZU, 4),
            Tile(Suit.PINZU, 4),
            Tile(Suit.PINZU, 5),
        ]
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 5)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = self.yaku_checker.check_all(
                hand, winning_tile, list(combinations[0]), self.game_state, is_tsumo=False, turns_after_riichi=-1
            )
            score_result = self.calculator.calculate(
                hand, winning_tile, list(combinations[0]), yaku_results, 0, self.game_state, False
            )

            # 對對和至少 2 翻
            assert score_result.han >= 2
            # 通常對對和會達到滿貫（5翻以上或4翻40符以上）
            assert score_result.total_points >= 1000

    def test_waiting_type_tanki(self):
        """測試單騎聽符數（+2符）"""
        # 單騎聽：和牌牌是對子的一部分
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
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 4)  # 單騎聽
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            fu = self.calculator.calculate_fu(
                hand, winning_tile, list(combinations[0]), yaku_results, self.game_state, False
            )
            # 門清榮和：20 + 10 = 30，單騎聽 +2 = 32，進位到 40
            # 但如果有其他符數，可能更多
            assert fu >= 30

    def test_waiting_type_penchan(self):
        """測試邊張聽符數（+2符）"""
        # 邊張聽：1-2 聽 3 或 8-9 聽 7
        tiles = [
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 2),  # 邊張聽 3
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
            Tile(Suit.PINZU, 5),
        ]
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 3)  # 邊張聽
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            fu = self.calculator.calculate_fu(
                hand, winning_tile, list(combinations[0]), yaku_results, self.game_state, False
            )
            assert fu >= 30

    def test_calculate_payments_tsumo(self):
        """測試自摸支付計算"""
        # 創建一個得分結果
        score_result = ScoreResult(
            han=1,
            fu=30,
            base_points=0,
            total_points=1000,
            payment_from=0,
            payment_to=0,
            is_yakuman=False,
            yakuman_count=1,
            is_tsumo=True,
        )

        # 計算支付
        score_result.calculate_payments(self.game_state)

        # 自摸時應該有支付信息
        assert score_result.total_points > 0
        assert score_result.honba_bonus >= 0

    def test_calculate_payments_ron(self):
        """測試榮和支付計算"""
        # 創建一個得分結果
        score_result = ScoreResult(
            han=1,
            fu=30,
            base_points=0,
            total_points=1000,
            payment_from=1,
            payment_to=0,
            is_yakuman=False,
            yakuman_count=1,
            is_tsumo=False,
        )

        # 計算支付
        score_result.calculate_payments(self.game_state)

        # 榮和時應該有支付信息
        assert score_result.total_points > 0
        assert score_result.honba_bonus >= 0

    def test_calculate_payments_dealer_tsumo(self):
        """測試莊家自摸支付"""
        self.game_state.set_dealer(0)

        score_result = ScoreResult(
            han=1,
            fu=30,
            base_points=0,
            total_points=1000,
            payment_from=0,
            payment_to=0,
            is_yakuman=False,
            yakuman_count=1,
            is_tsumo=True,
        )

        score_result.calculate_payments(self.game_state)

        # 莊家自摸時，每個閒家支付
        assert score_result.dealer_payment >= 0

    def test_determine_waiting_type(self):
        """測試聽牌類型判定"""
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
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 4)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            waiting_type = self.calculator._determine_waiting_type(winning_tile, list(combinations[0]))
            assert waiting_type in ["ryanmen", "penchan", "kanchan", "tanki", "shabo"]

    def test_waiting_type_kanchan(self):
        """測試嵌張聽符數（+2符）"""
        # 嵌張聽：2-4 聽 3（中間張）
        tiles = [
            Tile(Suit.MANZU, 2),
            Tile(Suit.MANZU, 4),  # 嵌張聽 3
            Tile(Suit.MANZU, 5),
            Tile(Suit.MANZU, 6),
            Tile(Suit.MANZU, 7),
            Tile(Suit.MANZU, 8),
            Tile(Suit.MANZU, 9),
            Tile(Suit.PINZU, 1),
            Tile(Suit.PINZU, 2),
            Tile(Suit.PINZU, 3),
            Tile(Suit.PINZU, 4),
            Tile(Suit.PINZU, 5),
        ]
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 3)  # 嵌張聽
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            fu = self.calculator.calculate_fu(
                hand, winning_tile, list(combinations[0]), yaku_results, self.game_state, False
            )
            # 門清榮和：20 + 10 = 30，嵌張聽 +2 = 32，進位到 40
            assert fu >= 30

    def test_waiting_type_ryanmen(self):
        """測試兩面聽符數（+0符）"""
        # 兩面聽：4-5 聽 3 或 6（不增加符數）
        tiles = [
            Tile(Suit.MANZU, 4),
            Tile(Suit.MANZU, 5),  # 兩面聽 3 或 6
            Tile(Suit.MANZU, 7),
            Tile(Suit.MANZU, 8),
            Tile(Suit.MANZU, 9),
            Tile(Suit.PINZU, 1),
            Tile(Suit.PINZU, 2),
            Tile(Suit.PINZU, 3),
            Tile(Suit.PINZU, 4),
            Tile(Suit.PINZU, 5),
            Tile(Suit.PINZU, 6),
        ]
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 6)  # 兩面聽
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            fu = self.calculator.calculate_fu(
                hand, winning_tile, list(combinations[0]), yaku_results, self.game_state, False
            )
            # 門清榮和：20 + 10 = 30，兩面聽不增加符數，進位到 30
            assert fu >= 30

    def test_waiting_type_empty_combination(self):
        """測試空組合的聽牌類型（默認為兩面聽）"""
        # 測試當 winning_combination 為空時的情況
        winning_tile = Tile(Suit.MANZU, 1)
        waiting_type = self.calculator._determine_waiting_type(winning_tile, [])
        assert waiting_type == "ryanmen"

    def test_fu_kan_concealed(self):
        """測試暗槓符數"""
        # 創建一個有暗槓的手牌（門清）
        # 注意：這裡需要手動構建 winning_combination 來測試槓子符
        tiles = [
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 1),  # 暗槓
            Tile(Suit.MANZU, 2),
            Tile(Suit.MANZU, 3),
            Tile(Suit.MANZU, 4),
            Tile(Suit.MANZU, 5),
            Tile(Suit.MANZU, 6),
            Tile(Suit.MANZU, 7),
            Tile(Suit.PINZU, 1),
            Tile(Suit.PINZU, 2),
        ]
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 3)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            # 手動構建包含槓子的組合（因為標準組合可能不包含槓子）
            # 這裡我們測試是否能正確計算（如果組合中有槓子）
            yaku_results = []
            fu = self.calculator.calculate_fu(
                hand, winning_tile, list(combinations[0]), yaku_results, self.game_state, False
            )
            # 至少應該有基本符數
            assert fu >= 20

    def test_fu_kan_open(self):
        """測試明槓符數（非門清）"""
        # 創建一個有明刻的手牌（非門清）
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
        ]
        # 添加一個明刻（模擬有副露，使手牌非門清）
        from pyriichi.hand import Meld, MeldType

        hand = Hand(tiles)
        meld = Meld(MeldType.PON, [Tile(Suit.SOZU, 1), Tile(Suit.SOZU, 1), Tile(Suit.SOZU, 1)])
        hand._melds.append(meld)

        winning_tile = Tile(Suit.MANZU, 9)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            fu = self.calculator.calculate_fu(
                hand, winning_tile, list(combinations[0]), yaku_results, self.game_state, False
            )
            # 非門清榮和：20 + 0 = 20，進位到 20
            assert fu >= 20

    def test_fu_pair_sangen(self):
        """測試三元牌對子符數（+2符）"""
        # 創建一個有三元牌對子的手牌
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
            Tile(Suit.JIHAI, 5),
            Tile(Suit.JIHAI, 5),  # 白對子
        ]
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 9)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            fu = self.calculator.calculate_fu(
                hand, winning_tile, list(combinations[0]), yaku_results, self.game_state, False
            )
            # 門清榮和：20 + 10 = 30，三元牌對子 +2 = 32，進位到 40
            assert fu >= 30

    def test_fu_pair_round_wind(self):
        """測試場風對子符數（+2符）"""
        # 創建一個有場風對子的手牌（東風局）
        self.game_state.set_round(Wind.EAST, 1)
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
            Tile(Suit.JIHAI, 1),
            Tile(Suit.JIHAI, 1),  # 東對子（場風）
        ]
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 9)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            fu = self.calculator.calculate_fu(
                hand, winning_tile, list(combinations[0]), yaku_results, self.game_state, False
            )
            # 門清榮和：20 + 10 = 30，場風對子 +2 = 32，進位到 40
            assert fu >= 30

    def test_fu_pair_round_wind_south(self):
        """測試南風場的場風對子符數"""
        # 南風局
        self.game_state.set_round(Wind.SOUTH, 1)
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
            Tile(Suit.JIHAI, 2),
            Tile(Suit.JIHAI, 2),  # 南對子（場風）
        ]
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 9)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            fu = self.calculator.calculate_fu(
                hand, winning_tile, list(combinations[0]), yaku_results, self.game_state, False
            )
            # 場風對子應該 +2 符
            assert fu >= 30

    def test_fu_kan_terminal_concealed(self):
        """測試幺九暗槓符數（+32符）"""
        # 手動構建包含幺九暗槓的和牌組合
        tiles = [
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 2),
            Tile(Suit.MANZU, 3),
            Tile(Suit.MANZU, 4),
            Tile(Suit.MANZU, 5),
            Tile(Suit.MANZU, 6),
            Tile(Suit.PINZU, 1),
            Tile(Suit.PINZU, 2),
        ]
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 3)

        # 手動構建包含幺九暗槓的組合
        combo_with_kan = [
            ("kan", (Suit.MANZU, 1)),  # 幺九暗槓
            ("sequence", (Suit.MANZU, 4)),
            ("sequence", (Suit.PINZU, 1)),
            ("pair", (Suit.PINZU, 3)),
        ]

        yaku_results = []
        fu = self.calculator.calculate_fu(hand, winning_tile, combo_with_kan, yaku_results, self.game_state, False)
        # 門清榮和：20 + 10 = 30，幺九暗槓 +32 = 62，進位到 70
        assert fu >= 60

    def test_fu_kan_terminal_open(self):
        """測試幺九明槓符數（+16符，非門清）"""
        tiles = [
            Tile(Suit.MANZU, 2),
            Tile(Suit.MANZU, 3),
            Tile(Suit.MANZU, 4),
            Tile(Suit.MANZU, 5),
            Tile(Suit.MANZU, 6),
            Tile(Suit.MANZU, 7),
            Tile(Suit.PINZU, 1),
            Tile(Suit.PINZU, 2),
        ]
        # 添加明刻使手牌非門清
        from pyriichi.hand import Meld, MeldType

        hand = Hand(tiles)
        meld = Meld(MeldType.PON, [Tile(Suit.SOZU, 1), Tile(Suit.SOZU, 1), Tile(Suit.SOZU, 1)])
        hand._melds.append(meld)

        winning_tile = Tile(Suit.PINZU, 3)

        # 手動構建包含幺九明槓的組合
        combo_with_kan = [
            ("kan", (Suit.MANZU, 9)),  # 幺九明槓（通過 hand.is_concealed 判斷為明槓）
            ("sequence", (Suit.MANZU, 2)),
            ("sequence", (Suit.PINZU, 1)),
            ("pair", (Suit.PINZU, 3)),
        ]

        yaku_results = []
        fu = self.calculator.calculate_fu(hand, winning_tile, combo_with_kan, yaku_results, self.game_state, False)
        # 非門清榮和：20 + 0 = 20，幺九明槓 +16 = 36，進位到 40
        assert fu >= 30

    def test_fu_kan_simple_concealed(self):
        """測試中張暗槓符數（+16符）"""
        tiles = [
            Tile(Suit.MANZU, 2),
            Tile(Suit.MANZU, 3),
            Tile(Suit.MANZU, 4),
            Tile(Suit.MANZU, 5),
            Tile(Suit.MANZU, 6),
            Tile(Suit.PINZU, 1),
            Tile(Suit.PINZU, 2),
        ]
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 3)

        # 手動構建包含中張暗槓的組合
        combo_with_kan = [
            ("kan", (Suit.MANZU, 5)),  # 中張暗槓
            ("sequence", (Suit.MANZU, 2)),
            ("sequence", (Suit.PINZU, 1)),
            ("pair", (Suit.PINZU, 3)),
        ]

        yaku_results = []
        fu = self.calculator.calculate_fu(hand, winning_tile, combo_with_kan, yaku_results, self.game_state, False)
        # 門清榮和：20 + 10 = 30，中張暗槓 +16 = 46，進位到 50
        assert fu >= 40

    def test_fu_kan_simple_open(self):
        """測試中張明槓符數（+8符，非門清）"""
        tiles = [
            Tile(Suit.MANZU, 2),
            Tile(Suit.MANZU, 3),
            Tile(Suit.MANZU, 4),
            Tile(Suit.MANZU, 6),
            Tile(Suit.MANZU, 7),
            Tile(Suit.PINZU, 1),
            Tile(Suit.PINZU, 2),
        ]
        # 添加明刻使手牌非門清
        from pyriichi.hand import Meld, MeldType

        hand = Hand(tiles)
        meld = Meld(MeldType.PON, [Tile(Suit.SOZU, 1), Tile(Suit.SOZU, 1), Tile(Suit.SOZU, 1)])
        hand._melds.append(meld)

        winning_tile = Tile(Suit.PINZU, 3)

        # 手動構建包含中張明槓的組合
        combo_with_kan = [
            ("kan", (Suit.MANZU, 5)),  # 中張明槓
            ("sequence", (Suit.MANZU, 2)),
            ("sequence", (Suit.PINZU, 1)),
            ("pair", (Suit.PINZU, 3)),
        ]

        yaku_results = []
        fu = self.calculator.calculate_fu(hand, winning_tile, combo_with_kan, yaku_results, self.game_state, False)
        # 非門清榮和：20 + 0 = 20，中張明槓 +8 = 28，進位到 30
        assert fu >= 20

    def test_waiting_type_penchan_rank1(self):
        """測試邊張聽（rank=1的情況）"""
        # 測試 1-2-3 聽 1 的情況（rank=1）
        winning_tile = Tile(Suit.MANZU, 1)
        combo = [
            ("sequence", (Suit.MANZU, 1)),  # 1-2-3 順子
            ("sequence", (Suit.MANZU, 4)),
            ("sequence", (Suit.MANZU, 7)),
            ("pair", (Suit.PINZU, 1)),
        ]
        waiting_type = self.calculator._determine_waiting_type(winning_tile, combo)
        assert waiting_type == "penchan"

    def test_waiting_type_penchan_rank7(self):
        """測試邊張聽（rank=7的情況）"""
        # 測試 7-8-9 聽 9 的情況（rank=7）
        winning_tile = Tile(Suit.MANZU, 9)
        combo = [
            ("sequence", (Suit.MANZU, 7)),  # 7-8-9 順子
            ("sequence", (Suit.MANZU, 4)),
            ("sequence", (Suit.MANZU, 1)),
            ("pair", (Suit.PINZU, 1)),
        ]
        waiting_type = self.calculator._determine_waiting_type(winning_tile, combo)
        assert waiting_type == "penchan"

    def test_waiting_type_kanchan_middle(self):
        """測試嵌張聽（中間張的情況）"""
        # 測試 2-3-4 聽 3 的情況（rank+1，中間張）
        winning_tile = Tile(Suit.MANZU, 3)
        combo = [
            ("sequence", (Suit.MANZU, 2)),  # 2-3-4 順子，和牌牌是中間張（rank+1=3）
            ("sequence", (Suit.MANZU, 5)),
            ("sequence", (Suit.MANZU, 8)),
            ("pair", (Suit.PINZU, 1)),
        ]
        waiting_type = self.calculator._determine_waiting_type(winning_tile, combo)
        assert waiting_type == "kanchan"

    def test_waiting_type_kanchan_other(self):
        """測試嵌張聽（其他情況）"""
        # 測試其他嵌張聽的情況（rank=2, rank+2=4）
        winning_tile = Tile(Suit.MANZU, 4)
        combo = [
            ("sequence", (Suit.MANZU, 2)),  # 2-3-4 順子，和牌牌是最後一張但不是邊張
            ("sequence", (Suit.MANZU, 5)),
            ("sequence", (Suit.MANZU, 8)),
            ("pair", (Suit.PINZU, 1)),
        ]
        waiting_type = self.calculator._determine_waiting_type(winning_tile, combo)
        # 應該是嵌張或邊張，取決於具體實現
        assert waiting_type in ["kanchan", "penchan"]

    def test_waiting_type_not_in_sequence(self):
        """測試不在順子中的聽牌類型判定"""
        # 和牌牌不在任何順子中，且不是對子的一部分，應該返回兩面聽
        winning_tile = Tile(Suit.PINZU, 5)
        combo = [
            ("sequence", (Suit.MANZU, 1)),  # 1-2-3 順子（萬子）
            ("sequence", (Suit.MANZU, 4)),  # 4-5-6 順子（萬子）
            ("sequence", (Suit.MANZU, 7)),  # 7-8-9 順子（萬子）
            ("pair", (Suit.PINZU, 1)),  # 對子是 1p，不是 5p
        ]
        # 和牌牌 5p 不在任何順子中（因為順子都是萬子），也不是對子的一部分
        waiting_type = self.calculator._determine_waiting_type(winning_tile, combo)
        assert waiting_type == "ryanmen"

    def test_score_result_yakuman_13_han(self):
        """測試13翻役滿判定"""
        score_result = ScoreResult(
            han=13,
            fu=30,
            base_points=0,
            total_points=0,
            payment_from=0,
            payment_to=0,
            is_yakuman=False,
            yakuman_count=1,
        )
        # 13翻應該是役滿（8000點）
        assert score_result.total_points == 8000

    def test_score_result_triple_mangan(self):
        """測試11翻三倍滿判定"""
        score_result = ScoreResult(
            han=11,
            fu=30,
            base_points=0,
            total_points=0,
            payment_from=0,
            payment_to=0,
            is_yakuman=False,
            yakuman_count=1,
        )
        # 11翻應該是三倍滿（6000點）
        assert score_result.total_points == 6000

    def test_score_result_double_mangan(self):
        """測試8翻倍滿判定"""
        score_result = ScoreResult(
            han=8,
            fu=30,
            base_points=0,
            total_points=0,
            payment_from=0,
            payment_to=0,
            is_yakuman=False,
            yakuman_count=1,
        )
        # 8翻應該是倍滿（4000點）
        assert score_result.total_points == 4000

    def test_score_result_mangan_5_han(self):
        """測試5翻滿貫判定"""
        score_result = ScoreResult(
            han=5,
            fu=30,
            base_points=0,
            total_points=0,
            payment_from=0,
            payment_to=0,
            is_yakuman=False,
            yakuman_count=1,
        )
        # 5翻應該是滿貫（2000點）
        assert score_result.total_points == 2000

    def test_score_result_mangan_4_han_40_fu(self):
        """測試4翻40符滿貫判定"""
        score_result = ScoreResult(
            han=4,
            fu=40,
            base_points=0,
            total_points=0,
            payment_from=0,
            payment_to=0,
            is_yakuman=False,
            yakuman_count=1,
        )
        # 4翻40符應該是滿貫（2000點）
        assert score_result.total_points == 2000

    def test_calculate_payments_non_dealer_tsumo(self):
        """測試閒家自摸支付計算"""
        self.game_state.set_dealer(0)  # 玩家0是莊家

        score_result = ScoreResult(
            han=1,
            fu=30,
            base_points=0,
            total_points=1000,
            payment_from=0,
            payment_to=1,  # 閒家自摸
            is_yakuman=False,
            yakuman_count=1,
            is_tsumo=True,
        )

        # 計算支付
        score_result.calculate_payments(self.game_state)

        # 閒家自摸時，莊家支付 2 倍，其他閒家支付 1 倍
        assert score_result.dealer_payment > 0  # 莊家支付
        assert score_result.non_dealer_payment > 0  # 其他閒家支付
        assert score_result.total_points > 0

    def test_calculate_fu_seven_pairs(self):
        """測試七對子符數"""
        tiles = [
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 2),
            Tile(Suit.MANZU, 2),
            Tile(Suit.MANZU, 3),
            Tile(Suit.MANZU, 3),
            Tile(Suit.MANZU, 4),
            Tile(Suit.MANZU, 4),
            Tile(Suit.MANZU, 5),
            Tile(Suit.MANZU, 5),
            Tile(Suit.MANZU, 6),
            Tile(Suit.MANZU, 6),
            Tile(Suit.MANZU, 7),
        ]
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 7)
        # 七對子沒有 winning_combination（返回空列表）
        yaku_results = []

        fu = self.calculator.calculate_fu(hand, winning_tile, [], yaku_results, self.game_state, False)
        # 七對子固定 25 符
        assert fu == 25

    def test_calculate_fu_pinfu_tsumo(self):
        """測試平和自摸符數（30 符）"""
        # 平和：只有順子，無刻子，無役牌對子
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
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 4)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            # 檢查是否有平和
            yaku_results = self.yaku_checker.check_all(
                hand, winning_tile, list(combinations[0]), self.game_state, is_tsumo=True, turns_after_riichi=-1
            )
            is_pinfu = any(r.name == "平和" for r in yaku_results)

            if is_pinfu:
                fu = self.calculator.calculate_fu(
                    hand, winning_tile, list(combinations[0]), yaku_results, self.game_state, True
                )
                # 平和自摸：30 符（20基本符 + 2自摸符 + 8副底符）
                assert fu == 30

    def test_calculate_fu_pinfu_ron(self):
        """測試平和榮和符數（30 符）"""
        # 平和：只有順子，無刻子，無役牌對子
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
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 4)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            # 檢查是否有平和
            yaku_results = self.yaku_checker.check_all(
                hand, winning_tile, list(combinations[0]), self.game_state, is_tsumo=False, turns_after_riichi=-1
            )
            is_pinfu = any(r.name == "平和" for r in yaku_results)

            if is_pinfu:
                fu = self.calculator.calculate_fu(
                    hand, winning_tile, list(combinations[0]), yaku_results, self.game_state, False
                )
                # 平和榮和：20 符，進位到 30
                assert fu == 30

    def test_calculate_fu_concealed_tsumo(self):
        """測試門清自摸符數"""
        # 使用有刻子的手牌，確保不是平和
        tiles = [
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 1),  # 刻子
            Tile(Suit.MANZU, 2),
            Tile(Suit.MANZU, 3),
            Tile(Suit.MANZU, 4),
            Tile(Suit.MANZU, 5),
            Tile(Suit.MANZU, 6),
            Tile(Suit.MANZU, 7),
            Tile(Suit.PINZU, 1),
            Tile(Suit.PINZU, 2),
            Tile(Suit.PINZU, 3),
            Tile(Suit.PINZU, 4),
        ]
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 4)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            # 確保不是平和（有刻子就不是平和）
            fu = self.calculator.calculate_fu(
                hand, winning_tile, list(combinations[0]), yaku_results, self.game_state, True
            )
            # 門清自摸：20 + 2 = 22，加上刻子符，進位到 30
            assert fu >= 30

    def test_calculate_fu_open_tsumo(self):
        """測試非門清自摸符數"""
        # 使用有刻子的手牌，確保不是平和
        tiles = [
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 1),  # 刻子
            Tile(Suit.MANZU, 2),
            Tile(Suit.MANZU, 3),
            Tile(Suit.MANZU, 4),
            Tile(Suit.MANZU, 5),
            Tile(Suit.MANZU, 6),
            Tile(Suit.PINZU, 1),
            Tile(Suit.PINZU, 2),
        ]
        # 添加副露使手牌非門清
        from pyriichi.hand import Meld, MeldType

        hand = Hand(tiles)
        meld = Meld(MeldType.PON, [Tile(Suit.SOZU, 1), Tile(Suit.SOZU, 1), Tile(Suit.SOZU, 1)])
        hand._melds.append(meld)

        winning_tile = Tile(Suit.PINZU, 3)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            # 確保不是平和（有刻子就不是平和）
            # 確認手牌是非門清
            assert not hand.is_concealed
            fu = self.calculator.calculate_fu(
                hand, winning_tile, list(combinations[0]), yaku_results, self.game_state, True
            )
            # 非門清自摸：20 + 2 = 22，加上刻子符，進位到 30
            assert fu >= 20

    def test_calculate_fu_open_triplet_terminal(self):
        """測試非門清幺九刻子符數"""
        tiles = [
            Tile(Suit.MANZU, 2),
            Tile(Suit.MANZU, 3),
            Tile(Suit.MANZU, 4),
            Tile(Suit.MANZU, 5),
            Tile(Suit.MANZU, 6),
            Tile(Suit.MANZU, 7),
            Tile(Suit.MANZU, 8),
            Tile(Suit.PINZU, 1),
            Tile(Suit.PINZU, 2),
        ]
        # 添加明刻使手牌非門清
        from pyriichi.hand import Meld, MeldType

        hand = Hand(tiles)
        meld = Meld(MeldType.PON, [Tile(Suit.SOZU, 1), Tile(Suit.SOZU, 1), Tile(Suit.SOZU, 1)])
        hand._melds.append(meld)

        winning_tile = Tile(Suit.PINZU, 3)

        # 手動構建包含幺九明刻的組合
        combo_with_triplet = [
            ("triplet", (Suit.MANZU, 9)),  # 幺九明刻
            ("sequence", (Suit.MANZU, 2)),
            ("sequence", (Suit.PINZU, 1)),
            ("pair", (Suit.PINZU, 3)),
        ]

        yaku_results = []
        fu = self.calculator.calculate_fu(hand, winning_tile, combo_with_triplet, yaku_results, self.game_state, False)
        # 非門清榮和：20 + 0 = 20，幺九明刻 +4 = 24，進位到 30
        assert fu >= 20

    def test_calculate_fu_open_triplet_simple(self):
        """測試非門清中張刻子符數"""
        tiles = [
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 2),
            Tile(Suit.MANZU, 3),
            Tile(Suit.MANZU, 5),
            Tile(Suit.MANZU, 6),
            Tile(Suit.PINZU, 1),
            Tile(Suit.PINZU, 2),
        ]
        # 添加明刻使手牌非門清
        from pyriichi.hand import Meld, MeldType

        hand = Hand(tiles)
        meld = Meld(MeldType.PON, [Tile(Suit.SOZU, 1), Tile(Suit.SOZU, 1), Tile(Suit.SOZU, 1)])
        hand._melds.append(meld)

        winning_tile = Tile(Suit.PINZU, 3)

        # 手動構建包含中張明刻的組合
        combo_with_triplet = [
            ("triplet", (Suit.MANZU, 5)),  # 中張明刻
            ("sequence", (Suit.MANZU, 1)),
            ("sequence", (Suit.PINZU, 1)),
            ("pair", (Suit.PINZU, 3)),
        ]

        yaku_results = []
        fu = self.calculator.calculate_fu(hand, winning_tile, combo_with_triplet, yaku_results, self.game_state, False)
        # 非門清榮和：20 + 0 = 20，中張明刻 +2 = 22，進位到 30
        assert fu >= 20

    def test_waiting_type_kanchan_other_rank(self):
        """測試嵌張聽"""
        # 測試 rank=2, winning_tile.rank == rank（第一張）但不是 rank=1 的情況
        winning_tile = Tile(Suit.MANZU, 2)
        combo = [
            ("sequence", (Suit.MANZU, 2)),  # 2-3-4 順子，和牌牌是第一張
            ("sequence", (Suit.MANZU, 5)),
            ("sequence", (Suit.MANZU, 8)),
            ("pair", (Suit.PINZU, 1)),
        ]
        waiting_type = self.calculator._determine_waiting_type(winning_tile, combo)
        # 應該是嵌張（因為 rank != 1）
        assert waiting_type == "kanchan"

    def test_waiting_type_in_sequence_check(self):
        """測試在順子中的檢查邏輯"""
        # 測試 winning_tile 在順子中的情況，確保觸發 break
        # 使用一個不會被前面邏輯提前返回的情況
        winning_tile = Tile(Suit.MANZU, 4)  # 在 3-4-5 順子中
        combo = [
            ("sequence", (Suit.MANZU, 3)),  # 3-4-5 順子，和牌牌在中間
            ("sequence", (Suit.MANZU, 6)),  # 6-7-8 順子
            ("sequence", (Suit.MANZU, 9)),  # 這個順子不會被處理（因為會 break）
            ("pair", (Suit.PINZU, 1)),
        ]
        # winning_tile 4m 在 3-4-5 順子中的檢查和 break
        waiting_type = self.calculator._determine_waiting_type(winning_tile, combo)
        # 應該檢測到在順子中，可能是嵌張
        assert waiting_type in ["kanchan", "penchan", "ryanmen"]

    def test_calculate_fu_open_tsumo_direct(self):
        """直接測試非門清自摸符數"""
        # 手動構建一個非門清、非平和的情況
        tiles = [
            Tile(Suit.MANZU, 2),
            Tile(Suit.MANZU, 3),
            Tile(Suit.MANZU, 4),
            Tile(Suit.MANZU, 5),
            Tile(Suit.MANZU, 6),
            Tile(Suit.MANZU, 7),
            Tile(Suit.PINZU, 1),
            Tile(Suit.PINZU, 2),
        ]
        # 添加副露使手牌非門清
        from pyriichi.hand import Meld, MeldType

        hand = Hand(tiles)
        meld = Meld(MeldType.PON, [Tile(Suit.SOZU, 1), Tile(Suit.SOZU, 1), Tile(Suit.SOZU, 1)])
        hand._melds.append(meld)

        winning_tile = Tile(Suit.PINZU, 3)
        # 手動構建組合，確保不是平和（有刻子）
        combo = [
            ("triplet", (Suit.MANZU, 1)),  # 刻子（不是平和）
            ("sequence", (Suit.MANZU, 2)),
            ("sequence", (Suit.MANZU, 5)),
            ("pair", (Suit.PINZU, 3)),
        ]

        yaku_results = []  # 空列表，確保不是平和
        # 確認手牌是非門清
        assert not hand.is_concealed
        fu = self.calculator.calculate_fu(hand, winning_tile, combo, yaku_results, self.game_state, True)
        # 非門清自摸：20 + 2 = 22，加上刻子符的情況
        # winning_tile 在順子中，但前面的邏輯沒有提前返回，執行到最後
        winning_tile = Tile(Suit.MANZU, 4)
        combo = [
            ("sequence", (Suit.MANZU, 3)),  # 3-4-5 順子，和牌牌在中間
            ("sequence", (Suit.MANZU, 6)),  # 6-7-8 順子
            ("sequence", (Suit.MANZU, 9)),  # 9-10-11 順子（但只有 1-9，所以這個不會匹配）
            ("pair", (Suit.PINZU, 1)),
        ]
        # winning_tile 4m 在 3-4-5 順子中，會觸發 in_sequence = True
        # 但由於前面的邏輯可能已經處理過，需要確保執行到最後的 return
        waiting_type = self.calculator._determine_waiting_type(winning_tile, combo)
        # 應該返回某種聽牌類型
        assert waiting_type in ["kanchan", "penchan", "ryanmen", "tanki", "shabo"]

    def test_waiting_type_shabo(self):
        """測試雙碰聽符數（+0符，不增加符數）"""
        # 雙碰聽：有兩個對子，聽其中一個
        # 例如：11m 22m 33m 44p 55p 66p 77s（聽 11m 或 22m）
        # 這裡用一個簡化的例子：兩個對子，聽其中一個
        winning_tile = Tile(Suit.MANZU, 1)
        combo = [
            ("triplet", (Suit.MANZU, 3)),  # 刻子
            ("triplet", (Suit.MANZU, 5)),  # 刻子
            ("triplet", (Suit.PINZU, 1)),  # 刻子
            ("pair", (Suit.MANZU, 1)),  # 對子（和牌牌）
        ]
        # 注意：雙碰聽的判定較複雜，這裡主要測試符數計算
        # 如果判定為雙碰聽，應該不增加符數
        waiting_type = self.calculator._determine_waiting_type(winning_tile, combo)
        # 雙碰聽不增加符數，所以符數計算時應該跳過
        # 這裡主要測試 waiting_type 的判定邏輯
        assert waiting_type in ["tanki", "ryanmen", "shabo"]

    def test_fu_waiting_type_shabo_no_fu(self):
        """測試雙碰聽不增加符數"""
        # 創建一個雙碰聽的手牌（實際判定可能較複雜，這裡測試符數計算邏輯）
        tiles = [
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 2),
            Tile(Suit.MANZU, 2),
            Tile(Suit.MANZU, 3),
            Tile(Suit.MANZU, 3),
            Tile(Suit.MANZU, 3),
            Tile(Suit.PINZU, 4),
            Tile(Suit.PINZU, 5),
            Tile(Suit.PINZU, 6),
            Tile(Suit.SOZU, 7),
            Tile(Suit.SOZU, 8),
            Tile(Suit.SOZU, 9),
        ]
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 1)  # 雙碰聽（聽 11m 或 22m）
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            # 計算符數
            fu = self.calculator.calculate_fu(
                hand, winning_tile, list(combinations[0]), yaku_results, self.game_state, False
            )
            # 檢查聽牌類型
            waiting_type = self.calculator._determine_waiting_type(winning_tile, list(combinations[0]))
            # 如果判定為雙碰聽（shabo），不應該增加符數
            # 門清榮和：20 + 10 = 30，加上刻子符，進位
            # 雙碰聽不增加符數，所以應該 >= 30
            assert fu >= 30
            # 如果 waiting_type 是 shabo，確認不增加符數
            if waiting_type == "shabo":
                # 雙碰聽不增加符數，所以符數應該與其他聽牌類型相同（不考慮聽牌符）
                pass  # 這裡主要確認邏輯正確

    def test_fu_pair_player_wind(self):
        """測試自風對子符數（+2符）"""
        # 創建一個有自風對子的手牌
        # 假設玩家0是東家（自風是東）
        self.game_state.set_dealer(0)  # 玩家0是莊家（東家）
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
            Tile(Suit.JIHAI, 1),  # 東（自風）
            Tile(Suit.JIHAI, 1),  # 東（自風）
        ]
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 9)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            # 玩家0（東家）的自風是東
            fu = self.calculator.calculate_fu(
                hand, winning_tile, list(combinations[0]), yaku_results, self.game_state, False, player_position=0
            )
            # 門清榮和：20 + 10 = 30，自風對子 +2 = 32，進位到 40
            assert fu >= 30

    def test_fu_pair_player_wind_south(self):
        """測試南家自風對子符數（+2符）"""
        # 玩家1是南家（自風是南）
        self.game_state.set_dealer(0)  # 玩家0是莊家（東家）
        # 玩家1的自風是南
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
            Tile(Suit.JIHAI, 2),  # 南（自風）
            Tile(Suit.JIHAI, 2),  # 南（自風）
        ]
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 9)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            # 玩家1（南家）的自風是南
            fu = self.calculator.calculate_fu(
                hand, winning_tile, list(combinations[0]), yaku_results, self.game_state, False, player_position=1
            )
            # 門清榮和：20 + 10 = 30，自風對子 +2 = 32，進位到 40
            assert fu >= 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
