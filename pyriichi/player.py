from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
import random

from pyriichi.rules import GameAction, GameState
from pyriichi.tiles import Tile
from pyriichi.hand import Hand

class BasePlayer(ABC):
    """玩家基類 (Abstract Base Class for Players)"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def decide_action(
        self,
        game_state: GameState,
        player_index: int,
        hand: Hand,
        available_actions: List[GameAction]
    ) -> Tuple[GameAction, Optional[Tile]]:
        """
        決定下一步動作

        Args:
            game_state: 當前遊戲狀態
            player_index: 玩家索引 (0-3)
            hand: 玩家手牌
            available_actions: 可執行的動作列表

        Returns:
            (選擇的動作, 相關的牌)
            - 如果動作是 DISCARD，Tile 是要打出的牌
            - 如果動作是 CHI/PON/KAN，Tile 是相關的牌（通常是 target tile）
            - 其他動作 Tile 通常為 None
        """
        pass

class RandomPlayer(BasePlayer):
    """隨機行動的 AI 玩家"""

    def decide_action(
        self,
        game_state: GameState,
        player_index: int,
        hand: Hand,
        available_actions: List[GameAction]
    ) -> Tuple[GameAction, Optional[Tile]]:
        """
        決定下一步動作（隨機）

        Args:
            game_state: 當前遊戲狀態
            player_index: 玩家索引
            hand: 玩家手牌
            available_actions: 可執行的動作列表

        Returns:
            (選擇的動作, 相關的牌)
        """

        if not available_actions:
            # 理論上不應該發生，除非遊戲結束
            return GameAction.PASS, None

        # 簡單策略：優先和牌，其次立直，否則隨機
        # 但既然是 RandomPlayer，我們就真的隨機嗎？
        # 為了讓遊戲能進行下去，至少要能正確打牌

        # 如果可以和牌，優先和牌 (為了測試方便)
        if GameAction.RON in available_actions:
            return GameAction.RON, None
        if GameAction.TSUMO in available_actions:
            return GameAction.TSUMO, None

        # 隨機選擇一個動作
        # 過濾掉 PASS，除非只有 PASS (例如鳴牌詢問時)
        # 但在此簡化模型中，如果輪到自己切牌，通常沒有 PASS
        # 如果是回應他家打牌，可能有 PASS

        # 這裡做一個簡單的權重：
        # 如果是切牌階段 (DRAW 後)，必須 DISCARD 或 KAN/RICHI/TSUMO
        # 如果是回應階段，可以 PASS

        # 為了避免死循環或卡住，我們優先選擇 DISCARD 如果在列表中
        if GameAction.DISCARD in available_actions:
            # 隨機打出一張牌
            # 這裡需要從手牌中選擇一張
            # hand.tiles 包含所有手牌
            # 我們需要處理立直後的強制切牌嗎？規則引擎會限制 available_actions 嗎？
            # 規則引擎目前只返回 DISCARD 動作，不限制打哪張（除非立直）
            # 但 RandomPlayer 應該遵守規則

            # 檢查是否立直
            if hand.is_riichi:
                # 立直後只能打出剛摸到的牌 (如果有的話)
                # 但 hand 對象可能已經包含了摸到的牌
                # 規則引擎應該處理這個邏輯嗎？
                # 通常立直後，如果不能和牌/暗槓，就必須打出摸到的牌
                # 這裡簡單隨機打一張，如果違規，規則引擎會報錯嗎？
                # 為了安全，我們打出最後一張（假設是摸到的）
                tile_to_discard = hand.tiles[-1]
                return GameAction.DISCARD, tile_to_discard

            # 非立直，隨機打一張
            tile_to_discard = random.choice(hand.tiles)
            return GameAction.DISCARD, tile_to_discard

        # 如果是回應階段 (有 PON, CHI, KAN, RON, PASS)
        # 隨機選擇，但 PASS 權重高一點，避免亂鳴牌
        action = random.choice(available_actions)

        # 如果選了需要參數的動作，需要提供 Tile
        # 目前簡化：CHI/PON/KAN 的 Tile 參數通常由規則引擎上下文決定，
        # 但這裡接口要求返回 Tile。
        # 對於 DISCARD，Tile 是打出的牌。
        # 對於 CHI/PON/KAN，Tile 是什麼？
        # 通常是 "用哪組牌去吃/碰"。
        # 這裡暫時返回 None，假設規則引擎能處理或不需要（對於簡單 AI）
        # 實際上 execute_action 對於 CHI/PON 需要 tile 參數嗎？
        # execute_action(player, action, tile)
        # 對於 DISCARD，tile 是打出的牌。
        # 對於 CHI，tile 是被吃的牌？不，被吃的牌是 last_discarded。
        # tile 參數在 CHI 中通常是用來指定 "用哪兩張牌吃" (如果有多種吃法)
        # 這裡 RandomPlayer 可能無法處理複雜吃法，暫時返回 None

        return action, None

class SimplePlayer(BasePlayer):
    """簡單進攻 AI (Simple Attack AI)"""

    def decide_action(
        self,
        game_state: GameState,
        player_index: int,
        hand: Hand,
        available_actions: List[GameAction]
    ) -> Tuple[GameAction, Optional[Tile]]:
        """
        決定下一步動作（簡單進攻策略）

        Args:
            game_state: 當前遊戲狀態
            player_index: 玩家索引
            hand: 玩家手牌
            available_actions: 可執行的動作列表

        Returns:
            (選擇的動作, 相關的牌)
        """

        if not available_actions:
            return GameAction.PASS, None

        # 1. 優先和牌
        if GameAction.RON in available_actions:
            return GameAction.RON, None
        if GameAction.TSUMO in available_actions:
            return GameAction.TSUMO, None

        # 2. 優先立直
        if GameAction.RICHI in available_actions:
            return GameAction.RICHI, None

        # 3. 處理切牌
        if GameAction.DISCARD in available_actions:
            # 如果立直中，只能打出剛摸到的牌（通常是最後一張）
            if hand.is_riichi:
                return GameAction.DISCARD, hand.tiles[-1]

            # 簡單切牌策略：
            # 字牌 -> 老頭牌 -> 中張牌
            # 孤張優先（這裡簡化為只看牌本身，不看是否成面子）

            # 為了避免打出已成面子的牌，我們應該先分析手牌
            # 但這裡做一個非常簡單的啟發式：
            # 給每張牌打分，分數越低越容易被打出

            best_discard = None
            min_score = 1000

            for tile in hand.tiles:
                score = 0

                # 字牌分數低
                if tile.is_honor:
                    score = 10
                # 老頭牌分數中
                elif tile.is_terminal:
                    score = 20
                # 中張牌分數高
                else:
                    score = 30 + (5 - abs(tile.rank - 5)) # 5是最高分(35)，1/9是26(但已被terminal捕獲)

                # 這裡還可以加入：是否為寶牌（加分）、是否為紅寶牌（加分）
                # 簡單起見暫不加

                # 為了增加隨機性，避免每次都打同一張
                score += random.randint(0, 5)

                if score < min_score:
                    min_score = score
                    best_discard = tile

            return GameAction.DISCARD, best_discard

        # 4. 處理鳴牌
        # 簡單 AI 傾向於門清（不鳴牌），除非能和牌
        # 所以遇到 PON/CHI/KAN (Daiminkan) 選擇 PASS
        if GameAction.PASS in available_actions:
            return GameAction.PASS, None

        # 如果只有鳴牌選項且不能 PASS (例如暗槓/加槓?)
        # 暗槓/加槓通常伴隨 DISCARD 選項，所以會在上面被處理嗎？
        # 不，get_available_actions 會返回 [DISCARD, ANKAN, KAN]
        # 如果我們選擇了 DISCARD，就不會執行這裡。
        # 但如果我們想槓呢？
        # 簡單 AI 暫時不槓

        # 如果被迫選擇（例如沒有 PASS，只有 ANKAN? 不可能，總有 DISCARD）
        # 除非是回應階段且必須回應？回應階段總有 PASS。

        # 隨機選擇剩餘的
        return random.choice(available_actions), None
