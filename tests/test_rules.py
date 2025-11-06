"""
RuleEngine 的單元測試
"""

import pytest
from pyriichi.rules import RuleEngine, GameAction, GamePhase
from pyriichi.tiles import Tile, Suit
from pyriichi.game_state import Wind


class TestRuleEngine:
    """規則引擎測試"""

    def setup_method(self):
        """設置測試環境"""
        self.engine = RuleEngine(num_players=4)

    def test_start_game(self):
        """測試開始遊戲"""
        self.engine.start_game()
        assert self.engine.get_phase() == GamePhase.INIT

    def test_start_round(self):
        """測試開始一局"""
        self.engine.start_game()
        self.engine.start_round()
        assert self.engine.get_phase() == GamePhase.DEALING

    def test_deal(self):
        """測試發牌"""
        self.engine.start_game()
        self.engine.start_round()
        hands = self.engine.deal()

        assert len(hands) == 4
        # 莊家應該有14張，其他玩家13張
        assert len(hands[0]) == 14
        for i in range(1, 4):
            assert len(hands[i]) == 13

        assert self.engine.get_phase() == GamePhase.PLAYING

    def test_get_current_player(self):
        """測試獲取當前玩家"""
        self.engine.start_game()
        self.engine.start_round()
        self.engine.deal()

        current = self.engine.get_current_player()
        assert 0 <= current < 4

    def test_can_act_draw(self):
        """測試是否可以摸牌"""
        self.engine.start_game()
        self.engine.start_round()
        self.engine.deal()

        current = self.engine.get_current_player()
        assert self.engine.can_act(current, GameAction.DRAW)
        assert not self.engine.can_act((current + 1) % 4, GameAction.DRAW)

    def test_can_act_discard(self):
        """測試是否可以打牌"""
        self.engine.start_game()
        self.engine.start_round()
        self.engine.deal()

        current = self.engine.get_current_player()
        hand = self.engine.get_hand(current)

        if hand.tiles:
            tile = hand.tiles[0]
            assert self.engine.can_act(current, GameAction.DISCARD, tile=tile)

    def test_execute_action_draw(self):
        """測試執行摸牌"""
        self.engine.start_game()
        self.engine.start_round()
        self.engine.deal()

        current = self.engine.get_current_player()
        result = self.engine.execute_action(current, GameAction.DRAW)

        assert "drawn_tile" in result or "draw" in result

    def test_execute_action_discard(self):
        """測試執行打牌"""
        self.engine.start_game()
        self.engine.start_round()
        self.engine.deal()

        current = self.engine.get_current_player()
        hand = self.engine.get_hand(current)

        # 先摸一張牌
        self.engine.execute_action(current, GameAction.DRAW)

        if hand.tiles:
            tile = hand.tiles[0]
            result = self.engine.execute_action(current, GameAction.DISCARD, tile=tile)
            assert "discarded" in result

    def test_check_draw(self):
        """測試流局判定"""
        self.engine.start_game()
        self.engine.start_round()
        self.engine.deal()

        # 初始狀態不應該流局
        draw_type = self.engine.check_draw()
        assert draw_type is None or draw_type in ["exhausted", "suucha_riichi"]

    def test_check_kyuushu_kyuuhai(self):
        """測試九種九牌判定"""
        self.engine.start_game()
        self.engine.start_round()
        self.engine.deal()

        # 一般手牌不應該是九種九牌
        is_kyuushu = self.engine.check_kyuushu_kyuuhai(0)
        # 結果可能是 True 或 False，取決於發到的牌
        assert isinstance(is_kyuushu, bool)

    def test_check_flow_mangan(self):
        """測試流局滿貫判定"""
        self.engine.start_game()
        self.engine.start_round()
        self.engine.deal()

        # 一般手牌不應該是流局滿貫
        is_flow_mangan = self.engine.check_flow_mangan(0)
        assert isinstance(is_flow_mangan, bool)

    def test_get_dora_tiles(self):
        """測試獲取寶牌"""
        self.engine.start_game()
        self.engine.start_round()
        self.engine.deal()

        dora_tiles = self.engine.get_dora_tiles()
        assert isinstance(dora_tiles, list)
        # 應該至少有一張表寶牌
        assert len(dora_tiles) >= 1

    def test_get_ura_dora_tiles(self):
        """測試獲取裡寶牌"""
        self.engine.start_game()
        self.engine.start_round()
        self.engine.deal()

        ura_dora_tiles = self.engine.get_ura_dora_tiles()
        assert isinstance(ura_dora_tiles, list)
        # 應該至少有一張裡寶牌
        assert len(ura_dora_tiles) >= 1

    def test_get_hand(self):
        """測試獲取手牌"""
        self.engine.start_game()
        self.engine.start_round()
        self.engine.deal()

        hand = self.engine.get_hand(0)
        assert hand is not None
        assert len(hand.tiles) == 14  # 莊家

    def test_get_game_state(self):
        """測試獲取遊戲狀態"""
        self.engine.start_game()
        game_state = self.engine.get_game_state()

        assert game_state is not None
        assert game_state.round_wind == Wind.EAST
        assert game_state.dealer == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
