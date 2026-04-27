"""Test module."""

import pytest

from pyriichi.hand import Hand, Meld, MeldType
from pyriichi.tiles import Suit, Tile
from pyriichi.utils import parse_tiles


class TestHand:
    """Tests for TestHand."""

    def test_hand_init(self):
        """Test hand init."""
        # 123m 456p 789s 123z 4z
        tiles = parse_tiles("123m456p789s1z2z3z4z")
        hand = Hand(tiles)

        assert len(hand.tiles) == 13
        assert hand.is_concealed

    def test_add_and_discard(self):
        """Test add and discard."""
        # 123m 456p 789s 123z 4z
        tiles = parse_tiles("123m456p789s1z2z3z4z")
        hand = Hand(tiles)

        new_tile = Tile(Suit.MANZU, 5)
        hand.add_tile(new_tile)
        assert len(hand.tiles) == 14

        hand.discard(new_tile)
        assert len(hand.tiles) == 13

    def test_standard_winning_hand(self):
        """Test standard winning hand."""
        tiles = parse_tiles("111m222m333m44p55p")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 4)

        assert hand.is_winning_hand(winning_tile)

        tiles = parse_tiles("123m234m345m456m1m")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 1)

        assert hand.is_winning_hand(winning_tile)

        tiles = parse_tiles("123m456p789s11z22z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.HONORS, 2)

        assert hand.is_winning_hand(winning_tile)

    def test_winning_hand_with_open_meld(self):
        """Test winning hand with open meld."""

        tiles = parse_tiles("23m567m789m55z55p1p")
        hand = Hand(tiles)

        hand.pon(Tile(Suit.PINZU, 5))
        hand.discard(Tile(Suit.PINZU, 1))

        winning_tile = Tile(Suit.MANZU, 4)

        assert hand.total_tile_count() == 13
        assert hand.is_winning_hand(winning_tile)

        combinations = hand.get_winning_combinations(winning_tile)
        assert len(combinations) > 0

    def test_winning_hand_with_kan(self):
        """Test winning hand with kan."""

        tiles = parse_tiles("1111m234m345p67s77z")
        hand = Hand(tiles)

        hand.kan(None)

        winning_tile = Tile(Suit.SOUZU, 8)

        waiting_tiles = hand.get_waiting_tiles()
        assert winning_tile in waiting_tiles

        assert hand.is_winning_hand(winning_tile)
        combinations = hand.get_winning_combinations(winning_tile)
        assert len(combinations) > 0

    def test_seven_pairs(self):
        """Test seven pairs."""
        tiles = parse_tiles("11m99m11p99p11s99s1z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.HONORS, 1)

        assert hand.is_tenpai()

        waiting_tiles = hand.get_waiting_tiles()
        assert len(waiting_tiles) == 1

        assert hand.is_winning_hand(winning_tile)

    def test_kokushi_musou(self):
        """Test kokushi musou."""
        tiles = parse_tiles("19m19p19s22z3z4z5z6z7z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.HONORS, 1)

        assert hand.is_tenpai()

        waiting_tiles = hand.get_waiting_tiles()
        assert len(waiting_tiles) == 1

        assert hand.is_winning_hand(winning_tile)

    def test_kokushi_musou_juusanmen(self):
        """Test kokushi musou juusanmen."""
        tiles = parse_tiles("19m19p19s1z2z3z4z5z6z7z")
        hand = Hand(tiles)

        assert hand.is_tenpai()

        waiting_tiles = hand.get_waiting_tiles()
        assert len(waiting_tiles) == 13

        assert hand.is_winning_hand(Tile(Suit.MANZU, 1))
        assert hand.is_winning_hand(Tile(Suit.MANZU, 9))
        assert hand.is_winning_hand(Tile(Suit.PINZU, 1))
        assert hand.is_winning_hand(Tile(Suit.PINZU, 9))
        assert hand.is_winning_hand(Tile(Suit.SOUZU, 1))
        assert hand.is_winning_hand(Tile(Suit.SOUZU, 9))
        assert hand.is_winning_hand(Tile(Suit.HONORS, 1))
        assert hand.is_winning_hand(Tile(Suit.HONORS, 2))
        assert hand.is_winning_hand(Tile(Suit.HONORS, 3))
        assert hand.is_winning_hand(Tile(Suit.HONORS, 4))
        assert hand.is_winning_hand(Tile(Suit.HONORS, 5))
        assert hand.is_winning_hand(Tile(Suit.HONORS, 6))
        assert hand.is_winning_hand(Tile(Suit.HONORS, 7))

    def test_not_winning_hand(self):
        """Test not winning hand."""
        tiles = parse_tiles("123m456p789s1z2z3z4z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 5)

        assert not hand.is_winning_hand(winning_tile)

    def test_tenpai(self):
        """Test tenpai."""
        tiles = parse_tiles("123m456p789s123p4p")
        hand = Hand(tiles)

        assert hand.is_tenpai()

        waiting_tiles = hand.get_waiting_tiles()
        assert Tile(Suit.PINZU, 4) in waiting_tiles

    def test_tenpai_with_open_meld(self):
        """Test tenpai with open meld."""

        # 23m 567m 789m 55z 55p 1p
        tiles = parse_tiles("23m567m789m55z55p1p")
        hand = Hand(tiles)

        hand.pon(Tile(Suit.PINZU, 5))
        hand.discard(Tile(Suit.PINZU, 1))

        assert hand.total_tile_count() == 13
        assert hand.is_tenpai()
        waiting_tiles = hand.get_waiting_tiles()
        assert Tile(Suit.MANZU, 4) in waiting_tiles

    def test_pon(self):
        """Test pon."""
        tiles = parse_tiles("111m234m567m89m11p")
        hand = Hand(tiles)

        tile = Tile(Suit.MANZU, 1)
        assert hand.can_pon(tile)

        meld = hand.pon(tile)
        assert meld.type == MeldType.PON_MELD
        assert len(meld.tiles) == 3
        assert not hand.is_concealed

    def test_chi(self):
        """Test chi."""
        tiles = parse_tiles("23m456p789s1z2z3z4z")
        hand = Hand(tiles)

        tile = Tile(Suit.MANZU, 1)
        sequences = hand.can_chi(tile, from_player=0)
        assert len(sequences) > 0

        meld = hand.chi(tile, sequences[0])
        assert meld.type == MeldType.CHI_MELD
        assert len(meld.tiles) == 3
        assert not hand.is_concealed

    def test_can_kan(self):
        """Test can kan."""
        from pyriichi.tiles import Suit, Tile

        tiles = parse_tiles("111m234m567m123p4p")
        hand = Hand(tiles)
        kan_tile = Tile(Suit.MANZU, 1)
        possible_kan = hand.can_kan(kan_tile)
        assert len(possible_kan) > 0

        tiles = parse_tiles("1111m234m567m123p")
        hand = Hand(tiles)
        possible_closed_kan = hand.can_kan(None)
        assert len(possible_closed_kan) > 0

    def test_cannot_open_kan_from_pair(self):
        """Test cannot open kan from pair."""

        # 111m 234m 567m 89m 11p
        hand = Hand(parse_tiles("111m234m567m89m11p"))
        hand.pon(Tile(Suit.PINZU, 1))

        kan_options = hand.can_kan(Tile(Suit.PINZU, 1))
        assert kan_options == []

    def test_open_kan_upgrade_after_pon(self):
        """Test open kan upgrade after pon."""

        # 123m 456m 789m 11p 99p
        hand = Hand(parse_tiles("123m456m789m11p99p"))
        hand.pon(Tile(Suit.PINZU, 1))

        hand.add_tile(Tile(Suit.PINZU, 1))

        melds = hand.can_kan()
        assert len(melds) > 0
        assert any(meld.type == MeldType.OPEN_KAN for meld in melds)

    def test_meld_invalid_chi(self):
        """Test meld invalid chi."""
        from pyriichi.hand import Meld, MeldType

        with pytest.raises(ValueError, match="吃必須是 3 張牌"):
            Meld(MeldType.CHI_MELD, parse_tiles("1m2m"))

    def test_meld_invalid_pon(self):
        """Test meld invalid pon."""
        with pytest.raises(ValueError, match="碰必須是 3 張牌"):
            Meld(MeldType.PON_MELD, parse_tiles("1m1m"))

    def test_meld_invalid_kan(self):
        """Test meld invalid kan."""
        with pytest.raises(ValueError, match="槓必須是 4 張牌"):
            Meld(MeldType.OPEN_KAN, parse_tiles("1m1m1m"))

        with pytest.raises(ValueError, match="槓必須是 4 張牌"):
            Meld(MeldType.CLOSED_KAN, parse_tiles("1m1m"))

    def test_closed_kan(self):
        """Test closed kan."""
        # 111m 123m 456m 7m 123p
        tiles = parse_tiles("1111m234m567m123p")
        hand = Hand(tiles)
        initial_tile_count = len(hand.tiles)

        meld = hand.kan(None)
        assert meld.type == MeldType.CLOSED_KAN
        assert len(meld.tiles) == 4
        assert len(hand.tiles) == initial_tile_count - 4

    def test_open_kan(self):
        """Test open kan."""
        # 111m 234m 567m 123p 4p
        tiles = parse_tiles("111m234m567m123p4p")
        hand = Hand(tiles)
        initial_tile_count = len(hand.tiles)
        kan_tile = Tile(Suit.MANZU, 1)

        meld = hand.kan(kan_tile)
        assert meld.type == MeldType.OPEN_KAN
        assert len(meld.tiles) == 4
        assert meld.called_tile == kan_tile
        assert len(hand.tiles) == initial_tile_count - 3

    def test_open_kan_upgrade(self):
        """Test open kan upgrade."""
        # 123m 456m 789m 11p 99p
        tiles = parse_tiles("123m456m789m11p99p")
        hand = Hand(tiles)
        kan_tile = Tile(Suit.PINZU, 1)
        hand.pon(kan_tile)
        hand.add_tile(kan_tile)
        initial_tile_count = len(hand.tiles)

        meld = hand.kan(None)
        assert meld.type == MeldType.OPEN_KAN
        assert len(meld.tiles) == 4
        assert meld.called_tile == kan_tile
        assert len(hand.tiles) == initial_tile_count - 1

    def test_tsumo_winning_hand(self):
        """Test tsumo winning hand."""
        # 123m 456p 789s 11z 22z + 2z (tsumo)
        tiles = parse_tiles("123m456p789s11z22z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.HONORS, 2)
        hand.add_tile(winning_tile)

        assert len(hand.tiles) == 14
        assert hand.is_winning_hand(winning_tile, is_tsumo=True)

        tiles = parse_tiles("11m22m33m44m55m66m7m")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 7)
        hand.add_tile(winning_tile)

        assert len(hand.tiles) == 14
        assert hand.is_winning_hand(winning_tile, is_tsumo=True)

        tiles = parse_tiles("19m19p19s1z2z3z4z5z6z7z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 1)
        hand.add_tile(winning_tile)

        assert len(hand.tiles) == 14
        assert hand.is_winning_hand(winning_tile, is_tsumo=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
