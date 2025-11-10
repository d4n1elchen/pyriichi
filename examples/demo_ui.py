"""
PyRiichi Demo UI

提供一個最小化的 Tkinter 視覺介面示例，演示如何使用 PyRiichi
的 `RuleEngine` 進行基本的摸打流程。玩家（0 號）透過介面操作，
其餘三名對手僅會隨機摸牌並打出一張牌。
"""

import random
import tkinter as tk
from typing import Iterable, Optional

from pyriichi.hand import Meld
from pyriichi.rules import GameAction, GamePhase, RuleEngine, WinResult
from pyriichi.tiles import Tile, Suit


def tile_to_vertical_text(tile: Tile) -> str:
    """將牌轉換為垂直顯示的文字。"""
    text = tile.zh
    return "\n".join(text)


def format_tiles_chinese(tiles: Iterable[Tile]) -> str:
    """將多張牌格式化為中文字串。"""
    tile_list = list(tiles)
    return " ".join(tile.zh for tile in tile_list) if tile_list else "(無)"


def meld_to_chinese(meld: Meld) -> str:
    kind = meld.type.zh
    tiles_text = " ".join(tile.zh for tile in meld.tiles)
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

    def _has_action(self, player: int, action: GameAction) -> bool:
        """檢查指定玩家是否可以執行某動作。"""
        return action in self.engine.get_available_actions(player)

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
        self.log(f"新的一局開始！莊家為玩家 {self.engine.get_game_state().dealer}")
        self.log(f'你的起始手牌: {" ".join(tile.zh for tile in hands[self.human_player])}')

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
        if hand.total_tile_count() < 14 and self._has_action(self.human_player, GameAction.DRAW):
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

        if phase == GamePhase.RYUUKYOKU:
            self.log("本局流局，請重新開始。")
        elif phase == GamePhase.WINNING:
            self.log("出現和牌，示例在此結束。")
        else:
            self.log(f"遊戲階段：{phase.value}")

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

        if not self._has_action(self.human_player, GameAction.DRAW):
            self.log("目前無法摸牌。")
            return

        result = self.engine.execute_action(self.human_player, GameAction.DRAW)
        if result.ryuukyoku:
            self.log("牌山耗盡，流局！")
            self.last_drawn_tile = None
            self._cached_tsumo_result = None
            self.end_round_if_needed()
            return

        if result.drawn_tile is not None:
            self.log(f"你摸到了 {result.drawn_tile.zh}")
            self.last_drawn_tile = result.drawn_tile
        else:
            self.last_drawn_tile = None

        if result.is_last_tile:
            self.log("這是海底最後一張牌。")

        self._cached_tsumo_result = None
        self.refresh_ui()

    def discard_tile(self, tile) -> None:
        """玩家打出一張牌。"""

        if not self._has_action(self.human_player, GameAction.DISCARD):
            self.log("目前無法打牌。")
            return

        self.engine.execute_action(self.human_player, GameAction.DISCARD, tile=tile)
        self.log(f"你打出了 {tile.zh}")

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
        if len(hand.tiles) < 14 and self._has_action(player, GameAction.DRAW):
            result = self.engine.execute_action(player, GameAction.DRAW)
            if result.ryuukyoku:
                self.log(f"玩家 {player} 嶺上摸牌失敗，流局。")
                self.end_round_if_needed()
                return
            if result.drawn_tile is not None:
                self.log(f"玩家 {player} 摸牌")
            if result.is_last_tile:
                self.log(f"玩家 {player} 摸到了最後一張牌。")

        hand = self.engine.get_hand(player)
        if hand.tiles:
            tile = random.choice(hand.tiles)
            self.engine.execute_action(player, GameAction.DISCARD, tile=tile)
            self.log(f"玩家 {player} 打出了 {tile.zh}")

        self.refresh_ui()

        if not self.handle_reactions():
            self.schedule_next_turn()

    def handle_reactions(self, start_offset: int = 1) -> bool:
        """處理其他玩家對最新捨牌的鳴牌。"""

        last_tile = self.engine.get_last_discard()
        last_player = self.engine.get_last_discard_player()
        if last_tile is None or last_player is None:
            return False

        tile_label = last_tile.zh
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
                    self.log(f"你可以對 {tile_label} 鳴牌，請選擇。")
                    self.update_controls()
                    return True
                continue

            if self._has_action(caller, GameAction.KAN):
                self.clear_reaction_options()
                result = self.engine.execute_action(caller, GameAction.KAN, tile=last_tile)
                self.log(f"玩家 {caller} 槓了 {tile_label}")
                if result.rinshan_tile is not None:
                    self.log(f"玩家 {caller} 嶺上摸到 {result.rinshan_tile.zh}")
                self.refresh_ui()
                if caller != self.human_player:
                    self.root.after(self.ai_delay_ms, self.ai_take_turn)
                else:
                    self.last_drawn_tile = result.rinshan_tile
                    self.schedule_next_turn()
                return True

            if self._has_action(caller, GameAction.PON):
                self.clear_reaction_options()
                self.engine.execute_action(caller, GameAction.PON)
                self.log(f"玩家 {caller} 碰了 {tile_label}")
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
                    self.log(f"玩家 {caller} 吃了 {tile_label} ({format_tiles_chinese(combination)})")
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

        top_container = tk.Frame(self.hand_frame)
        top_container.pack(side=tk.TOP, anchor=tk.W)

        hand = self.engine.get_hand(self.human_player)
        discards = self.engine.get_discards(self.human_player)
        discard_label = tk.Label(
            top_container,
            text=f"捨牌池: {format_tiles_chinese(discards)}",
            anchor=tk.W,
        )
        discard_label.pack(side=tk.LEFT, padx=12)

        melds = hand.melds
        meld_text = " ".join(meld_to_chinese(meld) for meld in melds) if melds else "(無)"
        meld_label = tk.Label(
            top_container,
            text=f"我的副露: {meld_text}",
            anchor=tk.W,
        )
        meld_label.pack(side=tk.LEFT, padx=12)

        bottom_container = tk.Frame(self.hand_frame)
        bottom_container.pack(side=tk.TOP, anchor=tk.W)

        tiles_container = tk.Frame(bottom_container)
        tiles_container.pack(side=tk.LEFT, padx=4)

        sorted_tiles = sorted(hand.tiles)
        drawn_tile = None
        if self.last_drawn_tile is not None:
            for idx, tile in enumerate(sorted_tiles):
                if tile == self.last_drawn_tile:
                    drawn_tile = sorted_tiles.pop(idx)
                    break

        for tile in sorted_tiles:
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

        if drawn_tile is not None:
            btn = tk.Button(
                tiles_container,
                text=tile_to_vertical_text(drawn_tile),
                width=2,
                height=3,
                font=("Helvetica", 12),
                justify=tk.CENTER,
                anchor=tk.CENTER,
                relief=tk.RIDGE,
                bd=3,
                command=lambda t=drawn_tile: self.discard_tile(t),
                state=tk.NORMAL if enable else tk.DISABLED,
            )
            btn.pack(side=tk.LEFT, padx=3)

        action_container = tk.Frame(bottom_container)
        action_container.pack(side=tk.LEFT, padx=8)

        if enable and self._has_action(self.human_player, GameAction.ANKAN):
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

        # discards/melds 已在上方顯示

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
            concealed_count = len(hand.tiles)
            total_tiles = hand.total_tile_count()

            info = (
                f"玩家 {player} | 手牌:{total_tiles} 張 (暗牌 {concealed_count}) | "
                f"副露: {meld_text} | 捨牌: {discard_text}"
            )
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
            self.log(f"你碰了 {tile_label}")
            self.last_drawn_tile = None
            self._cached_tsumo_result = None
        elif action == GameAction.CHI:
            sequence = option["sequence"]
            self.engine.execute_action(self.human_player, GameAction.CHI, sequence=sequence)
            combination = option.get("combination") or (sequence + [tile])
            self.log(f"你吃了 {tile_label} ({format_tiles_chinese(combination)})")
            self.last_drawn_tile = None
            self._cached_tsumo_result = None
        elif action == GameAction.KAN:
            kan_tile = option.get("tile") or tile
            result = self.engine.execute_action(self.human_player, GameAction.KAN, tile=kan_tile)
            self.log(f"你槓了 {tile_label}")
            self.last_drawn_tile = result.rinshan_tile
            self._cached_tsumo_result = None
            if result.rinshan_tile is not None:
                self.log(f"你嶺上摸到 {result.rinshan_tile.zh}")
        elif action == GameAction.RON:
            win_result = option.get("win_result")
            self.perform_ron(tile, win_result)
            return

        self.clear_reaction_options()
        self.refresh_ui()
        self.schedule_next_turn()

    def _build_human_reaction_options(self, last_tile: Tile, tile_label: str, offset: int) -> list:
        options = []

        if self._has_action(self.human_player, GameAction.KAN):
            options.append(
                {
                    "action": GameAction.KAN,
                    "label": f"槓 {tile_label}",
                    "tile": last_tile,
                }
            )

        if self._has_action(self.human_player, GameAction.PON):
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
                        "label": f"吃 {format_tiles_chinese(combination)}",
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
        if not self._has_action(self.human_player, GameAction.ANKAN):
            self.log("目前無法暗槓。")
            return

        result = self.engine.execute_action(self.human_player, GameAction.ANKAN)
        self.log("你暗槓了。")
        self.last_drawn_tile = result.rinshan_tile
        self._cached_tsumo_result = None
        if result.rinshan_tile is not None:
            self.log(f"你嶺上摸到 {result.rinshan_tile.zh}")

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

        tile_label = self.last_drawn_tile.zh
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

        tile_label = tile.zh
        self._finalize_win(result, method_label="榮和", tile_label=tile_label)

    def _compute_win_result(self, player: int, tile: Tile, remove_tile: bool) -> Optional[WinResult]:
        # TODO: RuleEngine 若需支援「模擬移除手牌後再檢查和牌」的情境，應提供對應公開 API。
        return self.engine.check_win(player, tile)

    def _finalize_win(self, win_result: WinResult, method_label: str, tile_label: Optional[str]) -> None:
        message = f"你{method_label}!"
        if tile_label:
            message = f"你{method_label} {tile_label}!"
        self.log(message)

        self._log_win_result(win_result)

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

        can_draw = self.engine.get_phase() == GamePhase.PLAYING and self._has_action(self.human_player, GameAction.DRAW)
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
        remaining = self.engine.get_wall_remaining()
        if remaining is not None:
            info += f" | 牌山剩餘: {remaining}"

        dora_indicators = self.engine.get_revealed_dora_indicators()
        if dora_indicators:
            info += " | 寶牌指示: " + " ".join(tile.zh for tile in dora_indicators)
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
