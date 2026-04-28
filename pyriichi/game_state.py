"""
Game State Management - GameState implementation

Manages game state such as round number, wind, scores, etc.
"""

from typing import List, Optional

from pyriichi.enum_utils import TranslatableEnum
from pyriichi.rules_config import RulesetConfig
from pyriichi.tiles import Suit, Tile


class Wind(TranslatableEnum):
    """Wind"""

    EAST = ("east", "東", "東", "East")
    SOUTH = ("south", "南", "南", "South")
    WEST = ("west", "西", "西", "West")
    NORTH = ("north", "北", "北", "North")

    @property
    def tile(self) -> Tile:
        if self == Wind.EAST:
            return Tile(Suit.HONORS, 1)
        elif self == Wind.SOUTH:
            return Tile(Suit.HONORS, 2)
        elif self == Wind.WEST:
            return Tile(Suit.HONORS, 3)
        elif self == Wind.NORTH:
            return Tile(Suit.HONORS, 4)
        else:
            raise ValueError(f"Invalid wind: {self}")


class GameState:
    """Game State Manager"""

    def __init__(
        self,
        initial_scores: Optional[List[int]] = None,
        num_players: int = 4,
        ruleset: Optional[RulesetConfig] = None,
    ):
        """
        Initialize game state.

        Args:
            initial_scores (Optional[List[int]]): Initial scores list (default 25000 per player).
            num_players (int): Number of players.
            ruleset (Optional[RulesetConfig]): Ruleset configuration (default standard competitive rules).
        """
        if initial_scores is None:
            initial_scores = [25000] * num_players

        self._scores = initial_scores.copy()
        self._round_wind = Wind.EAST
        self._round_number = 1
        self._dealer = 0
        self._honba = 0
        self._riichi_sticks = 0
        self._num_players = num_players
        self._ruleset = ruleset if ruleset is not None else RulesetConfig.standard()

    @property
    def round_wind(self) -> Wind:
        return self._round_wind

    @property
    def round_number(self) -> int:
        return self._round_number

    @property
    def player_winds(self) -> List[Wind]:
        winds = [Wind.EAST, Wind.SOUTH, Wind.WEST, Wind.NORTH]
        return [
            winds[(i - self._dealer) % self._num_players]
            for i in range(self._num_players)
        ]

    @property
    def dealer(self) -> int:
        return self._dealer

    @property
    def honba(self) -> int:
        return self._honba

    @property
    def riichi_sticks(self) -> int:
        return self._riichi_sticks

    @property
    def scores(self) -> List[int]:
        return self._scores.copy()

    def set_round(self, round_wind: Wind, round_number: int) -> None:
        """
        Set round.

        Args:
            round_wind (Wind): Prevalent Wind.
            round_number (int): Round number.
        """
        self._round_wind = round_wind
        self._round_number = round_number

    def set_dealer(self, dealer: int) -> None:
        """
        Set dealer.

        Args:
            dealer (int): Dealer position.

        Raises:
            ValueError: If position is invalid.
        """
        if not (0 <= dealer < self._num_players):
            raise ValueError(f"莊家位置必須在 0-{self._num_players - 1} 之間")
        self._dealer = dealer

    def add_honba(self, count: int = 1) -> None:
        """
        Add honba count.

        Args:
            count (int): Amount to add (default 1).
        """
        self._honba += count

    def reset_honba(self) -> None:
        """Reset honba count to 0."""
        self._honba = 0

    def add_riichi_stick(self) -> None:
        """Add one Riichi Stick to Deposit."""
        self._riichi_sticks += 1

    def clear_riichi_sticks(self) -> None:
        """Clear Riichi Stick count."""
        self._riichi_sticks = 0

    @property
    def ruleset(self) -> RulesetConfig:
        return self._ruleset

    def update_score(self, player: int, points: int) -> None:
        """
        Update player score.

        Args:
            player (int): Player position.
            points (int): Points change (positive to increase, negative to decrease).

        Raises:
            ValueError: If player position is invalid.
        """
        if not (0 <= player < self._num_players):
            raise ValueError(f"玩家位置必須在 0-{self._num_players - 1} 之間")
        self._scores[player] += points

    def transfer_points(self, from_player: int, to_player: int, points: int) -> None:
        """
        Transfer points.

        Args:
            from_player (int): Player paying points.
            to_player (int): Player receiving points.
            points (int): Points to transfer.
        """
        self.update_score(from_player, -points)
        self.update_score(to_player, points)

    def next_round(self) -> bool:
        """
        Proceed to next round.

        Returns:
            bool: Whether there is a next round (False if game ended).
        """
        # west_round_extension end check.
        # In west round, the game ends once someone reaches return_score.
        if self._round_wind == Wind.WEST:
            max_score = max(self._scores)
            if max_score >= self.ruleset.return_score:
                return False

        self._round_number += 1

        # If 4 rounds completed, move to next wind
        if self._round_number > 4:
            if self._round_wind == Wind.EAST:
                self._round_wind = Wind.SOUTH
                self._round_number = 1
            elif self._round_wind == Wind.SOUTH:
                max_score = max(self._scores)
                if (
                    self.ruleset.west_round_extension
                    and max_score < self.ruleset.return_score
                ):
                    self._round_wind = Wind.WEST
                    self._round_number = 1
                else:
                    # return_score reached or west_round_extension disabled, game ends.
                    return False
            elif self._round_wind == Wind.WEST:
                # west round ends.
                return False

        return True

    def next_dealer(self, dealer_won: bool) -> None:
        """
        Set next dealer.

        Args:
            dealer_won (bool): Whether dealer won.
        """
        if not dealer_won:
            self._dealer = (self._dealer + 1) % self._num_players
            self.reset_honba()
        else:
            self.add_honba()
