"""
Score Calculator System - ScoreCalculator implementation

Provides functionality for calculating Fu, Han, and Points.
"""

from dataclasses import dataclass
from typing import List, Optional

from pyriichi.game_state import GameState
from pyriichi.hand import Combination, CombinationType, Hand
from pyriichi.tiles import Suit, Tile
from pyriichi.yaku import WaitingType, Yaku, YakuResult


@dataclass
class ScoreResult:
    """Score Calculation Result"""

    han: int  # Han
    fu: int  # Fu
    base_points: int  # Base Points
    total_points: (
        int  # Total Points (Payment per person for Tsumo, total payment for Ron)
    )
    payment_from: int  # Payer position (for Ron)
    payment_to: int  # Receiver position
    is_yakuman: bool  # Is Yakuman
    yakuman_count: int  # Yakuman multiplier
    is_tsumo: bool = False  # Is Tsumo
    dealer_payment: int = 0  # Dealer payment (for Tsumo)
    non_dealer_payment: int = 0  # Non-dealer payment (for Tsumo)
    honba_bonus: int = 0  # Honba bonus
    riichi_sticks_bonus: int = 0  # Riichi sticks distribution
    kiriage_mangan_enabled: bool = False  # Is Kiriage Mangan enabled
    pao_player: Optional[int] = None  # Pao player position
    pao_payment: int = 0  # Pao player payment amount

    def __post_init__(self):
        """Calculate final score."""
        if self.is_yakuman:
            self.total_points = 8000 * self.yakuman_count
        elif self.han >= 13:
            self.total_points = 8000  # Yakuman (Kazoe)
        elif self.han >= 11:
            self.total_points = 6000  # Sanbaiman
        elif self.han >= 8:
            self.total_points = 4000  # Baiman
        elif self.han >= 6:
            self.total_points = 3000  # Haneman
        elif self.han >= 5 or (self.han == 4 and self.fu >= 40):
            self.total_points = 2000  # Mangan
        elif self.kiriage_mangan_enabled and (
            (self.han == 4 and self.fu == 30) or (self.han == 3 and self.fu == 60)
        ):
            # Kiriage Mangan: 30 Fu 4 Han or 60 Fu 3 Han counts as Mangan
            self.total_points = 2000  # Mangan
        else:
            base = self.fu * (2 ** (self.han + 2))
            self.base_points = base
            # Points are not rounded up here, left for calculate_payments
            self.total_points = base

    def calculate_payments(self, game_state: GameState) -> None:
        """
        Calculate payment distribution.

        Tsumo Payment:
        - Dealer Tsumo: Each non-dealer pays base_payment + honba, total 3 * (base_payment + honba)
        - Non-dealer Tsumo: Dealer pays 2 * (base_payment + honba), other non-dealers pay base_payment + honba, total 2 * (base_payment + honba) + (base_payment + honba) * 2

        Ron Payment:
        - Payer pays full total_points (including Honba)

        Pao Payment (Yakuman):
        - Tsumo: Pao player pays all
        - Ron (Pao player deals in): Pao player pays all
        - Ron (Non-Pao player deals in): Pao player and deal-in player split payment

        Honba Bonus:
        - +300 points per Honba (Paid by everyone for Tsumo, by deal-in player for Ron)

        Riichi Sticks:
        - All Riichi sticks go to the winner

        Args:
            game_state (GameState): Game state (used to get Honba count and Riichi sticks).
        """

        self.honba_bonus = game_state.honba * 300

        self.riichi_sticks_bonus = game_state.riichi_sticks * 1000

        base_payment = self.total_points

        if self.pao_player is not None and self.is_yakuman:
            if self.is_tsumo:
                if self.payment_to == game_state.dealer:
                    # Dealer Tsumo: 16000 all -> 48000
                    total_win = (base_payment * 6 + 99) // 100 * 100
                else:
                    # Non-dealer Tsumo: 8000/16000 -> 32000
                    total_win = (base_payment * 4 + 99) // 100 * 100

                # Add Honba (For Tsumo, Honba is paid by everyone 100*honba, total 300*honba)
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
                    # Split between Pao player and deal-in player (Halved)

                    total_pay = total_win + total_honba
                    half_pay = total_pay // 2

                    self.pao_payment = half_pay
                    # Deal-in player pays the rest (usually also half)
                    pass
                else:
                    # Pao player deals in: Normal payment
                    self.pao_payment = 0  # Paid by payment_from (i.e., pao_player), not considered extra Pao payment

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
            # Non-dealer Ron: 4 * Basic + 300 * honba
            # Dealer Ron: 6 * Basic + 300 * honba

            total_honba = game_state.honba * 300

            if self.payment_to == game_state.dealer:
                win_points = (6 * base_payment + 99) // 100 * 100
            else:
                win_points = (4 * base_payment + 99) // 100 * 100

            self.total_points = win_points + total_honba + self.riichi_sticks_bonus
            self.dealer_payment = 0
            self.non_dealer_payment = 0  # Paid by payment_from for Ron, dealer/non_dealer payment not set here


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
    ) -> ScoreResult:
        """
        Calculate score.

        Args:
            hand (Hand): Hand tiles.
            winning_tile (Tile): Winning tile.
            winning_combination (List): Winning combinations.
            yaku_results (List[YakuResult]): List of Yaku results.
            dora_count (int): Number of Dora.
            game_state (GameState): Game state.
            is_tsumo (bool): Whether Tsumo.
            player_position (int): Player position.
            pao_player (Optional[int]): Pao player position.

        Returns:
            ScoreResult: Score calculation result.
        """
        # ... (Calculate fu, han, yakuman)
        # Calculate Fu
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
        yakuman_count = sum(bool(r.is_yakuman) for r in yaku_results)

        result = ScoreResult(
            han=han,
            fu=fu,
            base_points=0,
            total_points=0,
            payment_from=0,
            payment_to=0,
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
        Calculate Fu.

        Args:
            hand (Hand): Hand tiles.
            winning_tile (Tile): Winning tile.
            winning_combination (List): Winning combinations.
            yaku_results (List[YakuResult]): List of Yaku results.
            game_state (GameState): Game state.
            is_tsumo (bool): Whether Tsumo.
            player_position (int): Player position (used for Seat Wind Pair Fu).

        Returns:
            int: Fu value.
        """
        if any(r.yaku == Yaku.CHIITOITSU for r in yaku_results):
            return 25  # Chiitoitsu fixed 25 Fu

        if any(r.yaku == Yaku.PINFU for r in yaku_results):
            return 30 if is_tsumo else 20  # Pinfu fixed 30 Fu (Tsumo) or 20 Fu (Ron)

        fu = 20  # Base Fu

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

            # If Ron, and the combination contains the winning tile (and was originally concealed), treat as Open Triplet
            # Note: Only needed for Triplets (Sequence Fu is 0, Kans are always formed)
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

            # Yakuhai Pair +2 Fu
            if pair_tile.suit == Suit.JIHAI:
                if pair_tile.rank in [5, 6, 7]:  # Haku, Hatsu, Chun
                    fu += 2

                round_wind_tile = game_state.round_wind.tile
                if round_wind_tile == pair_tile:
                    fu += 2

                player_winds = game_state.player_winds
                if player_position < len(player_winds):
                    player_wind_tile = player_winds[player_position].tile
                    if player_wind_tile == pair_tile:
                        fu += 2

        waiting_type = self._determine_waiting_type(winning_tile, winning_combination)

        if waiting_type in {
            WaitingType.TANKI,
            WaitingType.PENCHAN,
            WaitingType.KANCHAN,
        }:
            fu += 2
        # Ryanmen and Shabo do not add Fu

        return ((fu + 9) // 10) * 10

    def _determine_waiting_type(
        self, winning_tile: Tile, winning_combination: List
    ) -> WaitingType:
        """
        Determine waiting type.

        Args:
            winning_tile (Tile): Winning tile.
            winning_combination (List): Winning combinations.

        Returns:
            WaitingType: Waiting type: 'ryanmen' (Two-sided), 'penchan' (Edge), 'kanchan' (Closed), 'tanki' (Single), 'shabo' (Dual).
        """
        if not winning_combination:
            return WaitingType.RYANMEN

        pair_combination = self._extract_pair(winning_combination)
        if pair_combination and any(
            tile == winning_tile for tile in pair_combination.tiles
        ):
            return WaitingType.TANKI

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
                return WaitingType.KANCHAN

            first_rank = tiles[0].rank
            last_rank = tiles[-1].rank
            if index in {0, 2}:
                if first_rank == 1 or last_rank == 9:
                    return WaitingType.PENCHAN
                return WaitingType.RYANMEN

        return WaitingType.RYANMEN

    def calculate_han(self, yaku_results: List[YakuResult], dora_count: int) -> int:
        """
        Calculate Han.

        Args:
            yaku_results (List[YakuResult]): List of Yaku results.
            dora_count (int): Number of Dora.

        Returns:
            int: Han value.
        """
        han = sum(r.han for r in yaku_results)
        han += dora_count
        return han
