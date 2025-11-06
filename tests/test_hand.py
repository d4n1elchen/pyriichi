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
        tiles = [
            Tile(Suit.MANZU, 1), Tile(Suit.MANZU, 2), Tile(Suit.MANZU, 3),
            Tile(Suit.MANZU, 2), Tile(Suit.MANZU, 3), Tile(Suit.MANZU, 4),
            Tile(Suit.MANZU, 3), Tile(Suit.MANZU, 4), Tile(Suit.MANZU, 5),
            Tile(Suit.MANZU, 4), Tile(Suit.MANZU, 5), Tile(Suit.MANZU, 6),
            Tile(Suit.MANZU, 1),
        ]
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 1)

        assert hand.is_winning_hand(winning_tile)

        # 123m 456p 789s 11z 22z（和牌牌2z）
        tiles = [
            Tile(Suit.MANZU, 1), Tile(Suit.MANZU, 2), Tile(Suit.MANZU, 3),
            Tile(Suit.PINZU, 4), Tile(Suit.PINZU, 5), Tile(Suit.PINZU, 6),
            Tile(Suit.SOZU, 7), Tile(Suit.SOZU, 8), Tile(Suit.SOZU, 9),
            Tile(Suit.JIHAI, 1), Tile(Suit.JIHAI, 1),
            Tile(Suit.JIHAI, 2), Tile(Suit.JIHAI, 2),
        ]
        hand = Hand(tiles)
        winning_tile = Tile(Suit.JIHAI, 2)

        assert hand.is_winning_hand(winning_tile)

        # 簡單測試：全是順子
        tiles = [
            Tile(Suit.MANZU, 1), Tile(Suit.MANZU, 2), Tile(Suit.MANZU, 3),
            Tile(Suit.MANZU, 4), Tile(Suit.MANZU, 5), Tile(Suit.MANZU, 6),
            Tile(Suit.MANZU, 7), Tile(Suit.MANZU, 8), Tile(Suit.MANZU, 9),
            Tile(Suit.PINZU, 1), Tile(Suit.PINZU, 2), Tile(Suit.PINZU, 3),
            Tile(Suit.PINZU, 4),
        ]
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 4)

        assert hand.is_winning_hand(winning_tile)

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
        tiles = [
            Tile(Suit.MANZU, 1), Tile(Suit.MANZU, 9),
            Tile(Suit.PINZU, 1), Tile(Suit.PINZU, 9),
            Tile(Suit.SOZU, 1), Tile(Suit.SOZU, 9),
            Tile(Suit.JIHAI, 1), Tile(Suit.JIHAI, 2),
            Tile(Suit.JIHAI, 3), Tile(Suit.JIHAI, 4),
            Tile(Suit.JIHAI, 5), Tile(Suit.JIHAI, 6),
            Tile(Suit.JIHAI, 7),  # 13張手牌
        ]
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
        tiles = [
            Tile(Suit.MANZU, 1), Tile(Suit.MANZU, 2), Tile(Suit.MANZU, 3),
            Tile(Suit.PINZU, 4), Tile(Suit.PINZU, 5), Tile(Suit.PINZU, 6),
            Tile(Suit.SOZU, 7), Tile(Suit.SOZU, 8), Tile(Suit.SOZU, 9),
            Tile(Suit.PINZU, 1), Tile(Suit.PINZU, 2), Tile(Suit.PINZU, 3),
            Tile(Suit.PINZU, 4),  # 13張手牌
        ]
        hand = Hand(tiles)

        assert hand.is_tenpai()

        waiting_tiles = hand.get_waiting_tiles()
        assert Tile(Suit.PINZU, 4) in waiting_tiles

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
