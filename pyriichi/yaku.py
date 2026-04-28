"""
YakuChecker System - YakuChecker implementation

Provides all yaku (Winning hand) adjudication functions.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

from pyriichi.enum_utils import TranslatableEnum
from pyriichi.game_state import GameState, Wind
from pyriichi.hand import Combination, CombinationType, Hand
from pyriichi.rules_config import RenhouPolicy
from pyriichi.tiles import Suit, Tile

__all__ = ["Yaku", "YakuResult", "YakuChecker"]


class Yaku(TranslatableEnum):
    """All yaku enum"""

    RIICHI = ("riichi", "立直", "立直", "Riichi")
    DOUBLE_RIICHI = ("double_riichi", "雙立直", "ダブルリーチ", "Double Riichi")
    IPPATSU = ("ippatsu", "一發", "一発", "Ippatsu")
    MENZEN_TSUMO = (
        "menzen_tsumo",
        "門前清自摸和",
        "門前清自摸和",
        "Fully Concealed Tsumo",
    )
    TANYAO = ("tanyao", "斷么九", "断么九", "All Simples")
    PINFU = ("pinfu", "平和", "平和", "Pinfu")
    IIPEIKOU = ("iipeikou", "一盃口", "一盃口", "Pure Double Sequence")
    RYANPEIKOU = ("ryanpeikou", "二盃口", "二盃口", "Twice Pure Double Sequence")
    TOITOI = ("toitoi", "對對和", "対々和", "All Triplets")
    SANANKOU = ("sanankou", "三暗刻", "三暗刻", "Three Concealed Triplets")
    SANKANTSU = ("sankantsu", "三槓子", "三槓子", "Three Kans")
    SANSHOKU_DOUJUN = (
        "sanshoku_doujun",
        "三色同順",
        "三色同順",
        "Mixed Triple Sequence",
    )
    SANSHOKU_DOUKOU = (
        "sanshoku_doukou",
        "三色同刻",
        "三色同刻",
        "Mixed Triple Triplets",
    )
    ITTSU = ("ittsu", "一氣通貫", "一気通貫", "Pure Straight")
    HONITSU = ("honitsu", "混一色", "混一色", "Half Flush")
    CHINITSU = ("chinitsu", "清一色", "清一色", "Full Flush")
    JUNCHAN = ("junchan", "純全帶么九", "純全帯么九", "Terminal in Each Set")
    CHANTA = ("chanta", "混全帶么九", "混全帯么九", "Outside Hand")
    HONROUTOU = ("honroutou", "混老頭", "混老頭", "All Terminals and Honors")
    SHOUSANGEN = ("shousangen", "小三元", "小三元", "Little Three Dragons")
    DAISANGEN = ("daisangen", "大三元", "大三元", "Big Three Dragons")
    SUUANKOU = ("suuankou", "四暗刻", "四暗刻", "Four Concealed Triplets")
    SUUANKOU_TANKI = (
        "suuankou_tanki",
        "四暗刻單騎",
        "四暗刻単騎",
        "Four Concealed Triplets Single Wait",
    )
    SUUKANTSU = ("suukantsu", "四槓子", "四槓子", "Four Kans")
    SHOUSUUSHI = ("shousuushi", "小四喜", "小四喜", "Little Four Winds")
    DAISUUSHI = ("daisuushi", "大四喜", "大四喜", "Big Four Winds")
    CHINROUTOU = ("chinroutou", "清老頭", "清老頭", "All Terminals")
    TSUUIISOU = ("tsuuiisou", "字一色", "字一色", "All Honors")
    RYUUIISOU = ("ryuuiisou", "綠一色", "緑一色", "All Green")
    CHUUREN_POUTOU = ("chuuren_poutou", "九蓮寶燈", "九蓮宝燈", "Nine Gates")
    PURE_CHUUREN_POUTOU = (
        "pure_chuuren_poutou",
        "純正九蓮寶燈",
        "純正九蓮宝燈",
        "Pure Nine Gates",
    )
    KOKUSHI_MUSOU = ("kokushi_musou", "國士無雙", "国士無双", "Thirteen Orphans")
    KOKUSHI_MUSOU_JUUSANMEN = (
        "kokushi_musou_juusanmen",
        "國士無雙十三面",
        "国士無双十三面",
        "Thirteen-Sided Thirteen Orphans",
    )
    TENHOU = ("tenhou", "天和", "天和", "Heavenly Hand")
    CHIHOU = ("chihou", "地和", "地和", "Earthly Hand")
    RENHOU = ("renhou", "人和", "人和", "Hand of Man")
    HAITEI = ("haitei", "海底摸月", "海底摸月", "Under the Sea")
    HOUTEI = ("houtei", "河底撈魚", "河底撈魚", "Under the River")
    RINSHAN = ("rinshan", "嶺上開花", "嶺上開花", "After a Kan")
    CHANKAN = ("chankan", "搶槓", "槍槓", "Robbing a Kan")
    CHIITOITSU = ("chiitoitsu", "七對子", "七対子", "Seven Pairs")
    HAKU = ("haku", "白", "白", "White")
    HATSU = ("hatsu", "發", "発", "Green")
    CHUN = ("chun", "中", "中", "Red")
    ROUND_WIND_EAST = ("round_wind_east", "場風東", "場風東", "Prevalent Wind East")
    ROUND_WIND_SOUTH = ("round_wind_south", "場風南", "場風南", "Prevalent Wind South")
    ROUND_WIND_WEST = ("round_wind_west", "場風西", "場風西", "Prevalent Wind West")
    ROUND_WIND_NORTH = ("round_wind_north", "場風北", "場風北", "Prevalent Wind North")
    SEAT_WIND_EAST = ("seat_wind_east", "自風東", "自風東", "Seat Wind East")
    SEAT_WIND_SOUTH = ("seat_wind_south", "自風南", "自風南", "Seat Wind South")
    SEAT_WIND_WEST = ("seat_wind_west", "自風西", "自風西", "Seat Wind West")
    SEAT_WIND_NORTH = ("seat_wind_north", "自風北", "自風北", "Seat Wind North")


class Machi(TranslatableEnum):
    """machi."""

    RYANMEN = ("ryanmen", "兩面", "両面", "Two-Sided Wait")
    PENCHAN = ("penchan", "邊張", "辺張", "Edge Wait")
    KANCHAN = ("kanchan", "嵌張", "嵌張", "Closed Wait")
    TANKI = ("tanki", "單騎", "単騎", "Single Wait")
    SHABO = ("shabo", "雙碰", "シャボ", "Pair-Pair Wait")


@dataclass(frozen=True)
class YakuResult:
    """YakuResult"""

    yaku: Yaku
    han: int
    is_yakuman: bool

    def __eq__(self, other):
        return self.yaku == other.yaku if isinstance(other, YakuResult) else False

    def __hash__(self):
        return hash(self.yaku)


class YakuChecker:
    """YakuChecker"""

    def _group_combinations(
        self, winning_combination: Optional[List[Combination]]
    ) -> Dict[CombinationType, List[Combination]]:
        """
        Group winning combinations by CombinationType.

        Args:
            winning_combination (Optional[List[Combination]]): Winning combinations.

        Returns:
            Dict[CombinationType, List[Combination]]: Grouped combinations dictionary.
        """
        groups: Dict[CombinationType, List[Combination]] = {
            CombinationType.PAIR: [],
            CombinationType.SEQUENCE: [],
            CombinationType.TRIPLET: [],
            CombinationType.KAN: [],
        }
        if not winning_combination:
            return groups

        for combination in winning_combination:
            if combination is None:
                continue
            groups.setdefault(combination.type, []).append(combination)

        return groups

    @staticmethod
    def _get_combination_key(combination: Combination) -> Tuple[Suit, int]:
        """
        Get combination representative key (Suit, Rank of smallest tile).

        For Sequence, use the starting tile as key; for triplet/kan/pair, since tiles are same, take any.

        Args:
            combination (Combination): Combination.

        Returns:
            Tuple[Suit, int]: (Suit, Rank).
        """
        tiles = sorted(combination.tiles)
        tile = tiles[0]
        return tile.suit, tile.rank

    @staticmethod
    def _flatten_tiles(winning_combination: Optional[List[Combination]]) -> List[Tile]:
        """
        Flatten tiles from all combinations into a single list.

        Args:
            winning_combination (Optional[List[Combination]]): Winning combinations.

        Returns:
            List[Tile]: List of all tiles.
        """
        if not winning_combination:
            return []
        tiles: List[Tile] = []
        for combination in winning_combination:
            tiles.extend(combination.tiles)
        return tiles

    def _extract_pair(
        self, winning_combination: Optional[List[Combination]]
    ) -> Optional[Combination]:
        """
        Extract pair from combinations (if exists).

        Args:
            winning_combination (Optional[List[Combination]]): Winning combinations.

        Returns:
            Optional[Combination]: Pair combination, or None if not exists.
        """
        if not winning_combination:
            return None
        for combination in winning_combination:
            if combination.type == CombinationType.PAIR:
                return combination
        return None

    def check_all(
        self,
        hand: Hand,
        winning_tile: Tile,
        winning_combination: List[Combination],
        game_state: GameState,
        is_tsumo: bool = False,
        is_ippatsu: bool = False,
        is_first_turn: bool = False,
        is_last_tile: bool = False,
        player_position: int = 0,
        is_rinshan: bool = False,
        is_chankan: bool = False,
    ) -> List[YakuResult]:
        """
        Check all matching yaku.

        Args:
            hand (Hand): hand.
            winning_tile (Tile): Winning tile.
            winning_combination (List[Combination]): Winning combinations (standard) or None (special like chiitoitsu).
            game_state (GameState): Game state.
            is_tsumo (bool): Is tsumo.
            is_ippatsu (bool): Is ippatsu.
            is_first_turn (bool): Is first turn.
            is_last_tile (bool): Is last tile (haitei/houtei).
            player_position (int): Player position (for seat_wind).
            is_rinshan (bool): Is rinshan.
            is_chankan (bool): Is chankan.

        Returns:
            List[YakuResult]: List of all matching yaku results.
        """
        # tenhou, chihou, renhou check first as yakuman
        if result := self.check_tenhou(
            hand, is_tsumo, is_first_turn, player_position, game_state
        ):
            return [result]
        if result := self.check_chihou(
            hand, is_tsumo, is_first_turn, player_position, game_state
        ):
            return [result]
        if result := self.check_renhou(
            hand, is_tsumo, is_first_turn, player_position, game_state
        ):
            return [result]

        # kokushi_musou check first as yakuman
        if result := self.check_kokushi_musou(hand, winning_tile):
            results = [result]
            # kokushi_musou can combine with riichi
            is_double_riichi = is_first_turn and hand.is_concealed
            results.extend(
                self.check_riichi(hand, game_state, is_ippatsu, is_double_riichi)
            )
            return results

        # chiitoitsu check
        if result := self.check_chiitoitsu(hand, winning_tile):
            results = [result]
            if hand.is_riichi:
                # double_riichi priority over riichi
                is_double_riichi = is_first_turn and hand.is_concealed
                if is_double_riichi:
                    results.insert(0, YakuResult(Yaku.DOUBLE_RIICHI, 2, False))
                else:
                    results.insert(0, YakuResult(Yaku.RIICHI, 1, False))
                if is_ippatsu:
                    results.insert(1, YakuResult(Yaku.IPPATSU, 1, False))
            return results

        # Other yakuman checks (Check first as yakuman overrides other yaku)
        # Note: Some yakuman can coexist (e.g. suuankou + tsuuiisou)
        yakuman_results = []
        if result := self.check_daisangen(hand, winning_combination):
            yakuman_results.append(result)
        if result := self.check_suukantsu(hand, winning_combination):
            yakuman_results.append(result)
        if result := self.check_suuankou(
            hand, winning_combination, winning_tile, game_state
        ):
            yakuman_results.append(result)

        if result := self.check_shousuushi(hand, winning_combination):
            yakuman_results.append(result)
        if result := self.check_daisuushi(hand, winning_combination):
            yakuman_results.append(result)
        if result := self.check_chinroutou(hand, winning_combination):
            yakuman_results.append(result)
        if result := self.check_tsuuiisou(hand, winning_combination):
            yakuman_results.append(result)
        if result := self.check_ryuuiisou(hand, winning_combination):
            yakuman_results.append(result)
        if result := self.check_chuuren_poutou(hand, winning_tile, game_state):
            yakuman_results.append(result)

        # If yakuman exists, return only yakuman (yakuman does not combine with other yaku, but multiple yakuman can combine)
        if yakuman_results:
            # yakuman can combine with riichi
            is_double_riichi = is_first_turn and hand.is_concealed
            yakuman_results.extend(
                self.check_riichi(hand, game_state, is_ippatsu, is_double_riichi)
            )
            return yakuman_results

        results = []

        # Basic yaku
        is_double_riichi = is_first_turn and hand.is_concealed
        results.extend(
            self.check_riichi(hand, game_state, is_ippatsu, is_double_riichi)
        )
        if result := self.check_menzen_tsumo(hand, game_state, is_tsumo):
            results.append(result)
        if result := self.check_haitei_houtei(hand, is_tsumo, is_last_tile):
            results.append(result)
        if result := self.check_rinshan(hand, is_rinshan):
            results.append(result)
        if result := self.check_chankan(hand, is_chankan):
            results.append(result)
        if result := self.check_tanyao(hand, winning_combination):
            results.append(result)
        if result := self.check_pinfu(
            hand, winning_combination, game_state, winning_tile, player_position
        ):
            results.append(result)

        if result := self.check_iipeikou(hand, winning_combination):
            results.append(result)
        if result := self.check_toitoi(hand, winning_combination):
            results.append(result)
        if result := self.check_sankantsu(hand, winning_combination):
            results.append(result)

        # yakuhai (May have multiple)
        yakuhai_results = self.check_yakuhai(
            hand, winning_combination, game_state, player_position
        )
        results.extend(yakuhai_results)

        # Special yaku (2-3 han)
        if result := self.check_sanshoku_doujun(hand, winning_combination):
            results.append(result)
        if result := self.check_ittsu(hand, winning_combination):
            results.append(result)
        if result := self.check_sanankou(hand, winning_combination):
            results.append(result)
        if result := self.check_chinitsu(hand, winning_combination):
            results.append(result)
        if result := self.check_honitsu(hand, winning_combination):
            results.append(result)
        if result := self.check_sanshoku_doukou(hand, winning_combination):
            results.append(result)
        if result := self.check_shousangen(hand, winning_combination):
            results.append(result)
        if result := self.check_honroutou(hand, winning_combination):
            results.append(result)

        # Advanced yaku (3 han or more)
        if result := self.check_junchan(hand, winning_combination, game_state):
            results.append(result)
        if result := self.check_chanta(hand, winning_combination, game_state):
            results.append(result)
        if result := self.check_ryanpeikou(hand, winning_combination):
            results.append(result)

        # yaku conflict detection and filtering
        results = self._filter_conflicting_yaku(
            results, winning_combination, game_state
        )

        return results

    def _filter_conflicting_yaku(
        self,
        results: List[YakuResult],
        winning_combination: List[Combination],
        game_state: GameState,
    ) -> List[YakuResult]:
        """
        Filter conflicting yaku.

        Args:
            results (List[YakuResult]): List of yaku results.
            winning_combination (List[Combination]): Winning combinations.
            game_state (GameState): Game state.

        Returns:
            List[YakuResult]: Filtered yaku list.
        """
        filtered = []
        yaku_set = {r.yaku for r in results}

        for result in results:
            should_include = True

            # 1. pinfu conflicts with yakuhai
            if result.yaku == Yaku.TOITOI:
                sequence_yaku = {
                    Yaku.SANSHOKU_DOUJUN,
                    Yaku.ITTSU,
                    Yaku.IIPEIKOU,
                    Yaku.RYANPEIKOU,
                }
                if yaku_set & sequence_yaku:
                    should_include = False

            elif result.yaku == Yaku.PINFU:
                yakuhai_set = {
                    Yaku.HAKU,
                    Yaku.HATSU,
                    Yaku.CHUN,
                    Yaku.ROUND_WIND_EAST,
                    Yaku.ROUND_WIND_SOUTH,
                    Yaku.ROUND_WIND_WEST,
                    Yaku.ROUND_WIND_NORTH,
                }
                if yaku_set & yakuhai_set:
                    should_include = False

            elif result.yaku == Yaku.TANYAO:
                # yaku containing terminals/honors
                terminal_yaku = {
                    Yaku.ITTSU,  # Sequence containing 1 and 9
                    Yaku.JUNCHAN,
                    Yaku.CHANTA,
                    Yaku.HONROUTOU,
                    Yaku.CHINROUTOU,
                }
                if yaku_set & terminal_yaku:
                    should_include = False

            # 4. iipeikou conflicts with ryanpeikou
            if result.yaku == Yaku.IIPEIKOU and Yaku.RYANPEIKOU in yaku_set:
                should_include = False

            # 5. chinitsu conflicts with honitsu
            if result.yaku == Yaku.CHINITSU and Yaku.HONITSU in yaku_set:
                should_include = False
            if result.yaku == Yaku.HONITSU and Yaku.CHINITSU in yaku_set:
                should_include = False

            # 6. junchan conflicts with chanta
            if result.yaku == Yaku.JUNCHAN and Yaku.CHANTA in yaku_set:
                should_include = False
            if result.yaku == Yaku.CHANTA and Yaku.JUNCHAN in yaku_set:
                should_include = False

            # 7. pinfu conflicts with toitoi (Structurally mutually exclusive)
            if result.yaku == Yaku.PINFU and Yaku.TOITOI in yaku_set:
                should_include = False
            if result.yaku == Yaku.TOITOI and Yaku.PINFU in yaku_set:
                should_include = False

            if should_include:
                filtered.append(result)

        return filtered

    def check_riichi(
        self,
        hand: Hand,
        game_state: GameState,
        is_ippatsu: Optional[bool] = None,
        is_double_riichi: bool = False,
    ) -> List[YakuResult]:
        """
        Check riichi, double_riichi, and ippatsu.

        riichi: Declare riichi when tenpai (1 han).
        double_riichi: Declare riichi in first turn (2 han, replaces riichi).
        ippatsu: Win within one turn after riichi (first own turn after riichi).

        Args:
            hand (Hand): hand.
            game_state (GameState): Game state.
            is_ippatsu (Optional[bool]): Is ippatsu.
            is_double_riichi (bool): Is double_riichi.

        Returns:
            List[YakuResult]: List of matching yaku results.
        """
        results: List[YakuResult] = []

        if not hand.is_riichi:
            return results

        # double_riichi priority over riichi
        if is_double_riichi:
            results.append(YakuResult(Yaku.DOUBLE_RIICHI, 2, False))
        else:
            results.append(YakuResult(Yaku.RIICHI, 1, False))

        if is_ippatsu:
            results.append(YakuResult(Yaku.IPPATSU, 1, False))

        return results

    def check_menzen_tsumo(
        self, hand: Hand, game_state: GameState, is_tsumo: bool = False
    ) -> Optional[YakuResult]:
        """
        Check menzen_tsumo.

        menzen_tsumo: tsumo win while menzen.

        Args:
            hand (Hand): hand.
            game_state (GameState): Game state.
            is_tsumo (bool): Is tsumo.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        if not hand.is_concealed:
            return None

        return YakuResult(Yaku.MENZEN_TSUMO, 1, False) if is_tsumo else None

    def check_tanyao(
        self, hand: Hand, winning_combination: List[Combination]
    ) -> Optional[YakuResult]:
        """
        Check tanyao (All Simples).

        tanyao: Composed entirely of simple tiles (2-8), no terminals or honors (1, 9, honors).

        Args:
            hand (Hand): hand.
            winning_combination (List[Combination]): Winning combinations.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        if not winning_combination:
            return None

        for combination in winning_combination:
            for tile in combination.tiles:
                if tile.is_honor or tile.is_terminal:
                    return None

        return YakuResult(Yaku.TANYAO, 1, False)

    def check_pinfu(
        self,
        hand: Hand,
        winning_combination: List[Combination],
        game_state: Optional[GameState] = None,
        winning_tile: Optional[Tile] = None,
        player_position: int = 0,
    ) -> Optional[YakuResult]:
        """
        Check pinfu.

        pinfu:
        1. menzen (Concealed).
        2. Composed entirely of sequences (except pair).
        3. Pair cannot be yakuhai (round_wind, seat_wind, haku/hatsu/chun).
        4. machi must be ryanmen (Two-sided wait) (depending on rules).

        Args:
            hand (Hand): hand.
            winning_combination (List): Winning combinations.
            game_state (Optional[GameState]): Game state.
            winning_tile (Optional[Tile]): Winning tile.
            player_position (int): Player position (for seat_wind).

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        if not hand.is_concealed:
            return None

        if not winning_combination:
            return None

        groups = self._group_combinations(winning_combination)
        pair_combination = self._extract_pair(winning_combination)
        sequences = groups[CombinationType.SEQUENCE]
        triplets = groups[CombinationType.TRIPLET] + groups[CombinationType.KAN]

        # Must have 4 sequences and no triplets/kans, and a pair exists
        if pair_combination is None or len(sequences) != 4 or triplets:
            return None

        # Pair cannot be yakuhai (check round_wind, seat_wind, haku/hatsu/chun)
        pair_tile = sorted(pair_combination.tiles)[0]
        if pair_tile.suit == Suit.HONORS:
            haku_hatsu_chun_ranks = [5, 6, 7]
            if pair_tile.rank in haku_hatsu_chun_ranks:
                return None  # haku/hatsu/chun pair, cannot be pinfu

            if game_state is not None:
                round_wind = game_state.round_wind
                wind_mapping = {
                    1: Wind.EAST,
                    2: Wind.SOUTH,
                    3: Wind.WEST,
                    4: Wind.NORTH,
                }
                if round_wind == wind_mapping.get(pair_tile.rank):
                    return None  # round_wind pair, cannot be pinfu

            # Check if it is seat_wind
            if game_state:
                seat_wind = game_state.seat_winds[player_position]
                if seat_wind.tile == pair_tile:
                    return None  # seat_wind pair, cannot be pinfu

        # Check machi (ryanmen / Two-sided wait) - depending on rules.
        ruleset = game_state.ruleset if game_state else None
        if ruleset and ruleset.pinfu_require_ryanmen and winning_tile is not None:
            machi = self._determine_machi(winning_tile, winning_combination)
            if machi != Machi.RYANMEN:
                return None  # Not ryanmen machi, cannot be pinfu.

        return YakuResult(Yaku.PINFU, 1, False)

    def check_iipeikou(
        self, hand: Hand, winning_combination: List[Combination]
    ) -> Optional[YakuResult]:
        """
        Check iipeikou.

        iipeikou: Two identical sequences while menzen.

        Args:
            hand (Hand): hand.
            winning_combination (List[Combination]): Winning combinations.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        if not hand.is_concealed:
            return None

        if not winning_combination:
            return None

        groups = self._group_combinations(winning_combination)
        sequences = [
            self._get_combination_key(seq) for seq in groups[CombinationType.SEQUENCE]
        ]

        # Check if there are two identical sequences
        if len(sequences) >= 2:
            for i in range(len(sequences)):
                for j in range(i + 1, len(sequences)):
                    if sequences[i] == sequences[j]:
                        return YakuResult(Yaku.IIPEIKOU, 1, False)

        return None

    def check_toitoi(
        self, hand: Hand, winning_combination: List[Combination]
    ) -> Optional[YakuResult]:
        """
        Check toitoi (All Pungs).

        toitoi: Composed entirely of triplets (4 triplets + 1 pair).

        Args:
            hand (Hand): hand.
            winning_combination (List[Combination]): Winning combinations.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        if not winning_combination:
            return None

        groups = self._group_combinations(winning_combination)
        pair_combination = self._extract_pair(winning_combination)
        sequences = groups[CombinationType.SEQUENCE]
        triplet_like = groups[CombinationType.TRIPLET] + groups[CombinationType.KAN]

        # If there are sequences, not toitoi. Must have 4 triplets/kans and a pair.
        if sequences:
            return None

        if pair_combination is not None and len(triplet_like) == 4:
            return YakuResult(Yaku.TOITOI, 2, False)

        return None

    def check_sankantsu(
        self, hand: Hand, winning_combination: List[Combination]
    ) -> Optional[YakuResult]:
        """
        Check Sankantsu (Three Quads).

        Sankantsu: Three kans.

        Args:
            hand (Hand): hand.
            winning_combination (List[Combination]): Winning combinations.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        if not winning_combination:
            return None

        groups = self._group_combinations(winning_combination)
        kan_count = len(groups[CombinationType.KAN])

        # Three kans
        return YakuResult(Yaku.SANKANTSU, 2, False) if kan_count == 3 else None

    def check_yakuhai(
        self,
        hand: Hand,
        winning_combination: List[Combination],
        game_state: GameState,
        player_position: int = 0,
    ) -> List[YakuResult]:
        """
        Check yakuhai (round_wind, seat_wind, haku/hatsu/chun triplets).

        Args:
            hand (Hand): hand.
            winning_combination (List[Combination]): Winning combinations.
            game_state (GameState): Game state.
            player_position (int): Player position.

        Returns:
            List[YakuResult]: List of yakuhai (may have multiple).
        """
        results = []
        if not winning_combination:
            return results

        haku_hatsu_chun_ranks = [5, 6, 7]
        wind_rank_mapping = {
            1: (Wind.EAST, Yaku.ROUND_WIND_EAST, Yaku.SEAT_WIND_EAST),
            2: (Wind.SOUTH, Yaku.ROUND_WIND_SOUTH, Yaku.SEAT_WIND_SOUTH),
            3: (Wind.WEST, Yaku.ROUND_WIND_WEST, Yaku.SEAT_WIND_WEST),
            4: (Wind.NORTH, Yaku.ROUND_WIND_NORTH, Yaku.SEAT_WIND_NORTH),
        }
        round_wind = game_state.round_wind
        seat_wind = (
            game_state.seat_winds[player_position]
            if 0 <= player_position < len(game_state.seat_winds)
            else None
        )

        groups = self._group_combinations(winning_combination)
        honor_sets = groups[CombinationType.TRIPLET] + groups[CombinationType.KAN]

        for combination in honor_sets:
            tile = sorted(combination.tiles)[0]
            if tile.suit != Suit.HONORS:
                continue

            rank = tile.rank
            if rank in haku_hatsu_chun_ranks:
                if rank == 5:
                    results.append(YakuResult(Yaku.HAKU, 1, False))
                elif rank == 6:
                    results.append(YakuResult(Yaku.HATSU, 1, False))
                elif rank == 7:
                    results.append(YakuResult(Yaku.CHUN, 1, False))

            if rank in wind_rank_mapping:
                target_wind, round_yaku, seat_yaku = wind_rank_mapping[rank]
                if round_wind == target_wind:
                    results.append(YakuResult(round_yaku, 1, False))
                if seat_wind == target_wind:
                    results.append(YakuResult(seat_yaku, 1, False))

        return results

    def check_sanshoku_doujun(
        self, hand: Hand, winning_combination: List[Combination]
    ) -> Optional[YakuResult]:
        """
        Check sanshoku_doujun.

        sanshoku_doujun: Sequences of the same number in manzu, pinzu, souzu.

        Args:
            hand (Hand): hand.
            winning_combination (List[Combination]): Winning combinations.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        if not winning_combination:
            return None

        # Count sequences
        sequences_by_suit = {Suit.MANZU: [], Suit.PINZU: [], Suit.SOUZU: []}

        groups = self._group_combinations(winning_combination)
        for sequence in groups[CombinationType.SEQUENCE]:
            suit, rank = self._get_combination_key(sequence)
            if suit in sequences_by_suit:
                sequences_by_suit[suit].append(rank)

        # Check if there are sequences of the same number in all three suits
        for rank in range(1, 8):  # Sequence max rank is 7
            has_manzu = rank in sequences_by_suit[Suit.MANZU]
            has_pinzu = rank in sequences_by_suit[Suit.PINZU]
            has_souzu = rank in sequences_by_suit[Suit.SOUZU]

            if has_manzu and has_pinzu and has_souzu:
                han = 2 if hand.is_concealed else 1
                return YakuResult(Yaku.SANSHOKU_DOUJUN, han, False)

        return None

    def check_ittsu(
        self, hand: Hand, winning_combination: List[Combination]
    ) -> Optional[YakuResult]:
        """
        Check Ittsu (Pure Straight).

        Ittsu: Sequences of 1-3, 4-6, 7-9 in the same suit.

        Args:
            hand (Hand): hand.
            winning_combination (List[Combination]): Winning combinations.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        if not winning_combination:
            return None

        # Count sequences by suit
        sequences_by_suit = {Suit.MANZU: [], Suit.PINZU: [], Suit.SOUZU: []}

        groups = self._group_combinations(winning_combination)
        for sequence in groups[CombinationType.SEQUENCE]:
            suit, rank = self._get_combination_key(sequence)
            if suit in sequences_by_suit:
                sequences_by_suit[suit].append(rank)

        # Check if Ittsu exists in any suit
        for suit in [Suit.MANZU, Suit.PINZU, Suit.SOUZU]:
            sequences = sequences_by_suit[suit]
            # Need 1-3, 4-6, 7-9 sequences
            has_123 = 1 in sequences
            has_456 = 4 in sequences
            has_789 = 7 in sequences

            if has_123 and has_456 and has_789:
                han = 2 if hand.is_concealed else 1
                return YakuResult(Yaku.ITTSU, han, False)

        return None

    def check_sanankou(
        self, hand: Hand, winning_combination: List[Combination]
    ) -> Optional[YakuResult]:
        """
        Check sanankou (Three Concealed Triplets).

        sanankou: Three concealed triplets (Triplets in menzen).

        Args:
            hand (Hand): hand.
            winning_combination (List[Combination]): Winning combination.

        Returns:
            Optional[YakuResult]: Yaku result, or None if it does not apply.
        """
        if not hand.is_concealed:
            return None

        if not winning_combination:
            return None

        groups = self._group_combinations(winning_combination)
        triplets = len(groups[CombinationType.TRIPLET])

        return YakuResult(Yaku.SANANKOU, 2, False) if triplets >= 3 else None

    def check_chinitsu(
        self, hand: Hand, winning_combination: List[Combination]
    ) -> Optional[YakuResult]:
        """
        Check chinitsu (Full Flush).

        chinitsu: Composed entirely of tiles from a single suit.

        Args:
            hand (Hand): hand.
            winning_combination (List[Combination]): Winning combinations.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        if not winning_combination:
            return None

        suits = set()
        for tile in self._flatten_tiles(winning_combination):
            if tile.suit == Suit.HONORS:
                return None
            suits.add(tile.suit)

        # Only one suit
        if len(suits) == 1:
            han = 6 if hand.is_concealed else 5
            return YakuResult(Yaku.CHINITSU, han, False)
        return None

    def check_honitsu(
        self, hand: Hand, winning_combination: List[Combination]
    ) -> Optional[YakuResult]:
        """
        Check honitsu (Half Flush).

        honitsu: Composed of tiles from a single suit and honors.

        Args:
            hand (Hand): hand.
            winning_combination (List[Combination]): Winning combinations.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        if not winning_combination:
            return None

        # Check number suits and honors
        number_suits = set()
        has_honor = False

        for tile in self._flatten_tiles(winning_combination):
            if tile.suit == Suit.HONORS:
                has_honor = True
            else:
                number_suits.add(tile.suit)

        # Only one number suit, and contains honors
        if len(number_suits) == 1 and has_honor:
            han = 3 if hand.is_concealed else 2
            return YakuResult(Yaku.HONITSU, han, False)

        return None

    def check_chiitoitsu(
        self, hand: Hand, winning_tile: Optional[Tile] = None
    ) -> Optional[YakuResult]:
        """
        Check chiitoitsu.

        chiitoitsu: Seven Pairs.
        Note: chiitoitsu does not have standard winning combinations, needs special handling.

        Args:
            hand (Hand): hand.
            winning_tile (Optional[Tile]): Winning tile.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        all_tiles = hand.tiles + [winning_tile] if winning_tile else hand.tiles
        if not hand.is_concealed or len(all_tiles) != 14:
            return None

        counts: Dict[Tile, int] = {}
        for tile in all_tiles:
            counts[tile] = counts.get(tile, 0) + 1
            if counts[tile] > 2:
                return None

        pairs = [count for count in counts.values() if count == 2]
        return None if len(pairs) != 7 else YakuResult(Yaku.CHIITOITSU, 2, False)

    def check_junchan(
        self,
        hand: Hand,
        winning_combination: List[Combination],
        game_state: Optional[GameState] = None,
    ) -> Optional[YakuResult]:
        """
        Check junchan (Pure Terminal Chow).

        junchan: Composed entirely of sequences, and each sequence contains 1 or 9.
        No honors, pairs can be any number tile (but actually usually 1 or 9).
        han value depends on menzen/Meld state (Standard competitive rules).

        Args:
            hand (Hand): hand.
            winning_combination (List[Combination]): Winning combinations.
            game_state (Optional[GameState]): Game state.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        if not winning_combination:
            return None

        # Check if contains honors
        for tile in self._flatten_tiles(winning_combination):
            if tile.is_honor:
                return None

        groups = self._group_combinations(winning_combination)
        sequences = groups[CombinationType.SEQUENCE]
        triplets = groups[CombinationType.TRIPLET] + groups[CombinationType.KAN]

        # Must be 4 sequences and each sequence contains 1 or 9
        if triplets:
            return None

        if len(sequences) == 4:
            for combination in sequences:
                tiles = sorted(combination.tiles)
                start_rank = tiles[0].rank
                if start_rank not in [1, 7]:
                    return None

            # Determine han based on rules
            ruleset = game_state.ruleset if game_state else None
            if ruleset:
                han = (
                    ruleset.junchan_closed_han
                    if hand.is_concealed
                    else ruleset.junchan_open_han
                )
            else:
                # Default: menzen 3 han, Meld 2 han
                han = 3 if hand.is_concealed else 2
            return YakuResult(Yaku.JUNCHAN, han, False)

        return None

    def check_chanta(
        self,
        hand: Hand,
        winning_combination: List,
        game_state: Optional[GameState] = None,
    ) -> Optional[YakuResult]:
        """
        Check chanta (Mixed Terminal Chow).

        chanta: Composed entirely of sequences and pairs, and each meld contains 1 or 9 or Honor.
        Can have honors, han value depends on menzen/Meld state (Standard competitive rules).

        Args:
            hand (Hand): hand.
            winning_combination (List): Winning combinations.
            game_state (Optional[GameState]): Game state.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        ruleset = game_state.ruleset if game_state else None
        if ruleset and not ruleset.chanta_enabled:
            return None

        if not winning_combination:
            return None

        # Check if has honors
        has_honor = False
        all_terminals = True

        for combination in winning_combination:
            tiles = combination.tiles
            if any(tile.is_honor for tile in tiles):
                has_honor = True

            if combination.type == CombinationType.SEQUENCE:
                sorted_tiles = sorted(tiles)
                start_rank = sorted_tiles[0].rank
                if start_rank not in [1, 7]:
                    all_terminals = False
                    break
            else:
                representative_tile = sorted(tiles)[0]
                if not (
                    representative_tile.is_terminal or representative_tile.is_honor
                ):
                    all_terminals = False
                    break

        # Must have honors, and all number tiles are terminals
        if has_honor and all_terminals:
            # Determine han based on rules
            if ruleset:
                han = (
                    ruleset.chanta_closed_han
                    if hand.is_concealed
                    else ruleset.chanta_open_han
                )
            else:
                # Default: menzen 2 han, Meld 1 han
                han = 2 if hand.is_concealed else 1
            return YakuResult(Yaku.CHANTA, han, False)

        return None

    def check_ryanpeikou(
        self, hand: Hand, winning_combination: List
    ) -> Optional[YakuResult]:
        """
        Check ryanpeikou.

        ryanpeikou: Two distinct identical sequences while menzen.
        Note: ryanpeikou overrides iipeikou, so check ryanpeikou first.

        Args:
            hand (Hand): hand.
            winning_combination (List): Winning combinations.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        if not hand.is_concealed:
            return None

        if not winning_combination:
            return None

        groups = self._group_combinations(winning_combination)
        sequences = [
            self._get_combination_key(seq) for seq in groups[CombinationType.SEQUENCE]
        ]

        # Must have 4 sequences
        if len(sequences) != 4:
            return None

        # Check if there are two distinct identical sequences
        sequence_counts = {}
        for seq in sequences:
            sequence_counts[seq] = sequence_counts.get(seq, 0) + 1

        # Count how many distinct sequences appear twice
        paired_sequences = [seq for seq, count in sequence_counts.items() if count >= 2]

        # ryanpeikou needs two distinct sequences each appearing twice
        if len(paired_sequences) == 2:
            # Check if each group appears exactly twice
            for seq in paired_sequences:
                if sequence_counts[seq] != 2:
                    return None
            return YakuResult(Yaku.RYANPEIKOU, 3, False)

        return None

    def check_sanshoku_doukou(
        self, hand: Hand, winning_combination: List
    ) -> Optional[YakuResult]:
        """
        Check sanshoku_doukou.

        sanshoku_doukou: Triplets of the same number in manzu, pinzu, souzu.

        Args:
            hand (Hand): hand.
            winning_combination (List): Winning combinations.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        if not winning_combination:
            return None

        # Count triplets
        triplets_by_suit = {Suit.MANZU: [], Suit.PINZU: [], Suit.SOUZU: []}

        groups = self._group_combinations(winning_combination)
        for triplet in groups[CombinationType.TRIPLET]:
            suit, rank = self._get_combination_key(triplet)
            if suit in triplets_by_suit:
                triplets_by_suit[suit].append(rank)

        # Check if there are triplets of the same number in all three suits
        for rank in range(1, 10):
            has_manzu = rank in triplets_by_suit[Suit.MANZU]
            has_pinzu = rank in triplets_by_suit[Suit.PINZU]
            has_souzu = rank in triplets_by_suit[Suit.SOUZU]

            if has_manzu and has_pinzu and has_souzu:
                return YakuResult(Yaku.SANSHOKU_DOUKOU, 2, False)

        return None

    def check_shousangen(
        self, hand: Hand, winning_combination: List
    ) -> Optional[YakuResult]:
        """
        Check shousangen.

        shousangen: Two haku/hatsu/chun triplets and one haku/hatsu/chun pair.

        Args:
            hand (Hand): hand.
            winning_combination (List): Winning combinations.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        if not winning_combination:
            return None

        haku_hatsu_chun_ranks = [5, 6, 7]
        haku_hatsu_chun_triplets = []
        haku_hatsu_chun_pair = None

        groups = self._group_combinations(winning_combination)
        triplet_like = groups[CombinationType.TRIPLET] + groups[CombinationType.KAN]
        for combination in triplet_like:
            tile = sorted(combination.tiles)[0]
            if tile.suit == Suit.HONORS and tile.rank in haku_hatsu_chun_ranks:
                haku_hatsu_chun_triplets.append(tile.rank)

        pair_combination = self._extract_pair(winning_combination)
        if pair_combination:
            pair_tile = sorted(pair_combination.tiles)[0]
            if (
                pair_tile.suit == Suit.HONORS
                and pair_tile.rank in haku_hatsu_chun_ranks
            ):
                haku_hatsu_chun_pair = pair_tile.rank

        # Two haku/hatsu/chun triplets + one haku/hatsu/chun pair
        if len(haku_hatsu_chun_triplets) == 2 and haku_hatsu_chun_pair is not None:
            return YakuResult(Yaku.SHOUSANGEN, 2, False)

        return None

    def check_honroutou(
        self, hand: Hand, winning_combination: List
    ) -> Optional[YakuResult]:
        """
        Check honroutou.

        honroutou: Composed entirely of terminals and honors.

        Args:
            hand (Hand): hand.
            winning_combination (List): Winning combinations.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        if not winning_combination:
            return None

        # Check if all tiles are terminals or honors
        for combination in winning_combination:
            for tile in combination.tiles:
                if not (tile.is_terminal or tile.is_honor):
                    return None

        return YakuResult(Yaku.HONROUTOU, 2, False)

    def check_daisangen(
        self, hand: Hand, winning_combination: List
    ) -> Optional[YakuResult]:
        """
        Check daisangen.

        daisangen: Three haku/hatsu/chun triplets.

        Args:
            hand (Hand): hand.
            winning_combination (List): Winning combinations.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        if not winning_combination:
            return None

        haku_hatsu_chun_ranks = [5, 6, 7]
        haku_hatsu_chun_triplets = []

        groups = self._group_combinations(winning_combination)
        triplet_like = groups[CombinationType.TRIPLET] + groups[CombinationType.KAN]
        for combination in triplet_like:
            tile = sorted(combination.tiles)[0]
            if tile.suit == Suit.HONORS and tile.rank in haku_hatsu_chun_ranks:
                haku_hatsu_chun_triplets.append(tile.rank)

        # Three haku/hatsu/chun triplets
        if len(haku_hatsu_chun_triplets) == 3:
            return YakuResult(Yaku.DAISANGEN, 13, True)

        return None

    def check_suukantsu(
        self, hand: Hand, winning_combination: List
    ) -> Optional[YakuResult]:
        """
        Check Suukantsu (Four Quads).

        Suukantsu: Four kans.

        Args:
            hand (Hand): hand.
            winning_combination (List): Winning combinations.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        if not winning_combination:
            return None

        groups = self._group_combinations(winning_combination)
        kan_count = len(groups[CombinationType.KAN])

        # Four kans
        return YakuResult(Yaku.SUUKANTSU, 13, True) if kan_count == 4 else None

    def check_suuankou(
        self,
        hand: Hand,
        winning_combination: List,
        winning_tile: Optional[Tile] = None,
        game_state: Optional[GameState] = None,
    ) -> Optional[YakuResult]:
        """
        Check suuankou (Four Concealed Triplets).

        suuankou: Four concealed triplets (or suuankou tanki).
        Depending on rules, suuankou tanki (Single Wait) may be Double yakuman.

        Args:
            hand (Hand): hand.
            winning_combination (List): Winning combinations.
            winning_tile (Optional[Tile]): Winning tile.
            game_state (Optional[GameState]): Game state.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        if not hand.is_concealed:
            return None

        if not winning_combination:
            return None

        groups = self._group_combinations(winning_combination)
        triplet_like = groups[CombinationType.TRIPLET] + groups[CombinationType.KAN]
        triplets = len(triplet_like)

        is_tanki = False
        pair_combination = self._extract_pair(winning_combination)
        if pair_combination and winning_tile:
            pair_tile = sorted(pair_combination.tiles)[0]
            if (
                pair_tile.suit == winning_tile.suit
                and pair_tile.rank == winning_tile.rank
            ):
                is_tanki = True

        # Four Concealed Triplets
        if triplets == 4:
            ruleset = game_state.ruleset if game_state else None
            if ruleset and ruleset.suuankou_tanki_double and is_tanki:
                return YakuResult(Yaku.SUUANKOU_TANKI, 26, True)
            return YakuResult(Yaku.SUUANKOU, 13, True)

        return None

    def check_kokushi_musou(
        self, hand: Hand, winning_tile: Optional[Tile] = None
    ) -> Optional[YakuResult]:
        """
        Check kokushi_musou.

        kokushi_musou: One of each of the 13 terminals and honors, plus one duplicate.
        kokushi_musou_juusanmen: one of each of the 13 terminals and honors, plus one duplicate, and that tile is the machi.

        Args:
            hand (Hand): hand.
            winning_tile (Optional[Tile]): Winning tile.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        if not hand.is_concealed:
            return None

        if len(hand.tiles) == 14:
            tiles = hand.tiles
        else:
            tiles = hand.tiles + [winning_tile] if winning_tile else hand.tiles
        if len(tiles) != 14:
            return None

        # Required 13 terminals and honors
        required_tiles = [
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 9),
            Tile(Suit.PINZU, 1),
            Tile(Suit.PINZU, 9),
            Tile(Suit.SOUZU, 1),
            Tile(Suit.SOUZU, 9),
            Tile(Suit.HONORS, 1),
            Tile(Suit.HONORS, 2),
            Tile(Suit.HONORS, 3),
            Tile(Suit.HONORS, 4),
            Tile(Suit.HONORS, 5),
            Tile(Suit.HONORS, 6),
            Tile(Suit.HONORS, 7),
        ]

        # Count each tile
        counts = {}
        for tile in tiles:
            counts[tile] = counts.get(tile, 0) + 1

        # Check if only one duplicate
        pairs = 0
        for key, count in counts.items():
            if key not in required_tiles:
                return None  # Non-Terminal/Honor tile
            if count == 2:
                if pairs != 0:
                    return None  # More than one duplicate
                pairs += 1

        if hand.tiles == required_tiles:
            return YakuResult(Yaku.KOKUSHI_MUSOU_JUUSANMEN, 26, True)
        else:
            return YakuResult(Yaku.KOKUSHI_MUSOU, 13, True)

    def check_shousuushi(
        self, hand: Hand, winning_combination: List
    ) -> Optional[YakuResult]:
        """
        Check Shousuushi (Little Four Winds).

        Shousuushi: Three Wind triplets and one Wind pair.

        Args:
            hand (Hand): hand.
            winning_combination (List): Winning combinations.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        if not winning_combination:
            return None

        kaze = [1, 2, 3, 4]  # East, South, West, North
        kaze_triplets = []
        kaze_pair = None

        groups = self._group_combinations(winning_combination)
        triplet_like = groups[CombinationType.TRIPLET] + groups[CombinationType.KAN]
        for combination in triplet_like:
            tile = sorted(combination.tiles)[0]
            if tile.suit == Suit.HONORS and tile.rank in kaze:
                kaze_triplets.append(tile.rank)

        pair_combination = self._extract_pair(winning_combination)
        if pair_combination:
            pair_tile = sorted(pair_combination.tiles)[0]
            if pair_tile.suit == Suit.HONORS and pair_tile.rank in kaze:
                kaze_pair = pair_tile.rank

        # Three Wind triplets + One Wind pair
        if len(kaze_triplets) == 3 and kaze_pair is not None:
            return YakuResult(Yaku.SHOUSUUSHI, 13, True)

        return None

    def check_daisuushi(
        self, hand: Hand, winning_combination: List
    ) -> Optional[YakuResult]:
        """
        Check Daisuushi (Big Four Winds).

        Daisuushi: Four Wind triplets.

        Args:
            hand (Hand): hand.
            winning_combination (List): Winning combinations.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        if not winning_combination:
            return None

        kaze = [1, 2, 3, 4]  # East, South, West, North
        kaze_triplets = []

        groups = self._group_combinations(winning_combination)
        triplet_like = groups[CombinationType.TRIPLET] + groups[CombinationType.KAN]
        for combination in triplet_like:
            tile = sorted(combination.tiles)[0]
            if tile.suit == Suit.HONORS and tile.rank in kaze:
                kaze_triplets.append(tile.rank)

        # Four Wind triplets
        if len(kaze_triplets) == 4:
            return YakuResult(Yaku.DAISUUSHI, 13, True)

        return None

    def check_chinroutou(
        self, hand: Hand, winning_combination: List
    ) -> Optional[YakuResult]:
        """
        Check chinroutou (All terminals).

        chinroutou: Composed entirely of Terminal triplets (No honors).

        Args:
            hand (Hand): hand.
            winning_combination (List): Winning combinations.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        if not winning_combination:
            return None

        for combination in winning_combination:
            tiles = combination.tiles

            # If has honors, not chinroutou
            if any(tile.is_honor for tile in tiles):
                return None

            if combination.type not in {
                CombinationType.TRIPLET,
                CombinationType.KAN,
                CombinationType.PAIR,
            }:
                return None

            if any(not tile.is_terminal for tile in tiles):
                return None
        return YakuResult(Yaku.CHINROUTOU, 13, True)

    def check_tsuuiisou(
        self, hand: Hand, winning_combination: List
    ) -> Optional[YakuResult]:
        """
        Check tsuuiisou (All honors).

        tsuuiisou: Composed entirely of honors.

        Args:
            hand (Hand): hand.
            winning_combination (List): Winning combinations.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        if not winning_combination:
            return None

        for tile in self._flatten_tiles(winning_combination):
            if not tile.is_honor:
                return None

        return YakuResult(Yaku.TSUUIISOU, 13, True)

    def check_ryuuiisou(
        self, hand: Hand, winning_combination: List
    ) -> Optional[YakuResult]:
        """
        Check ryuuiisou.

        ryuuiisou: Composed entirely of ryuuiisou tiles (2, 3, 4, 6, 8 souzu, hatsu).

        Args:
            hand (Hand): hand.
            winning_combination (List): Winning combinations.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        if not winning_combination:
            return None

        # ryuuiisou tiles: 2, 3, 4, 6, 8 souzu, hatsu
        ryuuiisou_tiles = [
            (Suit.SOUZU, 2),
            (Suit.SOUZU, 3),
            (Suit.SOUZU, 4),
            (Suit.SOUZU, 6),
            (Suit.SOUZU, 8),
            (Suit.HONORS, 6),  # hatsu
        ]

        ryuuiisou_tile_set = set(ryuuiisou_tiles)
        for tile in self._flatten_tiles(winning_combination):
            if (tile.suit, tile.rank) not in ryuuiisou_tile_set:
                return None

        return YakuResult(Yaku.RYUUIISOU, 13, True)

    def check_chuuren_poutou(
        self, hand: Hand, winning_tile: Tile, game_state: Optional[GameState] = None
    ) -> Optional[YakuResult]:
        """
        Check chuuren_poutou.

        chuuren_poutou: Same suit with 1112345678999 + any one tile of same suit.
        pure_chuuren_poutou: chuuren_poutou and waiting for 9-way wait.
        Depending on rules, pure_chuuren_poutou may be double_yakuman.

        Args:
            hand (Hand): hand.
            winning_tile (Tile): Winning tile.
            game_state (Optional[GameState]): Game state.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        if not hand.is_concealed:
            return None

        all_tiles = hand.tiles + [winning_tile] if winning_tile else hand.tiles

        if len(all_tiles) != 14:
            return None

        # Check if same number suit
        suits = set[Suit]()
        for tile in all_tiles:
            if tile.suit != Suit.HONORS:  # Only check number tiles
                suits.add(tile.suit)
            else:
                return None  # Has honors, not chuuren_poutou

        # Must be only one suit
        if len(suits) != 1:
            return None

        suit = suits.pop()

        # Count tiles of that suit
        counts: Dict[int, int] = {}
        for tile in all_tiles:
            if tile.suit == suit:
                counts[tile.rank] = counts.get(tile.rank, 0) + 1

        # Check 1 & 9 at least 3, others at least 1
        for rank, count in counts.items():
            if (rank in {1, 9} and count < 3) or (rank not in {1, 9} and count < 1):
                return None

        # Check total count is 14 (1-9 at least required count, plus extra 1)
        total = sum(counts.values())
        if total != 14:
            return None

        # Check if pure_chuuren_poutou
        is_pure = True
        hand_counts: Dict[int, int] = {}
        for tile in hand.tiles:
            hand_counts[tile.rank] = hand_counts.get(tile.rank, 0) + 1
            if (tile.rank in {1, 9} and hand_counts[tile.rank] > 3) or (
                tile.rank not in {1, 9} and hand_counts[tile.rank] > 1
            ):
                is_pure = False
                break

        if is_pure:
            ruleset = game_state.ruleset if game_state else None
            if ruleset and ruleset.pure_chuuren_poutou_double:
                return YakuResult(Yaku.PURE_CHUUREN_POUTOU, 26, True)
            else:
                return YakuResult(Yaku.PURE_CHUUREN_POUTOU, 13, True)

        return YakuResult(Yaku.CHUUREN_POUTOU, 13, True)

    def check_tenhou(
        self,
        hand: Hand,
        is_tsumo: bool,
        is_first_turn: bool,
        player_position: int,
        game_state: GameState,
    ) -> Optional[YakuResult]:
        """
        Check tenhou.

        tenhou: dealer wins by tsumo on first turn.
        Conditions:
        1. dealer (player_position == dealer)
        2. First turn (is_first_turn)
        3. tsumo (is_tsumo)
        4. menzen (hand.is_concealed)

        Args:
            hand (Hand): hand.
            is_tsumo (bool): Is tsumo.
            is_first_turn (bool): Is first turn.
            player_position (int): Player position.
            game_state (GameState): Game state.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        # Must be dealer
        if player_position != game_state.dealer:
            return None

        # Must be first turn
        if not is_first_turn:
            return None

        # Must be tsumo
        if not is_tsumo:
            return None

        # Must be menzen
        return YakuResult(Yaku.TENHOU, 13, True) if hand.is_concealed else None

    def check_chihou(
        self,
        hand: Hand,
        is_tsumo: bool,
        is_first_turn: bool,
        player_position: int,
        game_state: GameState,
    ) -> Optional[YakuResult]:
        """
        Check chihou.

        chihou: non-dealer wins by tsumo on first turn.
        Conditions:
        1. non-dealer (player_position != dealer)
        2. First turn (is_first_turn)
        3. tsumo (is_tsumo)
        4. menzen (hand.is_concealed)

        Args:
            hand (Hand): hand.
            is_tsumo (bool): Is tsumo.
            is_first_turn (bool): Is first turn.
            player_position (int): Player position.
            game_state (GameState): Game state.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        # Must be non-dealer
        if player_position == game_state.dealer:
            return None

        # Must be first turn
        if not is_first_turn:
            return None

        # Must be tsumo
        if not is_tsumo:
            return None

        # Must be menzen
        return YakuResult(Yaku.CHIHOU, 13, True) if hand.is_concealed else None

    def check_renhou(
        self,
        hand: Hand,
        is_tsumo: bool,
        is_first_turn: bool,
        player_position: int,
        game_state: GameState,
    ) -> Optional[YakuResult]:
        """
        Check renhou.

        renhou: non-dealer wins by ron on first turn.
        Conditions:
        1. non-dealer (player_position != dealer)
        2. First turn (is_first_turn)
        3. ron (not is_tsumo)
        4. menzen (hand.is_concealed)

        han value depends on rules:
        - RenhouPolicy.YAKUMAN: yakuman (13 han)
        - RenhouPolicy.TWO_HAN: 2 han (standard competitive rules)
        - RenhouPolicy.OFF: Disabled

        Args:
            hand (Hand): hand.
            is_tsumo (bool): Is tsumo.
            is_first_turn (bool): Is first turn.
            player_position (int): Player position.
            game_state (GameState): Game state.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        ruleset = game_state.ruleset

        # Check if enabled
        if ruleset.renhou_policy == RenhouPolicy.OFF:
            return None

        # Must be non-dealer
        if player_position == game_state.dealer:
            return None

        # Must be first turn
        if not is_first_turn:
            return None

        # Must be ron
        if is_tsumo:
            return None

        # Must be menzen
        if not hand.is_concealed:
            return None

        # Return han based on rules
        if ruleset.renhou_policy == RenhouPolicy.YAKUMAN:
            return YakuResult(Yaku.RENHOU, 13, True)
        elif ruleset.renhou_policy == RenhouPolicy.TWO_HAN:
            return YakuResult(Yaku.RENHOU, 2, False)
        else:
            return None

    def check_haitei_houtei(
        self, hand: Hand, is_tsumo: bool, is_last_tile: bool
    ) -> Optional[YakuResult]:
        """
        Check haitei / houtei.

        haitei: Win by tsumo on the last tile (1 han).
        houtei: Win by ron on the last tile (1 han).

        Args:
            hand (Hand): hand.
            is_tsumo (bool): Is tsumo.
            is_last_tile (bool): Is last tile.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        if not is_last_tile:
            return None

        if is_tsumo:
            return YakuResult(Yaku.HAITEI, 1, False)
        else:
            return YakuResult(Yaku.HOUTEI, 1, False)

    def check_rinshan(self, hand: Hand, is_rinshan: bool) -> Optional[YakuResult]:
        """
        Check rinshan.

        rinshan: Win by tsumo from the dead wall after a kan (1 han).

        Args:
            hand (Hand): hand.
            is_rinshan (bool): Is rinshan.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        return YakuResult(Yaku.RINSHAN, 1, False) if is_rinshan else None

    def _determine_machi(self, winning_tile: Tile, winning_combination: List) -> Machi:
        """
        Determine tenpai type.

        Args:
            winning_tile (Tile): Winning tile.
            winning_combination (List): Winning combinations.

        Returns:
            Machi: machi value: ryanmen (Two-sided), penchan (Edge),
                kanchan (Closed), tanki (Single), shabo (Dual).
        """
        if not winning_combination:
            return Machi.RYANMEN  # Default to ryanmen

        pair_combination = self._extract_pair(winning_combination)
        if pair_combination and any(
            tile == winning_tile for tile in pair_combination.tiles
        ):
            return Machi.TANKI

        for combination in winning_combination:
            if combination.type != CombinationType.SEQUENCE:
                continue

            if winning_tile not in combination.tiles:
                continue

            tiles = sorted(combination.tiles)
            # Find index of winning tile in sequence
            try:
                index = tiles.index(winning_tile)
            except ValueError:
                # winning_tile might be different object, use attribute matching
                index = next(
                    (
                        i
                        for i, tile in enumerate(tiles)
                        if tile.suit == winning_tile.suit
                        and tile.rank == winning_tile.rank
                    ),
                    -1,
                )
                if index == -1:
                    continue

            if index == 1:
                return Machi.KANCHAN

            first_rank = tiles[0].rank
            last_rank = tiles[-1].rank
            if index == 0 or index == 2:
                if first_rank == 1 or last_rank == 9:
                    return Machi.PENCHAN
                return Machi.RYANMEN

        # Default to ryanmen
        return Machi.RYANMEN

    def check_chankan(
        self, hand: Hand, is_chankan: bool = False
    ) -> Optional[YakuResult]:
        """
        Check chankan (Robbing the kan).

        Args:
            hand (Hand): hand.
            is_chankan (bool): Is chankan.

        Returns:
            Optional[YakuResult]: yaku result, or None if not matching.
        """
        return YakuResult(Yaku.CHANKAN, 1, False) if is_chankan else None
