"""
規則引擎 - RuleEngine implementation

提供遊戲流程控制、動作執行和規則判定功能。
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from pyriichi.tiles import Tile, TileSet, Suit
from pyriichi.hand import Hand
from pyriichi.game_state import GameState
from pyriichi.yaku import YakuChecker, YakuResult
from pyriichi.scoring import ScoreCalculator, ScoreResult


class GameAction(Enum):
    """遊戲動作"""

    DRAW = "draw"  # 摸牌
    DISCARD = "discard"  # 打牌
    CHI = "chi"  # 吃
    PON = "pon"  # 碰
    KAN = "kan"  # 槓
    ANKAN = "ankan"  # 暗槓
    RICHI = "riichi"  # 立直
    WIN = "win"  # 和牌
    TSUMO = "tsumo"  # 自摸
    RON = "ron"  # 榮和
    PASS = "pass"  # 過


class GamePhase(Enum):
    """遊戲階段"""

    INIT = "init"  # 初始化
    DEALING = "dealing"  # 發牌
    PLAYING = "playing"  # 遊戲中
    WINNING = "winning"  # 和牌
    DRAW = "draw"  # 流局
    ENDED = "ended"  # 結束


@dataclass
class ActionResult:
    """動作執行結果"""

    drawn_tile: Optional[Tile] = None
    is_last_tile: Optional[bool] = None
    draw: Optional[bool] = None
    draw_reason: Optional[str] = None
    discarded: Optional[bool] = None
    riichi: Optional[bool] = None
    chankan: Optional[bool] = None
    winners: List[int] = field(default_factory=list)
    rinshan_tile: Optional[Tile] = None
    kan: Optional[bool] = None
    ankan: Optional[bool] = None
    rinshan_win: Optional["WinResult"] = None


@dataclass
class WinResult:
    """和牌結果"""

    win: bool
    player: int
    yaku: List[YakuResult]
    han: int
    fu: int
    points: int
    score_result: ScoreResult
    chankan: Optional[bool] = None
    rinshan: Optional[bool] = None


@dataclass
class DrawResult:
    """流局結果"""

    draw: bool
    draw_type: Optional[str] = None
    flow_mangan_players: List[int] = field(default_factory=list)
    kyuushu_kyuuhai: Optional[bool] = None
    kyuushu_kyuuhai_player: Optional[int] = None


class RuleEngine:
    """規則引擎"""

    def __init__(self, num_players: int = 4):
        """
        初始化規則引擎

        Args:
            num_players: 玩家數量（默認 4）
        """
        self._num_players = num_players
        self._tile_set: Optional[TileSet] = None
        self._hands: List[Hand] = []
        self._current_player = 0
        self._phase = GamePhase.INIT
        self._game_state = GameState(num_players=num_players)
        self._yaku_checker = YakuChecker()
        self._score_calculator = ScoreCalculator()
        self._last_discarded_tile: Optional[Tile] = None
        self._last_discarded_player: Optional[int] = None

        # 狀態追蹤
        self._riichi_turns: Dict[int, int] = {}  # {player_id: turns_after_riichi}
        self._is_first_round: bool = True  # 是否為第一巡
        self._discard_history: List[Tuple[int, Tile]] = []  # [(player, tile), ...] 捨牌歷史
        self._kan_count: int = 0  # 槓的總次數
        self._turn_count: int = 0  # 回合數
        self._is_first_turn_after_deal: bool = True  # 發牌後是否為第一回合
        self._pending_kan_tile: Optional[Tuple[int, Tile]] = None  # (player, tile) 待處理的槓牌，用於搶槓判定
        self._winning_players: List[int] = []  # 多人和牌時的玩家列表（用於三家和了）

    def start_game(self) -> None:
        """開始新遊戲"""
        self._game_state = GameState(num_players=self._num_players)
        self._phase = GamePhase.INIT

    def start_round(self) -> None:
        """開始新一局"""
        self._tile_set = TileSet()
        self._tile_set.shuffle()
        self._phase = GamePhase.DEALING
        self._current_player = self._game_state.dealer
        self._last_discarded_tile = None
        self._last_discarded_player = None

        # 重置狀態追蹤
        self._riichi_turns = {}
        self._is_first_round = True
        self._discard_history = []
        self._kan_count = 0
        self._turn_count = 0
        self._is_first_turn_after_deal = True
        self._pending_kan_tile = None
        self._winning_players = []

    def deal(self) -> Dict[int, List[Tile]]:
        """
        發牌

        Returns:
            每個玩家的手牌字典 {player_id: [tiles]}
        """
        if self._phase != GamePhase.DEALING:
            raise ValueError("只能在發牌階段發牌")

        if not self._tile_set:
            raise ValueError("牌組未初始化")
        hands_tiles = self._tile_set.deal(num_players=self._num_players)
        self._hands = [Hand(tiles) for tiles in hands_tiles]

        self._phase = GamePhase.PLAYING
        self._is_first_turn_after_deal = True

        return {i: hand.tiles for i, hand in enumerate(self._hands)}

    def get_current_player(self) -> int:
        """獲取當前行動玩家"""
        return self._current_player

    def get_phase(self) -> GamePhase:
        """獲取當前遊戲階段"""
        return self._phase

    def can_act(self, player: int, action: GameAction, tile: Optional[Tile] = None, **kwargs) -> bool:
        """
        檢查玩家是否可以執行某個動作

        Args:
            player: 玩家位置
            action: 動作類型
            tile: 相關的牌
            **kwargs: 其他參數

        Returns:
            是否可以執行
        """
        if self._phase != GamePhase.PLAYING:
            return False

        if action == GameAction.DRAW:
            return player == self._current_player

        if action == GameAction.DISCARD:
            return player == self._current_player and tile is not None

        if action == GameAction.RICHI:
            hand = self._hands[player]
            return hand.is_concealed and not hand.is_riichi and hand.is_tenpai()

        if action == GameAction.KAN:
            if tile is None:
                return False
            hand = self._hands[player]
            return len(hand.can_kan(tile)) > 0

        if action == GameAction.ANKAN:
            hand = self._hands[player]
            return len(hand.can_kan(None)) > 0

        return False

    def execute_action(self, player: int, action: GameAction, tile: Optional[Tile] = None, **kwargs) -> ActionResult:
        """
        執行動作

        Args:
            player: 玩家位置
            action: 動作類型
            tile: 相關的牌
            **kwargs: 其他參數

        Returns:
            動作執行結果
        """
        if not self.can_act(player, action, tile, **kwargs):
            raise ValueError(f"玩家 {player} 不能執行動作 {action}")

        result = ActionResult()

        if action == GameAction.DRAW:
            if not self._tile_set:
                raise ValueError("牌組未初始化")
            drawn_tile = self._tile_set.draw()
            if drawn_tile:
                self._hands[player].add_tile(drawn_tile)
                result.drawn_tile = drawn_tile
                # 檢查是否為最後一張牌（海底撈月）
                if self._tile_set.is_exhausted():
                    result.is_last_tile = True
            else:
                # 流局
                self._phase = GamePhase.DRAW
                result.draw = True

        elif action == GameAction.DISCARD:
            if tile is None:
                raise ValueError("打牌動作必須指定牌")
            if not self._tile_set:
                raise ValueError("牌組未初始化")
            if self._hands[player].discard(tile):
                self._last_discarded_tile = tile
                self._last_discarded_player = player
                # 記錄捨牌歷史（用於四風連打判定）
                self._discard_history.append((player, tile))
                # 只保留前四張捨牌
                if len(self._discard_history) > 4:
                    self._discard_history.pop(0)

                # 更新立直後回合數
                # 立直後，每當其他玩家行動時，立直玩家的回合數增加
                for p in list(self._riichi_turns.keys()):
                    if p != player:
                        self._riichi_turns[p] += 1
                # 如果立直玩家自己打牌，也增加回合數（但這表示已經過了一巡）
                if player in self._riichi_turns:
                    self._riichi_turns[player] += 1

                # 檢查是否為最後一張牌（河底撈魚）
                if self._tile_set.is_exhausted():
                    result.is_last_tile = True

                self._current_player = (player + 1) % self._num_players
                self._turn_count += 1
                self._is_first_turn_after_deal = False
                self._is_first_round = False
                result.discarded = True

        elif action == GameAction.RICHI:
            self._hands[player].set_riichi(True)
            self._game_state.add_riichi_stick()
            self._game_state.update_score(player, -1000)
            # 記錄立直回合數
            self._riichi_turns[player] = 0
            result.riichi = True

        elif action == GameAction.KAN:
            # 明槓：檢查是否有其他玩家可以搶槓
            if tile is None:
                raise ValueError("明槓必須指定被槓的牌")

            # 先檢查是否有其他玩家可以搶槓和
            self._pending_kan_tile = (player, tile)
            chankan_winners = self._check_chankan(player, tile)

            if chankan_winners:
                # 有玩家搶槓，不執行槓，轉為和牌處理
                result.chankan = True
                result.winners = chankan_winners
                self._pending_kan_tile = None
                return result

            # 執行明槓
            meld = self._hands[player].kan(tile)
            self._kan_count += 1

            # 從嶺上摸牌（嶺上開花）
            if self._tile_set:
                rinshan_tile = self._tile_set.draw_wall_tile()
                if rinshan_tile:
                    self._hands[player].add_tile(rinshan_tile)
                    result.rinshan_tile = rinshan_tile
                    result.kan = True
                    self._pending_kan_tile = None

                    # 檢查嶺上開花（槓後摸牌和牌）
                    rinshan_win = self.check_rinshan_win(player, rinshan_tile)
                    if rinshan_win:
                        result.rinshan_win = rinshan_win
                        self._phase = GamePhase.WINNING
                else:
                    # 王牌區耗盡，流局
                    self._phase = GamePhase.DRAW
                    result.draw = True
                    result.draw_reason = "wall_exhausted"

        elif action == GameAction.ANKAN:
            # 暗槓
            meld = self._hands[player].kan(None)
            self._kan_count += 1

            # 從嶺上摸牌（嶺上開花）
            if self._tile_set:
                rinshan_tile = self._tile_set.draw_wall_tile()
                if rinshan_tile:
                    self._hands[player].add_tile(rinshan_tile)
                    result.rinshan_tile = rinshan_tile
                    result.ankan = True

                    # 檢查嶺上開花（槓後摸牌和牌）
                    rinshan_win = self.check_rinshan_win(player, rinshan_tile)
                    if rinshan_win:
                        result.rinshan_win = rinshan_win
                        self._phase = GamePhase.WINNING
                else:
                    # 王牌區耗盡，流局
                    self._phase = GamePhase.DRAW
                    result.draw = True
                    result.draw_reason = "wall_exhausted"

        return result

    def check_win(
        self, player: int, winning_tile: Tile, is_chankan: bool = False, is_rinshan: bool = False
    ) -> Optional[WinResult]:
        """
        檢查是否可以和牌

        Args:
            player: 玩家位置
            winning_tile: 和牌牌
            is_chankan: 是否為搶槓和
            is_rinshan: 是否為嶺上開花

        Returns:
            和牌結果（包含役種、得分等），如果不能和則返回 None
        """
        hand = self._hands[player]

        if not hand.is_winning_hand(winning_tile):
            return None

        # 獲取和牌組合
        combinations = hand.get_winning_combinations(winning_tile)
        if not combinations:
            return None

        # 使用第一個組合進行役種判定
        winning_combination = list(combinations[0]) if combinations[0] else []

        # 檢查役種
        is_tsumo = player == self._current_player or is_rinshan
        # 獲取立直後的回合數
        turns_after_riichi = self._riichi_turns.get(player, -1)
        # 檢查是否為第一巡
        is_first_turn = self._is_first_turn_after_deal
        # 檢查是否為最後一張牌（需要檢查牌山狀態）
        is_last_tile = self._tile_set.is_exhausted() if self._tile_set else False
        yaku_results = self._yaku_checker.check_all(
            hand,
            winning_tile,
            winning_combination,
            self._game_state,
            is_tsumo,
            turns_after_riichi,
            is_first_turn,
            is_last_tile,
            player,
            is_rinshan,
        )

        if not yaku_results:
            return None  # 沒有役不能和牌

        # 計算寶牌數量
        dora_count = self._count_dora(player, winning_tile, winning_combination)

        score_result = self._score_calculator.calculate(
            hand, winning_tile, winning_combination, yaku_results, dora_count, self._game_state, is_tsumo, player
        )

        score_result.payment_to = player
        # 如果是榮和，設置支付者
        if not is_tsumo and self._last_discarded_player is not None:
            score_result.payment_from = self._last_discarded_player
        elif is_chankan and self._pending_kan_tile:
            # 搶槓和：支付者為槓牌玩家
            kan_player, _ = self._pending_kan_tile
            score_result.payment_from = kan_player

        result = WinResult(
            win=True,
            player=player,
            yaku=yaku_results,
            han=score_result.han,
            fu=score_result.fu,
            points=score_result.total_points,
            score_result=score_result,
            chankan=is_chankan if is_chankan else None,
            rinshan=is_rinshan if is_rinshan else None,
        )

        return result

    def check_draw(self) -> Optional[str]:
        """
        檢查是否流局

        Returns:
            流局類型（"exhausted", "kyuushu", "suufon_renda", "suucha_riichi", "suukantsu", "sancha_ron"），否則返回 None
        """
        # 檢查四風連打（優先檢查，因為可以在第一巡發生）
        if self.check_suufon_renda():
            return "suufon_renda"

        # 檢查三家和了（多人和牌流局）
        if self.check_sancha_ron():
            return "sancha_ron"

        # 檢查四槓散了（四個槓之後流局）
        if self._kan_count >= 4:
            return "suukantsu"

        # 牌山耗盡流局
        if self._tile_set and self._tile_set.is_exhausted():
            return "exhausted"

        # 檢查是否所有玩家都聽牌（全員聽牌流局）
        if self._check_all_tenpai():
            return "suucha_riichi"

        return None

    def _check_all_tenpai(self) -> bool:
        """檢查是否所有玩家都聽牌"""
        if self._phase != GamePhase.PLAYING:
            return False

        # 檢查所有玩家是否聽牌
        for i, hand in enumerate(self._hands):
            if not hand.is_tenpai():
                return False

        return True

    def check_kyuushu_kyuuhai(self, player: int) -> bool:
        """
        檢查是否九種九牌（九種幺九牌）

        條件：第一巡且手牌有9種或以上不同種類的幺九牌

        Args:
            player: 玩家位置

        Returns:
            是否為九種九牌
        """
        # 必須是第一巡
        if not self._is_first_turn_after_deal:
            return False

        hand = self._hands[player]
        if len(hand.tiles) != 13:
            return False

        # 統計幺九牌種類
        terminal_and_honor_tiles = set()
        for tile in hand.tiles:
            if tile.is_terminal or tile.is_honor:
                terminal_and_honor_tiles.add((tile.suit, tile.rank))

        # 如果有9種或以上不同種類的幺九牌，則為九種九牌
        return len(terminal_and_honor_tiles) >= 9

    def check_suufon_renda(self) -> bool:
        """
        檢查是否四風連打（前四捨牌都是同一風牌）

        Returns:
            是否為四風連打
        """
        # 必須有至少4張捨牌歷史
        if len(self._discard_history) < 4:
            return False

        # 檢查前四張捨牌是否都是同一風牌
        first_tile = self._discard_history[0][1]

        # 必須是風牌（字牌 rank 1-4）
        if first_tile.suit != Suit.JIHAI or not (1 <= first_tile.rank <= 4):
            return False

        # 檢查前四張是否都是同一風牌
        for _, tile in self._discard_history[:4]:
            if tile.suit != Suit.JIHAI or tile.rank != first_tile.rank:
                return False

        return True

    def check_flow_mangan(self, player: int) -> bool:
        """
        檢查流局滿貫

        流局滿貫條件：
        1. 流局時聽牌
        2. 聽牌牌必須是幺九牌或字牌
        3. 沒有副露（門清）

        Args:
            player: 玩家位置

        Returns:
            是否為流局滿貫
        """
        hand = self._hands[player]

        # 必須是門清
        if not hand.is_concealed:
            return False

        # 必須聽牌
        if not hand.is_tenpai():
            return False

        # 檢查聽牌牌是否都是幺九牌或字牌
        waiting_tiles = hand.get_waiting_tiles()
        if not waiting_tiles:
            return False

        for tile in waiting_tiles:
            if not (tile.is_terminal or tile.is_honor):
                return False

        return True

    def _count_dora(self, player: int, winning_tile: Tile, winning_combination: List) -> int:
        """
        計算寶牌數量

        Args:
            player: 玩家位置
            winning_tile: 和牌牌
            winning_combination: 和牌組合

        Returns:
            寶牌翻數（表寶牌 + 裡寶牌 + 紅寶牌）
        """
        if not self._tile_set:
            return 0

        dora_count = 0
        hand = self._hands[player]

        # 收集所有牌（手牌 + 和牌牌）
        all_tiles = hand.tiles + [winning_tile]

        # 表寶牌
        dora_indicator = self._tile_set.get_dora_indicator(0)
        if dora_indicator:
            dora_tile = self._tile_set.get_dora(dora_indicator)
            for tile in all_tiles:
                if tile.suit == dora_tile.suit and tile.rank == dora_tile.rank:
                    dora_count += 1

        # 裡寶牌（立直時）
        if hand.is_riichi:
            ura_indicator = self._tile_set.get_dora_indicator(1)
            if ura_indicator:
                ura_dora_tile = self._tile_set.get_dora(ura_indicator)
                for tile in all_tiles:
                    if tile.suit == ura_dora_tile.suit and tile.rank == ura_dora_tile.rank:
                        dora_count += 1

        # 紅寶牌
        for tile in all_tiles:
            if tile.is_red:
                dora_count += 1

        return dora_count

    def get_hand(self, player: int) -> Hand:
        """獲取玩家的手牌"""
        if not (0 <= player < self._num_players):
            raise ValueError(f"玩家位置必須在 0-{self._num_players-1} 之間")
        return self._hands[player]

    def get_game_state(self) -> GameState:
        """獲取遊戲狀態"""
        return self._game_state

    def get_discards(self, player: int) -> List[Tile]:
        """獲取玩家的舍牌"""
        if not (0 <= player < self._num_players):
            raise ValueError(f"玩家位置必須在 0-{self._num_players-1} 之間")
        return self._hands[player].discards

    def handle_draw(self) -> DrawResult:
        """
        處理流局

        Returns:
            流局結果，包含流局類型、流局滿貫玩家等
        """
        draw_type = self.check_draw()
        if not draw_type:
            return DrawResult(draw=False)

        result = DrawResult(
            draw=True,
            draw_type=draw_type,
            flow_mangan_players=[],
        )

        # 檢查流局滿貫
        if draw_type == "exhausted":
            for i in range(self._num_players):
                if self.check_flow_mangan(i):
                    result.flow_mangan_players.append(i)
                    # 流局滿貫：3000 點
                    self._game_state.update_score(i, 3000)
                    for j in range(self._num_players):
                        if j != i:
                            self._game_state.update_score(j, -1000)

        # 處理九種九牌（第一巡）
        # 檢查九種九牌在第一巡時可以流局
        if self._is_first_turn_after_deal:
            for i in range(self._num_players):
                if self.check_kyuushu_kyuuhai(i):
                    result.kyuushu_kyuuhai = True
                    result.kyuushu_kyuuhai_player = i
                    # 九種九牌流局時，莊家連莊
                    break

        # 處理全員聽牌流局
        if draw_type == "suucha_riichi":
            # 全員聽牌流局時，莊家支付 300 點給每個閒家
            dealer = self._game_state.dealer
            for i in range(self._num_players):
                if i != dealer:
                    self._game_state.transfer_points(dealer, i, 300)

        self._phase = GamePhase.DRAW
        return result

    def end_round(self, winner: Optional[int] = None) -> None:
        """
        結束一局

        Args:
            winner: 獲勝玩家（如果為 None，則為流局）
        """
        if winner is not None:
            # 和牌處理
            dealer = self._game_state.dealer
            dealer_won = winner == dealer

            # 更新莊家
            self._game_state.next_dealer(dealer_won)

            # 如果莊家未獲勝，進入下一局
            if not dealer_won:
                has_next = self._game_state.next_round()
                if not has_next:
                    self._phase = GamePhase.ENDED
        else:
            # 流局處理
            dealer = self._game_state.dealer
            dealer_won = False  # 流局時莊家不連莊（除非九種九牌）
            self._game_state.next_dealer(dealer_won)

            has_next = self._game_state.next_round()
            if not has_next:
                self._phase = GamePhase.ENDED

    def get_dora_tiles(self) -> List[Tile]:
        """
        獲取所有表寶牌

        Returns:
            表寶牌列表
        """
        if not self._tile_set:
            return []

        dora_tiles = []
        dora_indicator = self._tile_set.get_dora_indicator(0)
        if dora_indicator:
            dora_tiles.append(self._tile_set.get_dora(dora_indicator))

        return dora_tiles

    def get_ura_dora_tiles(self) -> List[Tile]:
        """
        獲取所有裡寶牌（僅在立直時顯示）

        Returns:
            裡寶牌列表
        """
        if not self._tile_set:
            return []

        ura_dora_tiles = []
        ura_indicator = self._tile_set.get_dora_indicator(1)
        if ura_indicator:
            ura_dora_tiles.append(self._tile_set.get_dora(ura_indicator))

        return ura_dora_tiles

    def _check_chankan(self, kan_player: int, kan_tile: Tile) -> List[int]:
        """
        檢查搶槓（其他玩家是否可以榮和槓牌）

        Args:
            kan_player: 執行槓的玩家
            kan_tile: 被槓的牌

        Returns:
            可以搶槓和牌的玩家列表
        """
        winners = []
        for player in range(self._num_players):
            if player == kan_player:
                continue  # 不能搶自己的槓

            # 檢查是否可以和這張牌
            win_result = self.check_win(player, kan_tile, is_chankan=True)
            if win_result:
                winners.append(player)

        return winners

    def check_sancha_ron(self) -> bool:
        """
        檢查是否三家和了（多人和牌流局）

        當多個玩家同時可以榮和同一張牌時，如果有三個或以上玩家和牌，則為三家和了（流局）

        Returns:
            是否為三家和了
        """
        if self._last_discarded_tile is None or self._last_discarded_player is None:
            return False

        # 檢查有多少玩家可以榮和這張牌
        winning_players = []
        for player in range(self._num_players):
            if player == self._last_discarded_player:
                continue  # 不能榮和自己的牌

            if self.check_win(player, self._last_discarded_tile):
                winning_players.append(player)

        # 如果三個或以上玩家和牌，則為三家和了
        return len(winning_players) >= 3

    def check_rinshan_win(self, player: int, rinshan_tile: Tile) -> Optional[WinResult]:
        """
        檢查嶺上開花（槓後摸牌和牌）

        Args:
            player: 玩家位置
            rinshan_tile: 從嶺上摸到的牌

        Returns:
            和牌結果，如果不能和則返回 None
        """
        return self.check_win(player, rinshan_tile, is_rinshan=True)
