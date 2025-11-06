"""
GameState 的單元測試
"""

import pytest
from pyriichi.game_state import GameState, Wind


class TestGameState:
    """遊戲狀態測試"""

    def setup_method(self):
        """設置測試環境"""
        self.game_state = GameState(num_players=4)

    def test_initial_state(self):
        """測試初始狀態"""
        assert self.game_state.round_wind == Wind.EAST
        assert self.game_state.round_number == 1
        assert self.game_state.dealer == 0
        assert self.game_state.honba == 0
        assert self.game_state.riichi_sticks == 0
        assert len(self.game_state.scores) == 4
        assert all(score == 25000 for score in self.game_state.scores)

    def test_set_round(self):
        """測試設置局數"""
        self.game_state.set_round(Wind.SOUTH, 2)
        assert self.game_state.round_wind == Wind.SOUTH
        assert self.game_state.round_number == 2

    def test_set_dealer(self):
        """測試設置莊家"""
        self.game_state.set_dealer(2)
        assert self.game_state.dealer == 2

        # 測試無效的莊家位置
        with pytest.raises(ValueError):
            self.game_state.set_dealer(4)

    def test_add_honba(self):
        """測試增加本場數"""
        self.game_state.add_honba()
        assert self.game_state.honba == 1

        self.game_state.add_honba(2)
        assert self.game_state.honba == 3

    def test_reset_honba(self):
        """測試重置本場數"""
        self.game_state.add_honba(3)
        self.game_state.reset_honba()
        assert self.game_state.honba == 0

    def test_add_riichi_stick(self):
        """測試增加供託棒"""
        self.game_state.add_riichi_stick()
        assert self.game_state.riichi_sticks == 1

        self.game_state.add_riichi_stick()
        assert self.game_state.riichi_sticks == 2

    def test_clear_riichi_sticks(self):
        """測試清除供託棒"""
        self.game_state.add_riichi_stick()
        self.game_state.add_riichi_stick()
        self.game_state.add_riichi_stick()
        self.game_state.clear_riichi_sticks()
        assert self.game_state.riichi_sticks == 0

    def test_update_score(self):
        """測試更新玩家點數"""
        self.game_state.update_score(0, 1000)
        assert self.game_state.scores[0] == 26000

        self.game_state.update_score(0, -500)
        assert self.game_state.scores[0] == 25500

        # 測試無效的玩家位置
        with pytest.raises(ValueError):
            self.game_state.update_score(4, 1000)

    def test_transfer_points(self):
        """測試轉移點數"""
        self.game_state.transfer_points(0, 1, 1000)
        assert self.game_state.scores[0] == 24000
        assert self.game_state.scores[1] == 26000

    def test_next_round(self):
        """測試進入下一局"""
        # 初始是東1局
        assert self.game_state.round_wind == Wind.EAST
        assert self.game_state.round_number == 1

        # 下一局：東2局
        has_next = self.game_state.next_round()
        assert has_next is True
        assert self.game_state.round_wind == Wind.EAST
        assert self.game_state.round_number == 2

        # 繼續到東4局
        self.game_state.next_round()
        self.game_state.next_round()
        assert self.game_state.round_number == 4

        # 下一局：南1局
        has_next = self.game_state.next_round()
        assert has_next is True
        assert self.game_state.round_wind == Wind.SOUTH
        assert self.game_state.round_number == 1

        # 繼續到南4局
        self.game_state.next_round()
        self.game_state.next_round()
        self.game_state.next_round()
        assert self.game_state.round_number == 4

        # 下一局：遊戲結束
        has_next = self.game_state.next_round()
        assert has_next is False

    def test_next_dealer(self):
        """測試下一局莊家"""
        # 初始莊家是0
        assert self.game_state.dealer == 0

        # 莊家未獲勝，莊家輪換
        self.game_state.next_dealer(dealer_won=False)
        assert self.game_state.dealer == 1
        assert self.game_state.honba == 0  # 本場重置

        # 莊家獲勝，莊家不變，本場增加
        self.game_state.next_dealer(dealer_won=True)
        assert self.game_state.dealer == 1  # 莊家不變
        assert self.game_state.honba == 1  # 本場增加

        # 繼續測試莊家輪換
        self.game_state.next_dealer(dealer_won=False)
        assert self.game_state.dealer == 2
        assert self.game_state.honba == 0

        # 測試莊家輪換到最後一個玩家後回到0
        self.game_state.set_dealer(3)
        self.game_state.next_dealer(dealer_won=False)
        assert self.game_state.dealer == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
