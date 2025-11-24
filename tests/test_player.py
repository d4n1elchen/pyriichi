import pytest
from unittest.mock import MagicMock
from pyriichi.player import RandomPlayer
from pyriichi.rules import GameAction, GameState
from pyriichi.hand import Hand
from pyriichi.tiles import Tile, Suit

class TestRandomPlayer:
    def setup_method(self):
        self.player = RandomPlayer("TestBot")
        self.game_state = MagicMock(spec=GameState)
        self.hand = MagicMock(spec=Hand)
        self.hand.tiles = [Tile(Suit.MANZU, 1), Tile(Suit.MANZU, 2)]
        self.hand.is_riichi = False

    def test_decide_action_discard(self):
        """測試切牌階段"""
        available_actions = [GameAction.DISCARD]
        action, tile = self.player.decide_action(self.game_state, 0, self.hand, available_actions)

        assert action == GameAction.DISCARD
        assert tile in self.hand.tiles

    def test_decide_action_ron(self):
        """測試優先榮和"""
        available_actions = [GameAction.RON, GameAction.PASS]
        action, tile = self.player.decide_action(self.game_state, 0, self.hand, available_actions)

        assert action == GameAction.RON
        assert tile is None

    def test_decide_action_riichi_discard(self):
        """測試立直後切牌"""
        self.hand.is_riichi = True
        available_actions = [GameAction.DISCARD]
        action, tile = self.player.decide_action(self.game_state, 0, self.hand, available_actions)

        assert action == GameAction.DISCARD
        assert tile == self.hand.tiles[-1] # 應該打出最後一張

    def test_decide_action_response(self):
        """測試回應階段（隨機選擇）"""
        available_actions = [GameAction.PON, GameAction.PASS]
        # 由於是隨機，我們運行多次確保不會崩潰
        for _ in range(10):
            action, tile = self.player.decide_action(self.game_state, 0, self.hand, available_actions)
            assert action in available_actions
