import os
import queue
import random
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox
from typing import Dict, List, Optional, Tuple

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pyriichi.game_state import GameState, Wind
from pyriichi.hand import Hand, Meld
from pyriichi.player import (
    BasePlayer,
    DefensivePlayer,
    PublicInfo,
    RandomPlayer,
    SimplePlayer,
)
from pyriichi.rules import GameAction, GamePhase, RuleEngine
from pyriichi.tiles import Suit, Tile

# --- Constants ---
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 900

# Colors
COLOR_TABLE_BG = "#006400"  # Deep Green Felt
COLOR_TILE_FACE = "#FDF5E6"  # Cream/Bone
COLOR_TILE_BACK = "#E6B422"  # Gold/Yellow
COLOR_TILE_BORDER = "#8B4513"  # SaddleBrown
COLOR_TEXT_WHITE = "#FFFFFF"
COLOR_TEXT_GOLD = "#FFD700"

# Tile Dimensions (Canvas Units)
TILE_WIDTH = 40
TILE_HEIGHT = 56

# Fonts
FONT_LARGE = ("Arial", 24, "bold")
FONT_MEDIUM = ("Arial", 16, "bold")
FONT_SMALL = ("Arial", 12)
FONT_TINY = ("Arial", 10)
FONT_TILE = (
    "Kaiti TC",
    24,
    "bold",
)  # Use a nice Chinese font if available, fallback to sans
FONT_TILE_SMALL = ("Arial", 10, "bold")  # For the number/suit indicator


class TileRenderer:
    """Handles drawing of Mahjong tiles on a Canvas using text."""

    @staticmethod
    def draw_tile(
        canvas: tk.Canvas,
        x: float,
        y: float,
        tile: Optional[Tile],
        width: float = TILE_WIDTH,
        height: float = TILE_HEIGHT,
        face_up: bool = True,
        selected: bool = False,
        scale: float = 1.0,
        angle: float = 0.0,
        dimmed: bool = False,
    ):
        w = width * scale
        h = height * scale

        cx = x + w / 2
        cy = y + h / 2

        # Helper for rotation
        def rotate_point(px, py, ox, oy, theta):
            import math

            rad = math.radians(theta)
            c, s = math.cos(rad), math.sin(rad)
            dx, dy = px - ox, py - oy
            return ox + dx * c - dy * s, oy + dx * s + dy * c

        # Calculate corners for body
        corners = [
            (x, y),
            (x + w, y),
            (x + w, y + h),
            (x, y + h),
        ]
        rotated_corners = [rotate_point(px, py, cx, cy, angle) for px, py in corners]

        # Calculate corners for shadow (offset)
        # Fixed offset to simulate global light source
        shadow_offset = width * 0.1
        shadow_corners = [
            (px + shadow_offset, py + shadow_offset) for px, py in rotated_corners
        ]

        # Draw Shadow
        canvas.create_polygon(
            shadow_corners, fill="#333333", outline="", tags=("tile", "shadow")
        )

        # Border/Body
        bg_color = COLOR_TILE_FACE if face_up else COLOR_TILE_BACK
        if selected:
            bg_color = "#FFD700"  # Highlight selected
        elif dimmed:
            # Darken the background color for dimming
            if face_up:
                bg_color = "#CCCCCC"  # Darker cream
            else:
                bg_color = "#B8860B"  # Darker gold

        # Main Tile Body
        canvas.create_polygon(
            rotated_corners,
            fill=bg_color,
            outline=COLOR_TILE_BORDER,
            width=1,
            tags=("tile", "body"),
        )

        if face_up and tile:
            TileRenderer._draw_text_pattern(canvas, cx, cy, w, h, tile, angle, dimmed)

    @staticmethod
    def _draw_text_pattern(
        canvas: tk.Canvas,
        cx: float,
        cy: float,
        w: float,
        h: float,
        tile: Tile,
        angle: float,
        dimmed: bool = False,
    ):
        # Determine color
        color = "#000000"

        if tile.is_red:
            color = "#FF0000"
        elif tile.suit == Suit.MANZU:
            color = "#B22222"  # Red
        elif tile.suit == Suit.PINZU:
            color = "#000080"  # Navy Blue
        elif tile.suit == Suit.SOZU:
            color = "#006400"  # Green
        elif tile.suit == Suit.JIHAI:
            if tile.rank == 5:  # Haku (White)
                color = "#000000"  # Black as requested
            elif tile.rank == 6:  # Hatsu (Green)
                color = "#006400"
            elif tile.rank == 7:  # Chun (Red)
                color = "#B22222"
            else:
                color = "#000000"  # Winds are black

        if dimmed:
            # Darken colors
            if color == "#000000":
                color = "#555555"
            elif color == "#FF0000":
                color = "#8B0000"
            elif color == "#B22222":
                color = "#8B0000"
            elif color == "#000080":
                color = "#00004d"
            elif color == "#006400":
                color = "#004d00"

        # Get localized name
        text = tile.get_name("zh")
        # Remove "赤" prefix if present (we use red dot and color instead)
        text = text.replace("赤", "")

        # Draw Text
        # Use same font for everything
        font_size = int(h * 0.5)
        font = ("Kaiti TC", font_size, "bold")

        # Vertical layout for number + suit if needed
        if len(text) > 1 and tile.suit != Suit.JIHAI:
            # Vertical layout
            # We need to position them relative to center, but rotated.
            # Offset for top char (Number) and bottom char (Suit)

            # Calculate offsets based on angle
            offset = h * 0.2

            if angle == 0:
                dx1, dy1 = 0, -offset
                dx2, dy2 = 0, offset
            elif angle == 90:
                dx1, dy1 = -offset, 0
                dx2, dy2 = offset, 0
            elif angle == -90:
                dx1, dy1 = offset, 0
                dx2, dy2 = -offset, 0
            elif angle == 180:
                dx1, dy1 = 0, offset
                dx2, dy2 = 0, -offset
            else:
                import math

                rad = math.radians(angle)
                c, s = math.cos(rad), math.sin(rad)
                dx1 = offset * s
                dy1 = -offset * c
                dx2 = -dx1
                dy2 = -dy1

            cx1, cy1 = cx + dx1, cy + dy1
            cx2, cy2 = cx + dx2, cy + dy2

            number_char = text[0]
            suit_char = text[1:]

            # Use smaller font for split
            split_font = ("Kaiti TC", int(h * 0.35), "bold")

            canvas.create_text(
                cx1, cy1, text=number_char, fill=color, font=split_font, angle=angle
            )
            canvas.create_text(
                cx2, cy2, text=suit_char, fill=color, font=split_font, angle=angle
            )
        else:
            # Single char or Honors
            canvas.create_text(cx, cy, text=text, fill=color, font=font, angle=angle)

        if tile.is_red:
            # Add a small red dot indicator
            # Rotate position
            import math

            rad = math.radians(angle)
            c, s = math.cos(rad), math.sin(rad)

            dx = w * 0.35
            dy = -h * 0.35
            rcx = cx + dx * c - dy * s
            rcy = cy + dx * s + dy * c

            r = w * 0.05
            canvas.create_oval(
                rcx - r, rcy - r, rcx + r, rcy + r, fill="red", outline="red"
            )


class MahjongTable(tk.Canvas):
    def __init__(self, master, width=WINDOW_WIDTH, height=WINDOW_HEIGHT):
        super().__init__(master, width=width, height=height, bg=COLOR_TABLE_BG)
        self.width = width
        self.height = height
        self.center_x = width / 2
        self.center_y = height / 2

        # Game State Data
        self.hands: Dict[int, Hand] = {}
        self.discards: Dict[int, List[Tile]] = {}
        self.melds: Dict[int, List[str]] = {}
        self.scores: Dict[int, int] = {}
        self.dealer: int = 0
        self.current_player: int = 0
        self.round_wind: str = "EAST"
        self.round_number: int = 1
        self.honba: int = 0
        self.riichi_sticks: int = 0
        self.wall_remaining: int = 0
        self.dora_indicators: List[Tile] = []

        # Interaction
        self.human_seat: int = 0
        self.selected_tile_idx: int = -1
        self.on_tile_click_callback = None

        # Riichi Selection Mode
        self.riichi_mode: bool = False
        self.valid_riichi_discards: List[Tile] = []

        self.bind("<Button-1>", self._on_click)
        self.bind("<Motion>", self._on_mouse_move)

    def update_state(self, state: dict):
        self.hands = state.get(
            "hands_obj", {}
        )  # Expecting Hand objects or list of Tiles
        self.discards = state.get("discards_obj", {})  # Expecting list of Tiles
        self.melds = state.get("melds_obj", {})
        self.scores = state.get("scores", {})
        self.dealer = state.get("dealer", 0)
        self.current_player = state.get("current_player", 0)
        self.round_wind_name = state.get("round_wind_zh", "東")  # Use localized name
        self.round_number = state.get("round_number", 1)
        self.honba = state.get("honba", 0)
        self.riichi_sticks = state.get("riichi_sticks", 0)
        self.wall_remaining = state.get("wall_remaining", 0)
        self.dora_indicators = state.get("dora_indicators_obj", [])

        self.render()

    def render(self):
        self.delete("all")

        # Draw Center Info
        self._render_center_info()

        # Draw Players (Hands, Discards)
        for i in range(4):
            rel_pos = (i - self.human_seat) % 4
            self._render_player(i, rel_pos)

        # Ensure shadows are behind everything else, but above center panel
        self.tag_lower("shadow")
        self.tag_raise("shadow", "center_panel")

    def _render_center_info(self):
        w, h = 260, 260
        x = self.center_x - w / 2
        y = self.center_y - h / 2

        self.create_rectangle(
            x,
            y,
            x + w,
            y + h,
            fill="#004d40",
            outline="#FFD700",
            width=2,
            tags="center_panel",
        )

        # Round Info
        info_text = f"{self.round_wind_name} {self.round_number} 局\n{self.honba} 本場"
        self.create_text(
            self.center_x,
            self.center_y - 50,
            text=info_text,
            fill=COLOR_TEXT_WHITE,
            font=FONT_MEDIUM,
            justify="center",
        )

        # Wall Remaining
        self.create_text(
            self.center_x,
            self.center_y - 20,
            text=f"剩餘: {self.wall_remaining}",
            fill="#AAAAAA",
            font=FONT_SMALL,
            justify="center",
        )

        # Riichi Sticks (Unclaimed)
        active_riichi_count = 0
        for hand in self.hands.values():
            if hand and hand.is_riichi:  # Ensure hand is not None
                active_riichi_count += 1

        center_sticks = self.riichi_sticks - active_riichi_count

        if center_sticks > 0:
            stick_y = self.center_y - 15
            self._draw_riichi_stick(self.center_x - 30, stick_y, 40, 8)
            self.create_text(
                self.center_x + 10,
                stick_y,
                text=f"x {center_sticks}",
                fill=COLOR_TEXT_WHITE,
                font=FONT_SMALL,
                anchor="w",
            )

        # Dora
        self.create_text(
            self.center_x,
            self.center_y + 5,
            text="寶牌",
            fill=COLOR_TEXT_GOLD,
            font=FONT_SMALL,
        )
        dora_start_x = (
            self.center_x - (len(self.dora_indicators) * TILE_WIDTH * 0.8) / 2
        )
        for idx, tile in enumerate(self.dora_indicators):
            TileRenderer.draw_tile(
                self,
                dora_start_x + idx * TILE_WIDTH * 0.8,
                self.center_y + 25,
                tile,
                scale=0.8,
            )

    def _draw_riichi_stick(self, x, y, w, h, angle=0):
        """Draw a 1000 point stick (Riichi stick)"""

        # Helper for rotation
        def rotate_point(px, py, ox, oy, theta):
            import math

            rad = math.radians(theta)
            c, s = math.cos(rad), math.sin(rad)
            dx, dy = px - ox, py - oy
            return ox + dx * c - dy * s, oy + dx * s + dy * c

        center_x = x + w / 2
        center_y = y

        # Calculate corners relative to center
        half_w = w / 2
        half_h = h / 2

        corners = [
            (center_x - half_w, center_y - half_h),
            (center_x + half_w, center_y - half_h),
            (center_x + half_w, center_y + half_h),
            (center_x - half_w, center_y + half_h),
        ]

        rotated_corners = [
            rotate_point(px, py, center_x, center_y, angle) for px, py in corners
        ]

        # White body
        self.create_polygon(rotated_corners, fill="#F0F0F0", outline="#CCCCCC")

        # Red dot in center
        r = h * 0.3
        # Dot is always at center, just circle
        self.create_oval(
            center_x - r,
            center_y - r,
            center_x + r,
            center_y + r,
            fill="#FF0000",
            outline="#FF0000",
        )

    def _render_player(self, player_idx: int, rel_pos: int):
        # rel_pos: 0=Bottom, 1=Right, 2=Top, 3=Left

        # Coordinates setup
        # Center of the table
        cx, cy = self.center_x, self.center_y

        # Hand & River Parameters
        hand_offset = 30  # Distance from edge

        # Score Position (Inside Center Panel) & Rotation
        # Center panel is approx 260x260 (radius 130)
        score_radius = 95

        if rel_pos == 0:  # Bottom (Human)
            # Hand centered horizontally at bottom
            hand_len = 13
            hand = self.hands.get(player_idx)
            if hand:
                hand_len = len(hand.tiles)

            hand_width = hand_len * TILE_WIDTH
            hand_x = (self.width - hand_width) / 2
            hand_y = self.height - TILE_HEIGHT - hand_offset

            score_x, score_y = cx, cy + score_radius
            score_angle = 0

        elif rel_pos == 1:  # Right
            # Hand centered vertically at right
            hand_len = 13
            hand = self.hands.get(player_idx)
            if hand:
                hand_len = len(hand.tiles) if isinstance(hand, Hand) else hand

            # Vertical hand
            spacing = TILE_WIDTH * 0.9
            hand_height = hand_len * spacing
            hand_x = self.width - TILE_HEIGHT - hand_offset
            hand_y = (self.height - hand_height) / 2  # Top of the stack

            score_x, score_y = cx + score_radius, cy
            score_angle = 90

        elif rel_pos == 2:  # Top
            # Hand centered horizontally at top
            hand_len = 13
            hand = self.hands.get(player_idx)
            if hand:
                hand_len = len(hand.tiles) if isinstance(hand, Hand) else hand

            hand_width = hand_len * TILE_WIDTH
            hand_x = (self.width - hand_width) / 2
            hand_y = hand_offset

            score_x, score_y = cx, cy - score_radius
            score_angle = 180

        elif rel_pos == 3:  # Left
            # Hand centered vertically at left
            hand_len = 13
            hand = self.hands.get(player_idx)
            if hand:
                hand_len = len(hand.tiles) if isinstance(hand, Hand) else hand

            spacing = TILE_WIDTH * 0.9
            hand_height = hand_len * spacing
            hand_x = hand_offset
            hand_y = (self.height + hand_height) / 2  # Bottom of the stack (drawing up)

            score_x, score_y = cx - score_radius, cy
            score_angle = -90

        # Draw Score
        score = (
            self.scores[player_idx]
            if isinstance(self.scores, list) and player_idx < len(self.scores)
            else self.scores.get(player_idx, 25000)
        )

        # Calculate Seat Wind
        # 0=East, 1=South, 2=West, 3=North
        winds = [Wind.EAST, Wind.SOUTH, Wind.WEST, Wind.NORTH]
        seat_wind_idx = (player_idx - self.dealer) % 4
        seat_wind = winds[seat_wind_idx]

        self.create_text(
            score_x,
            score_y,
            text=f"{seat_wind.zh}\n{score}",
            fill=COLOR_TEXT_WHITE,
            font=FONT_SMALL,
            justify="center",
            angle=score_angle,
        )

        # Draw Riichi Stick if player is in Riichi
        hand = self.hands.get(player_idx)
        if hand and hand.is_riichi:
            offset = 25

            if rel_pos == 0:  # Bottom
                sx, sy = score_x, score_y + offset
                angle = 0
            elif rel_pos == 1:  # Right
                sx, sy = score_x + offset, score_y
                angle = 90
            elif rel_pos == 2:  # Top
                sx, sy = score_x, score_y - offset
                angle = 180
            elif rel_pos == 3:  # Left
                sx, sy = score_x - offset, score_y
                angle = -90

            # Draw stick centered at sx, sy
            w, h = 40, 8
            self._draw_riichi_stick(sx - w / 2, sy, w, h, angle)

        # Draw River (Discards)
        discards = self.discards.get(player_idx, [])
        self._render_river(discards, 0, 0, rel_pos)

        # Draw Hand
        hand = self.hands.get(player_idx)
        melds = self.melds.get(player_idx, [])

        if hand:
            if rel_pos == 0:  # Human - Face Up
                self._render_human_hand(hand, hand_x, hand_y, melds)
            else:  # AI - Face Down (or simplified)
                self._render_ai_hand(hand, hand_x, hand_y, rel_pos, melds)

    def _render_river(self, discards: List[Tile], x: float, y: float, rel_pos: int):
        # 6 tiles per row
        scale = 0.8
        w = TILE_WIDTH * scale
        h = TILE_HEIGHT * scale

        # Center panel dimensions (approx 260x260)
        center_half_size = 130
        padding = 10

        # Recalculate start positions to align with center panel
        cx, cy = self.center_x, self.center_y

        angle = 0
        if rel_pos == 1:
            angle = 90  # Right player discards face left (CCW)
        elif rel_pos == 2:
            angle = 180  # Top player discards upside down
        elif rel_pos == 3:
            angle = -90  # Left player discards face right (CW)

        for i, tile in enumerate(discards):
            row = i // 6
            col = i % 6

            if rel_pos == 0:  # Bottom
                # Start: Left-aligned with center box, Below center box
                # Fills: Left -> Right (Cols), Top -> Bottom (Rows)
                start_x = cx - 3 * w
                start_y = cy + center_half_size + padding

                dx = start_x + col * w
                dy = start_y + row * h

            elif rel_pos == 1:  # Right
                # Start: Right of center box, Top-aligned with center box (visually centered vertically)
                start_x = cx + center_half_size + padding
                start_y = cy + 2 * w

                dx = start_x + row * h
                dy = start_y - col * w  # Grow Up

            elif rel_pos == 2:  # Top
                # Start: Left-aligned with center box, Above center box
                start_x = cx + 2 * w
                start_y = cy - center_half_size - padding

                dx = start_x - col * w  # Grow Left
                dy = (
                    start_y - row * h - h
                )  # Grow Up (minus h because drawing from top-left of tile)

            elif rel_pos == 3:  # Left
                # Start: Left of center box, Top-aligned with center box
                # Fills: Top -> Bottom (Cols), Right -> Left (Rows - growing away)
                start_x = cx - center_half_size - padding
                start_y = cy - 3 * w

                dx = start_x - row * h - h  # Grow Left
                dy = start_y + col * w

            TileRenderer.draw_tile(self, dx, dy, tile, scale=scale, angle=angle)

    def _render_human_hand(self, hand: Hand, x: float, y: float, melds: List[Meld]):
        tiles = hand.tiles
        # Sort
        tiles = sorted(tiles, key=lambda t: (t.suit.value, t.rank, t.is_red))

        # Check for drawn tile
        drawn_tile = hand.last_drawn_tile

        tiles_to_render = list(tiles)
        drawn_tile_to_render = None

        # Only separate if it's the current player (human)
        if (
            self.current_player == self.human_seat
            and drawn_tile
            and drawn_tile in tiles_to_render
        ):
            # Remove one instance
            tiles_to_render.remove(drawn_tile)
            drawn_tile_to_render = drawn_tile

        is_my_turn = self.current_player == self.human_seat
        should_dim_turn = not is_my_turn

        for i, tile in enumerate(tiles_to_render):
            dx = x + i * TILE_WIDTH
            dy = y

            if i == self.selected_tile_idx:
                # If in Riichi mode, only lift if valid discard
                if self.riichi_mode and tile not in self.valid_riichi_discards:
                    pass
                else:
                    dy -= 20

            is_dimmed = should_dim_turn
            if self.riichi_mode and not is_dimmed:
                # If in Riichi mode, dim tiles that are NOT in valid_riichi_discards
                if tile not in self.valid_riichi_discards:
                    is_dimmed = True

            TileRenderer.draw_tile(
                self,
                dx,
                dy,
                tile,
                face_up=True,
                selected=(i == self.selected_tile_idx),
                dimmed=is_dimmed,
            )

            self.addtag_overlapping(
                f"hand_tile:{i}", dx, dy, dx + TILE_WIDTH, dy + TILE_HEIGHT
            )

        if drawn_tile_to_render:
            i = len(tiles_to_render)
            # Add gap
            dx = x + i * TILE_WIDTH + 15  # 15px gap
            dy = y

            # Check if selected (index would be last)
            if self.selected_tile_idx == i:
                # If in Riichi mode, only lift if valid discard
                if (
                    self.riichi_mode
                    and drawn_tile_to_render not in self.valid_riichi_discards
                ):
                    pass
                else:
                    dy -= 20

            is_dimmed = should_dim_turn
            if self.riichi_mode and not is_dimmed:
                if drawn_tile_to_render not in self.valid_riichi_discards:
                    is_dimmed = True

            TileRenderer.draw_tile(
                self,
                dx,
                dy,
                drawn_tile_to_render,
                face_up=True,
                selected=(self.selected_tile_idx == i),
                dimmed=is_dimmed,
            )

            self.addtag_overlapping(
                f"hand_tile:{i}", dx, dy, dx + TILE_WIDTH, dy + TILE_HEIGHT
            )

        if melds:
            # Adjust start x based on whether we had a drawn tile
            extra_width = TILE_WIDTH + 15 if drawn_tile_to_render else 0
            meld_start_x = x + len(tiles_to_render) * TILE_WIDTH + extra_width + 20
            self._render_melds(melds, meld_start_x, y, 0)

    def _render_ai_hand(
        self, hand: Hand, x: float, y: float, rel_pos: int, melds: List[Meld]
    ):
        count = len(hand.tiles) if isinstance(hand, Hand) else hand
        if isinstance(hand, int):
            count = hand
        elif isinstance(hand, Hand):
            count = len(hand.tiles)

        spacing = TILE_WIDTH * 0.9

        for i in range(count):
            if rel_pos == 2:  # Top
                dx = x + i * TILE_WIDTH
                dy = y
                TileRenderer.draw_tile(self, dx, dy, None, face_up=False, angle=180)
            elif rel_pos == 1:  # Right
                dx = x
                dy = y + i * spacing  # Vertical
                TileRenderer.draw_tile(self, dx, dy, None, face_up=False, angle=90)
            elif rel_pos == 3:  # Left
                dx = x
                dy = y - i * spacing  # Vertical (Up)
                TileRenderer.draw_tile(self, dx, dy, None, face_up=False, angle=-90)
            else:
                dx = x
                dy = y
                TileRenderer.draw_tile(self, dx, dy, None, face_up=False)

        # Draw Melds
        if melds:
            if rel_pos == 2:  # Top (Left of hand)
                self._render_melds(melds, x - 20, y, rel_pos)

            elif rel_pos == 1:  # Right (Bottom of hand)
                self._render_melds(melds, x, y + count * spacing + 20, rel_pos)

            elif rel_pos == 3:  # Left (Top of hand)
                self._render_melds(melds, x, y - count * spacing - 20, rel_pos)

    def _render_melds(self, melds: List[Meld], x: float, y: float, rel_pos: int):
        # Render melds sequentially
        current_x, current_y = x, y

        for meld in melds:
            tiles = meld.tiles

            for tile in tiles:
                angle = 0
                if rel_pos == 1:
                    angle = 90
                elif rel_pos == 2:
                    angle = 180
                elif rel_pos == 3:
                    angle = -90

                TileRenderer.draw_tile(
                    self, current_x, current_y, tile, face_up=True, angle=angle
                )

                if rel_pos == 0:
                    current_x += TILE_WIDTH
                elif rel_pos == 1:
                    current_y += TILE_WIDTH * 0.9
                elif rel_pos == 2:
                    current_x -= TILE_WIDTH  # Grow Left
                elif rel_pos == 3:
                    current_y -= TILE_WIDTH * 0.9  # Grow Up

            # Spacing between melds
            if rel_pos == 0:
                current_x += 10
            elif rel_pos == 1:
                current_y += 10
            elif rel_pos == 2:
                current_x -= 10
            elif rel_pos == 3:
                current_y -= 10

    def _on_mouse_move(self, event):
        if self.current_player != self.human_seat:
            if self.selected_tile_idx != -1:  # If not human's turn, clear selection
                self.selected_tile_idx = -1
                self.render()
            return

        items = self.find_overlapping(event.x, event.y, event.x, event.y)

        new_selection = -1

        for item in items:
            tags = self.gettags(item)
            for tag in tags:
                if tag.startswith("hand_tile:"):
                    idx = int(tag.split(":")[1])
                    new_selection = idx
                    break
            if new_selection != -1:
                break

        if new_selection != self.selected_tile_idx:
            self.selected_tile_idx = new_selection
            self.render()

    def _on_click(self, event):
        if self.current_player != self.human_seat:
            return

        if self.selected_tile_idx != -1:
            # Confirm discard
            # Check if it's the human's turn
            # We already checked current_player == self.human_seat

            if self.on_tile_click_callback:
                # We need the tile object.
                hand = self.hands.get(self.human_seat)
                if hand and isinstance(hand, Hand):
                    tiles = sorted(
                        hand.tiles, key=lambda t: (t.suit.value, t.rank, t.is_red)
                    )
                    drawn_tile = hand.last_drawn_tile
                    if drawn_tile and drawn_tile in tiles:
                        tiles.remove(drawn_tile)
                        tiles.append(drawn_tile)

                    if 0 <= self.selected_tile_idx < len(tiles):
                        tile = tiles[self.selected_tile_idx]

                        if self.riichi_mode:
                            if tile not in self.valid_riichi_discards:
                                return

                        self.on_tile_click_callback(tile)  # Corrected callback name
                        self.selected_tile_idx = -1
                        self.render()


# --- Game Logic Classes ---


class GUIHumanPlayer(BasePlayer):
    def __init__(self, name: str, input_queue: queue.Queue, output_queue: queue.Queue):
        super().__init__(name)
        self.input_queue = input_queue
        self.output_queue = output_queue

    def decide_action(
        self,
        game_state: GameState,
        player_index: int,
        hand: Hand,
        available_actions: List[GameAction],
        public_info: Optional[PublicInfo] = None,
    ) -> Tuple[GameAction, Optional[Tile]]:
        self.output_queue.put(
            {
                "type": "human_turn",
                "actions": available_actions,
                "hand": hand,
            }
        )

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
        self.next_round_event = threading.Event()

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
                    GUIHumanPlayer("玩家", self.human_input_queue, self.update_queue)
                )
            else:
                self.players.append(ai_class(f"電腦 {i}"))

        # Assign players to engine
        self.update_queue.put(
            {
                "type": "setup_complete",
                "human_seat": self.human_seat,
                "round_wind": self.engine.game_state.round_wind.name,
            }
        )

    def _notify_state_update(self):
        state = {
            "type": "state_update",
            "round_wind_zh": self.engine.game_state.round_wind.zh,
            "round_number": self.engine.game_state.round_number,
            "honba": self.engine.game_state.honba,
            "riichi_sticks": self.engine.game_state.riichi_sticks,
            "wall_remaining": self.engine.tileset.remaining
            if self.engine.tileset
            else 0,
            "scores": self.engine.game_state.scores,
            "dora_indicators_obj": self.engine.tileset.get_dora_indicators(1),
            "hands_obj": {i: self.engine.get_hand(i) for i in range(4)},
            "discards_obj": {i: self.engine.get_discards(i) for i in range(4)},
            "melds_obj": {i: self.engine.get_hand(i).melds for i in range(4)},
            "dealer": self.engine.game_state.dealer,
            "current_player": self.engine.get_current_player(),
        }
        self.update_queue.put(state)

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
                waiting_map = self.engine.waiting_for_actions
                if waiting_map:
                    waiting_pids = list(waiting_map.keys())
                    for pid in waiting_pids:
                        if not self.running:
                            break

                        player = self.players[pid]
                        available_actions = self.engine.get_available_actions(pid)

                        public_info = PublicInfo(
                            turn_number=self.engine._turn_count,
                            dora_indicators=self.engine.tileset.get_dora_indicators(1),
                            discards={i: self.engine.get_discards(i) for i in range(4)},
                            melds={i: self.engine.get_hand(i).melds for i in range(4)},
                            riichi_players=[
                                i for i, r in self.engine._riichi_ippatsu.items() if r
                            ],
                            scores=self.engine.game_state.scores,
                        )

                        if pid != self.human_seat:
                            time.sleep(0.5)
                            action, tile = player.decide_action(
                                self.engine.game_state,
                                pid,
                                self.engine.get_hand(pid),
                                available_actions,
                                public_info,
                            )
                        else:
                            action, tile = player.decide_action(
                                self.engine.game_state,
                                pid,
                                self.engine.get_hand(pid),
                                available_actions,
                            )

                        try:
                            result = self.engine.execute_action(pid, action, tile)
                            self._notify_state_update()

                            if result.winners or result.ryuukyoku:
                                break  # Inner loop break
                        except Exception as e:
                            print(f"Error executing action: {e}")
                            import traceback

                            traceback.print_exc()

                    if result.winners or result.ryuukyoku:
                        self.update_queue.put(
                            {
                                "type": "game_end",
                                "reason": "win" if result.winners else "draw",
                                "winners": result.winners,
                                "win_results": result.win_results,
                            }
                        )

                        self.next_round_event.wait()
                        self.next_round_event.clear()
                        break
                    continue

                current_player_idx = self.engine.get_current_player()
                player = self.players[current_player_idx]
                actions = self.engine.get_available_actions(current_player_idx)

                if not actions:
                    continue

                public_info = PublicInfo(
                    turn_number=self.engine._turn_count,
                    dora_indicators=self.engine.tileset.get_dora_indicators(1),
                    discards={i: self.engine.get_discards(i) for i in range(4)},
                    melds={i: self.engine.get_hand(i).melds for i in range(4)},
                    riichi_players=[
                        i for i, r in self.engine._riichi_ippatsu.items() if r
                    ],
                    scores=self.engine.game_state.scores,
                )

                if current_player_idx != self.human_seat:
                    time.sleep(0.5)
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

                try:
                    result = self.engine.execute_action(
                        current_player_idx, action, tile
                    )
                    self._notify_state_update()
                except Exception as e:
                    print(f"Error executing action: {e}")
                    import traceback

                    traceback.print_exc()

                if result.winners or result.ryuukyoku:
                    self.update_queue.put(
                        {
                            "type": "game_end",
                            "reason": "win" if result.winners else "draw",
                            "winners": result.winners,
                            "win_results": result.win_results,
                        }
                    )

                    self.next_round_event.wait()
                    self.next_round_event.clear()
                    break

            if self.engine.get_phase() == GamePhase.ENDED:
                break
            self.engine.game_state.next_round()

        self.update_queue.put({"type": "match_end"})


class GameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PyRiichi 麻將 (Canvas Version)")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg="#212121")

        self.human_input_queue = queue.Queue()
        self.update_queue = queue.Queue()
        self.game_thread = None
        self.human_seat = -1
        self.current_actions = []

        self._init_ui()
        self.show_start_screen()
        self.root.after(100, self.poll_updates)

    def _init_ui(self):
        self.main_container = tk.Frame(self.root, bg="#212121")
        self.main_container.pack(fill=tk.BOTH, expand=True)

    def show_start_screen(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

        frame = tk.Frame(self.main_container, bg="#212121")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            frame,
            text="PyRiichi 麻將",
            font=("Arial", 32, "bold"),
            fg="#FFD700",
            bg="#212121",
        ).pack(pady=20)

        tk.Label(frame, text="選擇難度:", fg="white", bg="#212121").pack(pady=5)
        self.diff_var = tk.StringVar(value="Medium")
        tk.Radiobutton(
            frame,
            text="簡單",
            variable=self.diff_var,
            value="Easy",
            bg="#212121",
            fg="white",
            selectcolor="#424242",
        ).pack()
        tk.Radiobutton(
            frame,
            text="普通",
            variable=self.diff_var,
            value="Medium",
            bg="#212121",
            fg="white",
            selectcolor="#424242",
        ).pack()
        tk.Radiobutton(
            frame,
            text="困難",
            variable=self.diff_var,
            value="Hard",
            bg="#212121",
            fg="white",
            selectcolor="#424242",
        ).pack()

        tk.Button(
            frame,
            text="開始遊戲",
            command=self.start_game,
            font=("Arial", 14),
        ).pack(pady=20)

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

        self.table = MahjongTable(self.main_container)
        self.table.pack(fill=tk.BOTH, expand=True)
        self.table.on_tile_click_callback = self.on_tile_click

        self.action_panel = tk.Frame(
            self.main_container, bg="#212121", bd=2, relief="raised"
        )
        self.action_panel.place(relx=0.5, rely=0.85, anchor="center")
        self.action_panel.place_forget()  # Hide initially

        self.settlement_panel = SettlementPanel(
            self.main_container, self.on_next_round_click
        )

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
            self.table.human_seat = self.human_seat
        elif msg_type == "state_update":
            self.table.update_state(msg)
        elif msg_type == "human_turn":
            self.enable_human_controls(msg["actions"])
        elif msg_type == "game_end":
            self.show_round_result(msg)
        elif msg_type == "match_end":
            messagebox.showinfo("遊戲結束", "對局結束!")
            self.show_start_screen()
        elif msg_type == "error":
            messagebox.showerror("錯誤", msg["message"])

    def enable_human_controls(self, actions: List[GameAction]):
        self.current_actions = actions

        for widget in self.action_panel.winfo_children():
            widget.destroy()

        has_buttons = False
        for action in actions:
            if action == GameAction.DISCARD:
                continue

            has_buttons = True
            btn = tk.Button(
                self.action_panel,
                text=action.zh,  # Use localized name
                font=("Arial", 12, "bold"),
                command=lambda a=action: self.on_action_click(a),
            )
            btn.pack(side=tk.LEFT, padx=5, pady=5)

        if has_buttons:
            self.action_panel.place(relx=0.5, rely=0.85, anchor="center")
        else:
            self.action_panel.place_forget()

    def on_tile_click(self, tile: Tile):
        if self.table.riichi_mode:
            if tile in self.table.valid_riichi_discards:
                self.human_input_queue.put({"action": GameAction.RICHI, "tile": tile})
                self._exit_riichi_mode()
            return

        if GameAction.DISCARD in self.current_actions:
            self.human_input_queue.put({"action": GameAction.DISCARD, "tile": tile})
            self.action_panel.place_forget()
            self.current_actions = []

    def on_action_click(self, action: GameAction):
        if action == GameAction.RICHI:
            self._enter_riichi_mode()
            return

        self.human_input_queue.put({"action": action, "tile": None})
        self.action_panel.place_forget()
        self.current_actions = []

    def _enter_riichi_mode(self):
        hand = self.table.hands.get(self.human_seat)
        if not hand:
            return

        valid_discards = hand.tenpai_discards
        if not valid_discards:
            return

        self.table.riichi_mode = True
        self.table.valid_riichi_discards = valid_discards
        self.table.render()

        for widget in self.action_panel.winfo_children():
            widget.destroy()

        btn = tk.Button(
            self.action_panel,
            text="取消立直",
            font=("Arial", 12, "bold"),
            command=self._cancel_riichi_mode,
        )
        btn.pack(side=tk.LEFT, padx=5, pady=5)

    def _cancel_riichi_mode(self):
        self._exit_riichi_mode()
        self.enable_human_controls(self.current_actions)

    def _exit_riichi_mode(self):
        self.table.riichi_mode = False
        self.table.valid_riichi_discards = []
        self.table.render()
        self.action_panel.place_forget()

    def on_next_round_click(self):
        if self.game_thread:
            self.game_thread.next_round_event.set()

    def show_round_result(self, msg):
        self.settlement_panel.show(msg)


class SettlementPanel(tk.Frame):
    def __init__(self, master, on_next_round):
        super().__init__(master)
        self.configure(bg="#1a1a1a", bd=2, relief="solid")
        self.on_next_round = on_next_round
        self.place_forget()

        self._init_widgets()

    def _init_widgets(self):
        self.header_label = tk.Label(
            self, text="", font=("Arial", 24, "bold"), fg="#FFD700", bg="#1a1a1a"
        )
        self.header_label.pack(side=tk.TOP, pady=20)

        self.content_frame = tk.Frame(self, bg="#1a1a1a")
        self.content_frame.pack(
            side=tk.TOP, fill=tk.BOTH, expand=True, padx=40, pady=(10, 80)
        )

        self.next_btn = tk.Button(
            self,
            text="下一局",
            font=("Arial", 16, "bold"),
            command=self._on_next,
            width=15,
            height=2,
        )
        self.next_btn.place(relx=0.5, rely=0.95, anchor="s")

    def show(self, data):
        self.lift()
        self.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.8, relheight=0.8)

        for widget in self.content_frame.winfo_children():
            widget.destroy()

        reason = data.get("reason")
        if reason == "draw":
            self._show_ryuukyoku(data)
        elif reason == "win":
            self._show_win(data)

    def hide(self):
        self.place_forget()

    def _on_next(self):
        self.hide()
        if self.on_next_round:
            self.on_next_round()

    def _show_ryuukyoku(self, data):
        self.header_label.config(text="流局")

        tk.Label(
            self.content_frame,
            text="荒牌流局",  # Default to exhausted wall for now
            font=("Arial", 20),
            fg="white",
            bg="#1a1a1a",
        ).pack(expand=True)

    def _show_win(self, data):
        self.header_label.config(text="和牌")

        winners = data["winners"]
        win_results = data["win_results"]

        for winner_idx in winners:
            res = win_results[winner_idx]

            w_frame = tk.Frame(self.content_frame, bg="#2d2d2d", bd=1, relief="solid")
            w_frame.pack(fill=tk.X, pady=10, ipady=10)

            left_frame = tk.Frame(w_frame, bg="#2d2d2d")
            left_frame.pack(side=tk.LEFT, padx=20)

            tk.Label(
                left_frame,
                text=f"玩家 {winner_idx}",
                font=("Arial", 18, "bold"),
                fg="#FFD700",
                bg="#2d2d2d",
            ).pack(anchor="w")

            score_text = f"{res.points} 點"
            tk.Label(
                left_frame,
                text=score_text,
                font=("Arial", 24, "bold"),
                fg="white",
                bg="#2d2d2d",
            ).pack(anchor="w")

            detail_text = f"{res.han} 翻 {res.fu} 符"
            if any(y.is_yakuman for y in res.yaku):
                detail_text = "役滿"

            tk.Label(
                left_frame,
                text=detail_text,
                font=("Arial", 14),
                fg="#aaaaaa",
                bg="#2d2d2d",
            ).pack(anchor="w")

            right_frame = tk.Frame(w_frame, bg="#2d2d2d")
            right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)

            row = 0
            col = 0
            for yaku_res in res.yaku:
                y_text = f"{yaku_res.yaku.zh} ({yaku_res.han} 翻)"
                if yaku_res.is_yakuman:
                    y_text = f"{yaku_res.yaku.zh} (役滿)"

                tk.Label(
                    right_frame,
                    text=y_text,
                    font=("Arial", 14),
                    fg="white",
                    bg="#2d2d2d",
                    width=20,
                    anchor="w",
                ).grid(row=row, column=col, sticky="w", pady=2)

                col += 1
                if col > 1:
                    col = 0
                    row += 1


if __name__ == "__main__":
    root = tk.Tk()
    app = GameApp(root)
    root.mainloop()
