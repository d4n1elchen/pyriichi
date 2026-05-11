"""
Score Calculator System - ScoreCalculator implementation

Provides functionality for calculating fu, han, and Points.
"""

from dataclasses import dataclass
from typing import List, Optional

from pyriichi.game_state import GameState
from pyriichi.hand import Combination, CombinationType, Hand
from pyriichi.tiles import Suit, Tile
from pyriichi.yaku import Machi, Yaku, YakuResult


@dataclass
class ScoreResult:
    """Score Calculation Result"""

    han: int  # han
    fu: int  # fu
    base_points: int  # Base Points
    total_points: (
        int  # Total Points (Payment per person for tsumo, total payment for ron)
    )
    payment_from: int  # Payer position (for ron)
    payment_to: int  # Receiver position
    is_yakuman: bool  # Is yakuman
    yakuman_count: int  # yakuman multiplier
    is_tsumo: bool = False  # Is tsumo
    dealer_payment: int = 0  # dealer payment (for tsumo)
    non_dealer_payment: int = 0  # Non-dealer payment (for tsumo)
    honba_bonus: int = 0  # honba bonus
    riichi_sticks_bonus: int = 0  # Riichi Stick distribution
    kiriage_mangan_enabled: bool = False  # Is kiriage_mangan enabled
    pao_player: Optional[int] = None  # pao player position
    pao_payment: int = 0  # pao player payment amount

    def __post_init__(self):
        """Calculate final score."""
        if self.is_yakuman:
            self.total_points = 8000 * self.yakuman_count
        elif self.han >= 13:
            self.total_points = 8000  # yakuman (Kazoe)
        elif self.han >= 11:
            self.total_points = 6000  # sanbaiman
        elif self.han >= 8:
            self.total_points = 4000  # baiman
        elif self.han >= 6:
            self.total_points = 3000  # haneman
        elif self.han >= 5 or (self.han == 4 and self.fu >= 40):
            self.total_points = 2000  # mangan
        elif self.kiriage_mangan_enabled and (
            (self.han == 4 and self.fu == 30) or (self.han == 3 and self.fu == 60)
        ):
            # kiriage_mangan: 30 fu 4 han or 60 fu 3 han counts as mangan
            self.total_points = 2000  # mangan
        else:
            base = self.fu * (2 ** (self.han + 2))
            self.base_points = base
            # Points are not rounded up here, left for calculate_payments
            self.total_points = base

    def calculate_payments(self, game_state: GameState) -> None:
        """
        Calculate payment distribution.

        tsumo Payment:
        - dealer tsumo: Each non-dealer pays base_payment + honba, total 3 * (base_payment + honba)
        - non-dealer tsumo: dealer pays 2 * (base_payment + honba), other non-dealers pay base_payment + honba, total 2 * (base_payment + honba) + (base_payment + honba) * 2

        ron Payment:
        - Payer pays full total_points (including honba)

        pao Payment (yakuman):
        - tsumo: pao player pays all
        - ron (pao player deals in): pao player pays all
        - ron (Non-pao player deals in): pao player and deal-in player split payment

        honba Bonus:
        - +300 points per honba (Paid by everyone for tsumo, by deal-in player for ron)

        Riichi Stick:
        - All Riichi Sticks go to the winner

        Args:
            game_state (GameState): Game state (used to get honba count and Riichi Sticks).
        """

        self.honba_bonus = game_state.honba * 300

        self.riichi_sticks_bonus = game_state.riichi_sticks * 1000

        base_payment = self.total_points

        if self.pao_player is not None and self.is_yakuman:
            if self.is_tsumo:
                if self.payment_to == game_state.dealer:
                    # dealer tsumo: 16000 all -> 48000
                    total_win = (base_payment * 6 + 99) // 100 * 100
                else:
                    # non-dealer tsumo: 8000/16000 -> 32000
                    total_win = (base_payment * 4 + 99) // 100 * 100

                # Add honba (For tsumo, honba is paid by everyone 100*honba, total 300*honba)
                total_honba = game_state.honba * 300

                self.total_points = total_win + total_honba + self.riichi_sticks_bonus

                self.pao_payment = total_win + total_honba
                self.dealer_payment = 0
                self.non_dealer_payment = 0
                return

            else:
                if self.payment_to == game_state.dealer:
                    total_win = (base_payment * 6 + 99) // 100 * 100
                else:
                    total_win = (base_payment * 4 + 99) // 100 * 100

                total_honba = game_state.honba * 300
                self.total_points = total_win + total_honba + self.riichi_sticks_bonus

                if self.payment_from != self.pao_player:
                    # Split between pao player and deal-in player (Halved)

                    total_pay = total_win + total_honba
                    half_pay = total_pay // 2

                    self.pao_payment = half_pay
                    # Deal-in player pays the rest (usually also half)
                    pass
                else:
                    # pao player deals in: normal payment
                    self.pao_payment = 0  # Paid by payment_from (i.e., pao_player), not considered extra pao payment

                self.dealer_payment = 0
                self.non_dealer_payment = 0
                return

        if self.is_tsumo:
            # Each person pays: base_payment + honba_bonus
            honba_per_person = game_state.honba * 100

            if self.payment_to == game_state.dealer:
                self.dealer_payment = 0
                self.non_dealer_payment = (
                    2 * base_payment + 99
                ) // 100 * 100 + honba_per_person
                self.total_points = (
                    self.non_dealer_payment * 3 + self.riichi_sticks_bonus
                )
            else:
                self.dealer_payment = (
                    2 * base_payment + 99
                ) // 100 * 100 + honba_per_person
                self.non_dealer_payment = (
                    base_payment + 99
                ) // 100 * 100 + honba_per_person
                self.total_points = (
                    self.dealer_payment
                    + self.non_dealer_payment * 2
                    + self.riichi_sticks_bonus
                )
        else:
            # non-dealer ron: 4 * basic + 300 * honba
            # dealer ron: 6 * basic + 300 * honba

            total_honba = game_state.honba * 300

            if self.payment_to == game_state.dealer:
                win_points = (6 * base_payment + 99) // 100 * 100
            else:
                win_points = (4 * base_payment + 99) // 100 * 100

            self.total_points = win_points + total_honba + self.riichi_sticks_bonus
            self.dealer_payment = 0
            self.non_dealer_payment = 0  # Paid by payment_from for ron, dealer/non_dealer payment not set here


class ScoreCalculator:
    """Score Calculator"""

    @staticmethod
    def _group_combinations(winning_combination: Optional[List[Combination]]) -> dict:
        groups = {
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
    def _extract_pair(
        winning_combination: Optional[List[Combination]],
    ) -> Optional[Combination]:
        if not winning_combination:
            return None
        for combination in winning_combination:
            if combination.type == CombinationType.PAIR:
                return combination
        return None

    def calculate(
        self,
        hand: Hand,
        winning_tile: Tile,
        winning_combination: List,
        yaku_results: List[YakuResult],
        dora_count: int,
        game_state: GameState,
        is_tsumo: bool,
        player_position: int = 0,
        pao_player: Optional[int] = None,
        payment_to: Optional[int] = None,
        payment_from: Optional[int] = None,
    ) -> ScoreResult:
        """
        Calculate score.

        Args:
            hand (Hand): hand tiles.
            winning_tile (Tile): Winning tile.
            winning_combination (List): Winning combinations.
            yaku_results (List[YakuResult]): List of yaku results.
            dora_count (int): Number of dora.
            game_state (GameState): Game state.
            is_tsumo (bool): Whether tsumo.
            player_position (int): Player position.
            pao_player (Optional[int]): pao player position.
            payment_to (Optional[int]): Winning player position.
            payment_from (Optional[int]): Paying player position for ron.

        Returns:
            ScoreResult: Score calculation result.
        """
        # ... (Calculate fu, han, yakuman)
        # Calculate fu
        fu = self.calculate_fu(
            hand,
            winning_tile,
            winning_combination,
            yaku_results,
            game_state,
            is_tsumo,
            player_position,
        )

        han = self.calculate_han(yaku_results, dora_count)

        is_yakuman = any(r.is_yakuman for r in yaku_results)
        yakuman_count = sum(
            max(1, result.han // 13) for result in yaku_results if result.is_yakuman
        )
        resolved_payment_to = player_position if payment_to is None else payment_to
        resolved_payment_from = 0 if payment_from is None else payment_from

        result = ScoreResult(
            han=han,
            fu=fu,
            base_points=0,
            total_points=0,
            payment_from=resolved_payment_from,
            payment_to=resolved_payment_to,
            is_yakuman=is_yakuman,
            yakuman_count=yakuman_count,
            is_tsumo=is_tsumo,
            kiriage_mangan_enabled=game_state.ruleset.kiriage_mangan,
            pao_player=pao_player,
        )

        result.calculate_payments(game_state)

        return result

    def calculate_fu(
        self,
        hand: Hand,
        winning_tile: Tile,
        winning_combination: List,
        yaku_results: List[YakuResult],
        game_state: GameState,
        is_tsumo: bool,
        player_position: int = 0,
    ) -> int:
        """
        Calculate fu.

        Args:
            hand (Hand): hand tiles.
            winning_tile (Tile): Winning tile.
            winning_combination (List): Winning combinations.
            yaku_results (List[YakuResult]): List of yaku results.
            game_state (GameState): Game state.
            is_tsumo (bool): Whether tsumo.
            player_position (int): Player position (used for seat_wind pair fu).

        Returns:
            int: fu value.
        """
        if any(r.yaku == Yaku.CHIITOITSU for r in yaku_results):
            return 25  # chiitoitsu fixed 25 fu

        if any(r.yaku == Yaku.PINFU for r in yaku_results):
            return 20 if is_tsumo else 30

        fu = 20  # Base fu

        if hand.is_concealed and not is_tsumo:
            fu += 10
        elif is_tsumo:
            fu += 2

        for combination in winning_combination:
            if combination.type in [
                CombinationType.PAIR,
                CombinationType.SEQUENCE,
            ]:
                continue

            tile = combination.tiles[0]

            is_open = combination.is_open

            # If ron, and the combination contains the winning tile (and was originally concealed), treat as Open Triplet
            # Note: Only needed for Triplets (Sequence fu is 0, kans are always formed)
            if (
                not is_tsumo
                and not is_open
                and combination.type == CombinationType.TRIPLET
            ):
                if tile.suit == winning_tile.suit and tile.rank == winning_tile.rank:
                    is_open = True

            if combination.type == CombinationType.TRIPLET:
                base = 4 if is_open else 8
                fu += base if tile.is_terminal or tile.is_honor else base // 2
            elif combination.type == CombinationType.KAN:
                base = 16 if is_open else 32
                fu += base if tile.is_terminal or tile.is_honor else base // 2

        if pair_combination := self._extract_pair(winning_combination):
            pair_tile = pair_combination.tiles[0]

            # yakuhai Pair +2 fu
            if pair_tile.suit == Suit.HONORS:
                if pair_tile.rank in [5, 6, 7]:  # haku, hatsu, chun
                    fu += 2

                round_wind_tile = game_state.round_wind.tile
                if round_wind_tile == pair_tile:
                    fu += 2

                seat_winds = game_state.seat_winds
                if player_position < len(seat_winds):
                    seat_wind_tile = seat_winds[player_position].tile
                    if seat_wind_tile == pair_tile:
                        fu += 2

        machi = self._determine_machi(winning_tile, winning_combination)

        if machi in {
            Machi.TANKI,
            Machi.PENCHAN,
            Machi.KANCHAN,
        }:
            fu += 2
        # ryanmen and shabo do not add fu

        return ((fu + 9) // 10) * 10

    def _determine_machi(self, winning_tile: Tile, winning_combination: List) -> Machi:
        """
        Determine machi.

        Args:
            winning_tile (Tile): Winning tile.
            winning_combination (List): Winning combinations.

        Returns:
            Machi: machi value: ryanmen, penchan, kanchan, tanki, or shabo.
        """
        if not winning_combination:
            return Machi.RYANMEN

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
            try:
                index = tiles.index(winning_tile)
            except ValueError:
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
            if index in {0, 2}:
                if first_rank == 1 or last_rank == 9:
                    return Machi.PENCHAN
                return Machi.RYANMEN

        return Machi.RYANMEN

    def calculate_han(self, yaku_results: List[YakuResult], dora_count: int) -> int:
        """
        Calculate han.

        Args:
            yaku_results (List[YakuResult]): List of yaku results.
            dora_count (int): Number of dora.

        Returns:
            int: han value.
        """
        han = sum(r.han for r in yaku_results)
        han += dora_count
        return han
