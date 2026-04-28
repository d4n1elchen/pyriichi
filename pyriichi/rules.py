"""
Rule Engine - RuleEngine implementation

Provides game flow control, action execution, and rule adjudication functions.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from pyriichi.enum_utils import TranslatableEnum
from pyriichi.game_state import GameState, Wind
from pyriichi.hand import Hand, Meld, MeldType
from pyriichi.scoring import ScoreCalculator, ScoreResult
from pyriichi.tiles import Suit, Tile, TileSet
from pyriichi.yaku import Yaku, YakuChecker, YakuResult


class GameAction(TranslatableEnum):
    """Game Action"""

    DRAW = ("draw", "摸牌", "ツモ", "Draw")
    DISCARD = ("discard", "打牌", "打牌", "Discard")
    CHI = ("chi", "吃", "チー", "Chi")
    PON = ("pon", "碰", "ポン", "Pon")
    KAN = ("kan", "槓", "カン", "Kan")
    DECLARE_ANKAN = ("declare_ankan", "暗槓", "暗槓", "Closed Kan")
    DECLARE_RIICHI = ("declare_riichi", "立直", "リーチ", "Riichi")
    TSUMO = ("tsumo", "自摸", "ツモ", "Tsumo")
    RON = ("ron", "榮和", "ロン", "Ron")
    DECLARE_KYUUSHU_KYUUHAI = (
        "declare_kyuushu_kyuuhai",
        "九種九牌",
        "九種九牌",
        "Nine Terminals Abort",
    )
    PASS = ("pass", "過", "パス", "Pass")


class GamePhase(TranslatableEnum):
    """Game Phase"""

    INIT = ("init", "初始化", "初期化", "Init")
    DEALING = ("dealing", "發牌", "配牌", "Dealing")
    PLAYING = ("playing", "對局中", "対局中", "Playing")
    WINNING = ("winning", "和牌處理", "和了処理", "Winning")
    RYUUKYOKU = ("ryuukyoku", "流局", "流局", "Exhaustive Draw")
    ENDED = ("ended", "結束", "終了", "Ended")


class RyuukyokuType(TranslatableEnum):
    """ryuukyoku (Exhaustive Draw) Type"""

    SUUFON_RENDA = ("suufon_renda", "四風連打", "四風連打", "Four Winds Abort")
    SANCHA_RON = ("sancha_ron", "三家和了", "三家和了", "Triple Ron Abort")
    SUUKAN_SANRA = ("suukan_sanra", "四槓散了", "四槓散了", "Four Kan Abort")
    EXHAUSTIVE_DRAW = ("exhaustive_draw", "流局", "流局", "Exhaustive Draw")
    SUUCHA_RIICHI = (
        "suucha_riichi",
        "四家立直",
        "四家立直",
        "Four Riichi Abort",
    )
    KYUUSHU_KYUUHAI = (
        "kyuushu_kyuuhai",
        "九種九牌",
        "九種九牌",
        "Nine Terminals Abort",
    )


@dataclass
class WinResult:
    """Win Result"""

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
    """ryuukyoku (Exhaustive Draw) Result"""

    ryuukyoku: bool
    ryuukyoku_type: Optional[RyuukyokuType] = None
    flow_mangan_players: List[int] = field(default_factory=list)
    kyuushu_kyuuhai_player: Optional[int] = None


@dataclass
class ActionResult:
    """Action Execution Result"""

    success: bool = True
    phase: Optional[GamePhase] = None
    drawn_tile: Optional[Tile] = None
    is_last_tile: Optional[bool] = None
    ryuukyoku: Optional[RyuukyokuResult] = None
    discarded: Optional[bool] = None
    riichi: Optional[bool] = None
    chankan: Optional[bool] = None
    winners: List[int] = field(default_factory=list)
    rinshan_tile: Optional[Tile] = None
    kan: Optional[bool] = None
    closed_kan: Optional[bool] = None
    rinshan_win: Optional[WinResult] = None
    win_results: Dict[int, WinResult] = field(default_factory=dict)
    meld: Optional[Meld] = None
    called_action: Optional[GameAction] = None
    called_tile: Optional[Tile] = None
    waiting_for: Dict[int, List[GameAction]] = field(default_factory=dict)


class RuleEngine:
    """Rule Engine"""

    def __init__(self, num_players: int = 4):
        """
        Initialize the Rule Engine.

        Args:
            num_players (int): Number of players (default 4).
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

        self._is_first_round: bool = True
        self._discard_history: List[Tuple[int, Tile]] = []
        self._kan_count: int = 0
        self._turn_count: int = 0
        self._is_first_turn_after_deal: bool = True
        self._pending_kan_tile: Optional[Tuple[int, Tile]] = None
        self._winning_players: List[int] = []
        self._ignore_suukan_sanra: bool = False

        # furiten (Sacred Discard) status tracking
        self._furiten_permanent: Dict[int, bool] = {}  # riichi furiten (Permanent)
        self._furiten_temp: Dict[int, bool] = {}  # temp_furiten (Same Turn)
        self._furiten_temp_round: Dict[int, int] = (
            {}
        )  # Round where temp_furiten occurred

        self._pao_daisangen: Dict[int, int] = {}
        self._pao_daisuushi: Dict[int, int] = {}

        self._action_handlers = {
            GameAction.DRAW: self._handle_draw,
            GameAction.DISCARD: self._handle_discard,
            GameAction.PON: self._handle_pon,
            GameAction.CHI: self._handle_chi,
            GameAction.DECLARE_RIICHI: self._handle_riichi,
            GameAction.KAN: self._handle_kan,
            GameAction.DECLARE_ANKAN: self._handle_declare_ankan,
            GameAction.TSUMO: self._handle_tsumo,
            GameAction.RON: self._handle_ron,
            GameAction.DECLARE_KYUUSHU_KYUUHAI: self._handle_declare_kyuushu_kyuuhai,
            GameAction.PASS: self._handle_pass,
        }

        self._waiting_for_actions: Dict[int, List[GameAction]] = {}
        self._incoming_actions: Dict[int, Tuple[GameAction, Optional[Tile], Dict]] = {}
        self._riichi_ippatsu: Dict[int, bool] = {}
        self._riichi_ippatsu_discard: Dict[int, int] = {}

    def _handle_pass(
        self, player: int, tile: Optional[Tile] = None, **kwargs
    ) -> ActionResult:
        """
        handle PASS action.

        PASS action is usually intercepted and handled by execute_action in waiting state.
        If this method is called directly, it means it is called in a non-waiting state,
        which is usually not allowed unless there is special PASS logic (currently none).
        """
        return ActionResult(success=True)

    def start_game(self) -> None:
        """Start a new game."""
        self._game_state = GameState(num_players=self._num_players)
        self._phase = GamePhase.INIT

    def start_round(self) -> None:
        """Start a new round."""
        self._tile_set = TileSet()
        self._tile_set.shuffle()
        self._phase = GamePhase.DEALING
        self._current_player = self._game_state.dealer
        self._last_discarded_tile = None
        self._last_discarded_player = None

        self._riichi_ippatsu = {}
        self._riichi_ippatsu_discard = {}
        self._is_first_round = True
        self._discard_history = []
        self._kan_count = 0
        self._turn_count = 0
        self._is_first_turn_after_deal = True
        self._pending_kan_tile = None
        self._winning_players = []
        self._ignore_suukan_sanra = False

        # Reset hands last drawn tile
        for hand in self._hands:
            hand.reset_last_drawn_tile()

        self._furiten_permanent = {}
        self._furiten_temp = {}
        self._furiten_temp_round = {}
        self._pao_daisangen = {}
        self._pao_daisangen = {}
        self._pao_daisuushi = {}

        # nagashi_mangan tracking: Record if player's discards were called
        self._has_called_discard = {i: False for i in range(self._num_players)}

    def deal(self) -> Dict[int, List[Tile]]:
        """
        Deal tiles.

        Returns:
            Dict[int, List[Tile]]: Dictionary of player hands {player_id: [tiles]}.

        Raises:
            ValueError: If not in DEALING phase or tile set is not initialized.
        """
        if self._phase != GamePhase.DEALING:
            raise ValueError("只能在發牌階段發牌")

        if not self._tile_set:
            raise ValueError("牌組未初始化")
        hands_tiles = self._tile_set.deal(num_players=self._num_players)
        self._hands = [Hand(tiles) for tiles in hands_tiles]

        self._phase = GamePhase.PLAYING
        self._is_first_turn_after_deal = True

        # Set dealer waiting action
        dealer = self._game_state.dealer
        actions = self._calculate_turn_actions(dealer)
        self._waiting_for_actions = {dealer: actions}

        return {i: hand.tiles for i, hand in enumerate(self._hands)}

    def get_current_player(self) -> int:
        """
        Get the current active player.

        Returns:
            int: Current player position.
        """
        return self._current_player

    def get_last_discard_player(self) -> Optional[int]:
        """Get the player who last discarded."""
        return self._last_discarded_player

    def get_phase(self) -> GamePhase:
        """
        Get current game phase.

        Returns:
            GamePhase: Current game phase.
        """
        return self._phase

    @property
    def game_state(self) -> GameState:
        """
        Get game state.

        Returns:
            GameState: Game state object.
        """
        return self._game_state

    @property
    def waiting_for_actions(self) -> Dict[int, List[GameAction]]:
        """Get actions currently waiting to be executed"""
        return self._waiting_for_actions

    @property
    def tileset(self) -> Optional[TileSet]:
        """Get tile set object"""
        return self._tile_set

    def _calculate_turn_actions(self, player: int) -> List[GameAction]:
        """Calculate executable actions for player's turn"""
        actions: List[GameAction] = []

        if self._can_discard(player):
            actions.append(GameAction.DISCARD)

        if self._can_riichi(player):
            actions.append(GameAction.DECLARE_RIICHI)

        if self._can_kan(player):
            actions.append(GameAction.KAN)

        if self._can_declare_ankan(player):
            actions.append(GameAction.DECLARE_ANKAN)

        if self._can_tsumo(player):
            actions.append(GameAction.TSUMO)

        if self._check_kyuushu_kyuuhai(player):
            actions.append(GameAction.DECLARE_KYUUSHU_KYUUHAI)

        return actions

    def get_available_actions(self, player: int) -> List[GameAction]:
        """
        Get list of currently executable actions for the specified player.

        Args:
            player (int): Player position.

        Returns:
            List[GameAction]: List of executable actions.
        """
        if self._phase != GamePhase.PLAYING:
            return []

        if not (0 <= player < len(self._hands)):
            return []

        # If in waiting state (now includes in-turn actions)
        if self._waiting_for_actions:
            return self._waiting_for_actions.get(player, [])

        return []

    def _can_draw(self, player: int) -> bool:
        if player != self._current_player:
            return False
        hand = self._hands[player]
        return hand.total_tile_count() < 14

    def _can_discard(self, player: int) -> bool:
        if player != self._current_player:
            return False
        hand = self._hands[player]
        if not hand.tiles:
            return False
        return hand.total_tile_count() > 0

    def _can_pon(self, player: int) -> bool:
        if self._last_discarded_tile is None or self._last_discarded_player is None:
            return False
        if player == self._last_discarded_player:
            return False
        hand = self._hands[player]
        if hand.is_riichi:
            return False
        return hand.can_pon(self._last_discarded_tile)

    def _can_chi(self, player: int) -> bool:
        if self._last_discarded_tile is None or self._last_discarded_player is None:
            return False
        if (player - self._last_discarded_player) % self._num_players != 1:
            return False
        hand = self._hands[player]
        if hand.is_riichi:
            return False
        sequences = hand.can_chi(self._last_discarded_tile, from_player=0)
        return len(sequences) > 0

    def _can_riichi(self, player: int) -> bool:
        hand = self._hands[player]
        return (
            hand.is_concealed and not hand.is_riichi and len(hand.tenpai_discards) > 0
        )

    def _can_kan(self, player: int) -> bool:
        hand = self._hands[player]
        if hand.is_riichi:
            return False

        # open_kan on another player's discard
        if (
            self._last_discarded_tile is not None
            and self._last_discarded_player is not None
            and (
                self._last_discarded_player != player
                and hand.can_kan(self._last_discarded_tile)
            )
        ):
            return True

        # Self kan (must be current player)
        if player == self._current_player:
            # open_kan: upgrade existing pon_meld
            for meld in hand.can_kan(None):
                if meld.type == MeldType.OPEN_KAN and meld.called_tile is not None:
                    return True

        return False

    def _can_declare_ankan(self, player: int) -> bool:
        hand = self._hands[player]
        possible_kans = hand.can_kan(None)

        if not possible_kans:
            return False

        if not hand.is_riichi:
            return True

        # After riichi, can only declare_ankan if it doesn't change the machi tiles.
        # Here we need to check if each possible closed_kan changes the machi.
        # Since _can_declare_ankan only returns bool, any valid closed_kan is enough
        # Get current machi tiles.
        # In riichi state, the base machi list is after "discarding the drawn tile"
        # Because if not declare_ankan, must tsumogiri
        last_drawn = hand.last_drawn_tile
        if last_drawn is None:
            return False  # Should not happen in riichi turn

        # Temporarily remove the drawn tile
        try:
            hand._tiles.remove(last_drawn)
        except ValueError:
            return False

        current_machi_tiles = hand.get_machi_tiles()

        # Restore
        hand._tiles.append(last_drawn)

        if not current_machi_tiles:
            return False  # Should not happen, riichi must be tenpai

        for meld in possible_kans:
            if meld.type != MeldType.CLOSED_KAN:
                continue

            # Simulate closed_kan
            temp_hand = Hand([t for t in hand.tiles])
            temp_hand._melds = [m for m in hand.melds]
            temp_hand._is_riichi = True

            # Execute closed_kan
            tiles_to_remove = meld.tiles
            try:
                for t in tiles_to_remove:
                    temp_hand._tiles.remove(t)
            except ValueError:
                continue

            # Add closed_kan
            temp_hand._melds.append(meld)

            # Check if machi tiles changed.
            new_machi_tiles = temp_hand.get_machi_tiles()

            # Compare machi tile lists.
            if sorted(current_machi_tiles) == sorted(new_machi_tiles):
                return True

        return False

    def _can_tsumo(self, player: int) -> bool:
        """Check if player can tsumo (tsumo Win)"""
        if player != self._current_player:
            return False

        if self._last_drawn_tile is None:
            return False

        last_player, last_tile = self._last_drawn_tile
        if last_player != player:
            return False

        return self.check_win(player, last_tile, is_rinshan=False) is not None

    def _can_ron(self, player: int) -> bool:
        """Check if player can ron (Discard Win)"""
        if self._last_discarded_tile is None or self._last_discarded_player is None:
            return False

        if player == self._last_discarded_player:
            return False  # Cannot ron on own discard

        winners = self.check_multiple_ron(
            self._last_discarded_tile, self._last_discarded_player
        )
        return player in winners

    def execute_action(
        self, player: int, action: GameAction, tile: Optional[Tile] = None, **kwargs
    ) -> ActionResult:
        """
        Execute an action.

        Args:
            player (int): Player position.
            action (GameAction): Action type.
            tile (Optional[Tile]): Related tile.
            **kwargs: Other arguments.

        Returns:
            ActionResult: Action execution result.

        Raises:
            ValueError: If action is invalid or not implemented.
        """
        available_actions = self.get_available_actions(player)
        if action not in available_actions:
            raise ValueError(f"玩家 {player} 不能執行動作 {action}")

        handler = self._action_handlers.get(action)
        if handler is None:
            raise ValueError(f"動作 {action} 尚未實作")

        # Chombo Detection

        # If in waiting state, collect player response
        if self._waiting_for_actions:
            if player not in self._waiting_for_actions:
                raise ValueError(f"玩家 {player} 當前不需要執行動作")

            allowed_actions = self._waiting_for_actions[player]
            if action not in allowed_actions:
                raise ValueError(
                    f"玩家 {player} 不能執行動作 {action}，期待: {allowed_actions}"
                )

            # Record response
            self._incoming_actions[player] = (action, tile, kwargs)

            # If player missed ron (had ron opportunity but chose PASS or other), set temp_furiten
            if GameAction.RON in allowed_actions and action != GameAction.RON:
                self._furiten_temp[player] = True
                self._furiten_temp_round[player] = self._turn_count
            del self._waiting_for_actions[player]

            # If all players responded, resolve decisions
            if not self._waiting_for_actions:
                return self._resolve_decisions()
            else:
                # Need more player responses.
                return ActionResult(success=True)

        # Non-waiting state, execute directly (e.g., tsumo, declare_ankan, discard)
        return handler(player, tile=tile, **kwargs)

    def _resolve_decisions(self) -> ActionResult:
        """Resolve all player responses, execute highest priority action"""
        # Priority: ron > pon/kan > chi > PASS

        actions = self._incoming_actions
        self._incoming_actions = {}  # Clear

        # 0. Check current player's action (discard/tsumo/declare_ankan/riichi)
        # In this case, _waiting_for_actions should only contain current player
        # and actions should only have one entry
        if len(actions) == 1:
            player = list(actions.keys())[0]
            action, tile, kwargs = actions[player]

            # If it is current player's action (non-interrupt)
            if player == self._current_player and action not in (
                GameAction.RON,
                GameAction.PON,
                GameAction.CHI,
                GameAction.PASS,
            ):
                # Execute corresponding handler
                handler = self._action_handlers.get(action)
                if handler:
                    return handler(player, tile, **kwargs)
                else:
                    raise ValueError(f"動作 {action} 尚未實作")

        # 1. Check ron
        ron_players = [p for p, (a, _, _) in actions.items() if a == GameAction.RON]
        if ron_players:
            # Execute ron (handle multiple ron)
            # Note: If multiple rons, need to handle in order
            # If double_ron, we should set all at once?

            # Use check_multiple_ron to get real winners (considering head_bump)
            if self._last_discarded_tile is None or self._last_discarded_player is None:
                raise ValueError("無法執行榮和：無捨牌")

            real_winners = self.check_multiple_ron(
                self._last_discarded_tile, self._last_discarded_player
            )

            # Filter out players not in real_winners (e.g. intercepted by head_bump)
            valid_ron_players = [p for p in ron_players if p in real_winners]

            if not valid_ron_players:
                # Should not happen unless logic error
                return ActionResult(success=False)

            # Execute ron
            # Can we call _handle_ron for the first winner and manually add others?
            # Or _handle_ron should be refactored to support multiple winners?
            # Currently _handle_ron calls check_win internally and sets result.winners = [player]
            # We need a _handle_ron_multiple capable of handling multiple winners

            return self._handle_ron_multiple(valid_ron_players)

        # 2. Check pon/kan
        pon_kan_players = [
            p
            for p, (a, _, _) in actions.items()
            if a in (GameAction.PON, GameAction.KAN)
        ]
        if pon_kan_players:
            # Only one player can pon/kan (except special rules, but usually only one discard)
            # If multiple (impossible unless tile set error), take first
            player = pon_kan_players[0]
            action, tile, kwargs = actions[player]
            if action == GameAction.PON:
                return self._handle_pon(player, tile, **kwargs)
            else:
                return self._handle_kan(player, tile, **kwargs)  # This is open_kan

        # 3. Check chi
        chi_players = [p for p, (a, _, _) in actions.items() if a == GameAction.CHI]
        if chi_players:
            player = chi_players[0]
            action, tile, kwargs = actions[player]
            return self._handle_chi(player, tile, **kwargs)

        # 4. All PASS
        # Advance turn
        result = ActionResult()
        self._advance_turn(result)
        return result

    def _handle_ron_multiple(self, winners: List[int]) -> ActionResult:
        """handle multiple ron"""
        result = ActionResult()
        result.winners = winners
        result.win_results = {}

        tile = self._last_discarded_tile
        if tile is None:
            raise ValueError("無捨牌")

        for player in winners:
            win_res = self.check_win(
                player, tile, is_rinshan=False
            )  # ron is not rinshan
            if win_res:
                result.win_results[player] = win_res

        # handle score settlement (simplified here, end directly)
        # Actually should call _process_win_scoring etc.
        # To maintain compatibility, do we call _handle_ron for first player then supplement?
        # No, set state directly
        self._phase = GamePhase.WINNING  # or ENDED
        # Need full settlement logic here, temporarily reuse part of _handle_ron logic
        # But _handle_ron only handles single person.
        # We assume demo_ui will handle result.win_results

        # Update scores
        # Note: In multiple winners, kyoutaku sticks (riichi_stick) distribution depends on rules (usually head_bump or split)
        # Simplified here: Each winner calculates score, deducted from discarder.

        loser = self._last_discarded_player

        for player in winners:
            win_res = result.win_results[player]
            points = win_res.points
            # Simple deduction
            self._game_state.update_score(loser, -points)
            self._game_state.update_score(player, points)

        # handle riichi_stick ownership (give to first winner)
        if self._game_state.riichi_sticks > 0:
            first_winner = winners[0]  # In order? check_multiple_ron returns order?
            # Assume check_multiple_ron is in counter-clockwise order
            self._game_state.update_score(
                first_winner, self._game_state.riichi_sticks * 1000
            )
            self._game_state.clear_riichi_sticks()

        # honba (Counter Sticks) - Usually added to each winner? Or only first?
        # Standard rule: honba only for head_bump. In double_ron, usually added to all? Or only first?
        # tenhou: double_ron both get honba.
        # Not handling complex honba logic here, assume calculated in check_win (check_win includes honba? Usually yes)

        return result

    def _handle_draw(
        self, player: int, tile: Optional[Tile] = None, **kwargs
    ) -> ActionResult:
        result = ActionResult()
        # Check hand tile count
        hand = self._hands[player]
        if not self._tile_set:
            raise ValueError("牌組未初始化")

        # Calculate kan count (each kan increases hand limit by 1)
        kan_count = sum(
            1
            for meld in hand.melds
            if meld.type in [MeldType.OPEN_KAN, MeldType.CLOSED_KAN]
        )
        limit = 14 + kan_count

        if hand.total_tile_count() >= limit:
            raise ValueError(f"手牌已達 {limit} 張，不能再摸牌")
        # Draw tile
        drawn_tile = self._tile_set.draw()
        if drawn_tile:
            hand.add_tile(drawn_tile)
            result.drawn_tile = drawn_tile
        if self._tile_set.is_exhausted():
            result.is_last_tile = True

        # Calculate and set waiting actions
        actions = self._calculate_turn_actions(player)
        self._waiting_for_actions = {player: actions}
        result.waiting_for = self._waiting_for_actions
        if not drawn_tile:
            self._phase = GamePhase.RYUUKYOKU
            result.ryuukyoku = RyuukyokuResult(
                ryuukyoku=True, ryuukyoku_type=RyuukyokuType.EXHAUSTIVE_DRAW
            )
        return result

    def _check_interrupts(
        self, tile: Tile, discarded_player: int
    ) -> Dict[int, List[GameAction]]:
        """Check if any player can call or ron on the discarded."""
        interrupts = {}

        # Check ron - All other players
        # Check pon/kan - All other players
        # Check chi - Next player only

        for i in range(self._num_players):
            if i == discarded_player:
                continue

            actions = []

            # ron
            if self._can_ron(i):
                actions.append(GameAction.RON)

            # pon/kan
            if self._can_pon(i):
                actions.append(GameAction.PON)
            if self._can_kan(i):
                actions.append(GameAction.KAN)

            # chi (Next player only)
            if (
                i - discarded_player
            ) % self._num_players != 1:  # Changed from == 1 to != 1 to match _can_chi logic
                pass  # Skip if not next player
            else:
                if self._can_chi(i):
                    actions.append(GameAction.CHI)

            if actions:
                # If there are actions, must include PASS option
                actions.append(GameAction.PASS)
                interrupts[i] = actions

        return interrupts

    def _handle_discard(
        self, player: int, tile: Optional[Tile] = None, **kwargs
    ) -> ActionResult:
        result = ActionResult()
        if tile is None:
            raise ValueError("打牌動作必須指定牌")
        if not self._tile_set:
            raise ValueError("牌組未初始化")

        hand = self._hands[player]

        # After riichi, can only discard the drawn tile (unless declare_ankan, but declare_ankan is handled in _handle_kan)
        if hand.is_riichi:
            if hand.last_drawn_tile and tile != hand.last_drawn_tile:
                raise ValueError("立直後只能打出剛摸到的牌")

        if hand.discard(tile):
            # Record discard and handle related effects (but do not advance turn)
            self._last_discarded_tile = tile
            self._last_discarded_player = player
            self._discard_history.append((player, tile))
            if len(self._discard_history) > 4:
                self._discard_history.pop(0)

            if self._riichi_ippatsu and player in self._riichi_ippatsu:
                if self._riichi_ippatsu_discard.get(player) == 1:
                    self._riichi_ippatsu[player] = False
                self._riichi_ippatsu_discard[player] += 1

            if self._tile_set.is_exhausted():
                result.is_last_tile = True

            result.discarded = True
            hand.reset_last_drawn_tile()  # Clear last drawn tile after discard

            # Check if other players can call or ron
            interrupts = self._check_interrupts(tile, player)

            if interrupts:
                # Enter waiting state.
                self._waiting_for_actions = interrupts
                result.waiting_for = interrupts
            else:
                # No calls were made, so advance the turn and draw automatically.
                self._advance_turn(result)

        return result

    def _advance_turn(self, result: ActionResult) -> None:
        """Advance the turn and draw automatically."""
        self._current_player = (self._current_player + 1) % self._num_players
        self._turn_count += 1
        self._is_first_turn_after_deal = False
        self._is_first_round = False

        # Draw automatically.
        draw_result = self._handle_draw(self._current_player)
        if draw_result.drawn_tile:
            result.drawn_tile = draw_result.drawn_tile
            if draw_result.waiting_for:
                result.waiting_for = draw_result.waiting_for
        elif draw_result.ryuukyoku:
            result.ryuukyoku = draw_result.ryuukyoku
            self._phase = GamePhase.RYUUKYOKU

    def _handle_pon(
        self, player: int, tile: Optional[Tile] = None, **kwargs
    ) -> ActionResult:
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
        hand.reset_last_drawn_tile()  # Clear the last drawn tile after a call.

        # A player must discard after calling.
        self._waiting_for_actions = {player: [GameAction.DISCARD]}
        result.waiting_for = self._waiting_for_actions
        return result

    def _handle_chi(
        self, player: int, tile: Optional[Tile] = None, **kwargs
    ) -> ActionResult:
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
        hand.reset_last_drawn_tile()  # Clear the last drawn tile after a call.

        # A player must discard after calling.
        self._waiting_for_actions = {player: [GameAction.DISCARD]}
        result.waiting_for = self._waiting_for_actions
        return result

    def _handle_riichi(
        self, player: int, tile: Optional[Tile] = None, **kwargs
    ) -> ActionResult:
        if tile is None:
            raise ValueError("立直必須同時打出一張牌")

        hand = self._hands[player]

        # Check whether discarding this tile leaves the hand in tenpai.
        # Simulate the discard.
        try:
            hand._tiles.remove(tile)
        except ValueError:
            raise ValueError("手牌中沒有這張牌")

        hand._tile_counts_cache = None
        is_tenpai = hand.is_tenpai()

        # Restore the hand.
        hand._tiles.append(tile)
        hand._tile_counts_cache = None

        if not is_tenpai:
            raise ValueError("立直打牌後必須聽牌")

        # Execute the discard.
        # _handle_discard handles both discard logic and follow-up flow.
        discard_result = self._handle_discard(player, tile, **kwargs)

        # Execute riichi.
        hand.set_riichi(True)
        self._game_state.add_riichi_stick()
        self._game_state.update_score(player, -1000)
        self._riichi_ippatsu[player] = True
        self._riichi_ippatsu_discard[player] = 0

        # Merge the results.
        discard_result.riichi = True
        return discard_result

    def _handle_kan(
        self, player: int, tile: Optional[Tile] = None, **kwargs
    ) -> ActionResult:
        result = ActionResult()
        hand = self._hands[player]

        # If tile is None, try to use the last discarded for open_kan.
        if tile is None:
            if self._last_discarded_tile is None:
                raise ValueError("明槓必須指定被槓的牌")
            tile = self._last_discarded_tile

        # Check if it's an open_kan on discard
        # Must be an interrupt (player != current_player)
        if (
            self._last_discarded_tile
            and tile == self._last_discarded_tile
            and player != self._current_player
        ):
            # Remove from discarder
            if self._last_discarded_player is not None:
                self._remove_last_discard(self._last_discarded_player, tile)

            # Clear last discard state
            self._last_discarded_tile = None
            self._last_discarded_player = None

        meld = hand.kan(tile)
        self._kan_count += 1
        result.kan = True
        hand.reset_last_drawn_tile()  # Clear the last drawn tile after kan.
        self._current_player = player

        self._interrupt_ippatsu(GameAction.KAN, acting_player=player)

        if self._draw_rinshan_tile(player, result, kan_type=meld.type):
            self._pending_kan_tile = None

        return result

    def _handle_declare_ankan(
        self, player: int, tile: Optional[Tile] = None, **kwargs
    ) -> ActionResult:
        result = ActionResult()
        hand = self._hands[player]

        candidates = hand.can_kan(None)
        if not candidates:
            raise ValueError("手牌無法暗槓")

        # Support multiple closed_kan choices.
        selected = None
        if tile:
            for candidate in candidates:
                # Check whether the candidate matches the requested tile.
                # closed_kan and added_kan use identical tiles, so the first tile is enough.
                if (
                    candidate.tiles
                    and candidate.tiles[0].suit == tile.suit
                    and candidate.tiles[0].rank == tile.rank
                ):
                    selected = candidate
                    break

            if selected is None:
                raise ValueError(f"無法暗槓指定的牌: {tile}")
        else:
            # If no tile was specified and multiple choices exist, use the first one.
            selected = candidates[0]
        is_add_kan = (
            selected.type == MeldType.OPEN_KAN and selected.called_tile is not None
        )

        if is_add_kan:
            kan_tile = selected.tiles[0]
            self._pending_kan_tile = (player, kan_tile)
            if chankan_winners := self._check_chankan(player, kan_tile):
                result.chankan = True
                result.winners = chankan_winners
                self._pending_kan_tile = None
                return result

        # Use the selected tiles for kan.
        meld = hand.kan(selected.tiles[0])
        if meld:
            self._kan_count += 1
        kan_type = meld.type if meld else MeldType.CLOSED_KAN

        if kan_type == MeldType.CLOSED_KAN:
            result.closed_kan = True
        else:
            result.kan = True

        self._interrupt_ippatsu(GameAction.DECLARE_ANKAN, acting_player=player)

        self._draw_rinshan_tile(player, result, kan_type=kan_type)
        if self._pending_kan_tile:
            self._pending_kan_tile = None
        hand.reset_last_drawn_tile()  # Clear the last drawn tile after kan.

        result.closed_kan = True
        return result

    def _handle_tsumo(
        self, player: int, tile: Optional[Tile] = None, **kwargs
    ) -> ActionResult:
        """
        Handle a tsumo win.

        Args:
            player (int): Winning player.
            tile (Optional[Tile]): Winning tile, normally the just-drawn tile.
            **kwargs: Additional parameters such as is_rinshan.

        Returns:
            ActionResult: ActionResult containing the win result.

        Raises:
            ValueError: If the player cannot win by tsumo.
        """
        result = ActionResult()
        hand = self._hands[player]

        # Get the winning tile, normally the tile just drawn by this player.
        if tile is None:
            # Use the last drawn tile.
            if hand.last_drawn_tile:
                tile = hand.last_drawn_tile
            else:
                raise ValueError("無法確定自摸的牌")

        # Check whether the player can win by tsumo.
        is_rinshan = kwargs.get("is_rinshan", False)
        win_result = self.check_win(player, tile, is_rinshan=is_rinshan)

        if win_result is None:
            raise ValueError(f"玩家 {player} 無法用 {tile} 自摸和牌")

        # Apply score changes.
        self.apply_win_score(win_result)

        # Set the result.
        result.winners = [player]
        result.rinshan_win = win_result if is_rinshan else None
        result.win_results[player] = win_result

        # Move to winning phase.
        self._phase = GamePhase.WINNING

        return result

    def _handle_ron(
        self, player: int, tile: Optional[Tile] = None, **kwargs
    ) -> ActionResult:
        """
        Handle ron, including multiple ron.

        Args:
            player (int): Player declaring ron, possibly one of multiple winners.
            tile (Optional[Tile]): Winning tile, normally the last discarded.
            **kwargs: Additional parameters.

        Returns:
            ActionResult: ActionResult containing the win result.

        Raises:
            ValueError: If the player cannot win by ron.
        """
        result = ActionResult()

        # Get the tile won by ron, normally the last discarded.
        if self._last_discarded_tile is None or self._last_discarded_player is None:
            raise ValueError("沒有可榮和的捨牌")

        winning_tile = self._last_discarded_tile
        discarder = self._last_discarded_player

        # Check for multiple ron.
        potential_winners = self.check_multiple_ron(winning_tile, discarder)

        # Check whether sancha_ron aborts the round.
        if len(potential_winners) == 0:
            # An empty list means sancha_ron triggered an abortive draw.
            result.ryuukyoku = RyuukyokuResult(
                ryuukyoku=True, ryuukyoku_type=RyuukyokuType.SANCHA_RON
            )
            result.success = True
            result.phase = GamePhase.ENDED
            self._phase = GamePhase.ENDED
            return result

        # Verify that this player is allowed to declare ron.
        if player not in potential_winners:
            raise ValueError(f"玩家 {player} 不能榮和（配置限制或振聽）")

        # Process all winners.
        winners = potential_winners
        for winner in winners:
            win_result = self.check_win(winner, winning_tile, is_chankan=False)
            if win_result:
                self.apply_win_score(win_result)
                result.win_results[winner] = win_result

        # Set the result.
        result.winners = winners

        # Move to winning phase.
        self._phase = GamePhase.WINNING

        return result

    def end_round(self, winners: Optional[List[int]] = None) -> None:
        """
        End the current round.

        Args:
            winners (Optional[List[int]]): Winning players, or None for ryuukyoku.
                - Single ron or tsumo: [player_id]
                - double_ron or triple_ron: [player1, player2, player3]
        """
        if winners is not None and len(winners) > 0:
            # Handle a winning round.
            dealer = self._game_state.dealer
            # If any winner is the dealer, the dealer repeats.
            dealer_won = dealer in winners

            # Update dealer.
            self._game_state.next_dealer(dealer_won)

            # Check tobi.
            if self._check_tobi():
                self._phase = GamePhase.ENDED
                return

            # Check agari_yame.
            # If the dealer wins the final round while in first place, end the game.
            if dealer_won and self._game_state.ruleset.agari_yame:
                is_final_round = (
                    self._game_state.round_wind == Wind.SOUTH
                    and self._game_state.round_number == 4
                ) or (
                    self._game_state.round_wind == Wind.WEST
                    and self._game_state.round_number == 4
                )
                if is_final_round:
                    max_score = max(self._game_state.scores)
                    if self._game_state.scores[dealer] == max_score:
                        self._phase = GamePhase.ENDED
                        return

            # If the dealer did not win, advance to the next round.
            if not dealer_won:
                has_next = self._game_state.next_round()
                if not has_next:
                    self._phase = GamePhase.ENDED
        else:
            # Handle ryuukyoku.
            # On exhaustive_draw, check nagashi_mangan and noten_bappu.
            if self._tile_set and self._tile_set.is_exhausted():
                # Check nagashi_mangan.
                flow_mangan_players = []
                for i in range(self._num_players):
                    if self._check_nagashi_mangan(i):
                        flow_mangan_players.append(i)

                if flow_mangan_players:
                    # Apply nagashi_mangan score changes.
                    for winner in flow_mangan_players:
                        is_dealer = winner == self._game_state.dealer
                        payment = 4000 if is_dealer else 2000

                        # All players except the winner pay.
                        for i in range(self._num_players):
                            if i == winner:
                                continue

                            # Dealer pays more when the winner is not dealer.
                            pay_amount = payment
                            if not is_dealer and i == self._game_state.dealer:
                                pay_amount = 4000

                            self._game_state.update_score(i, -pay_amount)
                            self._game_state.update_score(winner, pay_amount)
                else:
                    # Calculate noten_bappu only when there is no nagashi_mangan.
                    self._calculate_noten_bappu()

            # Check tobi.
            if self._check_tobi():
                self._phase = GamePhase.ENDED
                return

            dealer_won = False  # Dealer does not repeat on ryuukyoku here.
            self._game_state.next_dealer(dealer_won)

            has_next = self._game_state.next_round()
            if not has_next:
                self._phase = GamePhase.ENDED

    def _handle_declare_kyuushu_kyuuhai(
        self, player: int, tile: Optional[Tile] = None, **kwargs
    ) -> ActionResult:
        """
        Handle a kyuushu_kyuuhai abortive draw.
        """
        if not self._check_kyuushu_kyuuhai(player):
            raise ValueError("不滿足九種九牌流局條件")

        result = ActionResult()
        result.ryuukyoku = RyuukyokuResult(
            ryuukyoku=True,
            ryuukyoku_type=RyuukyokuType.KYUUSHU_KYUUHAI,
            kyuushu_kyuuhai_player=player,
        )
        self._phase = GamePhase.RYUUKYOKU
        return result

    def _remove_last_discard(self, discarder: int, tile: Tile) -> None:
        self._hands[discarder].remove_last_discard(tile)
        if self._discard_history and self._discard_history[-1] == (discarder, tile):
            self._discard_history.pop()
        # Mark this player's discard as called, which affects nagashi_mangan.
        self._has_called_discard[discarder] = True

    def _draw_rinshan_tile(
        self, player: int, result: ActionResult, *, kan_type: MeldType
    ) -> bool:
        if not self._tile_set:
            return False

        hand = self._hands[player]
        if rinshan_tile := self._tile_set.draw_rinshan():
            hand.add_tile(rinshan_tile)
            result.rinshan_tile = rinshan_tile
            if kan_type == MeldType.OPEN_KAN:
                result.kan = True
            else:
                result.closed_kan = True

            if rinshan_win := self._check_rinshan_win(player, rinshan_tile):
                result.rinshan_win = rinshan_win
                self._ignore_suukan_sanra = True
                self._phase = GamePhase.WINNING
            else:
                # Calculate and set waiting actions.
                actions = self._calculate_turn_actions(player)
                self._waiting_for_actions = {player: actions}
                result.waiting_for = self._waiting_for_actions
            return True

        self._phase = GamePhase.RYUUKYOKU
        result.ryuukyoku = RyuukyokuResult(
            ryuukyoku=True, ryuukyoku_type=RyuukyokuType.EXHAUSTIVE_DRAW
        )
        return False

    def _apply_discard_effects(
        self, player: int, tile: Tile, result: ActionResult
    ) -> None:
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
        self,
        player: int,
        winning_tile: Tile,
        is_chankan: bool = False,
        is_rinshan: bool = False,
    ) -> Optional[WinResult]:
        """
        Check whether the player can win.

        Args:
            player (int): Player position.
            winning_tile (Tile): Winning tile.
            is_chankan (bool): Whether this is chankan.
            is_rinshan (bool): Whether this is rinshan.

        Returns:
            Optional[WinResult]: Win result with yaku and score, or None if the hand cannot win.
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

        # Get winning combinations.
        combinations = hand.get_winning_combinations(winning_tile, is_tsumo)
        if not combinations:
            return None

        # Check furiten for ron; furiten players can still win by tsumo.
        if not is_tsumo and self.is_furiten(player):
            return None

        # Check ippatsu.
        is_ippatsu = self._riichi_ippatsu.get(player, False)

        # Check whether this is the first turn.
        is_first_turn = self._is_first_turn_after_deal
        # Check whether this is the last tile.
        is_last_tile = self._tile_set.is_exhausted() if self._tile_set else False
        # Check renhou context.

        # Count dora.
        dora_count = self._count_dora(player, winning_tile)

        # Apply highest-score selection across all possible winning combinations.
        best_score_result = None
        best_yaku_results = None
        best_winning_combination = None

        # Special hands such as chiitoitsu or kokushi_musou may use an empty combination.
        combinations_to_check = combinations if combinations else [[]]

        for winning_combination in combinations_to_check:
            # Check yaku.
            yaku_results = self._yaku_checker.check_all(
                hand,
                winning_tile,
                winning_combination,
                self._game_state,
                is_tsumo=is_tsumo,
                is_ippatsu=is_ippatsu,
                is_first_turn=is_first_turn,
                is_last_tile=is_last_tile,
                player_position=player,
                is_rinshan=is_rinshan,
                is_chankan=is_chankan,
            )
            if not yaku_results:
                continue

            # Calculate score.
            score_result = self._score_calculator.calculate(
                hand,
                winning_tile,
                winning_combination,
                yaku_results,
                dora_count,
                self._game_state,
                is_tsumo,
                player_position=player,
            )

            # Update the best score.
            if (
                best_score_result is None
                or score_result.total_points > best_score_result.total_points
            ):
                best_score_result = score_result
                best_yaku_results = yaku_results
                best_winning_combination = winning_combination
            elif score_result.total_points == best_score_result.total_points:
                # If scores tie, prefer higher han.
                if score_result.han > best_score_result.han:
                    best_score_result = score_result
                    best_yaku_results = yaku_results
                    best_winning_combination = winning_combination
                # If han also ties, prefer higher fu.
                elif (
                    score_result.han == best_score_result.han
                    and score_result.fu > best_score_result.fu
                ):
                    best_score_result = score_result
                    best_yaku_results = yaku_results
                    best_winning_combination = winning_combination
                # Keep checking all combinations for simple and consistent selection.

        if best_score_result is None:
            return None

        # Determine pao responsibility.
        pao_player = None
        for result in best_yaku_results:
            if result.yaku == Yaku.DAISANGEN:
                pao_player = self._pao_daisangen.get(player)
                if pao_player is not None:
                    break
            elif result.yaku == Yaku.DAISUUSHI:
                pao_player = self._pao_daisuushi.get(player)
                if pao_player is not None:
                    break

        # Recalculate score with pao applied.
        score_result = self._score_calculator.calculate(
            hand,
            winning_tile,
            best_winning_combination,
            best_yaku_results,
            dora_count,
            self._game_state,
            is_tsumo,
            player,
            pao_player=pao_player,
        )

        score_result.payment_to = player
        # Set payer for ron.
        if not is_tsumo and self._last_discarded_player is not None:
            score_result.payment_from = self._last_discarded_player
        elif is_chankan and self._pending_kan_tile:
            # For chankan, the kan player pays.
            kan_player, _ = self._pending_kan_tile
            score_result.payment_from = kan_player

        if self._kan_count >= 4:
            self._ignore_suukan_sanra = True

        return WinResult(
            win=True,
            player=player,
            yaku=best_yaku_results,
            han=score_result.han,
            fu=score_result.fu,
            points=score_result.total_points,
            score_result=score_result,
            chankan=is_chankan or None,
            rinshan=is_rinshan or None,
        )

    def check_multiple_ron(self, discarded_tile: Tile, discarder: int) -> List[int]:
        """
        Check whether multiple players can ron the same discard.

        Return eligible ron winners according to configuration:
        - head_bump_only=True: return only the closest next player
        - allow_double_ron=True: return up to two players
        - allow_triple_ron=False and three players win: return an empty list to trigger ryuukyoku
        - allow_triple_ron=True and three players win: return three players

        Args:
            discarded_tile (Tile): Discarded Tile.
            discarder (int): Discarding player.

        Returns:
            List[int]: Eligible winners in turn order, with the closest next player first.
        """
        # Collect all players who can ron, excluding the discarder.
        potential_winners = []

        for offset in range(1, self._num_players):
            player = (discarder + offset) % self._num_players

            # Check whether this player can ron.
            win_result = self.check_win(
                player, discarded_tile, is_chankan=False, is_rinshan=False
            )
            if win_result is not None:
                potential_winners.append(player)

        # Return immediately when no one can ron.
        if not potential_winners:
            return []

        # Return immediately for a single winner.
        if len(potential_winners) == 1:
            return potential_winners

        # Handle multiple winners according to the ruleset.
        ruleset = self._game_state.ruleset

        # Check sancha_ron first because it may trigger ryuukyoku.
        if len(potential_winners) >= 3:
            # If triple_ron is disabled, return empty to trigger sancha_ron ryuukyoku.
            if not ruleset.allow_triple_ron:
                return []  # Trigger ryuukyoku.
            # If triple_ron is enabled, return up to three players.
            return potential_winners[:3]

        # head_bump mode allows only the closest next player to win.
        if ruleset.head_bump_only:
            # Return the closest next player.
            return [potential_winners[0]]

        # double_ron case with head_bump_only disabled.
        if len(potential_winners) == 2:
            if ruleset.allow_double_ron:
                return potential_winners
            else:
                # If double_ron is disabled, return the closest next player.
                return [potential_winners[0]]

        return potential_winners

    def _check_kyuushu_kyuuhai(self, player: int) -> bool:
        """
        Check whether kyuushu_kyuuhai abort conditions are met.

        Conditions:
        1. It must be the player's first turn.
        2. No player has called, including closed_kan.
        3. The hand has at least nine unique yaochuu tiles.
        """
        # It must be this player's turn.
        if player != self._current_player:
            return False

        # It must be the player's first turn before any discard.
        if len(self._hands[player].discards) > 0:
            return False

        # No melds, including closed_kan, may be on the table.
        for i in range(self._num_players):
            if len(self._hands[i].melds) > 0:
                return False

        # The hand must have at least nine unique yaochuu tiles.
        hand = self._hands[player]
        unique_yaochuu = {t for t in hand.tiles if t.is_yaochuu}
        return len(unique_yaochuu) >= 9

    def check_ryuukyoku(self) -> Optional[RyuukyokuType]:
        """
        Check whether the round ends in ryuukyoku.

        Returns:
            Optional[RyuukyokuType]: Ryuukyoku type, or None otherwise.
        """
        # Check suufon_renda first because it can happen on the first turn.
        if self._check_suufon_renda():
            return RyuukyokuType.SUUFON_RENDA

        # Check sancha_ron.
        if self._check_sancha_ron():
            return RyuukyokuType.SANCHA_RON

        # Check suukan_sanra after four kan.
        if self._kan_count >= 4 and not self._ignore_suukan_sanra:
            return RyuukyokuType.SUUKAN_SANRA

        # exhaustive_draw when the live wall is empty.
        if self._tile_set and self._tile_set.is_exhausted():
            return RyuukyokuType.EXHAUSTIVE_DRAW

        # Check whether all players are in riichi.
        return RyuukyokuType.SUUCHA_RIICHI if self._check_all_riichi() else None

    def _check_all_riichi(self) -> bool:
        """Check whether all players have declared riichi."""
        if self._phase != GamePhase.PLAYING:
            return False

        return all(hand.is_riichi for hand in self._hands)

    def _check_suufon_renda(self) -> bool:
        """
        Check suufon_renda, where the first four discards are the same wind.

        Returns:
            bool: True if suufon_renda applies.
        """
        # At least four discards are required.
        if len(self._discard_history) < 4:
            return False

        # Check whether the first four discards are the same wind tile.
        first_tile = self._discard_history[0][1]

        # It must be a wind tile: honor ranks 1-4.
        if first_tile.suit != Suit.HONORS or not (1 <= first_tile.rank <= 4):
            return False

        return not any(
            tile.suit != Suit.HONORS or tile.rank != first_tile.rank
            for _, tile in self._discard_history[:4]
        )

    def _check_nagashi_mangan(self, player: int) -> bool:
        """
        Check whether nagashi_mangan conditions are met.

        Conditions:
        1. Every discard is yaochuu.
        2. None of the discards has been called.
        """
        # Check whether any discard was called.
        if self._has_called_discard[player]:
            return False

        hand = self._hands[player]
        discards = hand.discards

        # At least one discard is required.
        if not discards:
            return False

        # Check whether every discard is yaochuu.
        return all(tile.is_yaochuu for tile in discards)

    def _count_dora(self, player: int, winning_tile: Optional[Tile] = None) -> int:
        """
        Count dora.

        Args:
            player: Player position.
            winning_tile: Winning tile.

        Returns:
            Dora han from dora, ura_dora, and red_dora.
        """
        if not self._tile_set:
            return 0

        dora_count = 0
        hand = self._hands[player]

        # Collect all tiles, including the winning tile when provided.
        all_tiles = hand.tiles + [winning_tile] if winning_tile else hand.tiles

        # Dora.
        if dora_indicators := self._tile_set.get_dora_indicators(self._kan_count):
            for dora_indicator in dora_indicators:
                dora_tile = self._tile_set.get_dora(dora_indicator)
                if dora_tile in all_tiles:
                    dora_count += 1

        # Ura_dora when in riichi.
        if hand.is_riichi:
            if ura_indicators := self._tile_set.get_ura_dora_indicators(
                self._kan_count
            ):
                for ura_indicator in ura_indicators:
                    ura_dora_tile = self._tile_set.get_dora(ura_indicator)
                    if ura_dora_tile in all_tiles:
                        dora_count += 1

        # red_dora.
        for tile in all_tiles:
            if tile.is_red_dora:
                dora_count += 1

        return dora_count

    def get_hand(self, player: int) -> Hand:
        """
        Get a player's hand.

        Args:
            player (int): Player position.

        Returns:
            Hand: Player hand object.

        Raises:
            ValueError: If player position is invalid.
        """
        if not (0 <= player < self._num_players):
            raise ValueError(f"玩家位置必須在 0-{self._num_players - 1} 之間")
        return self._hands[player]

    def get_game_state(self) -> GameState:
        """
        Get the game state.

        Returns:
            GameState: Game state object.
        """
        return self._game_state

    def get_discards(self, player: int) -> List[Tile]:
        """
        Get a player's discards.

        Args:
            player (int): Player position.

        Returns:
            List[Tile]: Player discard list.

        Raises:
            ValueError: If player position is invalid.
        """
        if not (0 <= player < self._num_players):
            raise ValueError(f"玩家位置必須在 0-{self._num_players - 1} 之間")
        return self._hands[player].discards

    def get_last_discard(self) -> Optional[Tile]:
        """
        Get the latest unprocessed discarded.

        Returns:
            Optional[Tile]: Latest discarded.
        """
        return self._last_discarded_tile

    def get_num_players(self) -> int:
        """
        Get the number of players.

        Returns:
            int: Number of players.
        """
        return self._num_players

    def get_wall_remaining(self) -> Optional[int]:
        """
        Get the number of tiles remaining in the live wall.

        Returns:
            Optional[int]: Number of live-wall tiles remaining.
        """
        return self._tile_set.remaining if self._tile_set else None

    def get_revealed_dora_indicators(self) -> List[Tile]:
        """
        Get currently revealed dora indicators.

        Returns:
            List[Tile]: Revealed dora indicator tiles.
        """
        return self._tile_set.get_dora_indicators() if self._tile_set else []

    def get_available_chi_sequences(self, player: int) -> List[List[Tile]]:
        """
        Get available chi sequences for the player against the kamicha discard.

        Args:
            player (int): Player position.

        Returns:
            List[List[Tile]]: Available chi sequences.
        """

        if self._last_discarded_tile is None or self._last_discarded_player is None:
            return []
        if (player - self._last_discarded_player) % self._num_players != 1:
            return []
        hand = self._hands[player]
        return [
            seq.copy() for seq in hand.can_chi(self._last_discarded_tile, from_player=0)
        ]

    def handle_ryuukyoku(self) -> RyuukyokuResult:
        """
        Handle ryuukyoku.

        Returns:
            RyuukyokuResult: Result containing type and nagashi_mangan players.
        """
        ryuukyoku_type = self.check_ryuukyoku()
        if not ryuukyoku_type:
            return RyuukyokuResult(ryuukyoku=False)

        result = RyuukyokuResult(
            ryuukyoku=True,
            ryuukyoku_type=ryuukyoku_type,
        )

        # Check nagashi_mangan.
        if ryuukyoku_type == RyuukyokuType.EXHAUSTIVE_DRAW:
            for i in range(self._num_players):
                if self.check_flow_mangan(i):
                    result.flow_mangan_players.append(i)
                    # nagashi_mangan: 3000 points.
                    self._game_state.update_score(i, 3000)
                    for j in range(self._num_players):
                        if j != i:
                            self._game_state.update_score(j, -1000)

        # Handle kyuushu_kyuuhai on the first turn.
        # Check whether kyuushu_kyuuhai can abort on the first turn.
        if self._is_first_turn_after_deal:
            for i in range(self._num_players):
                if self._check_kyuushu_kyuuhai(i):
                    result.ryuukyoku_type = RyuukyokuType.KYUUSHU_KYUUHAI
                    result.kyuushu_kyuuhai_player = i
                    # Dealer repeats on kyuushu_kyuuhai.
                    break

        # Handle all-riichi ryuukyoku.
        if ryuukyoku_type == RyuukyokuType.SUUCHA_RIICHI:
            # On all-riichi ryuukyoku, dealer pays 300 points to each non-dealer.
            dealer = self._game_state.dealer
            for i in range(self._num_players):
                if i != dealer:
                    self._game_state.transfer_points(dealer, i, 300)

        self._phase = GamePhase.RYUUKYOKU
        return result

    def apply_win_score(self, win_result: WinResult) -> None:
        """
        Apply score changes for a win.

        Args:
            win_result (WinResult): Win result.
        """
        score_result = win_result.score_result
        if not score_result:
            return

        winner = (
            win_result.player if hasattr(win_result, "player") else self._current_player
        )
        # Older callers may not provide player context, so payment_to is authoritative.

        winner = score_result.payment_to

        # Add points to the winner.
        self._game_state.update_score(winner, score_result.total_points)

        # Deduct points from losers.
        if score_result.is_tsumo:
            # tsumo.
            if score_result.pao_player is not None and score_result.pao_payment > 0:
                # pao tsumo: the responsible player pays everything.
                self._game_state.update_score(
                    score_result.pao_player, -score_result.pao_payment
                )
            else:
                # Normal tsumo.
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
            # ron.
            loser = score_result.payment_from

            if score_result.pao_player is not None and score_result.pao_payment > 0:
                # pao ron: split payment.
                # The responsible player pays pao_payment.
                self._game_state.update_score(
                    score_result.pao_player, -score_result.pao_payment
                )

                # The discarder pays the remainder.
                # Total payment = total_points - riichi_sticks.
                total_pay = score_result.total_points - score_result.riichi_sticks_bonus
                remaining_pay = total_pay - score_result.pao_payment
                self._game_state.update_score(loser, -remaining_pay)
            else:
                # Normal ron.
                # The discarder pays total_points minus riichi_sticks.
                # total_points includes riichi_sticks from the table, not from the discarder.
                # The discarder pays only base plus honba.
                # score_result.total_points = base + honba + sticks
                payment = score_result.total_points - score_result.riichi_sticks_bonus
                self._game_state.update_score(loser, -payment)

        # Clear riichi_sticks.
        if score_result.riichi_sticks_bonus > 0:
            self._game_state.clear_riichi_sticks()

        # honba is handled by next_dealer; this method only updates scores.

    def _check_chankan(self, kan_player: int, kan_tile: Tile) -> List[int]:
        """
        Check chankan, where other players can ron the kan tile.

        Args:
            kan_player: Player declaring kan.
            kan_tile: Tile used for kan.

        Returns:
            Players who can win by chankan.
        """
        winners = []
        for player in range(self._num_players):
            if player == kan_player:
                continue  # Cannot chankan on your own kan.

            if self.check_win(player, kan_tile, is_chankan=True):
                winners.append(player)

        return winners

    def _interrupt_ippatsu(self, action: GameAction, acting_player: int) -> None:
        """Interrupt ippatsu after a meld or kan."""
        if not self._riichi_ippatsu:
            return

        if action not in {
            GameAction.CHI,
            GameAction.PON,
            GameAction.KAN,
            GameAction.DECLARE_ANKAN,
        }:
            return

        if not self._game_state.ruleset.ippatsu_interrupt_on_meld_or_kan:
            return

        for player in self._riichi_ippatsu.keys():
            self._riichi_ippatsu[player] = False
            self._riichi_ippatsu_discard[player] = 0

    def _check_sancha_ron(self) -> bool:
        """
        Check whether sancha_ron applies.

        If three or more players can ron the same discard, the round can end in ryuukyoku.

        Returns:
            bool: True if sancha_ron applies.
        """
        if self._last_discarded_tile is None or self._last_discarded_player is None:
            return False

        # Count how many players can ron this tile.
        winning_players = []
        for player in range(self._num_players):
            if player == self._last_discarded_player:
                continue  # Cannot ron your own discard.

            if self.check_win(player, self._last_discarded_tile):
                winning_players.append(player)

        # Three or more ron winners means sancha_ron.
        return len(winning_players) >= 3

    def _check_rinshan_win(
        self, player: int, rinshan_tile: Tile
    ) -> Optional[WinResult]:
        """
        Check rinshan after drawing from the dead wall.

        Args:
            player: Player position.
            rinshan_tile: Tile drawn from rinshan.

        Returns:
            Win result, or None if the player cannot win.
        """
        return self.check_win(player, rinshan_tile, is_rinshan=True)

    def _calculate_noten_bappu(self) -> Dict[int, int]:
        """
        Calculate noten_bappu.

        Returns:
            Score deltas by player index.
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
            # One tenpai player: +3000 / -1000.
            winner = tenpai_players[0]
            changes[winner] = 3000
            for i in range(self._num_players):
                if i != winner:
                    changes[i] = -1000

        elif num_tenpai == 2:
            # Two tenpai players: +1500 / -1500.
            for i in range(self._num_players):
                if i in tenpai_players:
                    changes[i] = 1500
                else:
                    changes[i] = -1500

        elif num_tenpai == 3:
            # Three tenpai players: +1000 / -3000.
            loser = [i for i in range(self._num_players) if i not in tenpai_players][0]
            changes[loser] = -3000
            for i in tenpai_players:
                changes[i] = 1000

        # Apply score changes.
        for player, delta in changes.items():
            self._game_state.update_score(player, delta)

        return changes

    def check_furiten_discards(self, player: int) -> bool:
        """
        Check genbutsu furiten: the player's discards include a winning tile.

        Args:
            player: Player position.

        Returns:
            bool: True if the player is in discard-based furiten.
        """
        hand = self._hands[player]

        # A player who is not in tenpai cannot be furiten.
        if not hand.is_tenpai():
            return False

        # Get machi tiles.
        machi_tiles = hand.get_machi_tiles()
        if not machi_tiles:
            return False

        # Check the player's discard history.
        for discard in hand.discards:
            # If any discard is a machi tile, the player is in genbutsu furiten.
            if any(
                discard.suit == machi_tile.suit and discard.rank == machi_tile.rank
                for machi_tile in machi_tiles
            ):
                return True

        return False

    def check_furiten_temp(self, player: int) -> bool:
        """
        Check temp_furiten after passing on ron in the same turn cycle.

        Args:
            player: Player position.

        Returns:
            bool: True if the player is in temp_furiten.
        """
        # Check whether temp_furiten was set.
        if not self._furiten_temp.get(player, False):
            return False

        # Check whether it is the same turn cycle.
        furiten_round = self._furiten_temp_round.get(player, -1)
        return furiten_round == self._turn_count

    def check_furiten_riichi(self, player: int) -> bool:
        """
        Check riichi furiten after passing on ron during riichi.

        Args:
            player: Player position.

        Returns:
            bool: True if the player is in riichi furiten.
        """
        return self._furiten_permanent.get(player, False)

    def is_furiten(self, player: int) -> bool:
        """
        Check whether the player is in any furiten state.

        Args:
            player: Player position.

        Returns:
            bool: True if the player is furiten.
        """
        return (
            self.check_furiten_discards(player)
            or self.check_furiten_temp(player)
            or self.check_furiten_riichi(player)
        )

    def _check_tobi(self) -> bool:
        """
        Check whether tobi is triggered.

        Returns:
            bool: True if any score is below zero.
        """
        if not self._game_state.ruleset.tobi_enabled:
            return False

        for score in self._game_state.scores:
            if score < 0:
                return True

        return False
