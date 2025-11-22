"""
規則引擎 - RuleEngine implementation

提供遊戲流程控制、動作執行和規則判定功能。
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from pyriichi.tiles import Tile, TileSet, Suit
from pyriichi.hand import Hand, Meld, MeldType
from pyriichi.game_state import GameState
from pyriichi.yaku import YakuChecker, YakuResult, Yaku
from pyriichi.scoring import ScoreCalculator, ScoreResult
from pyriichi.enum_utils import TranslatableEnum


class GameAction(TranslatableEnum):
    """遊戲動作"""

    DRAW = ("draw", "摸牌", "ツモ", "Draw")
    DISCARD = ("discard", "打牌", "捨て牌", "Discard")
    CHI = ("chi", "吃牌", "チー", "Chi")
    PON = ("pon", "碰牌", "ポン", "Pon")
    KAN = ("kan", "明槓", "カン", "Kan")
    ANKAN = ("ankan", "暗槓", "暗槓", "Ankan")
    RICHI = ("riichi", "立直", "リーチ", "Riichi")
    TSUMO = ("tsumo", "自摸", "ツモ", "Tsumo")
    RON = ("ron", "榮和", "ロン", "Ron")


class GamePhase(TranslatableEnum):
    """遊戲階段"""

    INIT = ("init", "初始化", "初期化", "Init")
    DEALING = ("dealing", "發牌", "配牌", "Dealing")
    PLAYING = ("playing", "對局中", "対局中", "Playing")
    WINNING = ("winning", "和牌處理", "和了処理", "Winning")
    RYUUKYOKU = ("ryuukyoku", "流局", "流局", "Ryuukyoku")
    ENDED = ("ended", "結束", "終了", "Ended")


class RyuukyokuType(TranslatableEnum):
    """流局類型"""

    SUUFON_RENDA = ("suufon_renda", "四風連打", "四風連打", "Suufon Renda")
    SANCHA_RON = ("sancha_ron", "三家和了", "三家和了", "Sancha Ron")
    SUUKANTSU = ("suukantsu", "四槓散了", "四槓散了", "Suukantsu")
    EXHAUSTED = ("exhausted", "牌山耗盡", "牌山が尽きる", "Exhausted Wall")
    SUUCHA_RIICHI = ("suucha_riichi", "四家立直", "四家立直", "Suucha Riichi")
    KYUUSHU_KYUUHAI = ("kyuushu_kyuuhai", "九種九牌", "九種九牌", "Kyuushu Kyuuhai")


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
class RyuukyokuResult:
    """流局結果"""

    ryuukyoku: bool
    ryuukyoku_type: Optional[RyuukyokuType] = None
    flow_mangan_players: List[int] = field(default_factory=list)
    kyuushu_kyuuhai_player: Optional[int] = None


@dataclass
class ActionResult:
    """動作執行結果"""

    drawn_tile: Optional[Tile] = None
    is_last_tile: Optional[bool] = None
    ryuukyoku: Optional[RyuukyokuResult] = None
    discarded: Optional[bool] = None
    riichi: Optional[bool] = None
    chankan: Optional[bool] = None
    winners: List[int] = field(default_factory=list)
    rinshan_tile: Optional[Tile] = None
    kan: Optional[bool] = None
    ankan: Optional[bool] = None
    rinshan_win: Optional[WinResult] = None
    meld: Optional[Meld] = None
    called_action: Optional[GameAction] = None
    called_tile: Optional[Tile] = None


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
        self._last_drawn_tile: Optional[Tuple[int, Tile]] = None

        # 狀態追蹤
        self._riichi_ippatsu: Dict[int, bool] = {}
        self._riichi_ippatsu_discard: Dict[int, int] = {}
        self._is_first_round: bool = True
        self._discard_history: List[Tuple[int, Tile]] = []
        self._kan_count: int = 0
        self._turn_count: int = 0
        self._is_first_turn_after_deal: bool = True
        self._pending_kan_tile: Optional[Tuple[int, Tile]] = None
        self._winning_players: List[int] = []
        self._ignore_suukantsu: bool = False

        # 振聽狀態追蹤
        self._furiten_permanent: Dict[int, bool] = {}  # 立直振聽（永久）
        self._furiten_temp: Dict[int, bool] = {}       # 同巡振聽（臨時）
        self._furiten_temp_round: Dict[int, int] = {}  # 同巡振聽發生的回合

        # 包牌狀態追蹤 {player_index: pao_player_index}
        self._pao_daisangen: Dict[int, int] = {}
        self._pao_daisuushi: Dict[int, int] = {}

        self._action_handlers = {
            GameAction.DRAW: self._handle_draw,
            GameAction.DISCARD: self._handle_discard,
            GameAction.PON: self._handle_pon,
            GameAction.CHI: self._handle_chi,
            GameAction.RICHI: self._handle_riichi,
            GameAction.KAN: self._handle_kan,
            GameAction.ANKAN: self._handle_ankan,
        }

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
        self._riichi_ippatsu = {}
        self._riichi_ippatsu_discard = {}
        self._is_first_round = True
        self._discard_history = []
        self._kan_count = 0
        self._turn_count = 0
        self._is_first_turn_after_deal = True
        self._pending_kan_tile = None
        self._winning_players = []
        self._ignore_suukantsu = False
        self._last_drawn_tile = None

        # 重置振聽狀態
        self._furiten_permanent = {}
        self._furiten_temp = {}
        self._furiten_temp_round = {}
        self._pao_daisangen = {}
        self._pao_daisuushi = {}

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

    def get_available_actions(self, player: int) -> List[GameAction]:
        """
        取得指定玩家當前可執行的動作列表

        Args:
            player: 玩家位置

        Returns:
            可執行的動作列表
        """
        if self._phase != GamePhase.PLAYING:
            return []

        if not (0 <= player < len(self._hands)):
            return []

        actions: List[GameAction] = []

        if self._can_draw(player):
            actions.append(GameAction.DRAW)

        if self._can_discard(player):
            actions.append(GameAction.DISCARD)

        if self._can_pon(player):
            actions.append(GameAction.PON)

        if self._can_chi(player):
            actions.append(GameAction.CHI)

        if self._can_riichi(player):
            actions.append(GameAction.RICHI)

        if self._can_kan(player):
            actions.append(GameAction.KAN)

        if self._can_ankan(player):
            actions.append(GameAction.ANKAN)

        return actions

    def _can_draw(self, player: int) -> bool:
        if player != self._current_player:
            return False
        hand = self._hands[player]
        return hand.total_tile_count() < 14

    def _can_discard(self, player: int) -> bool:
        if player != self._current_player:
            return False
        hand = self._hands[player]
        return hand.total_tile_count() > 0

    def _can_pon(self, player: int) -> bool:
        if self._last_discarded_tile is None or self._last_discarded_player is None:
            return False
        if player == self._last_discarded_player:
            return False
        hand = self._hands[player]
        return hand.can_pon(self._last_discarded_tile)

    def _can_chi(self, player: int) -> bool:
        if self._last_discarded_tile is None or self._last_discarded_player is None:
            return False
        if (player - self._last_discarded_player) % self._num_players != 1:
            return False
        hand = self._hands[player]
        sequences = hand.can_chi(self._last_discarded_tile, from_player=0)
        return len(sequences) > 0

    def _can_riichi(self, player: int) -> bool:
        hand = self._hands[player]
        if not hand.is_concealed:
            return False
        return False if hand.is_riichi else hand.is_tenpai()

    def _can_kan(self, player: int) -> bool:
        hand = self._hands[player]

        # 他家捨牌可進行大明槓
        if (
            self._last_discarded_tile is not None
            and self._last_discarded_player is not None
            and (self._last_discarded_player != player and hand.can_kan(self._last_discarded_tile))
        ):
            return True

        # 自家加槓（需為當前玩家）
        if player == self._current_player:
            # 加槓：現有碰升級
            for meld in hand.can_kan(None):
                if meld.type == MeldType.KAN and meld.called_tile is not None:
                    return True

        return False

    def _can_ankan(self, player: int) -> bool:
        hand = self._hands[player]
        return bool(hand.can_kan(None))

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
        available_actions = self.get_available_actions(player)
        if action not in available_actions:
            raise ValueError(f"玩家 {player} 不能執行動作 {action}")

        handler = self._action_handlers.get(action)
        if handler is None:
            raise ValueError(f"動作 {action} 尚未實作")
        return handler(player, tile=tile, **kwargs)

    def _handle_draw(self, player: int, tile: Optional[Tile] = None, **kwargs) -> ActionResult:
        result = ActionResult()
        if not self._tile_set:
            raise ValueError("牌組未初始化")
        hand = self._hands[player]
        if hand.total_tile_count() >= 14:
            raise ValueError("手牌已達 14 張，不能再摸牌")
        if drawn_tile := self._tile_set.draw():
            hand.add_tile(drawn_tile)
            result.drawn_tile = drawn_tile
            self._last_drawn_tile = (player, drawn_tile)
            if self._tile_set.is_exhausted():
                result.is_last_tile = True
        else:
            self._phase = GamePhase.RYUUKYOKU
            result.ryuukyoku = RyuukyokuResult(ryuukyoku=True, ryuukyoku_type=RyuukyokuType.EXHAUSTED)
        return result

    def _handle_discard(self, player: int, tile: Optional[Tile] = None, **kwargs) -> ActionResult:
        result = ActionResult()
        if tile is None:
            raise ValueError("打牌動作必須指定牌")
        if not self._tile_set:
            raise ValueError("牌組未初始化")
        if self._hands[player].discard(tile):
            self._apply_discard_effects(player, tile, result)
            self._last_drawn_tile = None
        return result

    def _handle_pon(self, player: int, tile: Optional[Tile] = None, **kwargs) -> ActionResult:
        result = ActionResult()
        if self._last_discarded_tile is None or self._last_discarded_player is None:
            raise ValueError("沒有可碰的捨牌")
        if player == self._last_discarded_player:
            raise ValueError("不能碰自己打出的牌")

        tile_to_claim = self._last_discarded_tile
        hand = self._hands[player]
        if not hand.can_pon(tile_to_claim):
            raise ValueError("手牌無法碰這張牌")

        discarder = self._last_discarded_player
        self._remove_last_discard(discarder, tile_to_claim)

        meld = hand.pon(tile_to_claim)
        result.meld = meld
        result.called_action = GameAction.PON
        result.called_tile = tile_to_claim

        self._interrupt_ippatsu(GameAction.PON, acting_player=player)

        self._current_player = player
        self._last_discarded_tile = None
        self._last_discarded_player = None
        self._is_first_turn_after_deal = False
        self._last_drawn_tile = None
        return result

    def _handle_chi(self, player: int, tile: Optional[Tile] = None, **kwargs) -> ActionResult:
        result = ActionResult()
        if self._last_discarded_tile is None or self._last_discarded_player is None:
            raise ValueError("沒有可吃的捨牌")
        if (player - self._last_discarded_player) % self._num_players != 1:
            raise ValueError("只能吃上家的牌")

        tile_to_claim = self._last_discarded_tile
        hand = self._hands[player]
        sequences = hand.can_chi(tile_to_claim, from_player=0)
        if not sequences:
            raise ValueError("手牌無法吃這張牌")

        sequence = kwargs.get("sequence")
        if sequence is None:
            sequence = sequences[0]
        elif sequence not in sequences:
            raise ValueError("提供的順子無效")

        discarder = self._last_discarded_player
        self._remove_last_discard(discarder, tile_to_claim)

        meld = hand.chi(tile_to_claim, sequence)
        result.meld = meld
        result.called_action = GameAction.CHI
        result.called_tile = tile_to_claim

        self._interrupt_ippatsu(GameAction.CHI, acting_player=player)

        self._current_player = player
        self._last_discarded_tile = None
        self._last_discarded_player = None
        self._is_first_turn_after_deal = False
        self._last_drawn_tile = None
        return result

    def _handle_riichi(self, player: int, tile: Optional[Tile] = None, **kwargs) -> ActionResult:
        result = ActionResult()
        self._hands[player].set_riichi(True)
        self._game_state.add_riichi_stick()
        self._game_state.update_score(player, -1000)
        self._riichi_ippatsu[player] = True
        self._riichi_ippatsu_discard[player] = 0
        result.riichi = True
        return result

    def _handle_kan(self, player: int, tile: Optional[Tile] = None, **kwargs) -> ActionResult:
        result = ActionResult()
        if tile is None:
            raise ValueError("明槓必須指定被槓的牌")

        meld = self._hands[player].kan(tile)
        self._kan_count += 1
        self._last_drawn_tile = None

        self._interrupt_ippatsu(GameAction.KAN, acting_player=player)

        if self._draw_rinshan_tile(player, result, kan_type=meld.type):
            self._pending_kan_tile = None
        return result

    def _handle_ankan(self, player: int, tile: Optional[Tile] = None, **kwargs) -> ActionResult:
        result = ActionResult()
        hand = self._hands[player]

        candidates = hand.can_kan(None)
        if not candidates:
            raise ValueError("手牌無法暗槓")

        # TODO: 支援多個暗槓選擇（玩家可以選擇要暗槓哪一張牌）
        selected = candidates[0]
        is_add_kan = selected.type == MeldType.KAN and selected.called_tile is not None

        if is_add_kan:
            kan_tile = selected.tiles[0]
            self._pending_kan_tile = (player, kan_tile)
            if chankan_winners := self._check_chankan(player, kan_tile):
                result.chankan = True
                result.winners = chankan_winners
                self._pending_kan_tile = None
                return result

        meld = hand.kan(None)
        if meld:
            self._kan_count += 1
        kan_type = meld.type if meld else MeldType.ANKAN

        self._interrupt_ippatsu(GameAction.ANKAN, acting_player=player)

        self._draw_rinshan_tile(player, result, kan_type=kan_type)
        if self._pending_kan_tile:
            self._pending_kan_tile = None
        self._last_drawn_tile = None
        return result

    def _remove_last_discard(self, discarder: int, tile: Tile) -> None:
        self._hands[discarder].remove_last_discard(tile)
        if self._discard_history and self._discard_history[-1] == (discarder, tile):
            self._discard_history.pop()

    def _draw_rinshan_tile(self, player: int, result: ActionResult, *, kan_type: MeldType) -> bool:
        if not self._tile_set:
            return False

        if rinshan_tile := self._tile_set.draw_rinshan():
            self._hands[player].add_tile(rinshan_tile)
            result.rinshan_tile = rinshan_tile
            self._last_drawn_tile = (player, rinshan_tile)
            if kan_type == MeldType.KAN:
                result.kan = True
            else:
                result.ankan = True

            if rinshan_win := self._check_rinshan_win(player, rinshan_tile):
                result.rinshan_win = rinshan_win
                self._ignore_suukantsu = True
                self._phase = GamePhase.WINNING
            return True

        self._phase = GamePhase.RYUUKYOKU
        result.ryuukyoku = RyuukyokuResult(ryuukyoku=True, ryuukyoku_type=RyuukyokuType.EXHAUSTED)
        return False

    def _apply_discard_effects(self, player: int, tile: Tile, result: ActionResult) -> None:
        self._last_discarded_tile = tile
        self._last_discarded_player = player
        self._discard_history.append((player, tile))
        if len(self._discard_history) > 4:
            self._discard_history.pop(0)

        if self._riichi_ippatsu and player in self._riichi_ippatsu:
            if self._riichi_ippatsu_discard.get(player) == 1:
                self._riichi_ippatsu[player] = False
            self._riichi_ippatsu_discard[player] += 1
        if self._tile_set and self._tile_set.is_exhausted():
            result.is_last_tile = True

        self._current_player = (player + 1) % self._num_players
        self._turn_count += 1
        self._is_first_turn_after_deal = False
        self._is_first_round = False
        result.discarded = True

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

        last_draw = self._last_drawn_tile
        is_tsumo = is_rinshan
        if not is_tsumo and last_draw is not None:
            last_player, last_tile = last_draw
            if last_player == player and last_tile == winning_tile:
                is_tsumo = True

        if not hand.is_winning_hand(winning_tile, is_tsumo):
            return None

        # 獲取和牌組合
        combinations = hand.get_winning_combinations(winning_tile, is_tsumo)
        if not combinations:
            return None

        # 榮和時檢查振聽（振聽玩家不能榮和，但可以自摸）
        if not is_tsumo and self.is_furiten(player):
            return None

        # 使用第一個組合進行役種判定
        # TODO: 支援多個和牌組合
        winning_combination = combinations[0] if combinations else []

        # 檢查役種
        # 判定是否符合一發
        is_ippatsu = self._riichi_ippatsu.get(player, False)
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
            is_ippatsu,
            is_first_turn,
            is_last_tile,
            player,
            is_rinshan,
        )

        if not yaku_results:
            return None  # 沒有役不能和牌

        # 計算寶牌數量
        dora_count = self._count_dora(player, winning_tile)

        # 確定包牌者
        pao_player = None
        for result in yaku_results:
            if result.yaku == Yaku.DAISANGEN:
                pao_player = self._pao_daisangen.get(player)
                if pao_player is not None:
                    break
            elif result.yaku == Yaku.DAISUUSHI:
                pao_player = self._pao_daisuushi.get(player)
                if pao_player is not None:
                    break

        # 計算得分
        score_result = self._score_calculator.calculate(
            hand,
            winning_tile,
            winning_combination,
            yaku_results,
            dora_count,
            self._game_state,
            is_tsumo,
            player,
            pao_player=pao_player,
        )

        score_result.payment_to = player
        # 如果是榮和，設置支付者
        if not is_tsumo and self._last_discarded_player is not None:
            score_result.payment_from = self._last_discarded_player
        elif is_chankan and self._pending_kan_tile:
            # 搶槓和：支付者為槓牌玩家
            kan_player, _ = self._pending_kan_tile
            score_result.payment_from = kan_player

        if self._kan_count >= 4:
            self._ignore_suukantsu = True

        return WinResult(
            win=True,
            player=player,
            yaku=yaku_results,
            han=score_result.han,
            fu=score_result.fu,
            points=score_result.total_points,
            score_result=score_result,
            chankan=is_chankan or None,
            rinshan=is_rinshan or None,
        )

    def check_multiple_ron(self, discarded_tile: Tile, discarder: int) -> List[int]:
        """
        檢查多個玩家是否可以榮和同一張牌

        根據配置返回可以榮和的玩家列表：
        - head_bump_only=True: 只返回下家
        - allow_double_ron=True: 最多返回2人
        - allow_triple_ron=False且檢測到3人: 返回空列表（觸發流局）
        - allow_triple_ron=True且檢測到3人: 返回3人

        Args:
            discarded_tile: 被打出的牌
            discarder: 打牌者

        Returns:
            可以榮和的玩家列表（按逆時針順序，下家優先）
        """
        # 收集所有可以榮和的玩家（除了打牌者）
        potential_winners = []

        for offset in range(1, self._num_players):
            player = (discarder + offset) % self._num_players

            # 檢查此玩家是否可以榮和
            win_result = self.check_win(player, discarded_tile, is_chankan=False, is_rinshan=False)
            if win_result is not None:
                potential_winners.append(player)

        # 如果沒有人能榮和，直接返回
        if not potential_winners:
            return []

        # 如果只有一人，直接返回
        if len(potential_winners) == 1:
            return potential_winners

        # 多人可以榮和的情況，根據配置處理
        ruleset = self._game_state.ruleset

        # 首先檢查三家和了（優先級最高，因為可能觸發流局）
        if len(potential_winners) >= 3:
            # 如果禁用三響，返回空列表（將觸發三家和了流局）
            if not ruleset.allow_triple_ron:
                return []  # 觸發流局
            # 如果啟用三響，返回所有玩家（最多3人）
            return potential_winners[:3]

        # 頭跳模式：只允許下家榮和（適用於2人的情況）
        if ruleset.head_bump_only:
            # 返回第一個玩家（下家，逆時針最近）
            return [potential_winners[0]]

        # 雙響情況（2人），且 head_bump_only=False
        if len(potential_winners) == 2:
            if ruleset.allow_double_ron:
                return potential_winners
            else:
                # 禁用雙響但不是頭跳模式，返回下家
                return [potential_winners[0]]

        return potential_winners

    def check_ryuukyoku(self) -> Optional[RyuukyokuType]:
        """
        檢查是否流局

        Returns:
            流局類型，否則返回 None
        """
        # 檢查四風連打（優先檢查，因為可以在第一巡發生）
        if self._check_suufon_renda():
            return RyuukyokuType.SUUFON_RENDA

        # 檢查三家和了（多人和牌流局）
        if self._check_sancha_ron():
            return RyuukyokuType.SANCHA_RON

        # 檢查四槓散了（四個槓之後流局）
        if self._kan_count >= 4 and not self._ignore_suukantsu:
            return RyuukyokuType.SUUKANTSU

        # 牌山耗盡流局
        if self._tile_set and self._tile_set.is_exhausted():
            return RyuukyokuType.EXHAUSTED

        # 檢查是否所有玩家都聽牌（全員聽牌流局）
        return RyuukyokuType.SUUCHA_RIICHI if self._check_all_riichi() else None

    def _check_all_riichi(self) -> bool:
        """檢查是否所有玩家都立直"""
        if self._phase != GamePhase.PLAYING:
            return False

        return all(hand.is_riichi for hand in self._hands)

    def _check_kyuushu_kyuuhai(self, player: int) -> bool:
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

        terminal_and_honor_tiles = {(tile.suit, tile.rank) for tile in hand.tiles if tile.is_terminal or tile.is_honor}
        # 如果有9種或以上不同種類的幺九牌，則為九種九牌
        return len(terminal_and_honor_tiles) >= 9

    def _check_suufon_renda(self) -> bool:
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

        return not any(tile.suit != Suit.JIHAI or tile.rank != first_tile.rank for _, tile in self._discard_history[:4])

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

        if waiting_tiles := hand.get_waiting_tiles():
            return all((tile.is_terminal or tile.is_honor) for tile in waiting_tiles)
        else:
            return False

    def _count_dora(self, player: int, winning_tile: Optional[Tile] = None) -> int:
        """
        計算寶牌數量

        Args:
            player: 玩家位置
            winning_tile: 和牌牌

        Returns:
            寶牌翻數（表寶牌 + 裡寶牌 + 紅寶牌）
        """
        if not self._tile_set:
            return 0

        dora_count = 0
        hand = self._hands[player]

        # 收集所有牌（手牌 + 和牌牌）
        all_tiles = hand.tiles + [winning_tile] if winning_tile else hand.tiles

        # 表寶牌
        if dora_indicators := self._tile_set.get_dora_indicators(self._kan_count):
            for dora_indicator in dora_indicators:
                dora_tile = self._tile_set.get_dora(dora_indicator)
                if dora_tile in all_tiles:
                    dora_count += 1

        # 裡寶牌（立直時）
        if hand.is_riichi:
            if ura_indicators := self._tile_set.get_ura_dora_indicators(self._kan_count):
                for ura_indicator in ura_indicators:
                    ura_dora_tile = self._tile_set.get_dora(ura_indicator)
                    if ura_dora_tile in all_tiles:
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

    def get_last_discard(self) -> Optional[Tile]:
        """取得最新的捨牌（尚未被處理）。"""
        return self._last_discarded_tile

    def get_last_discard_player(self) -> Optional[int]:
        """取得最後捨牌的玩家。"""
        return self._last_discarded_player

    def get_num_players(self) -> int:
        """取得玩家數量。"""
        return self._num_players

    def get_wall_remaining(self) -> Optional[int]:
        """取得牌山剩餘張數。"""
        return self._tile_set.remaining if self._tile_set else None

    def get_revealed_dora_indicators(self) -> List[Tile]:
        """取得目前公開的寶牌指示牌。"""
        return self._tile_set.get_dora_indicators() if self._tile_set else []

    def get_available_chi_sequences(self, player: int) -> List[List[Tile]]:
        """取得玩家可用的吃牌組合（僅限上家捨牌）。"""

        if self._last_discarded_tile is None or self._last_discarded_player is None:
            return []
        if (player - self._last_discarded_player) % self._num_players != 1:
            return []
        hand = self._hands[player]
        return [seq.copy() for seq in hand.can_chi(self._last_discarded_tile, from_player=0)]

    def handle_ryuukyoku(self) -> RyuukyokuResult:
        """
        處理流局

        Returns:
            流局結果，包含流局類型、流局滿貫玩家等
        """
        ryuukyoku_type = self.check_ryuukyoku()
        if not ryuukyoku_type:
            return RyuukyokuResult(ryuukyoku=False)

        result = RyuukyokuResult(
            ryuukyoku=True,
            ryuukyoku_type=ryuukyoku_type,
        )

        # 檢查流局滿貫
        if ryuukyoku_type == RyuukyokuType.EXHAUSTED:
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
                if self._check_kyuushu_kyuuhai(i):
                    result.ryuukyoku_type = RyuukyokuType.KYUUSHU_KYUUHAI
                    result.kyuushu_kyuuhai_player = i
                    # 九種九牌流局時，莊家連莊
                    break

        # 處理全員聽牌流局
        if ryuukyoku_type == RyuukyokuType.SUUCHA_RIICHI:
            # 全員聽牌流局時，莊家支付 300 點給每個閒家
            dealer = self._game_state.dealer
            for i in range(self._num_players):
                if i != dealer:
                    self._game_state.transfer_points(dealer, i, 300)

        self._phase = GamePhase.RYUUKYOKU
        return result

    def apply_win_score(self, win_result: WinResult) -> None:
        """
        應用和牌分數

        Args:
            win_result: 和牌結果
        """
        score_result = win_result.score_result
        if not score_result:
            return

        winner = win_result.player if hasattr(win_result, "player") else self._current_player
        # 注意：WinResult 可能沒有 player 字段，如果沒有則假設是當前玩家
        # 但 check_win 返回的 WinResult 沒有 player 字段，我們需要確保它有
        # 或者從外部傳入。這裡我們假設調用者會確保上下文正確。
        # 實際上 check_win 返回的 WinResult 確實沒有 player 字段 (在之前的 edit 中被移除了?)
        # 讓我們檢查 check_win 的返回值。
        # 是的，我移除了 player=player。所以這裡我們需要依賴 score_result.payment_to

        winner = score_result.payment_to

        # 增加贏家分數
        self._game_state.update_score(winner, score_result.total_points)

        # 扣除輸家分數
        if score_result.is_tsumo:
            # 自摸
            if score_result.pao_player is not None and score_result.pao_payment > 0:
                # 包牌自摸：包牌者全付
                self._game_state.update_score(score_result.pao_player, -score_result.pao_payment)
            else:
                # 正常自摸
                dealer = self._game_state.dealer
                for i in range(self._num_players):
                    if i == winner:
                        continue

                    payment = 0
                    if i == dealer:
                        payment = score_result.dealer_payment
                    else:
                        payment = score_result.non_dealer_payment

                    self._game_state.update_score(i, -payment)
        else:
            # 榮和
            loser = score_result.payment_from

            if score_result.pao_player is not None and score_result.pao_payment > 0:
                # 包牌榮和（分擔）
                # 包牌者支付 pao_payment
                self._game_state.update_score(score_result.pao_player, -score_result.pao_payment)

                # 放銃者支付剩下的
                # 總支付 = total_points - riichi_sticks
                total_pay = score_result.total_points - score_result.riichi_sticks_bonus
                remaining_pay = total_pay - score_result.pao_payment
                self._game_state.update_score(loser, -remaining_pay)
            else:
                # 正常榮和
                # 放銃者支付 total_points - riichi_sticks
                # 注意：total_points 包含供託，但供託是從場上拿的，不是放銃者出的
                # 放銃者只支付 (base + honba)
                # score_result.total_points = base + honba + sticks
                payment = score_result.total_points - score_result.riichi_sticks_bonus
                self._game_state.update_score(loser, -payment)

        # 清空供託
        if score_result.riichi_sticks_bonus > 0:
            self._game_state._riichi_sticks = 0

        # 清空本場 (如果是自摸或莊家榮和? 不，通常由 next_dealer 處理)
        # 這裡只處理分數更新

    def end_round(self, winners: Optional[List[int]] = None) -> None:
        """
        結束一局

        Args:
            winners: 獲勝玩家列表（如果為 None，則為流局）
                    - 單人榮和/自摸：[player_id]
                    - 雙響/三響：[player1, player2, player3]
        """
        if winners is not None and len(winners) > 0:
            # 和牌處理
            dealer = self._game_state.dealer
            # 如果任一贏家是莊家，則連莊
            dealer_won = dealer in winners

            # 更新莊家
            self._game_state.next_dealer(dealer_won)

            # 檢查擊飛
            if self._check_tobi():
                self._phase = GamePhase.ENDED
                return

            # 如果莊家未獲勝，進入下一局
            if not dealer_won:
                has_next = self._game_state.next_round()
                if not has_next:
                    self._phase = GamePhase.ENDED
        else:
            # 流局處理
            # 如果是牌山耗盡流局，計算不聽罰符
            if self._tile_set and self._tile_set.is_exhausted():
                self._calculate_noten_bappu()

            # 檢查擊飛
            if self._check_tobi():
                self._phase = GamePhase.ENDED
                return

            dealer_won = False  # 流局時莊家不連莊（除非九種九牌）
            self._game_state.next_dealer(dealer_won)

            has_next = self._game_state.next_round()
            if not has_next:
                self._phase = GamePhase.ENDED

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

            if self.check_win(player, kan_tile, is_chankan=True):
                winners.append(player)

        return winners

    def _interrupt_ippatsu(self, action: GameAction, acting_player: int) -> None:
        """處理副露或槓造成的一發中斷。"""
        if not self._riichi_ippatsu:
            return

        if action not in {GameAction.CHI, GameAction.PON, GameAction.KAN, GameAction.ANKAN}:
            return

        if not self._game_state.ruleset.ippatsu_interrupt_on_meld_or_kan:
            return

        for player in self._riichi_ippatsu.keys():
            self._riichi_ippatsu[player] = False
            self._riichi_ippatsu_discard[player] = 0

    def _check_sancha_ron(self) -> bool:
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

    def _check_rinshan_win(self, player: int, rinshan_tile: Tile) -> Optional[WinResult]:
        """
        檢查嶺上開花（槓後摸牌和牌）

        Args:
            player: 玩家位置
            rinshan_tile: 從嶺上摸到的牌

        Returns:
            和牌結果，如果不能和則返回 None
        """
        return self.check_win(player, rinshan_tile, is_rinshan=True)

    def _calculate_noten_bappu(self) -> Dict[int, int]:
        """
        計算不聽罰符

        Returns:
            玩家分數變化字典 {player_index: score_change}
        """
        tenpai_players = []
        for i in range(self._num_players):
            if self._hands[i].is_tenpai():
                tenpai_players.append(i)

        num_tenpai = len(tenpai_players)
        changes = {}

        if num_tenpai == 0 or num_tenpai == 4:
            return {}

        if num_tenpai == 1:
            # 1人聽：+3000 / -1000
            winner = tenpai_players[0]
            changes[winner] = 3000
            for i in range(self._num_players):
                if i != winner:
                    changes[i] = -1000

        elif num_tenpai == 2:
            # 2人聽：+1500 / -1500
            for i in range(self._num_players):
                if i in tenpai_players:
                    changes[i] = 1500
                else:
                    changes[i] = -1500

        elif num_tenpai == 3:
            # 3人聽：+1000 / -3000
            loser = [i for i in range(self._num_players) if i not in tenpai_players][0]
            changes[loser] = -3000
            for i in tenpai_players:
                changes[i] = 1000

        # 應用分數變更
        for player, delta in changes.items():
            self._game_state.update_score(player, delta)

        return changes

    def check_furiten_discards(self, player: int) -> bool:
        """
        檢查現物振聽：玩家打過的牌包含在聽牌牌中

        Args:
            player: 玩家位置

        Returns:
            是否為現物振聽
        """
        hand = self._hands[player]

        # 未聽牌不算振聽
        if not hand.is_tenpai():
            return False

        # 獲取聽牌牌
        waiting_tiles = hand.get_waiting_tiles()
        if not waiting_tiles:
            return False

        # 檢查玩家的捨牌歷史
        for discard in hand.discards:
            # 如果打過的牌在聽牌牌中，則為現物振聽
            if any(discard.suit == wt.suit and discard.rank == wt.rank for wt in waiting_tiles):
                return True

        return False

    def check_furiten_temp(self, player: int) -> bool:
        """
        檢查同巡振聽：同巡內放過榮和機會

        Args:
            player: 玩家位置

        Returns:
            是否為同巡振聽
        """
        # 檢查是否設置了同巡振聽
        if not self._furiten_temp.get(player, False):
            return False

        # 檢查是否是同一回合
        furiten_round = self._furiten_temp_round.get(player, -1)
        return furiten_round == self._turn_count

    def check_furiten_riichi(self, player: int) -> bool:
        """
        檢查立直振聽：立直後放過榮和機會

        Args:
            player: 玩家位置

        Returns:
            是否為立直振聽
        """
        return self._furiten_permanent.get(player, False)

    def is_furiten(self, player: int) -> bool:
        """
        綜合檢查玩家是否處於振聽狀態

        Args:
            player: 玩家位置

        Returns:
            是否處於振聽狀態
        """
        return (
            self.check_furiten_discards(player) or
            self.check_furiten_temp(player) or
            self.check_furiten_riichi(player)
        )
    def _check_tobi(self) -> bool:
        """
        檢查是否觸發擊飛

        Returns:
            是否觸發擊飛
        """
        if not self._game_state.ruleset.tobi_enabled:
            return False

        for score in self._game_state.scores:
            if score < 0:
                return True

        return False
