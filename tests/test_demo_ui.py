"""Tests for the demo TUI helpers."""

import curses

from examples.demo_ui import Tui
from pyriichi.hand import Hand
from pyriichi.tiles import Suit, Tile
from tests.helpers import initialized_engine


class FakeScreen:
    def __init__(self):
        self.calls = []

    def getmaxyx(self):
        return (40, 120)

    def addstr(self, y, x, text, attr=0):
        self.calls.append((y, x, text, attr))


class TestDemoUi:
    """Tests for non-curses TUI helper behavior."""

    def test_chi_options_split_red_and_normal_five(self):
        """Test chi options distinguish red five and normal five."""
        normal_five = Tile(Suit.MANZU, 5)
        red_five = Tile(Suit.MANZU, 5, is_red_dora=True)
        six = Tile(Suit.MANZU, 6)
        hand = Hand([normal_five, red_five, six])
        tui = object.__new__(Tui)

        sequences = tui.concrete_chi_sequences(
            hand, [Tile(Suit.MANZU, 5), Tile(Suit.MANZU, 6)]
        )

        assert len(sequences) == 2
        assert [normal_five, six] in sequences
        assert [red_five, six] in sequences

    def test_hand_display_orders_red_five_deterministically(self):
        """Test hand display uses deterministic red five ordering."""
        red_five = Tile(Suit.MANZU, 5, is_red_dora=True)
        normal_five = Tile(Suit.MANZU, 5)

        assert Tui.sorted_tiles_for_display([red_five, normal_five]) == [
            normal_five,
            red_five,
        ]
        assert Tui.sorted_tiles_for_display([normal_five, red_five]) == [
            normal_five,
            red_five,
        ]

    def test_wrapped_tile_rows_show_all_tiles_without_overflow_marker(self):
        """Test wrapped tile rows draw every tile when max_rows is unlimited."""
        tui = object.__new__(Tui)
        tui.stdscr = FakeScreen()
        tui.engine = None
        tui.has_colors = False
        tiles = [Tile(Suit.MANZU, rank) for rank in range(1, 10)] + [
            Tile(Suit.PINZU, rank) for rank in range(1, 6)
        ]

        rows = tui.draw_wrapped_tile_rows(0, 0, tiles, 40, indexed=True)

        drawn_text = "".join(call[2] for call in tui.stdscr.calls)
        assert rows > 1
        assert "+1" not in drawn_text
        assert "14[五筒]" in drawn_text

    def test_hand_rows_add_extra_space_before_incoming_tile(self):
        """Test incoming tile is visually separated from the sorted hand."""
        tui = object.__new__(Tui)
        tui.stdscr = FakeScreen()
        tui.engine = None
        tui.has_colors = False
        tiles = [Tile(Suit.MANZU, 1), Tile(Suit.MANZU, 2)]

        tui.draw_tile_row(0, 0, tiles, 80, indexed=True, gap_before_index=1)

        first = tui.stdscr.calls[0]
        second = tui.stdscr.calls[1]
        first_width = tui.display_width(first[2])
        assert second[1] - first[1] - first_width == 3

    def test_compact_view_pins_status_and_shortcuts_to_bottom(self):
        """Test compact view keeps interactive hints visible at the bottom."""
        screen = FakeScreen()
        tui = Tui(screen)
        tui.engine = initialized_engine()
        tui.status = "Select tile"

        tui.render_compact()

        bottom_text = " ".join(call[2] for call in screen.calls if call[0] == 39)
        assert "Select tile" in bottom_text
        assert "Arrows: move" in bottom_text

    def test_compact_discards_use_river_tile_effects(self):
        """Test compact discards preserve river styling such as riichi marks."""
        screen = FakeScreen()
        tui = Tui(screen)
        tui.engine = initialized_engine()
        hand = tui.engine.get_hand(1)
        hand._discards = [Tile(Suit.MANZU, 1)]
        hand._riichi_turn = 0

        tui.render_compact()

        riichi_discard_attrs = [
            attr for _, _, text, attr in screen.calls if text == "[一萬]"
        ]
        assert any(
            attr & curses.A_UNDERLINE and attr & curses.A_REVERSE
            for attr in riichi_discard_attrs
        )
