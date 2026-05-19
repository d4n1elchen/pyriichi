"""Tests for the demo TUI helpers."""

from examples.demo_ui import Tui
from pyriichi.hand import Hand
from pyriichi.tiles import Suit, Tile


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
