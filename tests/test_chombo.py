from typing import List
import pytest
from pyriichi.game_state import GameState, Wind
from pyriichi.rules import RuleEngine, GameAction, GamePhase
from pyriichi.rules_config import RulesetConfig
from pyriichi.tiles import Tile, Suit, TileSet
from pyriichi.hand import Hand

def parse_tiles(tiles_str: str) -> List[Tile]:
    """
    解析牌字符串 (簡化版，僅用於測試)
    格式: "1m2m3m 4p5p6p 7s8s9s 1z1z1z 2z"
    """
    tiles = []
    i = 0
    while i < len(tiles_str):
        char = tiles_str[i]
        if char.isdigit():
            num = int(char)
            i += 1
            if i < len(tiles_str):
                suit_char = tiles_str[i]
                suit = None
                if suit_char == 'm': suit = Suit.MANZU
                elif suit_char == 'p': suit = Suit.PINZU
                elif suit_char == 's': suit = Suit.SOZU
                elif suit_char == 'z': suit = Suit.JIHAI

                if suit:
                    tiles.append(Tile(suit, num))
        i += 1
    return tiles

class TestChombo:
    def setup_method(self):
        self.engine = RuleEngine()
        self.engine.start_game()
        # Initialize hands list
        self.engine._hands = [Hand([]) for _ in range(4)]
        # Initialize tile set
        self.engine._tile_set = TileSet()
        self.engine._tile_set.tiles = []

        # Reset scores to default
        self.engine._game_state._scores = [25000] * 4
        self.engine._game_state.ruleset.chombo_penalty_enabled = True

    def test_chombo_false_ron(self):
        """測試錯和：無役宣告榮和"""
        # 設置玩家1的手牌（未聽牌或無役）
        # 123m 456p 789s 11z 2z (單騎2z，無役)
        hand_tiles = parse_tiles("1m2m3m4p5p6p7s8s9s1z1z2z")
        self.engine._hands[1] = Hand(hand_tiles)

        # 玩家0打出2z
        discard_tile = Tile(Suit.JIHAI, 2)
        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0
        self.engine._current_player = 0

        initial_scores = self.engine._game_state.scores.copy()

        # Mock get_available_actions to allow RON
        original_get_actions = self.engine.get_available_actions
        self.engine.get_available_actions = lambda p: [GameAction.RON]

        try:
            # 玩家1宣告榮和
            result = self.engine.execute_action(1, GameAction.RON)

            # 驗證錯和處理
            # 1. 動作失敗（返回 success=False）
            assert result.success is False

            # 2. 分數變化（閒家錯和：支付8000）
            # 莊家(0) +4000, 其他(2,3) +2000
            current_scores = self.engine._game_state.scores
            assert current_scores[1] == initial_scores[1] - 8000
            assert current_scores[0] == initial_scores[0] + 4000
            assert current_scores[2] == initial_scores[2] + 2000
            assert current_scores[3] == initial_scores[3] + 2000

            # 3. 遊戲階段
            # 由於 _handle_chombo 會重置或結束，這裡檢查是否進入下一局或結束
            # 如果是東1局，錯和後應該是東1局1本場（閒家錯和連莊）
            assert self.engine._game_state.round_wind == Wind.EAST
            assert self.engine._game_state.round_number == 1
            # 根據 _handle_chombo 實現：self._game_state.next_dealer(dealer_won)
            # 閒家錯和 -> dealer_won = True -> 連莊 + 本場+1
            assert self.engine._game_state.honba == 1
        finally:
            self.engine.get_available_actions = original_get_actions

    def test_chombo_false_riichi(self):
        """測試錯立直：流局時未聽牌"""
        # 設置玩家1立直但未聽牌
        hand_tiles = parse_tiles("1m2m3m4p5p6p7s8s9s1z1z2z3z") # 13張，未聽牌
        self.engine._hands[1] = Hand(hand_tiles)
        self.engine._hands[1].set_riichi(True) # Use setter method

        # 模擬流局
        self.engine._tile_set._tiles = [] # 清空牌山

        initial_scores = self.engine._game_state.scores.copy()

        # 結束回合
        self.engine.end_round()

        # 驗證錯和處理
        # 閒家錯和：支付8000
        current_scores = self.engine._game_state.scores
        assert current_scores[1] == initial_scores[1] - 8000

        # 驗證沒有計算流局滿貫或不聽罰符（分數變動僅來自錯和）
        # 如果計算了不聽罰符，分數會更低或不同
        # 錯和後直接結束該局，不進行其他結算

    def test_chombo_dealer(self):
        """測試莊家錯和"""
        # 莊家(0)錯和
        hand_tiles = parse_tiles("1m2m3m4p5p6p7s8s9s1z1z2z")
        self.engine._hands[0] = Hand(hand_tiles)

        discard_tile = Tile(Suit.JIHAI, 2)
        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 1

        initial_scores = self.engine._game_state.scores.copy()

        # Mock get_available_actions to allow RON
        original_get_actions = self.engine.get_available_actions
        self.engine.get_available_actions = lambda p: [GameAction.RON]

        try:
            result = self.engine.execute_action(0, GameAction.RON)

            # 莊家錯和：支付每人4000（共12000）
            current_scores = self.engine._game_state.scores
            assert current_scores[0] == initial_scores[0] - 12000
            assert current_scores[1] == initial_scores[1] + 4000

            # 莊家錯和 -> 下莊
            assert self.engine._game_state.dealer == 1
            assert self.engine._game_state.round_number == 2 # 東2局
        finally:
            self.engine.get_available_actions = original_get_actions
