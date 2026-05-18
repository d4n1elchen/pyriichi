"""Tenpai hint tests for RuleEngine."""

from pyriichi.hand import Hand
from pyriichi.tiles import Suit, Tile
from tests.helpers import initialized_engine, set_non_matching_scoring_dora


def _hint_hand() -> Hand:
    return Hand(
        [
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 2),
            Tile(Suit.MANZU, 3),
            Tile(Suit.MANZU, 4),
            Tile(Suit.MANZU, 5),
            Tile(Suit.MANZU, 6),
            Tile(Suit.MANZU, 7),
            Tile(Suit.MANZU, 8),
            Tile(Suit.MANZU, 9),
            Tile(Suit.PINZU, 1),
            Tile(Suit.PINZU, 1),
            Tile(Suit.SOUZU, 2),
            Tile(Suit.SOUZU, 2),
            Tile(Suit.SOUZU, 3),
        ]
    )


def test_tenpai_hint_counts_visible_wait_tiles():
    """Test tenpai hint returns waits and visible remaining counts."""
    engine = initialized_engine()
    set_non_matching_scoring_dora(engine)
    engine._hands[0] = _hint_hand()

    hint = engine.get_tenpai_hint_after_discard(0, Tile(Suit.SOUZU, 3))

    assert hint is not None
    assert [(wait.tile, wait.remaining) for wait in hint.waits] == [
        (Tile(Suit.PINZU, 1), 2),
        (Tile(Suit.SOUZU, 2), 2),
    ]
    assert hint.furiten is False


def test_tenpai_hint_marks_furiten_after_candidate_discard():
    """Test tenpai hint marks discard-based furiten."""
    engine = initialized_engine()
    set_non_matching_scoring_dora(engine)
    hand = _hint_hand()
    hand._discards = [Tile(Suit.PINZU, 1)]
    engine._hands[0] = hand

    hint = engine.get_tenpai_hint_after_discard(0, Tile(Suit.SOUZU, 3))

    assert hint is not None
    assert hint.furiten is True


def test_tenpai_hint_returns_none_for_noten_discard():
    """Test tenpai hint is absent when the discard does not leave tenpai."""
    engine = initialized_engine()
    set_non_matching_scoring_dora(engine)
    engine._hands[0] = _hint_hand()

    hint = engine.get_tenpai_hint_after_discard(0, Tile(Suit.MANZU, 1))

    assert hint is None
