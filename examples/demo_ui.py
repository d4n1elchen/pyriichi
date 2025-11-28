import os
import queue
import random
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, List, Optional, Tuple

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pyriichi.hand import Hand
from pyriichi.player import (
    BasePlayer,
    DefensivePlayer,
    PublicInfo,
    RandomPlayer,
    SimplePlayer,
)
from pyriichi.rules import GameAction, GamePhase, GameState, RuleEngine
from pyriichi.tiles import Suit, Tile

# --- Constants & Styles ---
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800

# Colors (Dark Theme)
COLOR_BG = "#212121"  # Dark Grey Background
COLOR_TABLE = "#004d40"  # Deep Teal (Mahjong Table)
COLOR_PANEL = "#424242"  # Lighter Grey for Panels
COLOR_TEXT = "#ffffff"  # White Text
COLOR_ACCENT = "#ffb74d"  # Orange Accent
COLOR_BUTTON = "#5c6bc0"  # Indigo Buttons

# Tile Colors
COLOR_MANZU = "#ef5350"  # Red
COLOR_PINZU = "#29b6f6"  # Light Blue
COLOR_SOZU = "#66bb6a"  # Green
COLOR_JIHAI = "#ffffff"  # White
COLOR_RED = "#d32f2f"  # Dark Red

FONT_TITLE = ("Helvetica", 24, "bold")
FONT_LARGE = ("Helvetica", 16, "bold")
FONT_MEDIUM = ("Helvetica", 12)
FONT_SMALL = ("Helvetica", 10)


def get_tile_color(tile_str: str) -> str:
    if "m" in tile_str:
        return COLOR_MANZU
    if "p" in tile_str:
        return COLOR_PINZU
    if "s" in tile_str:
        return COLOR_SOZU
    return COLOR_JIHAI


def get_tile_sort_key(tile_str: str):
    # Sort Key: Suit (m, p, s, z), Rank, IsRed
    is_red = "r" in tile_str
    clean = tile_str.replace("r", "")

    suit_map = {"m": 0, "p": 1, "s": 2, "z": 3}
    suit_char = clean[-1]
    rank = int(clean[:-1])

    # Red 5s (5mr, 5pr, 5sr) should sort with their respective 5s,
    # but perhaps come before or after regular 5s.
    # Let's make red 5s come before regular 5s of the same suit.
    red_sort_val = 0 if is_red else 1

    return (suit_map.get(suit_char, 4), rank, red_sort_val)


# --- Game Logic Classes ---


class GUIHumanPlayer(BasePlayer):
    def __init__(self, name: str, input_queue: queue.Queue, output_queue: queue.Queue):
        super().__init__(name)
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.last_drawn_tile: Optional[Tile] = None

    def decide_action(
        self,
        game_state: GameState,
        player_index: int,
        hand: Hand,
        available_actions: List[GameAction],
        public_info: Optional[PublicInfo] = None,
    ) -> Tuple[GameAction, Optional[Tile]]:
        # Auto-Draw Logic:
        # Only auto-draw if DRAW is available AND no interrupts (Chi/Pon/Kan/Ron) are available.
        # If interrupts are available, we must let the user choose (Pass or Interrupt).
        # Note: If we Pass, the engine will then offer DRAW again (or auto-draw if we implement that loop).
        # But here, if we have both, we should stop.

        interrupts = [
            GameAction.CHI,
            GameAction.PON,
            GameAction.KAN,
            GameAction.RON,
            GameAction.ANKAN,
        ]
        has_interrupt = any(action in available_actions for action in interrupts)

        if GameAction.DRAW in available_actions and not has_interrupt:
            return GameAction.DRAW, None

        # Notify GUI that it's human's turn
        self.output_queue.put(
            {
                "type": "human_turn",
                "actions": available_actions,
                "hand": hand,
                "last_drawn_tile": str(self.last_drawn_tile)
                if self.last_drawn_tile
                else None,
            }
        )

        # Wait for action from GUI
        action_data = self.input_queue.get()
        return action_data["action"], action_data.get("tile")


class GameThread(threading.Thread):
    def __init__(
        self, difficulty: str, update_queue: queue.Queue, human_input_queue: queue.Queue
    ):
        super().__init__()
        self.difficulty = difficulty
        self.update_queue = update_queue
        self.human_input_queue = human_input_queue
        self.engine = RuleEngine(num_players=4)
        self.running = True
        self.human_seat = -1
        self.players = []
        self.human_last_drawn_tile: Optional[Tile] = None

    def run(self):
        try:
            self._setup_game()
            self._game_loop()
        except Exception as e:
            import traceback

            traceback.print_exc()
            self.update_queue.put({"type": "error", "message": str(e)})

    def _setup_game(self):
        if self.difficulty == "Easy":
            ai_class = RandomPlayer
        elif self.difficulty == "Medium":
            ai_class = SimplePlayer
        else:
            ai_class = DefensivePlayer

        self.human_seat = random.randint(0, 3)
        self.players = []
        for i in range(4):
            if i == self.human_seat:
                self.players.append(
                    GUIHumanPlayer(f"You", self.human_input_queue, self.update_queue)
                )
            else:
                self.players.append(ai_class(f"AI {i}"))

        self.update_queue.put(
            {
                "type": "setup_complete",
                "human_seat": self.human_seat,
                "round_wind": self.engine.game_state.round_wind.name,
            }
        )

    def _game_loop(self):
        self.engine.start_game()

        while (
            self.running
            and self.engine.game_state.round_number <= 4
            and self.engine.game_state.round_wind
            == self.engine.game_state.round_wind.EAST
        ):
            self.engine.start_round()
            self.engine.deal()
            self._notify_state_update()

            while self.engine.get_phase() == GamePhase.PLAYING and self.running:
                current_player_idx = self.engine.get_current_player()
                player = self.players[current_player_idx]
                actions = self.engine.get_available_actions(current_player_idx)

                if not actions:
                    break

                if current_player_idx == self.human_seat and isinstance(
                    player, GUIHumanPlayer
                ):
                    player.last_drawn_tile = self.human_last_drawn_tile

                if current_player_idx != self.human_seat:
                    time.sleep(0.3)  # Faster pacing
                    public_info = PublicInfo(
                        turn_number=self.engine._turn_count,
                        dora_indicators=self.engine._tile_set.get_dora_indicators(1),
                        discards={i: self.engine.get_discards(i) for i in range(4)},
                        melds={i: self.engine.get_hand(i).melds for i in range(4)},
                        riichi_players=[
                            i for i, r in self.engine._riichi_ippatsu.items() if r
                        ],
                        scores=self.engine.game_state.scores,
                    )
                    action, tile = player.decide_action(
                        self.engine.game_state,
                        current_player_idx,
                        self.engine.get_hand(current_player_idx),
                        actions,
                        public_info,
                    )
                else:
                    action, tile = player.decide_action(
                        self.engine.game_state,
                        current_player_idx,
                        self.engine.get_hand(current_player_idx),
                        actions,
                    )

                result = self.engine.execute_action(current_player_idx, action, tile)

                # Track drawn tile for human
                if current_player_idx == self.human_seat:
                    if action == GameAction.DRAW and result.drawn_tile:
                        self.human_last_drawn_tile = result.drawn_tile
                    elif action == GameAction.DISCARD:
                        self.human_last_drawn_tile = None  # Reset after discard

                self._notify_state_update(
                    last_action=(current_player_idx, action, tile)
                )

                if result.winners:
                    self.update_queue.put(
                        {
                            "type": "game_end",
                            "reason": "win",
                            "winners": result.winners,
                            "win_results": result.win_results,
                        }
                    )
                    time.sleep(5)
                    break

                if result.ryuukyoku:
                    self.update_queue.put({"type": "game_end", "reason": "draw"})
                    time.sleep(3)
                    break

            if self.engine.get_phase() == GamePhase.ENDED:
                break
            self.engine.game_state.next_round()

        self.update_queue.put({"type": "match_end"})

    def _notify_state_update(self, last_action=None):
        state = {
            "type": "state_update",
            "round_wind": self.engine.game_state.round_wind.name,
            "round_number": self.engine.game_state.round_number,
            "honba": self.engine.game_state.honba,
            "riichi_sticks": self.engine.game_state.riichi_sticks,
            "scores": self.engine.game_state.scores,
            "dora_indicators": [
                str(t) for t in self.engine._tile_set.get_dora_indicators(1)
            ],
            "hands": {},
            "discards": {
                i: [str(t) for t in self.engine.get_discards(i)] for i in range(4)
            },
            "melds": {
                i: [str(m) for m in self.engine.get_hand(i).melds] for i in range(4)
            },
            "current_player": self.engine.get_current_player(),
            "last_action": last_action,
            "human_last_drawn_tile": str(self.human_last_drawn_tile)
            if self.human_last_drawn_tile
            else None,
        }

        for i in range(4):
            hand = self.engine.get_hand(i)
            if i == self.human_seat:
                state["hands"][i] = [str(t) for t in hand.tiles]
            else:
                state["hands"][i] = len(hand.tiles)

        self.update_queue.put(state)


# --- GUI Class ---


class MahjongGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PyRiichi Mahjong")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg=COLOR_BG)

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self._configure_styles()

        self.human_input_queue = queue.Queue()
        self.update_queue = queue.Queue()
        self.game_thread = None
        self.human_seat = -1
        self.current_actions = []

        self._init_ui()
        self.show_start_screen()
        self.root.after(100, self.poll_updates)

    def _configure_styles(self):
        self.style.configure("TFrame", background=COLOR_BG)
        self.style.configure(
            "TLabel", background=COLOR_BG, foreground=COLOR_TEXT, font=FONT_MEDIUM
        )
        self.style.configure(
            "TButton", font=FONT_MEDIUM, background=COLOR_BUTTON, foreground="white"
        )
        self.style.map("TButton", background=[("active", COLOR_ACCENT)])

        self.style.configure("Table.TFrame", background=COLOR_TABLE)
        self.style.configure("Panel.TFrame", background=COLOR_PANEL)

        self.style.configure(
            "Tile.TButton", font=FONT_LARGE, width=4, padding=5, background="white"
        )
        self.style.map("Tile.TButton", background=[("active", "#e0e0e0")])

    def _init_ui(self):
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)

    def show_start_screen(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

        frame = ttk.Frame(self.main_container)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(
            frame, text="PyRiichi Mahjong", font=FONT_TITLE, foreground=COLOR_ACCENT
        ).pack(pady=20)

        ttk.Label(frame, text="Select Difficulty:").pack(pady=5)
        self.diff_var = tk.StringVar(value="Medium")
        ttk.Radiobutton(frame, text="Easy", variable=self.diff_var, value="Easy").pack()
        ttk.Radiobutton(
            frame, text="Medium", variable=self.diff_var, value="Medium"
        ).pack()
        ttk.Radiobutton(frame, text="Hard", variable=self.diff_var, value="Hard").pack()

        ttk.Button(frame, text="Start Game", command=self.start_game).pack(pady=20)

    def start_game(self):
        difficulty = self.diff_var.get()
        self.game_thread = GameThread(
            difficulty, self.update_queue, self.human_input_queue
        )
        self.game_thread.start()
        self.create_game_board()

    def create_game_board(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

        # Layout: 3x3 Grid
        self.main_container.columnconfigure(1, weight=1)
        self.main_container.rowconfigure(1, weight=1)

        # Opponent Top
        self.frame_top = ttk.Frame(self.main_container, style="TFrame")
        self.frame_top.grid(row=0, column=1, sticky="ew", pady=10)

        # Opponent Left
        self.frame_left = ttk.Frame(self.main_container, style="TFrame")
        self.frame_left.grid(row=1, column=0, sticky="ns", padx=10)

        # Opponent Right
        self.frame_right = ttk.Frame(self.main_container, style="TFrame")
        self.frame_right.grid(row=1, column=2, sticky="ns", padx=10)

        # Center Table (River + Info)
        self.frame_table = ttk.Frame(
            self.main_container, style="Table.TFrame", padding=20
        )
        self.frame_table.grid(row=1, column=1, sticky="nsew")

        # Info Panel (Inside Table)
        self.frame_info = ttk.Frame(self.frame_table, style="Panel.TFrame", padding=10)
        self.frame_info.place(relx=0.5, rely=0.5, anchor="center")
        self.lbl_info = ttk.Label(
            self.frame_info, text="Round Info", font=FONT_SMALL, background=COLOR_PANEL
        )
        self.lbl_info.pack()
        self.lbl_dora = ttk.Label(
            self.frame_info,
            text="Dora",
            font=FONT_SMALL,
            foreground="gold",
            background=COLOR_PANEL,
        )
        self.lbl_dora.pack()

        # Human Player (Bottom)
        self.frame_bottom = ttk.Frame(self.main_container, style="TFrame", padding=10)
        self.frame_bottom.grid(row=2, column=0, columnspan=3, sticky="ew")

        self.frame_hand = ttk.Frame(self.frame_bottom)
        self.frame_hand.pack(side=tk.LEFT, expand=True)

        self.frame_actions = ttk.Frame(self.frame_bottom)
        self.frame_actions.pack(side=tk.RIGHT, padx=20)

        self.player_frames = {}  # To be mapped

    def poll_updates(self):
        try:
            while True:
                msg = self.update_queue.get_nowait()
                self.handle_message(msg)
        except queue.Empty:
            pass
        finally:
            self.root.after(50, self.poll_updates)

    def handle_message(self, msg):
        msg_type = msg["type"]
        if msg_type == "setup_complete":
            self.human_seat = msg["human_seat"]
            self.setup_player_positions()
        elif msg_type == "state_update":
            self.update_game_state(msg)
        elif msg_type == "human_turn":
            self.enable_human_controls(
                msg["actions"], msg["hand"], msg.get("last_drawn_tile")
            )
        elif msg_type == "game_end":
            self.show_round_result(msg)
        elif msg_type == "match_end":
            messagebox.showinfo("Game Over", "Match Finished!")
            self.show_start_screen()

    def setup_player_positions(self):
        self.pos_map = {
            "bottom": self.human_seat,
            "right": (self.human_seat + 1) % 4,
            "top": (self.human_seat + 2) % 4,
            "left": (self.human_seat + 3) % 4,
        }
        self.player_frames = {
            self.pos_map["top"]: self.frame_top,
            self.pos_map["left"]: self.frame_left,
            self.pos_map["right"]: self.frame_right,
        }

    def update_game_state(self, state):
        # Info
        self.lbl_info.config(
            text=f"{state['round_wind']} {state['round_number']} | Honba: {state['honba']} | Riichi: {state['riichi_sticks']}"
        )
        self.lbl_dora.config(text=f"Dora: {' '.join(state['dora_indicators'])}")

        # Render Opponents
        for pid, frame in self.player_frames.items():
            for w in frame.winfo_children():
                w.destroy()
            count = state["hands"][pid]
            melds = state["melds"][pid]
            score = state["scores"][pid]

            # Simple representation
            txt = f"P{pid}\n[{score}]\n{'🀠 ' * count}\n{' '.join(melds)}"
            ttk.Label(frame, text=txt, justify="center").pack()

        # Render River
        # Clear previous river tiles (simple approach: redraw all)
        # Ideally we'd have dedicated frames for each player's river in the table
        # For this demo, we'll just overlay labels in quadrants

        # Remove old river widgets
        for w in self.frame_table.winfo_children():
            if w != self.frame_info:
                w.destroy()

        # Draw rivers
        for i in range(4):
            pid = (self.human_seat + i) % 4
            discards = state["discards"][pid]

            # Position
            relx, rely, anchor = 0.5, 0.5, "center"
            if i == 0:
                relx, rely, anchor = 0.5, 0.8, "s"  # Bottom
            elif i == 1:
                relx, rely, anchor = 0.8, 0.5, "e"  # Right
            elif i == 2:
                relx, rely, anchor = 0.5, 0.2, "n"  # Top
            elif i == 3:
                relx, rely, anchor = 0.2, 0.5, "w"  # Left

            # Show last 6
            shown = discards[-6:]
            txt = " ".join(shown)
            lbl = tk.Label(
                self.frame_table, text=txt, bg=COLOR_TABLE, fg="white", font=FONT_MEDIUM
            )
            lbl.place(relx=relx, rely=rely, anchor=anchor)

        # Render Human Hand (Passive view, active controls handled in human_turn)
        # Only update if not currently in turn (to avoid flickering during interaction)
        # Actually, we should update to show the draw.
        self.render_human_hand(
            state["hands"][self.human_seat],
            state["melds"][self.human_seat],
            active=False,
            last_drawn_tile=state.get("human_last_drawn_tile"),
        )

    def render_human_hand(
        self,
        tiles_str: List[str],
        melds: List[str],
        active: bool = False,
        last_drawn_tile: Optional[str] = None,
    ):
        for w in self.frame_hand.winfo_children():
            w.destroy()

        # Sort everything first
        standing_tiles = sorted(tiles_str, key=get_tile_sort_key)

        # If we have a drawn tile, remove one instance of it and append to end
        has_drawn = False
        if last_drawn_tile and last_drawn_tile in standing_tiles:
            # Find the first occurrence of the drawn tile and move it to the end
            # This handles cases where there are multiple identical tiles
            idx_to_move = -1
            for i, t in enumerate(standing_tiles):
                if t == last_drawn_tile:
                    idx_to_move = i
                    break
            if idx_to_move != -1:
                moved_tile = standing_tiles.pop(idx_to_move)
                standing_tiles.append(moved_tile)
                has_drawn = True

        for idx, t_str in enumerate(standing_tiles):
            color = get_tile_color(t_str)

            # Add gap before drawn tile
            padx = 2
            if has_drawn and idx == len(standing_tiles) - 1:
                padx = (20, 2)

            btn = tk.Button(
                self.frame_hand,
                text=t_str,
                font=FONT_LARGE,
                width=4,
                bg="white",
                fg=color,
                state="normal" if active else "disabled",
                command=lambda t=t_str: self.on_tile_click(t),
            )
            btn.pack(side=tk.LEFT, padx=padx)

        if melds:
            ttk.Label(self.frame_hand, text="   " + " ".join(melds)).pack(side=tk.LEFT)

    def enable_human_controls(
        self,
        actions: List[GameAction],
        hand: Hand,
        last_drawn_tile: Optional[str] = None,
    ):
        self.current_actions = actions

        # Re-render hand as active
        tiles_str = [str(t) for t in hand.tiles]
        melds_str = [str(m) for m in hand.melds]

        self.render_human_hand(
            tiles_str, melds_str, active=True, last_drawn_tile=last_drawn_tile
        )

        # Action Buttons
        for w in self.frame_actions.winfo_children():
            w.destroy()

        for action in actions:
            if action == GameAction.DISCARD:
                continue

            btn = ttk.Button(
                self.frame_actions,
                text=action.name,
                command=lambda a=action: self.on_action_click(a),
            )
            btn.pack(side=tk.LEFT, padx=5)

    def render_human_hand_active(
        self, tiles_str: List[str], melds: List[str], has_drawn: bool
    ):
        for w in self.frame_hand.winfo_children():
            w.destroy()

        for idx, t_str in enumerate(tiles_str):
            color = get_tile_color(t_str)

            # Add gap before drawn tile
            padx = 2
            if has_drawn and idx == len(tiles_str) - 1:
                padx = (20, 2)  # Extra left padding

            btn = tk.Button(
                self.frame_hand,
                text=t_str,
                font=FONT_LARGE,
                width=4,
                bg="white",
                fg=color,
                command=lambda t=t_str: self.on_tile_click(t),
            )
            btn.pack(side=tk.LEFT, padx=padx)

        if melds:
            ttk.Label(self.frame_hand, text="   " + " ".join(melds)).pack(side=tk.LEFT)

    def on_tile_click(self, tile_str):
        if GameAction.DISCARD in self.current_actions:
            # Reconstruct tile
            is_red = "r" in tile_str
            clean = tile_str.replace("r", "")
            suit = Suit.JIHAI
            if "m" in clean:
                suit = Suit.MANZU
            elif "p" in clean:
                suit = Suit.PINZU
            elif "s" in clean:
                suit = Suit.SOZU
            rank = int(clean[0])
            tile = Tile(suit, rank, is_red=is_red)

            self.human_input_queue.put({"action": GameAction.DISCARD, "tile": tile})
            self._clear_actions()

    def on_action_click(self, action):
        self.human_input_queue.put({"action": action, "tile": None})
        self._clear_actions()

    def _clear_actions(self):
        for w in self.frame_actions.winfo_children():
            w.destroy()
        # Disable hand buttons
        for w in self.frame_hand.winfo_children():
            if isinstance(w, tk.Button):
                w.config(state="disabled")

    def show_round_result(self, msg):
        reason = msg["reason"]
        if reason == "win":
            winners = msg["winners"]
            win_results = msg["win_results"]
            txt = "WINNER(S):\n"
            for w in winners:
                res = win_results[w]
                txt += f"Player {w}: {res.points} pts ({res.han} Han / {res.fu} Fu)\n"
            messagebox.showinfo("Round End", txt)
        else:
            messagebox.showinfo("Round End", "Draw (Ryuukyoku)!")


if __name__ == "__main__":
    root = tk.Tk()
    app = MahjongGUI(root)
    root.mainloop()
