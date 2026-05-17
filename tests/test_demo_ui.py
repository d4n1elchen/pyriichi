"""Tests for the demo TUI helpers."""

from examples.demo_ui import Tui
from pyriichi.hand import Hand
from pyriichi.tiles import Suit, Tile


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
