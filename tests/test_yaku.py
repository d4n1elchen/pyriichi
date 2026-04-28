"""Test module."""

import pytest

from pyriichi.game_state import GameState, Wind
from pyriichi.hand import CombinationType, Hand, Meld, MeldType, make_combination
from pyriichi.tiles import Suit, Tile
from pyriichi.utils import parse_tiles
from pyriichi.yaku import Yaku, YakuChecker, YakuResult


class TestYakuChecker:
    """Tests for TestYakuChecker."""

    def setup_method(self):
        """Set up test fixtures."""
        self.checker = YakuChecker()
        self.game_state = GameState()
        self.game_state.set_round(Wind.EAST, 1)

    def _open_hand(self) -> Hand:
        """Create an open hand for direct yaku checks."""
        hand = Hand([])
        hand._melds.append(
            Meld(
                MeldType.CHI_MELD,
                parse_tiles("123m"),
                called_tile=Tile(Suit.MANZU, 1),
            )
        )
        return hand

    def test_riichi(self):
        """Test riichi."""
        tiles = parse_tiles("11m22m33m44m55m66m7m")
        hand = Hand(tiles)
        hand.set_riichi(True)

        results = self.checker.check_riichi(hand, self.game_state)
        assert results
        riichi = [r for r in results if r.yaku == Yaku.RIICHI]
        assert len(riichi) == 1
        assert riichi[0].han == 1

    def test_tanyao(self):
        """Test tanyao."""
        tiles = parse_tiles("234m567m345p678p4s")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.SOUZU, 4)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            result = self.checker.check_tanyao(hand, list(combinations[0]))
            assert result is not None
            assert result.yaku == Yaku.TANYAO
            assert result.han == 1

    def test_toitoi(self):
        """Test toitoi."""
        tiles = parse_tiles("111m222m333m444p5p")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 5)
        combinations = hand.get_winning_combinations(winning_tile)

        assert len(combinations) > 0
        result = self.checker.check_toitoi(hand, list(combinations[0]))
        assert result is not None
        assert result.yaku == Yaku.TOITOI
        assert result.han == 2

    def test_iipeikou(self):
        """Test iipeikou."""
        tiles = parse_tiles("123m123m456p789s1z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.HONORS, 1)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            result = self.checker.check_iipeikou(hand, list(combinations[0]))
            assert result is not None
            assert result.yaku == Yaku.IIPEIKOU
            assert result.han == 1

    def test_pinfu_can_combine_with_iipeikou(self):
        """Test pinfu can combine with iipeikou."""
        tiles = parse_tiles("123m123m456p34s22z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.SOUZU, 2)
        combinations = hand.get_winning_combinations(winning_tile)

        assert combinations
        results_by_combination = [
            self.checker.check_all(
                hand,
                winning_tile,
                list(combination),
                self.game_state,
                is_tsumo=False,
                is_ippatsu=False,
            )
            for combination in combinations
        ]

        assert any(
            any(result.yaku == Yaku.PINFU for result in results)
            and any(result.yaku == Yaku.IIPEIKOU for result in results)
            for results in results_by_combination
        )

    def test_pinfu_can_combine_with_ryanpeikou(self):
        """Test pinfu can combine with ryanpeikou."""
        results = [
            YakuResult(Yaku.PINFU, 1, False),
            YakuResult(Yaku.RYANPEIKOU, 3, False),
        ]

        filtered = self.checker._filter_conflicting_yaku(
            results,
            [],
            self.game_state,
        )

        assert YakuResult(Yaku.PINFU, 1, False) in filtered
        assert YakuResult(Yaku.RYANPEIKOU, 3, False) in filtered

    def test_yakuhai_haku_hatsu_chun(self):
        """Test yakuhai haku hatsu chun."""
        tiles = parse_tiles("123m456p789s555z1z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.HONORS, 1)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            results = self.checker.check_yakuhai(
                hand, list(combinations[0]), self.game_state
            )

            has_haku_hatsu_chun = any(
                r.yaku in {Yaku.HAKU, Yaku.HATSU, Yaku.CHUN} for r in results
            )
            assert has_haku_hatsu_chun

    def test_sanshoku_doujun(self):
        """Test sanshoku doujun."""
        tiles = parse_tiles("123m123p123s456p1z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.HONORS, 1)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            result = self.checker.check_sanshoku_doujun(hand, list(combinations[0]))
            assert result is not None
            assert result.yaku == Yaku.SANSHOKU_DOUJUN
            assert result.han == 2

    def test_open_sanshoku_doujun_han(self):
        """Test open sanshoku doujun han."""
        hand = self._open_hand()
        winning_combination = [
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 1),
            make_combination(CombinationType.SEQUENCE, Suit.PINZU, 1),
            make_combination(CombinationType.SEQUENCE, Suit.SOUZU, 1),
            make_combination(CombinationType.TRIPLET, Suit.HONORS, 1),
            make_combination(CombinationType.PAIR, Suit.HONORS, 2),
        ]

        result = self.checker.check_sanshoku_doujun(hand, winning_combination)

        assert result is not None
        assert result.yaku == Yaku.SANSHOKU_DOUJUN
        assert result.han == 1

    def test_ittsu(self):
        """Test ittsu."""
        tiles = parse_tiles("123m456m789m123p1z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.HONORS, 1)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            result = self.checker.check_ittsu(hand, list(combinations[0]))
            assert result is not None
            assert result.yaku == Yaku.ITTSU
            assert result.han == 2

    def test_open_ittsu_han(self):
        """Test open ittsu han."""
        hand = self._open_hand()
        winning_combination = [
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 1),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 4),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 7),
            make_combination(CombinationType.TRIPLET, Suit.HONORS, 1),
            make_combination(CombinationType.PAIR, Suit.HONORS, 2),
        ]

        result = self.checker.check_ittsu(hand, winning_combination)

        assert result is not None
        assert result.yaku == Yaku.ITTSU
        assert result.han == 1

    def test_sanankou(self):
        """Test sanankou."""
        tiles = parse_tiles("111m222m333m456p7p")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 7)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            result = self.checker.check_sanankou(hand, list(combinations[0]))
            assert result is not None
            assert result.yaku == Yaku.SANANKOU
            assert result.han == 2

    def test_chinitsu(self):
        """Test chinitsu."""
        tiles = parse_tiles("123m456m789m123m4m")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 4)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            result = self.checker.check_chinitsu(hand, list(combinations[0]))
            assert result is not None
            assert result.yaku == Yaku.CHINITSU
            assert result.han == 6

    def test_open_chinitsu_han(self):
        """Test open chinitsu han."""
        hand = self._open_hand()
        winning_combination = [
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 1),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 4),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 7),
            make_combination(CombinationType.TRIPLET, Suit.MANZU, 2),
            make_combination(CombinationType.PAIR, Suit.MANZU, 9),
        ]

        result = self.checker.check_chinitsu(hand, winning_combination)

        assert result is not None
        assert result.yaku == Yaku.CHINITSU
        assert result.han == 5

    def test_honitsu(self):
        """Test honitsu."""
        tiles = parse_tiles("123m456m789m111z2z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.HONORS, 2)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            result = self.checker.check_honitsu(hand, list(combinations[0]))
            assert result is not None
            assert result.yaku == Yaku.HONITSU
            assert result.han == 3

    def test_open_honitsu_han(self):
        """Test open honitsu han."""
        hand = self._open_hand()
        winning_combination = [
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 1),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 4),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 7),
            make_combination(CombinationType.TRIPLET, Suit.HONORS, 1),
            make_combination(CombinationType.PAIR, Suit.HONORS, 2),
        ]

        result = self.checker.check_honitsu(hand, winning_combination)

        assert result is not None
        assert result.yaku == Yaku.HONITSU
        assert result.han == 2

    def test_chiitoitsu(self):
        """Test chiitoitsu."""
        tiles = parse_tiles("11m22m33m44m55m66m7m")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 7)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            results = self.checker.check_all(
                hand,
                winning_tile,
                list(combinations[0]) if combinations else [],
                self.game_state,
                is_tsumo=False,
                is_ippatsu=False,
            )
        else:
            results = self.checker.check_all(
                hand,
                winning_tile,
                [],
                self.game_state,
                is_tsumo=False,
                is_ippatsu=False,
            )
        has_chiitoitsu = any(r.yaku == Yaku.CHIITOITSU for r in results)
        assert has_chiitoitsu

    def test_junchan(self):
        """Test junchan."""
        tiles = parse_tiles("123m789m123p789s1m")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 1)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            result = self.checker.check_junchan(
                hand, list(combinations[0]), self.game_state
            )
            assert result is not None
            assert result.yaku == Yaku.JUNCHAN
            assert result.han == 3

    def test_chanta(self):
        """Test chanta."""
        tiles = parse_tiles("123m789m123p111z2z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.HONORS, 2)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            result = self.checker.check_chanta(
                hand, list(combinations[0]), self.game_state
            )
            assert result is not None
            assert result.yaku == Yaku.CHANTA
            assert result.han == 2

    def test_ryanpeikou(self):
        """Test ryanpeikou."""
        tiles = parse_tiles("123m123m456m456m1z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.HONORS, 1)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            found = False
            for combo in combinations:
                result = self.checker.check_ryanpeikou(hand, list(combo))
                if result is not None:
                    assert result.yaku == Yaku.RYANPEIKOU
                    assert result.han == 3
                    found = True
                    break
            assert found, "應該能找到二盃口"

    def test_sanshoku_doukou(self):
        """Test sanshoku doukou."""
        tiles = parse_tiles("111m111p111s234m1z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.HONORS, 1)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            result = self.checker.check_sanshoku_doukou(hand, list(combinations[0]))
            assert result is not None
            assert result.yaku == Yaku.SANSHOKU_DOUKOU
            assert result.han == 2

    def test_shousangen(self):
        """Test shousangen."""
        tiles = parse_tiles("123m456p555z666z7z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.HONORS, 7)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            result = self.checker.check_shousangen(hand, list(combinations[0]))
            assert result is not None
            assert result.yaku == Yaku.SHOUSANGEN
            assert result.han == 2

    def test_honroutou(self):
        """Test honroutou."""
        tiles = parse_tiles("111m999m111p111z2z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.HONORS, 2)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            result = self.checker.check_honroutou(hand, list(combinations[0]))
            assert result is not None
            assert result.yaku == Yaku.HONROUTOU
            assert result.han == 2

    def test_daisangen(self):
        """Test daisangen."""
        tiles = parse_tiles("123m555z666z777z1z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.HONORS, 1)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            results = self.checker.check_all(
                hand,
                winning_tile,
                list(combinations[0]),
                self.game_state,
                is_tsumo=False,
                is_ippatsu=False,
            )
            yakuman = [r for r in results if r.is_yakuman]
            assert len(yakuman) > 0
            assert yakuman[0].yaku == Yaku.DAISANGEN
            assert yakuman[0].han == 13

    def test_yakuman_excludes_non_yakuman_yaku(self):
        """Test yakuman excludes non-yakuman yaku."""
        tiles = parse_tiles("123m555z666z777z1z")
        hand = Hand(tiles)
        hand.set_riichi(True)
        winning_tile = Tile(Suit.HONORS, 1)
        combinations = hand.get_winning_combinations(winning_tile)

        assert combinations
        results = self.checker.check_all(
            hand,
            winning_tile,
            list(combinations[0]),
            self.game_state,
            is_tsumo=False,
            is_ippatsu=True,
        )

        assert any(result.yaku == Yaku.DAISANGEN for result in results)
        assert all(result.is_yakuman for result in results)

    def test_suuankou(self):
        """Test suuankou."""
        tiles = parse_tiles("111m222m333m444m5m")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 5)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            triplets = sum(
                1
                for m in list(combinations[0])
                if m.type in {CombinationType.TRIPLET, CombinationType.KAN}
            )
            if triplets == 4:
                results = self.checker.check_all(
                    hand,
                    winning_tile,
                    list(combinations[0]),
                    self.game_state,
                    is_tsumo=False,
                    is_ippatsu=False,
                )
                yakuman = [r for r in results if r.is_yakuman]
                if yakuman:
                    suuankou_tanki = next(
                        (r for r in yakuman if r.yaku == Yaku.SUUANKOU_TANKI), None
                    )
                    if suuankou_tanki:
                        assert suuankou_tanki.han == 26
                    else:
                        suuankou = next(
                            (r for r in yakuman if r.yaku == Yaku.SUUANKOU), None
                        )
                        if suuankou:
                            assert suuankou.han == 13
                else:
                    pass

    def test_suuankou_tanki(self):
        """Test suuankou tanki."""
        tiles = parse_tiles("111m222m333m444m5m")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 5)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            results = self.checker.check_all(
                hand,
                winning_tile,
                list(combinations[0]),
                self.game_state,
                is_tsumo=False,
                is_ippatsu=False,
            )
            yakuman = [r for r in results if r.is_yakuman]
            if yakuman:
                suuankou_tanki = next(
                    (r for r in yakuman if r.yaku == Yaku.SUUANKOU_TANKI), None
                )
                if suuankou_tanki:
                    assert suuankou_tanki.han == 26
                else:
                    suuankou = next(
                        (r for r in yakuman if r.yaku == Yaku.SUUANKOU), None
                    )
                    if suuankou:
                        assert suuankou.han == 13

    def test_kokushi_musou(self):
        """Test kokushi musou."""
        tiles = parse_tiles("19m19p19s1z2z3z4z5z6z7z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.HONORS, 7)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            results = self.checker.check_all(
                hand,
                winning_tile,
                list(combinations[0]) if combinations else [],
                self.game_state,
                is_tsumo=False,
                is_ippatsu=False,
            )
            yakuman = [r for r in results if r.is_yakuman]
            assert len(yakuman) > 0
            assert yakuman and yakuman[0].yaku in {
                Yaku.KOKUSHI_MUSOU,
                Yaku.KOKUSHI_MUSOU_JUUSANMEN,
            }
            assert yakuman[0].han == 13

    def test_kokushi_musou_excludes_non_yakuman_yaku(self):
        """Test kokushi musou excludes non-yakuman yaku."""
        tiles = parse_tiles("19m19p19s1z2z3z4z5z6z7z")
        hand = Hand(tiles)
        hand.set_riichi(True)
        winning_tile = Tile(Suit.HONORS, 7)

        results = self.checker.check_all(
            hand,
            winning_tile,
            [],
            self.game_state,
            is_tsumo=False,
            is_ippatsu=True,
        )

        assert any(
            result.yaku in {Yaku.KOKUSHI_MUSOU, Yaku.KOKUSHI_MUSOU_JUUSANMEN}
            for result in results
        )
        assert all(result.is_yakuman for result in results)

    def test_tsuuiisou(self):
        """Test tsuuiisou."""
        tiles = parse_tiles("111z222z333z555z6z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.HONORS, 6)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            results = self.checker.check_all(
                hand,
                winning_tile,
                list(combinations[0]),
                self.game_state,
                is_tsumo=False,
                is_ippatsu=False,
            )
            yakuman = [r for r in results if r.is_yakuman]
            assert len(yakuman) > 0
            tsuuiisou = [r for r in yakuman if r.yaku == Yaku.TSUUIISOU]
            if tsuuiisou:
                assert tsuuiisou[0].yaku == Yaku.TSUUIISOU
                assert tsuuiisou[0].han == 13
            else:
                result = self.checker.check_tsuuiisou(hand, list(combinations[0]))
                assert result is not None
                assert result.yaku == Yaku.TSUUIISOU
                assert result.han == 13

    def test_menzen_tsumo(self):
        """Test menzen tsumo."""
        tiles = parse_tiles("123m456m345p678p4s")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.SOUZU, 4)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            results = self.checker.check_all(
                hand,
                winning_tile,
                list(combinations[0]),
                self.game_state,
                is_tsumo=True,
                is_ippatsu=False,
            )
            menzen_tsumo = [r for r in results if r.yaku == Yaku.MENZEN_TSUMO]
            assert len(menzen_tsumo) > 0
            assert menzen_tsumo[0].han == 1

            results = self.checker.check_all(
                hand,
                winning_tile,
                list(combinations[0]),
                self.game_state,
                is_tsumo=False,
                is_ippatsu=False,
            )
            menzen_tsumo = [r for r in results if r.yaku == Yaku.MENZEN_TSUMO]
            assert len(menzen_tsumo) == 0

    def test_ippatsu(self):
        """Test ippatsu."""
        tiles = parse_tiles("234m567m345p678p4s")
        hand = Hand(tiles)
        hand.set_riichi(True)
        winning_tile = Tile(Suit.SOUZU, 4)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            results = self.checker.check_all(
                hand,
                winning_tile,
                list(combinations[0]),
                self.game_state,
                is_tsumo=False,
                is_ippatsu=True,
            )
            ippatsu = [r for r in results if r.yaku == Yaku.IPPATSU]
            assert len(ippatsu) > 0
            assert ippatsu[0].han == 1

            results = self.checker.check_all(
                hand,
                winning_tile,
                list(combinations[0]),
                self.game_state,
                is_tsumo=False,
                is_ippatsu=False,
            )
            ippatsu = [r for r in results if r.yaku == Yaku.IPPATSU]
            assert len(ippatsu) == 0

    def test_ryuuiisou(self):
        """Test ryuuiisou."""
        tiles = parse_tiles("234s234s666s888s6z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.HONORS, 6)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            results = self.checker.check_all(
                hand,
                winning_tile,
                list(combinations[0]),
                self.game_state,
                is_tsumo=False,
                is_ippatsu=False,
            )
            yakuman = [r for r in results if r.is_yakuman]
            assert len(yakuman) > 0
            ryuuiisou = [r for r in yakuman if r.yaku == Yaku.RYUUIISOU]
            if ryuuiisou:
                assert ryuuiisou[0].han == 13
            else:
                result = self.checker.check_ryuuiisou(hand, list(combinations[0]))
                assert result is not None
                assert result.yaku == Yaku.RYUUIISOU
                assert result.han == 13

    def test_chuuren_poutou(self):
        """Test chuuren poutou."""
        tiles = parse_tiles("111m234m567m8m999m")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 1)

        result = self.checker.check_chuuren_poutou(hand, winning_tile)
        assert result is not None
        assert result.yaku in {Yaku.CHUUREN_POUTOU, Yaku.PURE_CHUUREN_POUTOU}
        assert result.han >= 13

    def test_sankantsu(self):
        """Test sankantsu."""
        tiles = parse_tiles("1111m2222p3333s1z")
        hand = Hand(tiles)

        combo_with_kan = [
            make_combination(CombinationType.KAN, Suit.MANZU, 1),
            make_combination(CombinationType.KAN, Suit.PINZU, 2),
            make_combination(CombinationType.KAN, Suit.SOUZU, 3),
            make_combination(CombinationType.PAIR, Suit.HONORS, 1),
        ]
        result = self.checker.check_sankantsu(hand, combo_with_kan)
        assert result is not None
        assert result.yaku == Yaku.SANKANTSU
        assert result.han == 2

    def test_check_all(self):
        """Test check all."""
        tiles = parse_tiles("234m567m345p678p4s")
        hand = Hand(tiles)
        hand.set_riichi(True)
        winning_tile = Tile(Suit.SOUZU, 4)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            results = self.checker.check_all(
                hand,
                winning_tile,
                list(combinations[0]),
                self.game_state,
                is_tsumo=False,
                is_ippatsu=False,
            )
            assert len(results) > 0
            has_riichi = any(r.yaku == Yaku.RIICHI for r in results)
            assert has_riichi

    def test_yaku_conflicts(self):
        """Test yaku conflicts."""
        tiles = parse_tiles("234m567m234p567p5z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.HONORS, 5)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            results = self.checker.check_all(
                hand,
                winning_tile,
                list(combinations[0]),
                self.game_state,
                is_tsumo=False,
                is_ippatsu=False,
            )

        tiles = parse_tiles("123m456m789m234p5s")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.SOUZU, 5)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            results = self.checker.check_all(
                hand,
                winning_tile,
                list(combinations[0]),
                self.game_state,
                is_tsumo=False,
                is_ippatsu=False,
            )

        tiles = parse_tiles("222m222p222s555m1z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.HONORS, 1)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            results = self.checker.check_all(
                hand,
                winning_tile,
                list(combinations[0]),
                self.game_state,
                is_tsumo=False,
                is_ippatsu=False,
            )

        tiles = parse_tiles("123m123m789m789m1z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.HONORS, 1)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            results = self.checker.check_all(
                hand,
                winning_tile,
                list(combinations[0]),
                self.game_state,
                is_tsumo=False,
                is_ippatsu=False,
            )
            has_iipeikou = any(r.yaku == Yaku.IIPEIKOU for r in results)
            has_ryanpeikou = any(r.yaku == Yaku.RYANPEIKOU for r in results)
            if has_ryanpeikou:
                assert not has_iipeikou, "二盃口與一盃口應該互斥"

    def test_shousuushi(self):
        """Test shousuushi."""
        tiles = parse_tiles("111z222z333z44z12m")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 3)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            results = self.checker.check_all(
                hand,
                winning_tile,
                list(combinations[0]),
                self.game_state,
                is_tsumo=False,
                is_ippatsu=False,
            )
            yakuman = [r for r in results if r.is_yakuman]
            assert len(yakuman) > 0
            shousuushi = [r for r in yakuman if r.yaku == Yaku.SHOUSUUSHI]
            if shousuushi:
                assert shousuushi[0].han == 13
            else:
                result = self.checker.check_shousuushi(hand, list(combinations[0]))
                assert result is not None
                assert result.yaku == Yaku.SHOUSUUSHI
                assert result.han == 13
                assert result.is_yakuman

    def test_daisuushi(self):
        """Test daisuushi."""
        tiles = parse_tiles("111z222z333z444z1m")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 1)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            results = self.checker.check_all(
                hand,
                winning_tile,
                list(combinations[0]),
                self.game_state,
                is_tsumo=False,
                is_ippatsu=False,
            )
            yakuman = [r for r in results if r.is_yakuman]
            assert len(yakuman) > 0
            daisuushi = [r for r in yakuman if r.yaku == Yaku.DAISUUSHI]
            if daisuushi:
                assert daisuushi[0].han == 13
            else:
                result = self.checker.check_daisuushi(hand, list(combinations[0]))
                assert result is not None
                assert result.yaku == Yaku.DAISUUSHI
                assert result.han == 13
                assert result.is_yakuman

    def test_chinroutou(self):
        """Test chinroutou."""
        tiles = parse_tiles("111m999m111p999p1s")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.SOUZU, 1)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            results = self.checker.check_all(
                hand,
                winning_tile,
                list(combinations[0]),
                self.game_state,
                is_tsumo=False,
                is_ippatsu=False,
            )
            yakuman = [r for r in results if r.is_yakuman]
            assert len(yakuman) > 0
            chinroutou = [r for r in yakuman if r.yaku == Yaku.CHINROUTOU]
            if chinroutou:
                assert chinroutou[0].han == 13
            else:
                result = self.checker.check_chinroutou(hand, list(combinations[0]))
                assert result is not None
                assert result.yaku == Yaku.CHINROUTOU
                assert result.han == 13
                assert result.is_yakuman

    def test_pinfu_direct(self):
        """Test pinfu direct."""
        tiles = parse_tiles("234m567m234p567p5s")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.SOUZU, 5)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            result = self.checker.check_pinfu(
                hand, list(combinations[0]), self.game_state
            )
            if result:
                assert result.yaku == Yaku.PINFU
                assert result.han == 1
                assert not result.is_yakuman

    def test_tenhou_direct(self):
        """Test tenhou direct."""
        tiles = parse_tiles("123m456m345p678p4s")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.SOUZU, 4)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            self.game_state.set_dealer(0)
            result = self.checker.check_tenhou(
                hand,
                is_tsumo=True,
                is_first_turn=True,
                player_position=0,
                game_state=self.game_state,
            )
            if result:
                assert result.yaku == Yaku.TENHOU
                assert result.han == 13
                assert result.is_yakuman

    def test_chihou_direct(self):
        """Test chihou direct."""
        tiles = parse_tiles("123m456m345p678p4s")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.SOUZU, 4)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            self.game_state.set_dealer(0)
            result = self.checker.check_chihou(
                hand,
                is_tsumo=True,
                is_first_turn=True,
                player_position=1,
                game_state=self.game_state,
            )
            if result:
                assert result.yaku == Yaku.CHIHOU
                assert result.han == 13
                assert result.is_yakuman

    def test_renhou_direct(self):
        """Test renhou direct."""
        tiles = parse_tiles("123m456m345p678p4s")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.SOUZU, 4)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            self.game_state.set_dealer(0)
            result = self.checker.check_renhou(
                hand,
                is_tsumo=False,
                is_first_turn=True,
                player_position=1,
                game_state=self.game_state,
            )
            if result:
                assert result.yaku == Yaku.RENHOU
                assert result.han == 2
                assert not result.is_yakuman

    def test_haitei_direct(self):
        """Test haitei direct."""
        tiles = parse_tiles("123m456m345p678p4s")
        hand = Hand(tiles)

        result = self.checker.check_haitei_houtei(
            hand, is_tsumo=True, is_last_tile=True
        )
        assert result is not None
        assert result.yaku == Yaku.HAITEI
        assert result.han == 1
        assert not result.is_yakuman

    def test_houtei_direct(self):
        """Test houtei direct."""
        tiles = parse_tiles("123m456m345p678p4s")
        hand = Hand(tiles)

        result = self.checker.check_haitei_houtei(
            hand, is_tsumo=False, is_last_tile=True
        )
        assert result is not None
        assert result.yaku == Yaku.HOUTEI
        assert result.han == 1
        assert not result.is_yakuman

    def test_rinshan_direct(self):
        """Test rinshan direct."""
        tiles = parse_tiles("123m456m345p678p4s")
        hand = Hand(tiles)

        result = self.checker.check_rinshan(hand, is_rinshan=True)
        assert result is not None
        assert result.yaku == Yaku.RINSHAN
        assert result.han == 1
        assert not result.is_yakuman

    def test_suukantsu_direct(self):
        """Test suukantsu direct."""
        tiles = parse_tiles("123m12p")
        hand = Hand(tiles)

        combo_with_kan = [
            make_combination(CombinationType.KAN, Suit.MANZU, 1),
            make_combination(CombinationType.KAN, Suit.MANZU, 2),
            make_combination(CombinationType.KAN, Suit.MANZU, 3),
            make_combination(CombinationType.KAN, Suit.PINZU, 1),
            make_combination(CombinationType.PAIR, Suit.PINZU, 2),
        ]
        result = self.checker.check_suukantsu(hand, combo_with_kan)
        assert result is not None
        assert result.yaku == Yaku.SUUKANTSU
        assert result.han == 13
        assert result.is_yakuman

    def test_kokushi_musou_juusanmen_direct(self):
        """Test kokushi musou juusanmen direct."""
        tiles = parse_tiles("19m19p19s1z2z3z4z5z6z7z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.HONORS, 7)

        result = self.checker.check_kokushi_musou(hand, winning_tile)
        assert result is not None
        assert result.yaku == Yaku.KOKUSHI_MUSOU_JUUSANMEN
        assert result.han == 26
        assert result.is_yakuman

    def test_pure_chuuren_poutou_direct(self):
        """Test pure chuuren poutou direct."""
        tiles = parse_tiles("111m234m567m8m999m")
        hand = Hand(tiles)
        for winning_rank in range(1, 10):
            winning_tile = Tile(Suit.MANZU, winning_rank)
            result = self.checker.check_chuuren_poutou(
                hand, winning_tile, self.game_state
            )
            if result:
                if result.yaku == Yaku.PURE_CHUUREN_POUTOU:
                    assert result.han == 26
                    assert result.is_yakuman
                    break

    def test_double_riichi(self):
        """Test double_riichi."""
        tiles = parse_tiles("234m567m345p678p4s")
        hand = Hand(tiles)
        hand.set_riichi(True)
        winning_tile = Tile(Suit.SOUZU, 4)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            results = self.checker.check_all(
                hand,
                winning_tile,
                list(combinations[0]),
                self.game_state,
                is_tsumo=False,
                is_ippatsu=False,
                is_first_turn=True,
            )
            double_riichi = [r for r in results if r.yaku == Yaku.DOUBLE_RIICHI]
            assert len(double_riichi) > 0
            assert double_riichi[0].han == 2
            normal_riichi = [r for r in results if r.yaku == Yaku.RIICHI]
            assert len(normal_riichi) == 0

            results = self.checker.check_all(
                hand,
                winning_tile,
                list(combinations[0]),
                self.game_state,
                is_tsumo=False,
                is_ippatsu=False,
                is_first_turn=False,
            )
            normal_riichi = [r for r in results if r.yaku == Yaku.RIICHI]
            assert len(normal_riichi) > 0
            assert normal_riichi[0].han == 1
            double_riichi = [r for r in results if r.yaku == Yaku.DOUBLE_RIICHI]
            assert len(double_riichi) == 0

    def test_double_riichi_with_ippatsu(self):
        """Test double_riichi with ippatsu."""
        tiles = parse_tiles("234m567m345p678p4s")
        hand = Hand(tiles)
        hand.set_riichi(True)
        winning_tile = Tile(Suit.SOUZU, 4)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            results = self.checker.check_all(
                hand,
                winning_tile,
                list(combinations[0]),
                self.game_state,
                is_tsumo=False,
                is_ippatsu=True,
                is_first_turn=True,
            )
            double_riichi = [r for r in results if r.yaku == Yaku.DOUBLE_RIICHI]
            ippatsu = [r for r in results if r.yaku == Yaku.IPPATSU]
            assert len(double_riichi) > 0
            assert len(ippatsu) > 0
            assert double_riichi[0].han == 2
            assert ippatsu[0].han == 1

    def test_double_riichi_with_chiitoitsu(self):
        """Test double_riichi with chiitoitsu."""
        tiles = parse_tiles("11m22m33m44m55m66m7m")
        hand = Hand(tiles)
        hand.set_riichi(True)
        winning_tile = Tile(Suit.MANZU, 7)

        results = self.checker.check_all(
            hand,
            winning_tile,
            [],
            self.game_state,
            is_tsumo=False,
            is_ippatsu=False,
            is_first_turn=True,
        )
        chiitoitsu = [r for r in results if r.yaku == Yaku.CHIITOITSU]
        double_riichi = [r for r in results if r.yaku == Yaku.DOUBLE_RIICHI]
        assert len(chiitoitsu) > 0
        assert len(double_riichi) > 0
        assert double_riichi[0].han == 2


class TestPinfuSeatWind:
    def test_pinfu_with_seat_wind_pair(self):

        tiles = parse_tiles("123m456p789s234p11z")
        hand = Hand(tiles)

        game_state = GameState()

        winning_tile = Tile(Suit.MANZU, 1)
        tiles.remove(Tile(Suit.MANZU, 1))
        hand = Hand(tiles)

        winning_tile = Tile(Suit.MANZU, 1)

        checker = YakuChecker()

        combinations = hand.get_winning_combinations(winning_tile, is_tsumo=False)
        assert len(combinations) > 0
        winning_combination = combinations[0]

        result = checker.check_pinfu(
            hand=hand,
            winning_combination=winning_combination,
            game_state=game_state,
            winning_tile=winning_tile,
            player_position=0,
        )

        assert result is None, "Should not be pinfu because pair is seat_wind (east)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
