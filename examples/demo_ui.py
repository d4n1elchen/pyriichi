"""
PyRiichi Demo UI

提供一個最小化的 Tkinter 視覺介面示例，演示如何使用 PyRiichi
的 `RuleEngine` 進行基本的摸打流程。玩家（0 號）透過介面操作，
其餘三名對手僅會隨機摸牌並打出一張牌。

注意：此示例只cover最基本的流程，未實作鳴牌、和牌等完整規則，
僅供快速體驗 API 使用方式。
"""

import random
import tkinter as tk
from typing import Iterable, Optional

from pyriichi.hand import Meld
from pyriichi.rules import GameAction, GamePhase, RuleEngine, WinResult
from pyriichi.tiles import Tile, Suit


CHINESE_NUMERALS = {
    1: "一",
    2: "二",
    3: "三",
    4: "四",
    5: "五",
    6: "六",
    7: "七",
    8: "八",
    9: "九",
}

SUIT_CHINESE = {
    Suit.MANZU: "萬",
    Suit.PINZU: "筒",
    Suit.SOZU: "索",
}

HONOR_CHINESE = {
    1: "東",
    2: "南",
    3: "西",
    4: "北",
    5: "白",
    6: "發",
    7: "中",
}


MELD_TYPE_TEXT = {
    "chi": "吃",
    "pon": "碰",
    "kan": "槓",
    "ankan": "暗槓",
}


def tile_to_chinese(tile: Tile) -> str:
    """將牌轉換為中文表示。"""

    prefix = "赤" if tile.is_red else ""

    if tile.suit == Suit.JIHAI:
        return prefix + HONOR_CHINESE.get(tile.rank, f"字{tile.rank}")

    numeral = CHINESE_NUMERALS.get(tile.rank, str(tile.rank))
    suit = SUIT_CHINESE.get(tile.suit, tile.suit.value)
    return prefix + numeral + suit


def tile_to_vertical_text(tile: Tile) -> str:
    """將牌轉換為垂直顯示的文字。"""

    text = tile_to_chinese(tile)
    return "\n".join(text)


def format_tiles_chinese(tiles: Iterable[Tile]) -> str:
    """將多張牌格式化為中文字串。"""

    tile_list = list(tiles)
    if not tile_list:
        return "(無)"
    return " ".join(tile_to_chinese(tile) for tile in tile_list)


def meld_to_chinese(meld: Meld) -> str:
    kind = MELD_TYPE_TEXT.get(meld.meld_type.value, meld.meld_type.value)
    tiles_text = " ".join(tile_to_chinese(tile) for tile in meld.tiles)
    return f"{kind}({tiles_text})"


class MahjongDemoUI:
    """簡易立直麻將 Demo UI。"""

    def __init__(self, human_player: int = 0, ai_delay_ms: int = 600) -> None:
        self.human_player = human_player
        self.ai_players = [i for i in range(4) if i != human_player]
        self.ai_delay_ms = ai_delay_ms

        self.engine = RuleEngine(num_players=4)

        self.root = tk.Tk()
        self.root.title("PyRiichi Demo UI")

        self.last_drawn_tile: Optional[Tile] = None
        self._cached_tsumo_result: Optional[WinResult] = None

        self.info_label = tk.Label(self.root, text="初始化中...")
        self.info_label.pack(pady=8)

        controls_frame = tk.Frame(self.root)
        controls_frame.pack(pady=4)

        self.draw_button = tk.Button(controls_frame, text="摸牌", command=self.draw_tile)
        self.draw_button.pack(side=tk.LEFT, padx=4)

        reset_button = tk.Button(controls_frame, text="重新開始", command=self.start_new_round)
        reset_button.pack(side=tk.LEFT, padx=4)

        self.reaction_frame = tk.Frame(self.root)
        self.reaction_frame.pack(fill=tk.X, padx=8, pady=4)

        self.hand_frame = tk.Frame(self.root)
        self.hand_frame.pack(padx=8, pady=8)

        self.opponents_frame = tk.Frame(self.root)
        self.opponents_frame.pack(fill=tk.X, padx=8, pady=4)

        log_frame = tk.Frame(self.root)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        log_label = tk.Label(log_frame, text="遊戲記錄")
        log_label.pack(anchor=tk.W)

        self.log_text = tk.Text(log_frame, height=16, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.pending_reaction = None

        self.start_new_round()

    # ------------------------------------------------------------------
    # 遊戲流程控制
    # ------------------------------------------------------------------
    def start_new_round(self) -> None:
        """初始化並發牌。"""

        self.engine.start_game()
        self.engine.start_round()
        hands = self.engine.deal()

        self.last_drawn_tile = None
        self._cached_tsumo_result = None
        self.clear_reaction_options()
        self.log("新的一局開始！莊家為玩家 {}".format(self.engine.get_game_state().dealer))
        self.log("你的起始手牌: {}".format(format_tiles_chinese(hands[self.human_player])))

        self.refresh_ui()
        self.schedule_next_turn()

    def schedule_next_turn(self) -> None:
        """排程下一位玩家的行動。"""

        if self.engine.get_phase() != GamePhase.PLAYING:
            self.end_round_if_needed()
            return

        current = self.engine.get_current_player()
        self.update_info_label()

        self.refresh_hand_ui(enable=current == self.human_player)
        self.update_controls()

        if current == self.human_player:
            # 僅自動摸牌，打牌仍由玩家操作
            self.root.after(self.ai_delay_ms // 2, self.auto_human_draw)
        else:
            self.root.after(self.ai_delay_ms, self.ai_take_turn)

    def auto_human_draw(self) -> None:
        if self.engine.get_phase() != GamePhase.PLAYING:
            self.end_round_if_needed()
            return

        if self.pending_reaction:
            return

        hand = self.engine.get_hand(self.human_player)
        if hand.total_tile_count() < 14 and self.engine.can_act(self.human_player, GameAction.DRAW):
            self.draw_tile()
        else:
            # 若無法自動摸牌，恢復玩家手動操作
            self.refresh_hand_ui(enable=True)
            self.update_controls()
            self._cached_tsumo_result = None

    def end_round_if_needed(self, extra_message: Optional[str] = None) -> None:
        """若遊戲階段已經結束，停用操作並顯示訊息。"""

        phase = self.engine.get_phase()
        if phase == GamePhase.PLAYING:
            return

        self.clear_reaction_options()

        if extra_message:
            self.log(extra_message)

        if phase == GamePhase.DRAW:
            self.log("本局流局，請重新開始。")
        elif phase == GamePhase.WINNING:
            self.log("出現和牌，示例在此結束。")
        else:
            self.log("遊戲階段：{}".format(phase.value))

        self.refresh_hand_ui(enable=False)
        self.update_controls()

    # ------------------------------------------------------------------
    # 玩家操作
    # ------------------------------------------------------------------
    def draw_tile(self) -> None:
        """玩家摸牌。"""

        hand = self.engine.get_hand(self.human_player)
        if hand.total_tile_count() >= 14:
            self.log("手牌已達 14 張，請先打出一張牌。")
            return

        if not self.engine.can_act(self.human_player, GameAction.DRAW):
            self.log("目前無法摸牌。")
            return

        result = self.engine.execute_action(self.human_player, GameAction.DRAW)
        if result.draw:
            self.log("牌山耗盡，流局！")
            self.last_drawn_tile = None
            self._cached_tsumo_result = None
            self.end_round_if_needed()
            return

        if result.drawn_tile is not None:
            self.log("你摸到了 {}".format(tile_to_chinese(result.drawn_tile)))
            self.last_drawn_tile = result.drawn_tile
        else:
            self.last_drawn_tile = None

        if result.is_last_tile:
            self.log("這是海底最後一張牌。")

        self._cached_tsumo_result = None
        self.refresh_ui()

    def discard_tile(self, tile) -> None:
        """玩家打出一張牌。"""

        if not self.engine.can_act(self.human_player, GameAction.DISCARD, tile=tile):
            self.log("目前無法打牌。")
            return

        self.engine.execute_action(self.human_player, GameAction.DISCARD, tile=tile)
        self.log("你打出了 {}".format(tile_to_chinese(tile)))

        self.last_drawn_tile = None
        self._cached_tsumo_result = None

        self.refresh_ui()
        if not self.handle_reactions():
            self.schedule_next_turn()

    # ------------------------------------------------------------------
    # AI 行動
    # ------------------------------------------------------------------
    def ai_take_turn(self) -> None:
        """簡單 AI：摸牌後隨機打出一張牌。"""

        if self.engine.get_phase() != GamePhase.PLAYING:
            self.end_round_if_needed()
            return

        player = self.engine.get_current_player()
        if player == self.human_player:
            # 可能在排程期間狀態已變更
            self.schedule_next_turn()
            return

        hand = self.engine.get_hand(player)
        if len(hand.tiles) < 14 and self.engine.can_act(player, GameAction.DRAW):
            result = self.engine.execute_action(player, GameAction.DRAW)
            if result.draw:
                self.log("玩家 {} 嶺上摸牌失敗，流局。".format(player))
                self.end_round_if_needed()
                return
            if result.drawn_tile is not None:
                self.log("玩家 {} 摸牌".format(player))
            if result.is_last_tile:
                self.log("玩家 {} 摸到了最後一張牌。".format(player))

        hand = self.engine.get_hand(player)
        if hand.tiles:
            tile = random.choice(hand.tiles)
            self.engine.execute_action(player, GameAction.DISCARD, tile=tile)
            self.log("玩家 {} 打出了 {}".format(player, tile_to_chinese(tile)))

        self.refresh_ui()

        if not self.handle_reactions():
            self.schedule_next_turn()

    def handle_reactions(self, start_offset: int = 1) -> bool:
        """處理其他玩家對最新捨牌的鳴牌。"""

        last_tile = self.engine.get_last_discard()
        last_player = self.engine.get_last_discard_player()
        if last_tile is None or last_player is None:
            return False

        tile_label = tile_to_chinese(last_tile)
        num_players = self.engine.get_num_players()

        for offset in range(start_offset, num_players):
            caller = (last_player + offset) % num_players
            if caller == self.human_player:
                options = self._build_human_reaction_options(last_tile, tile_label, offset)
                if options:
                    self.pending_reaction = {
                        "tile": last_tile,
                        "tile_label": tile_label,
                        "options": options,
                        "next_offset": offset + 1,
                    }
                    self.show_reaction_options(tile_label, options)
                    self.log("你可以對 {} 鳴牌，請選擇。".format(tile_label))
                    self.update_controls()
                    return True
                continue

            if self.engine.can_act(caller, GameAction.PON):
                self.clear_reaction_options()
                self.engine.execute_action(caller, GameAction.PON)
                self.log("玩家 {} 碰了 {}".format(caller, tile_label))
                self.refresh_ui()
                if caller != self.human_player:
                    self.root.after(self.ai_delay_ms, self.ai_take_turn)
                else:
                    self.schedule_next_turn()
                return True

            if offset == 1:
                sequences = self.engine.get_available_chi_sequences(caller)
                if sequences:
                    sequence = sequences[0]
                    combination = sequence + [last_tile]
                    self.clear_reaction_options()
                    self.engine.execute_action(caller, GameAction.CHI, sequence=sequence)
                    self.log("玩家 {} 吃了 {} ({})".format(caller, tile_label, format_tiles_chinese(combination)))
                    self.refresh_ui()
                    if caller != self.human_player:
                        self.root.after(self.ai_delay_ms, self.ai_take_turn)
                    else:
                        self.schedule_next_turn()
                    return True

        return False

    # ------------------------------------------------------------------
    # UI 更新
    # ------------------------------------------------------------------
    def refresh_ui(self) -> None:
        self.update_info_label()
        self.refresh_hand_ui(enable=self.engine.get_current_player() == self.human_player)
        self.refresh_opponents_ui()
        self.update_controls()

    def refresh_hand_ui(self, enable: bool) -> None:
        """更新玩家的手牌顯示。"""

        for widget in self.hand_frame.winfo_children():
            widget.destroy()

        tiles_container = tk.Frame(self.hand_frame)
        tiles_container.pack(side=tk.LEFT, padx=4)

        hand = self.engine.get_hand(self.human_player)
        for tile in hand.tiles:
            btn = tk.Button(
                tiles_container,
                text=tile_to_vertical_text(tile),
                width=2,
                height=3,
                font=("Helvetica", 12),
                justify=tk.CENTER,
                anchor=tk.CENTER,
                relief=tk.RIDGE,
                bd=3,
                command=lambda t=tile: self.discard_tile(t),
                state=tk.NORMAL if enable else tk.DISABLED,
            )
            btn.pack(side=tk.LEFT, padx=3)

        discards = self.engine.get_discards(self.human_player)
        discard_label = tk.Label(
            self.hand_frame,
            text="捨牌池: {}".format(format_tiles_chinese(discards)),
            anchor=tk.W,
        )
        discard_label.pack(side=tk.LEFT, padx=12)

        melds = hand.melds
        meld_text = " ".join(meld_to_chinese(meld) for meld in melds) if melds else "(無)"
        meld_label = tk.Label(
            self.hand_frame,
            text="我的副露: {}".format(meld_text),
            anchor=tk.W,
        )
        meld_label.pack(side=tk.LEFT, padx=12)

        action_container = tk.Frame(self.hand_frame)
        action_container.pack(side=tk.LEFT, padx=8)

        if enable and self.engine.can_act(self.human_player, GameAction.ANKAN):
            ankan_btn = tk.Button(
                action_container,
                text="暗槓",
                command=self.perform_ankan,
            )
            ankan_btn.pack(side=tk.TOP, pady=2)

        tsumo_result = None
        if enable and self.engine.get_phase() == GamePhase.PLAYING and self.last_drawn_tile is not None:
            tsumo_result = self._compute_win_result(self.human_player, self.last_drawn_tile, remove_tile=True)

        self._cached_tsumo_result = tsumo_result

        if enable and tsumo_result is not None:
            tsumo_btn = tk.Button(
                action_container,
                text="自摸",
                command=self.perform_tsumo,
            )
            tsumo_btn.pack(side=tk.TOP, pady=2)

    def refresh_opponents_ui(self) -> None:
        """更新其他玩家的捨牌與副露資訊。"""

        for widget in self.opponents_frame.winfo_children():
            widget.destroy()

        num_players = self.engine.get_num_players()
        for player in range(num_players):
            if player == self.human_player:
                continue

            frame = tk.Frame(self.opponents_frame)
            frame.pack(anchor=tk.W, pady=2, fill=tk.X)

            hand = self.engine.get_hand(player)
            melds = hand.melds
            meld_text = " ".join(meld_to_chinese(meld) for meld in melds) if melds else "(無)"
            discards = self.engine.get_discards(player)
            discard_text = format_tiles_chinese(discards)

            info = f"玩家 {player} | 副露: {meld_text} | 捨牌: {discard_text}"
            label = tk.Label(frame, text=info, anchor=tk.W, justify=tk.LEFT)
            label.pack(fill=tk.X)

    def _reset_reaction_widgets(self) -> None:
        for widget in self.reaction_frame.winfo_children():
            widget.destroy()

    def clear_reaction_options(self) -> None:
        self.pending_reaction = None
        self._reset_reaction_widgets()
        self.update_controls()

    def show_reaction_options(self, tile_label: str, options: list) -> None:
        self._reset_reaction_widgets()

        prompt = tk.Label(self.reaction_frame, text=f"對 {tile_label} 的選擇：", anchor=tk.W)
        prompt.pack(anchor=tk.W)

        buttons_frame = tk.Frame(self.reaction_frame)
        buttons_frame.pack(anchor=tk.W, pady=4)

        for option in options:
            btn = tk.Button(
                buttons_frame,
                text=option["label"],
                command=lambda opt=option: self.on_reaction_choice(opt),
            )
            btn.pack(side=tk.LEFT, padx=4)

        pass_option = {"action": None}
        pass_btn = tk.Button(
            buttons_frame,
            text="不要鳴",
            command=lambda: self.on_reaction_choice(pass_option),
        )
        pass_btn.pack(side=tk.LEFT, padx=4)

    def on_reaction_choice(self, option: dict) -> None:
        if not self.pending_reaction:
            return

        tile = self.pending_reaction["tile"]
        tile_label = self.pending_reaction["tile_label"]
        next_offset = self.pending_reaction.get("next_offset", 1)

        if option.get("action") is None:
            self.clear_reaction_options()
            if not self.handle_reactions(start_offset=next_offset):
                self.schedule_next_turn()
            return

        action = option["action"]
        if action == GameAction.PON:
            self.engine.execute_action(self.human_player, GameAction.PON)
            self.log("你碰了 {}".format(tile_label))
            self.last_drawn_tile = None
            self._cached_tsumo_result = None
        elif action == GameAction.CHI:
            sequence = option["sequence"]
            self.engine.execute_action(self.human_player, GameAction.CHI, sequence=sequence)
            combination = option.get("combination") or (sequence + [tile])
            self.log("你吃了 {} ({})".format(tile_label, format_tiles_chinese(combination)))
            self.last_drawn_tile = None
            self._cached_tsumo_result = None
        elif action == GameAction.RON:
            win_result = option.get("win_result")
            self.perform_ron(tile, win_result)
            return

        self.clear_reaction_options()
        self.refresh_ui()
        self.schedule_next_turn()

    def _build_human_reaction_options(self, last_tile: Tile, tile_label: str, offset: int) -> list:
        options = []

        if self.engine.can_act(self.human_player, GameAction.PON):
            options.append({"action": GameAction.PON, "label": f"碰 {tile_label}"})

        if offset == 1:
            sequences = self.engine.get_available_chi_sequences(self.human_player)
            for seq in sequences:
                combination = seq + [last_tile]
                options.append(
                    {
                        "action": GameAction.CHI,
                        "sequence": seq,
                        "combination": combination,
                        "label": "吃 {}".format(format_tiles_chinese(combination)),
                    }
                )

        ron_result = self._compute_win_result(self.human_player, last_tile, remove_tile=False)
        if ron_result is not None:
            options.insert(
                0,
                {
                    "action": GameAction.RON,
                    "label": f"榮 {tile_label}",
                    "win_result": ron_result,
                },
            )

        return options

    def perform_ankan(self) -> None:
        if not self.engine.can_act(self.human_player, GameAction.ANKAN):
            self.log("目前無法暗槓。")
            return

        result = self.engine.execute_action(self.human_player, GameAction.ANKAN)
        self.log("你暗槓了。")
        self.last_drawn_tile = result.rinshan_tile
        self._cached_tsumo_result = None
        if result.rinshan_tile is not None:
            self.log("你嶺上摸到 {}".format(tile_to_chinese(result.rinshan_tile)))

        self.refresh_ui()
        self.schedule_next_turn()

    def perform_tsumo(self) -> None:
        if self.last_drawn_tile is None:
            self.log("目前無自摸機會。")
            return

        win_result = self._cached_tsumo_result or self._compute_win_result(
            self.human_player, self.last_drawn_tile, remove_tile=True
        )
        if win_result is None:
            self.log("目前無法自摸。")
            self._cached_tsumo_result = None
            self.refresh_ui()
            return

        tile_label = tile_to_chinese(self.last_drawn_tile)
        self._finalize_win(win_result, method_label="自摸", tile_label=tile_label)

    def perform_ron(self, tile: Tile, win_result: Optional[WinResult]) -> None:
        result = win_result or self._compute_win_result(self.human_player, tile, remove_tile=False)
        if result is None:
            next_offset = 1
            if self.pending_reaction:
                next_offset = self.pending_reaction.get("next_offset", 1)
            self.log("目前無法榮和。")
            self.clear_reaction_options()
            if not self.handle_reactions(start_offset=next_offset):
                self.schedule_next_turn()
            return

        tile_label = tile_to_chinese(tile)
        self._finalize_win(result, method_label="榮和", tile_label=tile_label)

    def _compute_win_result(self, player: int, tile: Tile, remove_tile: bool) -> Optional[WinResult]:
        hand = self.engine.get_hand(player)
        removed = False

        if remove_tile:
            for idx, t in enumerate(getattr(hand, "_tiles", [])):
                if t == tile:
                    hand._tiles.pop(idx)  # type: ignore[attr-defined]
                    hand._tile_counts_cache = None  # type: ignore[attr-defined]
                    removed = True
                    break
            if not removed:
                return None

        try:
            return self.engine.check_win(player, tile)
        finally:
            if remove_tile and removed:
                hand._tiles.append(tile)  # type: ignore[attr-defined]
                hand._tiles.sort()  # type: ignore[attr-defined]
                hand._tile_counts_cache = None  # type: ignore[attr-defined]

    def _finalize_win(self, win_result: WinResult, method_label: str, tile_label: Optional[str]) -> None:
        message = f"你{method_label}!"
        if tile_label:
            message = f"你{method_label} {tile_label}!"
        self.log(message)

        self._log_win_result(win_result)

        self.engine._phase = GamePhase.WINNING  # type: ignore[attr-defined]
        self.engine._last_discarded_tile = None  # type: ignore[attr-defined]
        self.engine._last_discarded_player = None  # type: ignore[attr-defined]

        self.last_drawn_tile = None
        self._cached_tsumo_result = None

        self.clear_reaction_options()
        self.engine.end_round(winner=self.human_player)
        self.refresh_ui()
        self.update_controls()

    def _log_win_result(self, win_result: WinResult) -> None:
        if win_result.yaku:
            self.log("役種:")
            for yaku in win_result.yaku:
                name = getattr(yaku, "name_cn", None) or getattr(yaku, "name", "")
                self.log(f"  - {name} ({yaku.han} 翻)")

        score = win_result.score_result
        if score:
            self.log(f"翻數: {score.han} | 符數: {score.fu} | 總點數: {score.total_points}")
            if score.is_tsumo:
                if score.dealer_payment:
                    self.log(f"莊家支付: {score.dealer_payment}")
                if score.non_dealer_payment:
                    self.log(f"閒家支付: {score.non_dealer_payment}")
            else:
                if score.payment_from is not None:
                    self.log(f"放銃玩家: {score.payment_from}")

    def update_controls(self) -> None:
        """依遊戲狀態更新功能按鈕。"""

        if self.pending_reaction:
            self.draw_button.config(state=tk.DISABLED)
            return

        can_draw = self.engine.get_phase() == GamePhase.PLAYING and self.engine.can_act(
            self.human_player, GameAction.DRAW
        )
        self.draw_button.config(state=tk.NORMAL if can_draw else tk.DISABLED)

    def update_info_label(self) -> None:
        """更新狀態列資訊。"""

        game_state = self.engine.get_game_state()
        current = self.engine.get_current_player()
        phase = self.engine.get_phase()
        info = (
            f"局風: {game_state.round_wind.name} | 局數: {game_state.round_number} | "
            f"莊家: {game_state.dealer} | 當前玩家: {current} | 階段: {phase.value}"
        )
        tile_set = getattr(self.engine, "_tile_set", None)
        if tile_set:
            info += f" | 牌山剩餘: {tile_set.remaining}"
            indicators = []
            for indicator in getattr(tile_set, "_dora_indicators", []):
                if indicator is not None:
                    indicators.append(tile_to_chinese(indicator))
            if indicators:
                info += " | 寶牌指示: " + " ".join(indicators)
        self.info_label.config(text=info)

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------
    def log(self, message: str) -> None:
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    print("PyRiichi Demo UI")
    print("=================")
    print("This is a demo UI for PyRiichi, a Japanese Mahjong engine.")
    print("It is a simple UI that allows you to play a game of Japanese Mahjong.")
    ui = MahjongDemoUI()
    ui.run()


if __name__ == "__main__":
    main()
