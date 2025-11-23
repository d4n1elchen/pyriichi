
import pytest
from pyriichi.game_state import GameState, Wind
from pyriichi.rules import RuleEngine, GamePhase
from pyriichi.rules_config import RulesetConfig

class TestGameEndConditions:
    def setup_method(self):
        self.engine = RuleEngine()
        self.engine.start_game()
        # Reset scores to default
        self.engine._game_state._scores = [25000] * 4

    def test_west_round_extension(self):
        """測試西入：南4局結束時無人達到30000點，進入西場"""
        # 設置為南4局
        self.engine._game_state.set_round(Wind.SOUTH, 4)
        self.engine._game_state.set_dealer(3) # 玩家3是莊家

        # 設置分數都小於30000
        self.engine._game_state._scores = [25000, 25000, 25000, 25000]

        # 確保啟用西入
        self.engine._game_state.ruleset.west_round_extension = True
        self.engine._game_state.ruleset.return_score = 30000

        # 模擬閒家獲勝（莊家輸掉），觸發 next_round
        # 這裡直接調用 next_round 測試 GameState 邏輯
        has_next = self.engine._game_state.next_round()

        assert has_next is True
        assert self.engine._game_state.round_wind == Wind.WEST
        assert self.engine._game_state.round_number == 1

    def test_west_round_sudden_death(self):
        """測試西入突然死亡：西場中有人達到30000點，遊戲結束"""
        # 設置為西1局
        self.engine._game_state.set_round(Wind.WEST, 1)

        # 設置有人超過30000
        self.engine._game_state._scores = [31000, 20000, 20000, 29000]

        self.engine._game_state.ruleset.return_score = 30000

        # 調用 next_round
        has_next = self.engine._game_state.next_round()

        assert has_next is False

    def test_no_west_round_if_score_reached(self):
        """測試不西入：南4局結束時有人達到30000點，遊戲結束"""
        self.engine._game_state.set_round(Wind.SOUTH, 4)
        self.engine._game_state._scores = [31000, 20000, 20000, 29000]

        has_next = self.engine._game_state.next_round()

        assert has_next is False

    def test_agari_yame(self):
        """測試安可：南4局莊家和牌且為第一名，遊戲結束"""
        self.engine._game_state.set_round(Wind.SOUTH, 4)
        self.engine._game_state.set_dealer(0) # 假設玩家0是莊家

        # 設置玩家0為第一名且超過30000（通常安可不要求超過30000，只要是Top即可？需確認規則）
        # 標準規則：只要是Top即可結束。
        self.engine._game_state._scores = [35000, 20000, 20000, 25000]

        self.engine._game_state.ruleset.agari_yame = True

        # 模擬莊家和牌
        winners = [0]
        self.engine.end_round(winners)

        assert self.engine._phase == GamePhase.ENDED

    def test_agari_yame_continuation(self):
        """測試安可續行：南4局莊家和牌但不是第一名，遊戲繼續（連莊）"""
        self.engine._game_state.set_round(Wind.SOUTH, 4)
        self.engine._game_state.set_dealer(0)

        # 設置玩家0不是第一名
        self.engine._game_state._scores = [30000, 35000, 20000, 15000]

        self.engine._game_state.ruleset.agari_yame = True

        # 模擬莊家和牌
        winners = [0]
        self.engine.end_round(winners)

        assert self.engine._phase != GamePhase.ENDED
        # 應該連莊
        assert self.engine._game_state.round_wind == Wind.SOUTH
        assert self.engine._game_state.round_number == 4
        assert self.engine._game_state.honba == 1
