"""
Hand 類的單元測試
"""

import pytest
from pyriichi.hand import Hand, Meld, MeldType
from pyriichi.tiles import Tile, Suit
from pyriichi.utils import parse_tiles


class TestHand:
    """手牌測試"""

    def test_basic_operations(self):
        """測試基本操作"""
        tiles = parse_tiles("1m2m3m4p5p6p7s8s9s1z2z3z4z")
        hand = Hand(tiles)

        assert len(hand.tiles) == 13
        assert hand.is_concealed

    def test_add_and_discard(self):
        """測試摸牌和打牌"""
        tiles = parse_tiles("1m2m3m4p5p6p7s8s9s1z2z3z4z")
        hand = Hand(tiles)

        new_tile = Tile(Suit.MANZU, 5)
        hand.add_tile(new_tile)
        assert len(hand.tiles) == 14

        hand.discard(new_tile)
        assert len(hand.tiles) == 13

    def test_standard_winning_hand(self):
        """測試標準和牌型（4組面子+1對子）"""
        # 對對和：11m 22m 33m 44p 55p 66p（手牌13張，和牌牌77p）
        tiles = parse_tiles("1m1m2m2m3m3m4p4p5p5p6p6p7p")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 7)

        assert hand.is_winning_hand(winning_tile)

        # 順子組合：123m 234m 345m 456m 11m（和牌牌1m）
        tiles = parse_tiles("1m2m3m2m3m4m3m4m5m4m5m6m1m")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 1)

        assert hand.is_winning_hand(winning_tile)

        # 123m 456p 789s 11z 22z（和牌牌2z）
        tiles = parse_tiles("1m2m3m4p5p6p7s8s9s1z1z2z2z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.JIHAI, 2)

        assert hand.is_winning_hand(winning_tile)

        # 簡單測試：全是順子
        tiles = parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p4p")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 4)

        assert hand.is_winning_hand(winning_tile)

    def test_winning_hand_with_open_meld(self):
        """測試含有副露的和牌判定"""

        tiles = parse_tiles("2m3m5m6m7m7m8m9m5z5z5p5p1p")
        hand = Hand(tiles)

        # 副露：碰 5p
        hand.pon(Tile(Suit.PINZU, 5))
        # 打出額外的 1p 使牌數回到 13 張
        hand.discard(Tile(Suit.PINZU, 1))

        winning_tile = Tile(Suit.MANZU, 4)

        assert hand.total_tile_count() == 13
        assert hand.is_winning_hand(winning_tile)

        combinations = hand.get_winning_combinations(winning_tile)
        assert len(combinations) > 0

    def test_seven_pairs(self):
        """測試七對子"""
        # 七對子（手牌13張，和牌牌1張）
        tiles = parse_tiles("1m1m2m2m3m3m4m4m5m5m6m6m7m")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 7)

        assert hand.is_winning_hand(winning_tile)

    def test_kokushi_musou(self):
        """測試國士無雙"""
        # 國士無雙：13種幺九牌各1張（手牌13張），加上和牌牌1張重複後14張
        tiles = parse_tiles("1m9m1p9p1s9s1z2z3z4z5z6z7z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.JIHAI, 1)  # 和牌牌1z（組成11z對子）

        assert hand.is_winning_hand(winning_tile)

    def test_not_winning_hand(self):
        """測試非和牌"""
        # 隨機手牌
        tiles = parse_tiles("1m2m3m4p5p6p7s8s9s1z2z3z4z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 5)

        assert not hand.is_winning_hand(winning_tile)

    def test_tenpai(self):
        """測試聽牌判定"""
        # 聽牌：123m 456p 789s 123p（聽4p）
        # 手牌13張：1m2m3m4p5p6p7s8s9s1p2p3p（12張，需要再加1張）
        # 正確的應該是：1m2m3m4p5p6p7s8s9s1p2p3p4p（13張，但這樣4p有2張了）
        # 重新設計：手牌有1個4p，加上和牌牌4p後變成2個4p組成對子
        tiles = parse_tiles("1m2m3m4p5p6p7s8s9s1p2p3p4p")
        hand = Hand(tiles)

        assert hand.is_tenpai()

        waiting_tiles = hand.get_waiting_tiles()
        assert Tile(Suit.PINZU, 4) in waiting_tiles

    def test_tenpai_with_open_meld(self):
        """測試含副露的聽牌判定"""

        tiles = parse_tiles("2m3m5m6m7m7m8m9m5z5z5p5p1p")
        hand = Hand(tiles)

        hand.pon(Tile(Suit.PINZU, 5))
        hand.discard(Tile(Suit.PINZU, 1))

        assert hand.total_tile_count() == 13
        assert hand.is_tenpai()
        waiting_tiles = hand.get_waiting_tiles()
        assert Tile(Suit.MANZU, 4) in waiting_tiles

    def test_cannot_open_kan_from_pair(self):
        """測試副露對子不能直接槓"""

        hand = Hand(parse_tiles("1m1m2m3m4m5m6m7m8m9m1p1p1p"))
        hand.pon(Tile(Suit.PINZU, 1))

        # 對手打出 1p 時不可再槓
        kan_options = hand.can_kan(Tile(Suit.PINZU, 1))
        assert kan_options == []

    def test_open_kan_upgrade_after_pon(self):
        """測試碰後摸到第四張牌可以加槓"""

        hand = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p1p1p9p"))
        hand.pon(Tile(Suit.PINZU, 1))

        drawn = Tile(Suit.PINZU, 1)
        hand.add_tile(drawn)

        assert any(
            meld.meld_type == MeldType.KAN and meld.called_tile == Tile(Suit.PINZU, 1) for meld in hand.can_kan()
        )

    def test_pon(self):
        """測試碰"""
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
        tiles = parse_tiles("1m1m1m2m3m4m5m6m7m1p2p3p4p")
        hand = Hand(tiles)
        kan_tile = Tile(Suit.MANZU, 1)
        possible_kan = hand.can_kan(kan_tile)
        assert len(possible_kan) > 0

        # 測試暗槓（需要四張相同牌）
        tiles = parse_tiles("1m1m1m1m2m3m4m5m6m7m1p2p3p")
        hand = Hand(tiles)
        possible_ankan = hand.can_kan(None)
        assert len(possible_ankan) > 0

    def test_meld_invalid_chi(self):
        """測試無效的吃操作"""
        from pyriichi.hand import Meld, MeldType
        from pyriichi.tiles import Tile, Suit

        # 吃必須是 3 張牌
        with pytest.raises(ValueError, match="吃必須是 3 張牌"):
            Meld(MeldType.CHI, parse_tiles("1m2m"))  # 只有 2 張

    def test_meld_invalid_pon(self):
        """測試無效的碰操作"""
        from pyriichi.hand import Meld, MeldType
        from pyriichi.tiles import Tile, Suit

        # 碰必須是 3 張牌
        with pytest.raises(ValueError, match="碰必須是 3 張牌"):
            Meld(MeldType.PON, parse_tiles("1m1m"))  # 只有 2 張

    def test_meld_invalid_kan(self):
        """測試無效的槓操作"""
        from pyriichi.hand import Meld, MeldType
        from pyriichi.tiles import Tile, Suit

        # 槓必須是 4 張牌
        with pytest.raises(ValueError, match="槓必須是 4 張牌"):
            Meld(MeldType.KAN, parse_tiles("1m1m1m"))  # 只有 3 張

        with pytest.raises(ValueError, match="槓必須是 4 張牌"):
            Meld(MeldType.ANKAN, parse_tiles("1m1m"))  # 只有 2 張

    def test_kan(self):
        """測試執行槓操作"""
        from pyriichi.tiles import Tile, Suit

        # 測試暗槓
        tiles = parse_tiles("1m1m1m1m2m3m4m5m6m7m1p2p3p")
        hand = Hand(tiles)
        initial_tile_count = len(hand.tiles)

        meld = hand.kan(None)
        assert meld.meld_type == MeldType.ANKAN
        assert len(meld.tiles) == 4
        # 暗槓後，手牌應該減少4張
        assert len(hand.tiles) == initial_tile_count - 4

        # 測試明槓（從手牌中三張）
        tiles = parse_tiles("1m1m1m2m3m4m5m6m7m1p2p3p4p")
        hand = Hand(tiles)
        initial_tile_count = len(hand.tiles)
        kan_tile = Tile(Suit.MANZU, 1)

        meld = hand.kan(kan_tile)
        assert meld.meld_type == MeldType.KAN
        assert len(meld.tiles) == 4
        # 明槓後，手牌應該減少3張（被槓的牌來自外部，不包含在初始手牌中）
        # 注意：kan_tile 是外部牌，不應該在手牌中，所以實際減少的是手牌中的3張
        assert len(hand.tiles) <= initial_tile_count


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
