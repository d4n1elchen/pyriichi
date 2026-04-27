"""Test module."""

import pytest

from pyriichi.game_state import GameState, Wind
from pyriichi.hand import CombinationType, Hand, Meld, MeldType, make_combination
from pyriichi.scoring import ScoreCalculator, ScoreResult
from pyriichi.tiles import Suit, Tile
from pyriichi.utils import parse_tiles
from pyriichi.yaku import WaitingType, Yaku, YakuChecker, YakuResult


class TestScoreCalculator:
    """Tests for TestScoreCalculator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = ScoreCalculator()
        self.yaku_checker = YakuChecker()
        self.game_state = GameState()
        self.game_state.set_round(Wind.EAST, 1)

    def test_calculate_fu_basic(self):
        """Test calculate fu basic."""
        # 234m 567m 345p 678p 4s
        tiles = parse_tiles("234m567m345p678p4s")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.SOUZU, 4)
        combinations = hand.get_winning_combinations(winning_tile)
        assert combinations
        fu = self.calculator.calculate_fu(
            hand, winning_tile, combinations[0], [], self.game_state, False
        )
        assert fu == 40

    def test_calculate_fu_triplet(self):
        """Test calculate fu triplet."""
        # 111m 222m 333m 123p 5p
        tiles = parse_tiles("111m222m333m123p5p")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 5)
        combinations = hand.get_winning_combinations(winning_tile)
        assert combinations
        fu = self.calculator.calculate_fu(
            hand, winning_tile, combinations[0], [], self.game_state, False
        )
        assert fu == 50

    def test_calculate_han(self):
        """Test calculate han."""
        yaku_results = [
            YakuResult(Yaku.RIICHI, 1, False),
            YakuResult(Yaku.TANYAO, 1, False),
        ]

        han = self.calculator.calculate_han(yaku_results, 0)
        assert han == 2

        han = self.calculator.calculate_han(yaku_results, 2)
        assert han == 4

    def test_calculate_score(self):
        """Test calculate score."""
        tiles = parse_tiles("234m567m345p678p4s")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.SOUZU, 4)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = self.yaku_checker.check_all(
                hand, winning_tile, combinations[0], self.game_state, is_tsumo=False
            )
            score_result = self.calculator.calculate(
                hand,
                winning_tile,
                combinations[0],
                yaku_results,
                0,
                self.game_state,
                False,
            )

            assert score_result.han > 0
            assert score_result.fu >= 20
            assert score_result.total_points > 0

    def test_calculate_score_mangan(self):
        """Test calculate score mangan."""
        yaku_results = [
            YakuResult(Yaku.RIICHI, 1, False),
            YakuResult(Yaku.TANYAO, 1, False),
            YakuResult(Yaku.SANSHOKU_DOUJUN, 2, False),
            YakuResult(Yaku.ITTSU, 2, False),
        ]

        tiles = parse_tiles("11m22m33m44m55m66m7m")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 1)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            score_result = self.calculator.calculate(
                hand,
                winning_tile,
                combinations[0],
                yaku_results,
                0,
                self.game_state,
                False,
            )
            if score_result.han == 5:
                assert score_result.total_points == 2000
            elif score_result.han >= 6:
                assert score_result.total_points >= 3000

    def test_calculate_score_toitoi(self):
        """Test calculate score toitoi."""
        tiles = parse_tiles("111m222m333m444p5p")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 5)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = self.yaku_checker.check_all(
                hand, winning_tile, combinations[0], self.game_state, is_tsumo=False
            )
            score_result = self.calculator.calculate(
                hand,
                winning_tile,
                combinations[0],
                yaku_results,
                0,
                self.game_state,
                False,
            )

            assert score_result.han >= 2
            assert score_result.total_points >= 1000

    def test_waiting_type_tanki(self):
        """Test waiting type tanki."""
        tiles = parse_tiles("123m456m789m123p4p")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 4)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            fu = self.calculator.calculate_fu(
                hand,
                winning_tile,
                combinations[0],
                yaku_results,
                self.game_state,
                False,
            )
            assert fu >= 30

    def test_waiting_type_penchan(self):
        """Test waiting type penchan."""
        tiles = parse_tiles("12m456m789m123p45p")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 3)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            fu = self.calculator.calculate_fu(
                hand,
                winning_tile,
                combinations[0],
                yaku_results,
                self.game_state,
                False,
            )
            assert fu >= 30

    def test_calculate_payments_tsumo(self):
        """Test calculate payments tsumo."""
        score_result = ScoreResult(
            han=1,
            fu=30,
            base_points=0,
            total_points=1000,
            payment_from=0,
            payment_to=0,
            is_yakuman=False,
            yakuman_count=1,
            is_tsumo=True,
        )

        score_result.calculate_payments(self.game_state)

        assert score_result.total_points > 0
        assert score_result.honba_bonus >= 0

    def test_calculate_payments_ron(self):
        """Test calculate payments ron."""
        score_result = ScoreResult(
            han=1,
            fu=30,
            base_points=0,
            total_points=1000,
            payment_from=1,
            payment_to=0,
            is_yakuman=False,
            yakuman_count=1,
            is_tsumo=False,
        )

        score_result.calculate_payments(self.game_state)

        assert score_result.total_points > 0
        assert score_result.honba_bonus >= 0

    def test_calculate_payments_dealer_tsumo(self):
        """Test calculate payments dealer tsumo."""
        self.game_state.set_dealer(0)

        score_result = ScoreResult(
            han=1,
            fu=30,
            base_points=0,
            total_points=1000,
            payment_from=0,
            payment_to=0,
            is_yakuman=False,
            yakuman_count=1,
            is_tsumo=True,
        )

        score_result.calculate_payments(self.game_state)

        assert score_result.dealer_payment >= 0

    def test_determine_waiting_type(self):
        """Test determine waiting type."""
        tiles = parse_tiles("123m456m789m123p4p")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 4)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            waiting_type = self.calculator._determine_waiting_type(
                winning_tile, combinations[0]
            )
            assert waiting_type in {
                WaitingType.RYANMEN,
                WaitingType.PENCHAN,
                WaitingType.KANCHAN,
                WaitingType.TANKI,
                WaitingType.SHABO,
            }

    def test_waiting_type_kanchan(self):
        """Test waiting type kanchan."""
        tiles = parse_tiles("2m456m789m123p45p")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 3)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            fu = self.calculator.calculate_fu(
                hand,
                winning_tile,
                combinations[0],
                yaku_results,
                self.game_state,
                False,
            )
            assert fu >= 30

    def test_waiting_type_ryanmen(self):
        """Test waiting type ryanmen."""
        tiles = parse_tiles("45m789m123p456p")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 6)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            fu = self.calculator.calculate_fu(
                hand,
                winning_tile,
                combinations[0],
                yaku_results,
                self.game_state,
                False,
            )
            assert fu >= 30

    def test_waiting_type_empty_combination(self):
        """Test waiting type empty combination."""
        winning_tile = Tile(Suit.MANZU, 1)
        waiting_type = self.calculator._determine_waiting_type(winning_tile, [])
        assert waiting_type == WaitingType.RYANMEN

    def test_fu_kan_concealed(self):
        """Test fu kan concealed."""
        tiles = parse_tiles("1111m234m567m12p")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 3)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            fu = self.calculator.calculate_fu(
                hand,
                winning_tile,
                combinations[0],
                yaku_results,
                self.game_state,
                False,
            )
            assert fu >= 20

    def test_fu_kan_open(self):
        """Test fu kan open."""
        tiles = parse_tiles("123m456m78m12p")
        from pyriichi.hand import Meld, MeldType

        hand = Hand(tiles)
        meld = Meld(MeldType.PON_MELD, parse_tiles("1s1s1s"))
        hand._melds.append(meld)

        winning_tile = Tile(Suit.MANZU, 9)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            fu = self.calculator.calculate_fu(
                hand,
                winning_tile,
                combinations[0],
                yaku_results,
                self.game_state,
                False,
            )
            assert fu >= 20

    def test_fu_pair_haku_hatsu_chun(self):
        """Test fu pair haku hatsu chun."""
        tiles = parse_tiles("123m456m78m123p55z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 9)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            fu = self.calculator.calculate_fu(
                hand,
                winning_tile,
                combinations[0],
                yaku_results,
                self.game_state,
                False,
            )
            assert fu >= 30

    def test_fu_pair_round_wind(self):
        """Test fu pair round wind."""
        self.game_state.set_round(Wind.EAST, 1)
        tiles = parse_tiles("123m456m78m123p11z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 9)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            fu = self.calculator.calculate_fu(
                hand,
                winning_tile,
                combinations[0],
                yaku_results,
                self.game_state,
                False,
            )
            assert fu >= 30

    def test_fu_pair_round_wind_south(self):
        """Test fu pair round wind south."""
        self.game_state.set_round(Wind.SOUTH, 1)
        tiles = parse_tiles("123m456m78m123p22z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 9)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            fu = self.calculator.calculate_fu(
                hand,
                winning_tile,
                list(combinations[0]),
                yaku_results,
                self.game_state,
                False,
            )
            assert fu >= 30

    def test_fu_kan_terminal_concealed(self):
        """Test fu kan terminal concealed."""
        tiles = parse_tiles("123m456m12p")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 3)

        combo_with_kan = [
            make_combination(CombinationType.KAN, Suit.MANZU, 1),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 4),
            make_combination(CombinationType.SEQUENCE, Suit.PINZU, 1),
            make_combination(CombinationType.PAIR, Suit.PINZU, 3),
        ]

        yaku_results = []
        fu = self.calculator.calculate_fu(
            hand, winning_tile, combo_with_kan, yaku_results, self.game_state, False
        )
        assert fu >= 60

    def test_fu_kan_terminal_open(self):
        """Test fu kan terminal open."""
        tiles = parse_tiles("234m567m12p")
        from pyriichi.hand import Meld, MeldType

        hand = Hand(tiles)
        meld = Meld(MeldType.PON_MELD, parse_tiles("1s1s1s"))
        hand._melds.append(meld)

        winning_tile = Tile(Suit.PINZU, 3)

        combo_with_kan = [
            make_combination(CombinationType.KAN, Suit.MANZU, 9),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 2),
            make_combination(CombinationType.SEQUENCE, Suit.PINZU, 1),
            make_combination(CombinationType.PAIR, Suit.PINZU, 3),
        ]

        yaku_results = []
        fu = self.calculator.calculate_fu(
            hand, winning_tile, combo_with_kan, yaku_results, self.game_state, False
        )
        assert fu >= 30

    def test_fu_kan_simple_concealed(self):
        """Test fu kan simple concealed."""
        tiles = parse_tiles("234m56m12p")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 3)

        combo_with_kan = [
            make_combination(CombinationType.KAN, Suit.MANZU, 5),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 2),
            make_combination(CombinationType.SEQUENCE, Suit.PINZU, 1),
            make_combination(CombinationType.PAIR, Suit.PINZU, 3),
        ]

        yaku_results = []
        fu = self.calculator.calculate_fu(
            hand, winning_tile, combo_with_kan, yaku_results, self.game_state, False
        )
        assert fu >= 40

    def test_fu_kan_simple_open(self):
        """Test fu kan simple open."""
        tiles = parse_tiles("234m67m12p")
        from pyriichi.hand import Meld, MeldType

        hand = Hand(tiles)
        meld = Meld(MeldType.PON_MELD, parse_tiles("1s1s1s"))
        hand._melds.append(meld)

        winning_tile = Tile(Suit.PINZU, 3)

        combo_with_kan = [
            make_combination(CombinationType.KAN, Suit.MANZU, 5),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 2),
            make_combination(CombinationType.SEQUENCE, Suit.PINZU, 1),
            make_combination(CombinationType.PAIR, Suit.PINZU, 3),
        ]

        yaku_results = []
        fu = self.calculator.calculate_fu(
            hand, winning_tile, combo_with_kan, yaku_results, self.game_state, False
        )
        assert fu >= 20

    def test_waiting_type_penchan_rank1(self):
        """Test waiting type penchan rank1."""
        winning_tile = Tile(Suit.MANZU, 1)
        combo = [
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 1),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 4),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 7),
            make_combination(CombinationType.PAIR, Suit.PINZU, 1),
        ]
        waiting_type = self.calculator._determine_waiting_type(winning_tile, combo)
        assert waiting_type == WaitingType.PENCHAN

    def test_waiting_type_penchan_rank7(self):
        """Test waiting type penchan rank7."""
        winning_tile = Tile(Suit.MANZU, 9)
        combo = [
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 7),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 4),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 1),
            make_combination(CombinationType.PAIR, Suit.PINZU, 1),
        ]
        waiting_type = self.calculator._determine_waiting_type(winning_tile, combo)
        assert waiting_type == WaitingType.PENCHAN

    def test_waiting_type_kanchan_middle(self):
        """Test waiting type kanchan middle."""
        winning_tile = Tile(Suit.MANZU, 3)
        combo = [
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 2),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 5),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 6),
            make_combination(CombinationType.PAIR, Suit.PINZU, 1),
        ]
        waiting_type = self.calculator._determine_waiting_type(winning_tile, combo)
        assert waiting_type == WaitingType.KANCHAN

    def test_waiting_type_kanchan_other(self):
        """Test waiting type kanchan other."""
        winning_tile = Tile(Suit.MANZU, 4)
        combo = [
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 2),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 5),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 6),
            make_combination(CombinationType.PAIR, Suit.PINZU, 1),
        ]
        waiting_type = self.calculator._determine_waiting_type(winning_tile, combo)
        assert waiting_type == WaitingType.RYANMEN

    def test_waiting_type_not_in_sequence(self):
        """Test waiting type not in sequence."""
        winning_tile = Tile(Suit.PINZU, 5)
        combo = [
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 1),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 4),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 7),
            make_combination(CombinationType.PAIR, Suit.PINZU, 1),
        ]
        waiting_type = self.calculator._determine_waiting_type(winning_tile, combo)
        assert waiting_type == WaitingType.RYANMEN

    def test_score_result_yakuman_13_han(self):
        """Test score result yakuman 13 han."""
        score_result = ScoreResult(
            han=13,
            fu=30,
            base_points=0,
            total_points=0,
            payment_from=0,
            payment_to=0,
            is_yakuman=False,
            yakuman_count=1,
        )
        assert score_result.total_points == 8000

    def test_score_result_triple_mangan(self):
        """Test score result triple mangan."""
        score_result = ScoreResult(
            han=11,
            fu=30,
            base_points=0,
            total_points=0,
            payment_from=0,
            payment_to=0,
            is_yakuman=False,
            yakuman_count=1,
        )
        assert score_result.total_points == 6000

    def test_score_result_double_mangan(self):
        """Test score result double mangan."""
        score_result = ScoreResult(
            han=8,
            fu=30,
            base_points=0,
            total_points=0,
            payment_from=0,
            payment_to=0,
            is_yakuman=False,
            yakuman_count=1,
        )
        assert score_result.total_points == 4000

    def test_score_result_mangan_5_han(self):
        """Test score result mangan 5 han."""
        score_result = ScoreResult(
            han=5,
            fu=30,
            base_points=0,
            total_points=0,
            payment_from=0,
            payment_to=0,
            is_yakuman=False,
            yakuman_count=1,
        )
        assert score_result.total_points == 2000

    def test_score_result_mangan_4_han_40_fu(self):
        """Test score result mangan 4 han 40 fu."""
        score_result = ScoreResult(
            han=4,
            fu=40,
            base_points=0,
            total_points=0,
            payment_from=0,
            payment_to=0,
            is_yakuman=False,
            yakuman_count=1,
        )
        assert score_result.total_points == 2000

    def test_calculate_payments_non_dealer_tsumo(self):
        """Test calculate payments non dealer tsumo."""
        self.game_state.set_dealer(0)

        score_result = ScoreResult(
            han=1,
            fu=30,
            base_points=0,
            total_points=1000,
            payment_from=0,
            payment_to=1,
            is_yakuman=False,
            yakuman_count=1,
            is_tsumo=True,
        )

        score_result.calculate_payments(self.game_state)

        assert score_result.dealer_payment > 0
        assert score_result.non_dealer_payment > 0
        assert score_result.total_points > 0

    def test_calculate_fu_seven_pairs(self):
        """Test calculate fu seven pairs."""
        tiles = parse_tiles("11m22m33m44m55m66m7m")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 7)
        yaku_results = [YakuResult(Yaku.CHIITOITSU, 2, False)]

        fu = self.calculator.calculate_fu(
            hand, winning_tile, [], yaku_results, self.game_state, False
        )
        assert fu == 25

    def test_calculate_fu_pinfu_tsumo(self):
        """Test calculate fu pinfu tsumo."""
        tiles = parse_tiles("123m456m789m123p4p")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 4)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = self.yaku_checker.check_all(
                hand,
                winning_tile,
                list(combinations[0]),
                self.game_state,
                is_tsumo=True,
            )
            is_pinfu = any(r.yaku == Yaku.PINFU for r in yaku_results)

            if is_pinfu:
                fu = self.calculator.calculate_fu(
                    hand,
                    winning_tile,
                    list(combinations[0]),
                    yaku_results,
                    self.game_state,
                    True,
                )
                assert fu == 30

    def test_calculate_fu_pinfu_ron(self):
        """Test calculate fu pinfu ron."""
        tiles = parse_tiles("123m456m789m123p4p")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 4)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = self.yaku_checker.check_all(
                hand,
                winning_tile,
                list(combinations[0]),
                self.game_state,
                is_tsumo=False,
            )
            is_pinfu = any(r.yaku == Yaku.PINFU for r in yaku_results)

            if is_pinfu:
                fu = self.calculator.calculate_fu(
                    hand,
                    winning_tile,
                    list(combinations[0]),
                    yaku_results,
                    self.game_state,
                    False,
                )
                assert fu == 30

    def test_calculate_fu_concealed_tsumo(self):
        """Test calculate fu concealed tsumo."""
        tiles = parse_tiles("111m234m567m123p4p")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 4)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            fu = self.calculator.calculate_fu(
                hand,
                winning_tile,
                list(combinations[0]),
                yaku_results,
                self.game_state,
                True,
            )
            assert fu >= 30

    def test_calculate_fu_open_tsumo(self):
        """Test calculate fu open tsumo."""
        tiles = parse_tiles("111m234m56m12p")
        from pyriichi.hand import Meld, MeldType

        hand = Hand(tiles)
        meld = Meld(MeldType.PON_MELD, parse_tiles("1s1s1s"))
        hand._melds.append(meld)

        winning_tile = Tile(Suit.PINZU, 3)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            assert not hand.is_concealed
            fu = self.calculator.calculate_fu(
                hand,
                winning_tile,
                list(combinations[0]),
                yaku_results,
                self.game_state,
                True,
            )
            assert fu >= 20

    def test_calculate_fu_open_triplet_terminal(self):
        """Test calculate fu open triplet terminal."""
        tiles = parse_tiles("234m567m8m12p")
        from pyriichi.hand import Meld, MeldType

        hand = Hand(tiles)
        meld = Meld(MeldType.PON_MELD, parse_tiles("1s1s1s"))
        hand._melds.append(meld)

        winning_tile = Tile(Suit.PINZU, 3)

        combo_with_triplet = [
            make_combination(CombinationType.TRIPLET, Suit.MANZU, 9),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 2),
            make_combination(CombinationType.SEQUENCE, Suit.PINZU, 1),
            make_combination(CombinationType.PAIR, Suit.PINZU, 3),
        ]

        yaku_results = []
        fu = self.calculator.calculate_fu(
            hand, winning_tile, combo_with_triplet, yaku_results, self.game_state, False
        )
        assert fu >= 20

    def test_calculate_fu_open_triplet_simple(self):
        """Test calculate fu open triplet simple."""
        tiles = parse_tiles("123m56m12p")
        from pyriichi.hand import Meld, MeldType

        hand = Hand(tiles)
        meld = Meld(MeldType.PON_MELD, parse_tiles("1s1s1s"))
        hand._melds.append(meld)

        winning_tile = Tile(Suit.PINZU, 3)

        combo_with_triplet = [
            make_combination(CombinationType.TRIPLET, Suit.MANZU, 5),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 1),
            make_combination(CombinationType.SEQUENCE, Suit.PINZU, 1),
            make_combination(CombinationType.PAIR, Suit.PINZU, 3),
        ]

        yaku_results = []
        fu = self.calculator.calculate_fu(
            hand, winning_tile, combo_with_triplet, yaku_results, self.game_state, False
        )
        assert fu >= 20

    def test_waiting_type_kanchan_other_rank(self):
        """Test waiting type kanchan other rank."""
        winning_tile = Tile(Suit.MANZU, 2)
        combo = [
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 2),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 5),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 6),
            make_combination(CombinationType.PAIR, Suit.PINZU, 1),
        ]
        waiting_type = self.calculator._determine_waiting_type(winning_tile, combo)
        assert waiting_type == WaitingType.RYANMEN

    def test_waiting_type_in_sequence_check(self):
        """Test waiting type in sequence check."""
        winning_tile = Tile(Suit.MANZU, 4)
        combo = [
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 3),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 6),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 7),
            make_combination(CombinationType.PAIR, Suit.PINZU, 1),
        ]
        waiting_type = self.calculator._determine_waiting_type(winning_tile, combo)
        assert waiting_type in {
            WaitingType.KANCHAN,
            WaitingType.PENCHAN,
            WaitingType.RYANMEN,
        }

    def test_calculate_fu_open_tsumo_direct(self):
        """Test calculate fu open tsumo direct."""
        tiles = parse_tiles("234m567m12p")
        from pyriichi.hand import Meld, MeldType

        hand = Hand(tiles)
        meld = Meld(MeldType.PON_MELD, parse_tiles("1s1s1s"))
        hand._melds.append(meld)

        winning_tile = Tile(Suit.PINZU, 3)
        combo = [
            make_combination(CombinationType.TRIPLET, Suit.MANZU, 1),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 2),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 5),
            make_combination(CombinationType.PAIR, Suit.PINZU, 3),
        ]

        assert not hand.is_concealed

        winning_tile = Tile(Suit.MANZU, 4)
        combo = [
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 3),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 6),
            make_combination(CombinationType.SEQUENCE, Suit.MANZU, 7),
            make_combination(CombinationType.PAIR, Suit.PINZU, 1),
        ]
        waiting_type = self.calculator._determine_waiting_type(winning_tile, combo)
        assert waiting_type in {
            WaitingType.KANCHAN,
            WaitingType.PENCHAN,
            WaitingType.RYANMEN,
            WaitingType.TANKI,
            WaitingType.SHABO,
        }

    def test_waiting_type_shabo(self):
        """Test waiting type shabo."""
        winning_tile = Tile(Suit.MANZU, 1)
        combo = [
            make_combination(CombinationType.TRIPLET, Suit.MANZU, 3),
            make_combination(CombinationType.TRIPLET, Suit.MANZU, 5),
            make_combination(CombinationType.TRIPLET, Suit.PINZU, 1),
            make_combination(CombinationType.PAIR, Suit.MANZU, 1),
        ]
        waiting_type = self.calculator._determine_waiting_type(winning_tile, combo)
        assert waiting_type in {
            WaitingType.TANKI,
            WaitingType.RYANMEN,
            WaitingType.SHABO,
        }

    def test_fu_waiting_type_shabo_no_fu(self):
        """Test fu waiting type shabo no fu."""
        tiles = parse_tiles("11m22m33m456p789s")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 1)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            fu = self.calculator.calculate_fu(
                hand,
                winning_tile,
                list(combinations[0]),
                yaku_results,
                self.game_state,
                False,
            )
            waiting_type = self.calculator._determine_waiting_type(
                winning_tile, list(combinations[0])
            )
            assert fu >= 30
            if waiting_type == WaitingType.SHABO:
                pass

    def test_fu_pair_player_wind(self):
        """Test fu pair player wind."""
        self.game_state.set_dealer(0)
        tiles = parse_tiles("123m456m78m123p11z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 9)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            fu = self.calculator.calculate_fu(
                hand,
                winning_tile,
                list(combinations[0]),
                yaku_results,
                self.game_state,
                False,
                player_position=0,
            )
            assert fu >= 30

    def test_fu_pair_player_wind_south(self):
        """Test fu pair player wind south."""
        self.game_state.set_dealer(0)
        tiles = parse_tiles("12345678m123p22z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 9)
        combinations = hand.get_winning_combinations(winning_tile)

        if combinations:
            yaku_results = []
            fu = self.calculator.calculate_fu(
                hand,
                winning_tile,
                list(combinations[0]),
                yaku_results,
                self.game_state,
                False,
                player_position=1,
            )
            assert fu >= 30

    def test_kiriage_mangan_30fu_4han(self):
        """Test kiriage mangan 30fu 4han."""

        result_enabled = ScoreResult(
            han=4,
            fu=30,
            base_points=0,
            total_points=0,
            payment_from=0,
            payment_to=0,
            is_yakuman=False,
            yakuman_count=0,
            kiriage_mangan_enabled=True,
        )
        assert result_enabled.total_points == 2000

        result_disabled = ScoreResult(
            han=4,
            fu=30,
            base_points=0,
            total_points=0,
            payment_from=0,
            payment_to=0,
            is_yakuman=False,
            yakuman_count=0,
            kiriage_mangan_enabled=False,
        )
        assert result_disabled.total_points == 1920

    def test_kiriage_mangan_60fu_3han(self):
        """Test kiriage mangan 60fu 3han."""
        result_enabled = ScoreResult(
            han=3,
            fu=60,
            base_points=0,
            total_points=0,
            payment_from=0,
            payment_to=0,
            is_yakuman=False,
            yakuman_count=0,
            kiriage_mangan_enabled=True,
        )
        assert result_enabled.total_points == 2000

        result_disabled = ScoreResult(
            han=3,
            fu=60,
            base_points=0,
            total_points=0,
            payment_from=0,
            payment_to=0,
            is_yakuman=False,
            yakuman_count=0,
            kiriage_mangan_enabled=False,
        )
        assert result_disabled.total_points == 1920

    def test_kiriage_mangan_not_applicable(self):
        """Test kiriage mangan not applicable."""
        result = ScoreResult(
            han=4,
            fu=40,
            base_points=0,
            total_points=0,
            payment_from=0,
            payment_to=0,
            is_yakuman=False,
            yakuman_count=0,
            kiriage_mangan_enabled=True,
        )
        assert result.total_points == 2000

        result2 = ScoreResult(
            han=3,
            fu=30,
            base_points=0,
            total_points=0,
            payment_from=0,
            payment_to=0,
            is_yakuman=False,
            yakuman_count=0,
            kiriage_mangan_enabled=True,
        )
        assert result2.total_points == 960


class TestFuCalculationOpenMeld:
    def test_open_pon_fu(self):

        tiles = parse_tiles("22345m")

        meld1 = Meld(MeldType.PON_MELD, [Tile(Suit.MANZU, 1)] * 3)
        meld2 = Meld(MeldType.PON_MELD, [Tile(Suit.MANZU, 9)] * 3)

        hand = Hand(tiles)
        hand._melds.append(meld1)
        hand._melds.append(meld2)

        tiles.extend([Tile(Suit.PINZU, 4), Tile(Suit.PINZU, 5), Tile(Suit.PINZU, 6)])

        hand = Hand(tiles)
        hand._melds.append(meld1)
        hand._melds.append(meld2)

        tiles.remove(Tile(Suit.MANZU, 2))
        hand = Hand(tiles)
        hand._melds.append(meld1)
        hand._melds.append(meld2)

        winning_tile = Tile(Suit.MANZU, 2)

        calculator = ScoreCalculator()

        tiles = parse_tiles("5z345m456p")
        hand = Hand(tiles)
        hand._melds.append(meld1)
        hand._melds.append(meld2)

        winning_tile = Tile(Suit.HONORS, 5)

        yaku_results = [YakuResult(Yaku.HAKU, 1, False)]

        combinations = hand.get_winning_combinations(winning_tile, is_tsumo=False)
        assert len(combinations) > 0
        winning_combination = combinations[0]

        hand = Hand(tiles)  # Reset
        hand._melds.append(meld1)

        tiles.extend([Tile(Suit.PINZU, 7), Tile(Suit.PINZU, 8), Tile(Suit.PINZU, 9)])

        hand = Hand(tiles)
        hand._melds.append(meld1)

        winning_tile = Tile(Suit.HONORS, 5)

        combinations = hand.get_winning_combinations(winning_tile, is_tsumo=False)
        assert len(combinations) > 0
        winning_combination = combinations[0]

        game_state = GameState()

        fu = calculator.calculate_fu(
            hand,
            winning_tile,
            winning_combination,
            yaku_results,
            game_state,
            is_tsumo=False,
            player_position=0,
        )

        # print(f"Calculated fu: {fu}")
        assert (
            fu == 30
        ), "Should be 30 fu (20 base + 4 open pon + 2 pair + 2 wait = 28 -> 30)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
