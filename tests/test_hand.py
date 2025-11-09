"""
Hand 類的單元測試
"""

import pytest
from pyriichi.hand import Hand, Meld, MeldType
from pyriichi.tiles import Tile, Suit
from pyriichi.utils import parse_tiles


class TestHand:
    """手牌測試"""

    def test_hand_init(self):
        """測試手牌初始化"""
        # 123m 456p 789s 123z 4z
        tiles = parse_tiles("1m2m3m4p5p6p7s8s9s1z2z3z4z")
        hand = Hand(tiles)

        assert len(hand.tiles) == 13
        assert hand.is_concealed

    def test_add_and_discard(self):
        """測試摸牌和打牌"""
        # 123m 456p 789s 123z 4z
        tiles = parse_tiles("1m2m3m4p5p6p7s8s9s1z2z3z4z")
        hand = Hand(tiles)

        new_tile = Tile(Suit.MANZU, 5)
        hand.add_tile(new_tile)
        assert len(hand.tiles) == 14

        hand.discard(new_tile)
        assert len(hand.tiles) == 13

    def test_standard_winning_hand(self):
        """測試標準和牌型（4組面子+1對子）"""
        # 對對和：111m 222m 333m 44p 55p（和牌牌 4p）
        tiles = parse_tiles("1m1m1m2m2m2m3m3m3m4p4p5p5p")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 4)

        assert hand.is_winning_hand(winning_tile)

        # 順子組合：123m 234m 345m 456m 1m（和牌牌 1m）
        tiles = parse_tiles("1m2m3m2m3m4m3m4m5m4m5m6m1m")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 1)

        assert hand.is_winning_hand(winning_tile)

        # 123m 456p 789s 11z 22z（和牌牌 2z）
        tiles = parse_tiles("1m2m3m4p5p6p7s8s9s1z1z2z2z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.JIHAI, 2)

        assert hand.is_winning_hand(winning_tile)

    def test_winning_hand_with_open_meld(self):
        """測試含有副露的和牌判定"""

        # 手牌：23m 567m 789m 55z 55p 1p
        tiles = parse_tiles("2m3m5m6m7m7m8m9m5z5z5p5p1p")
        hand = Hand(tiles)

        # 副露：碰 5p
        hand.pon(Tile(Suit.PINZU, 5))
        # 打出額外的 1p 使牌數回到 13 張
        hand.discard(Tile(Suit.PINZU, 1))

        # 和牌牌 4p
        winning_tile = Tile(Suit.MANZU, 4)

        assert hand.total_tile_count() == 13
        assert hand.is_winning_hand(winning_tile)

        combinations = hand.get_winning_combinations(winning_tile)
        assert len(combinations) > 0

    def test_seven_pairs(self):
        """測試七對子"""
        # 七對子： 11m 22m 33m 44m 55m 66m 77m（和牌牌 7m）
        tiles = parse_tiles("1m1m2p2p3s3s4p4p5m5m6s6s7m")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 7)

        assert hand.is_tenpai()

        waiting_tiles = hand.get_waiting_tiles()
        assert len(waiting_tiles) == 1

        assert hand.is_winning_hand(winning_tile)

    def test_kokushi_musou(self):
        """測試國士無雙"""
        # 國士無雙：2z 重複，聽 1z
        tiles = parse_tiles("1m9m1p9p1s9s2z2z3z4z5z6z7z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.JIHAI, 1)

        assert hand.is_tenpai()

        waiting_tiles = hand.get_waiting_tiles()
        assert len(waiting_tiles) == 1

        assert hand.is_winning_hand(winning_tile)

    def test_kokushi_musou_juusanmen(self):
        """測試國士無雙十三面"""
        # 國士無雙十三面：13種幺九牌各1張，再有一張幺九牌（13面聽）
        tiles = parse_tiles("1m9m1p9p1s9s1z2z3z4z5z6z7z")
        hand = Hand(tiles)

        assert hand.is_tenpai()

        waiting_tiles = hand.get_waiting_tiles()
        assert len(waiting_tiles) == 13

        assert hand.is_winning_hand(Tile(Suit.MANZU, 1))
        assert hand.is_winning_hand(Tile(Suit.MANZU, 9))
        assert hand.is_winning_hand(Tile(Suit.PINZU, 1))
        assert hand.is_winning_hand(Tile(Suit.PINZU, 9))
        assert hand.is_winning_hand(Tile(Suit.SOZU, 1))
        assert hand.is_winning_hand(Tile(Suit.SOZU, 9))
        assert hand.is_winning_hand(Tile(Suit.JIHAI, 1))
        assert hand.is_winning_hand(Tile(Suit.JIHAI, 2))
        assert hand.is_winning_hand(Tile(Suit.JIHAI, 3))
        assert hand.is_winning_hand(Tile(Suit.JIHAI, 4))
        assert hand.is_winning_hand(Tile(Suit.JIHAI, 5))
        assert hand.is_winning_hand(Tile(Suit.JIHAI, 6))
        assert hand.is_winning_hand(Tile(Suit.JIHAI, 7))

    def test_not_winning_hand(self):
        """測試非和牌"""
        # 隨機手牌
        tiles = parse_tiles("1m2m3m4p5p6p7s8s9s1z2z3z4z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 5)

        assert not hand.is_winning_hand(winning_tile)

    def test_tenpai(self):
        """測試聽牌判定"""
        # 123m 456p 789s 123p 4p (聽 4p)
        tiles = parse_tiles("1m2m3m4p5p6p7s8s9s1p2p3p4p")
        hand = Hand(tiles)

        assert hand.is_tenpai()

        waiting_tiles = hand.get_waiting_tiles()
        assert Tile(Suit.PINZU, 4) in waiting_tiles

    def test_tenpai_with_open_meld(self):
        """測試含副露的聽牌判定"""

        # 23m 567m 789m 55z 55p 1p
        tiles = parse_tiles("2m3m5m6m7m7m8m9m5z5z5p5p1p")
        hand = Hand(tiles)

        hand.pon(Tile(Suit.PINZU, 5))
        hand.discard(Tile(Suit.PINZU, 1))

        assert hand.total_tile_count() == 13
        assert hand.is_tenpai()
        waiting_tiles = hand.get_waiting_tiles()
        assert Tile(Suit.MANZU, 4) in waiting_tiles

    def test_pon(self):
        """測試碰"""
        # 手牌：11123m 456p 789s 12z
        tiles = parse_tiles("1m1m1m2m3m4p5p6p7s8s9s1z2z")
        hand = Hand(tiles)

        tile = Tile(Suit.MANZU, 1)
        assert hand.can_pon(tile)

        meld = hand.pon(tile)
        assert meld.meld_type == MeldType.PON
        assert len(meld.tiles) == 3
        assert not hand.is_concealed

    def test_chi(self):
        """測試吃"""
        # 手牌：23m 456p 789s 123z 4z
        tiles = parse_tiles("2m3m4p5p6p7s8s9s1z2z3z4z")
        hand = Hand(tiles)

        tile = Tile(Suit.MANZU, 1)  # 上家打出的1m
        sequences = hand.can_chi(tile, from_player=0)
        assert len(sequences) > 0

        meld = hand.chi(tile, sequences[0])
        assert meld.meld_type == MeldType.CHI
        assert len(meld.tiles) == 3
        assert not hand.is_concealed

    def test_can_kan(self):
        """測試是否可以槓"""
        from pyriichi.tiles import Tile, Suit

        # 測試明槓（需要三張相同牌）
        # 手牌：111234567m 123p 4p
        tiles = parse_tiles("1m1m1m2m3m4m5m6m7m1p2p3p4p")
        hand = Hand(tiles)
        kan_tile = Tile(Suit.MANZU, 1)
        possible_kan = hand.can_kan(kan_tile)
        assert len(possible_kan) > 0

        # 測試暗槓（需要四張相同牌）
        # 手牌：111m 123m 456m 7m 123p
        tiles = parse_tiles("1m1m1m1m2m3m4m5m6m7m1p2p3p")
        hand = Hand(tiles)
        possible_ankan = hand.can_kan(None)
        assert len(possible_ankan) > 0

    def test_cannot_open_kan_from_pair(self):
        """測試副露對子不能直接槓"""

        # 111m 234m 567m 89m 11p
        hand = Hand(parse_tiles("1m1m1m2m3m4m5m6m7m8m9m1p1p"))
        hand.pon(Tile(Suit.PINZU, 1))

        # 對手打出 1p 時不可再槓
        kan_options = hand.can_kan(Tile(Suit.PINZU, 1))
        assert kan_options == []

    def test_open_kan_upgrade_after_pon(self):
        """測試碰後摸到第四張牌可以加槓"""

        # 123m 456m 789m 11p 99p
        hand = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p1p9p9p"))
        hand.pon(Tile(Suit.PINZU, 1))

        # 摸到第四張牌
        hand.add_tile(Tile(Suit.PINZU, 1))

        melds = hand.can_kan()
        assert len(melds) > 0
        assert any(meld.meld_type == MeldType.KAN for meld in melds)

    def test_meld_invalid_chi(self):
        """測試無效的吃操作"""
        from pyriichi.hand import Meld, MeldType
        from pyriichi.tiles import Tile, Suit

        # 吃必須是 3 張牌
        with pytest.raises(ValueError, match="吃必須是 3 張牌"):
            # 手牌：12m
            Meld(MeldType.CHI, parse_tiles("1m2m"))  # 只有 2 張

    def test_meld_invalid_pon(self):
        """測試無效的碰操作"""
        # 碰必須是 3 張牌
        with pytest.raises(ValueError, match="碰必須是 3 張牌"):
            # 手牌：11m
            Meld(MeldType.PON, parse_tiles("1m1m"))  # 只有 2 張

    def test_meld_invalid_kan(self):
        """測試無效的槓操作"""
        # 槓必須是 4 張牌
        with pytest.raises(ValueError, match="槓必須是 4 張牌"):
            # 手牌：111m
            Meld(MeldType.KAN, parse_tiles("1m1m1m"))  # 只有 3 張

        with pytest.raises(ValueError, match="槓必須是 4 張牌"):
            # 手牌：11m
            Meld(MeldType.ANKAN, parse_tiles("1m1m"))  # 只有 2 張

    def test_ankan(self):
        """測試執行暗槓操作"""
        # 111m 123m 456m 7m 123p
        tiles = parse_tiles("1m1m1m1m2m3m4m5m6m7m1p2p3p")
        hand = Hand(tiles)
        initial_tile_count = len(hand.tiles)

        meld = hand.kan(None)
        assert meld.meld_type == MeldType.ANKAN
        assert len(meld.tiles) == 4
        # 暗槓後，手牌應該減少4張
        assert len(hand.tiles) == initial_tile_count - 4

    def test_open_kan(self):
        """測試執行明槓操作"""
        # 111m 234m 567m 123p 4p
        tiles = parse_tiles("1m1m1m2m3m4m5m6m7m1p2p3p4p")
        hand = Hand(tiles)
        initial_tile_count = len(hand.tiles)
        kan_tile = Tile(Suit.MANZU, 1)

        meld = hand.kan(kan_tile)
        assert meld.meld_type == MeldType.KAN
        assert len(meld.tiles) == 4
        assert meld.called_tile == kan_tile
        # 明槓後，手牌應該減少3張（被槓的牌來自外部，不包含在初始手牌中）
        assert len(hand.tiles) == initial_tile_count - 3

    def test_open_kan_upgrade(self):
        """測試加槓操作"""
        # 123m 456m 789m 11p 99p
        tiles = parse_tiles("1m2m3m4m5m6m7m8m9m1p1p9p9p")
        hand = Hand(tiles)
        kan_tile = Tile(Suit.PINZU, 1)
        hand.pon(kan_tile)
        hand.add_tile(kan_tile)
        initial_tile_count = len(hand.tiles)

        meld = hand.kan(None)
        assert meld.meld_type == MeldType.KAN
        assert len(meld.tiles) == 4
        assert meld.called_tile == kan_tile
        # 加槓後，手牌應該會少一張摸到的加槓牌
        assert len(hand.tiles) == initial_tile_count - 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
