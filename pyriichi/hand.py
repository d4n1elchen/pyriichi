"""
hand Management System - hand and Meld implementation

Provides hand operations, meld management, and winning hand determination.
"""

from enum import Enum
from typing import List, Optional, Tuple

from pyriichi.enum_utils import TranslatableEnum
from pyriichi.tiles import Suit, Tile


class CombinationType(Enum):
    """Winning combination type"""

    PAIR = "pair"
    TRIPLET = "triplet"
    SEQUENCE = "sequence"
    KAN = "kan"


class Combination:
    """Winning combination"""

    def __init__(self, combination_type: CombinationType, tiles: List[Tile]):
        if combination_type == CombinationType.PAIR:
            if len(tiles) != 2:
                raise ValueError("對子必須是 2 張牌")
        elif combination_type == CombinationType.TRIPLET:
            if len(tiles) != 3:
                raise ValueError("刻子必須是 3 張牌")
        elif combination_type == CombinationType.SEQUENCE:
            if len(tiles) != 3:
                raise ValueError("順子必須是 3 張牌")
        elif combination_type == CombinationType.KAN:
            if len(tiles) != 4:
                raise ValueError("槓子必須是 4 張牌")

        self._type = combination_type
        self._tiles = tiles
        self._is_open = False

    def set_open(self, is_open: bool):
        self._is_open = is_open

    @property
    def is_open(self) -> bool:
        return self._is_open

    @property
    def type(self) -> CombinationType:
        return self._type

    @property
    def tiles(self) -> List[Tile]:
        return self._tiles


def make_combination(combo_type: CombinationType, suit: Suit, rank: int) -> Combination:
    """
    Quickly create a `Combination` based on type and suit/rank.

    Args:
        combo_type (CombinationType): Combination type.
        suit (Suit): Tile suit.
        rank (int): Number tile rank or Honor tile index.

    Returns:
        Combination: Corresponding `Combination` instance.

    Raises:
        ValueError: If combination type is unsupported or sequence parameters are invalid.
    """

    if combo_type == CombinationType.SEQUENCE:
        if suit == Suit.HONORS:
            raise ValueError("字牌不能組成順子")
        if not (1 <= rank <= 7):
            raise ValueError("順子起始點數必須介於 1 到 7 之間")
        tiles = [Tile(suit, rank + i) for i in range(3)]
    elif combo_type == CombinationType.TRIPLET:
        tiles = [Tile(suit, rank) for _ in range(3)]
    elif combo_type == CombinationType.KAN:
        tiles = [Tile(suit, rank) for _ in range(4)]
    elif combo_type == CombinationType.PAIR:
        tiles = [Tile(suit, rank) for _ in range(2)]
    else:
        raise ValueError(f"不支援的組合類型：{combo_type}")

    return Combination(combo_type, tiles)


class MeldType(TranslatableEnum):
    """Meld type"""

    CHI_MELD = ("chi_meld", "吃", "チー", "Chi Meld")
    PON_MELD = ("pon_meld", "碰", "ポン", "Pon Meld")
    OPEN_KAN = ("open_kan", "明槓", "明槓", "Open Kan")
    CLOSED_KAN = ("closed_kan", "暗槓", "暗槓", "Closed Kan")


class Meld:
    """Meld."""

    def __init__(
        self, meld_type: MeldType, tiles: List[Tile], called_tile: Optional[Tile] = None
    ):
        """
        Initialize Meld.

        Args:
            meld_type (MeldType): Meld type.
            tiles (List[Tile]): List of tiles in the meld.
            called_tile (Optional[Tile]): The called tile (required for chi/pon).

        Raises:
            ValueError: If tile count is invalid.
        """
        if meld_type == MeldType.CHI_MELD and len(tiles) != 3:
            raise ValueError("吃必須是 3 張牌")
        if meld_type == MeldType.PON_MELD and len(tiles) != 3:
            raise ValueError("碰必須是 3 張牌")
        if meld_type in [MeldType.OPEN_KAN, MeldType.CLOSED_KAN] and len(tiles) != 4:
            raise ValueError("槓必須是 4 張牌")

        self._type = meld_type
        self._tiles = sorted(tiles)
        self._called_tile = called_tile

    @property
    def type(self) -> MeldType:
        return self._type

    @property
    def tiles(self) -> List[Tile]:
        return self._tiles.copy()

    @property
    def called_tile(self) -> Optional[Tile]:
        return self._called_tile

    def is_concealed(self) -> bool:
        return self._type == MeldType.CLOSED_KAN

    def is_open(self) -> bool:
        return not self.is_concealed()

    def __str__(self) -> str:
        tiles_str = "".join(str(t) for t in self._tiles)
        return f"{self._type.value}({tiles_str})"

    def __repr__(self) -> str:
        return f"Meld({self._type.value}, {self._tiles})"


class Hand:
    """hand Manager"""

    def __init__(self, tiles: List[Tile]):
        """
        Initialize hand.

        Args:
            tiles (List[Tile]): Initial hand tiles (13 or 14 tiles).
        """
        self._tiles = tiles.copy()
        self._melds: List[Meld] = []
        self._discards: List[Tile] = []
        self._is_riichi = False
        self._riichi_turn: Optional[int] = None
        self._tile_counts_cache: Optional[dict] = None
        self._tenpai_discards: Optional[List[Tile]] = None
        self._last_drawn_tile: Optional[Tile] = None

    def add_tile(self, tile: Tile) -> None:
        self._tiles.append(tile)
        self._tile_counts_cache = None
        self._tenpai_discards = self.calculate_tenpai_discards()
        self._last_drawn_tile = tile

    def discard(self, tile: Tile) -> bool:
        """
        Discard a tile.

        Args:
            tile (Tile): Tile to discard.

        Returns:
            bool: Whether discard was successful.
        """
        try:
            self._tiles.remove(tile)
            self._discards.append(tile)
            self._tile_counts_cache = None
            self._tenpai_discards = None
            return True
        except ValueError:
            return False

    def remove_last_discard(self, tile: Tile) -> None:
        """
        Remove the last discard (retrieved when calling a tile).

        Args:
            tile (Tile): Expected tile to remove (for validation).

        Raises:
            ValueError: If no discards or last discard does not match.
        """

        if not self._discards:
            raise ValueError("沒有可移除的捨牌")
        last_tile = self._discards[-1]
        if last_tile != tile:
            raise ValueError("最後一張捨牌與指定牌不符")
        self._discards.pop()

    def total_tile_count(self) -> int:
        """
        Get total tile count (including melds).

        Returns:
            int: Total tile count.
        """

        meld_count = sum(len(meld.tiles) for meld in self._melds)
        return len(self._tiles) + meld_count

    def can_chi(self, tile: Tile, from_player: int) -> List[List[Tile]]:
        """
        Check if chi is possible.

        Args:
            tile (Tile): The tile being called.
            from_player (int): Discarding player position (0=kamicha, 1=toimen, 2=shimocha).

        Returns:
            List[List[Tile]]: List of possible sequences (each sequence contains 3 tiles).
        """
        if from_player != 0:  # Can only chi from kamicha (Left player)
            return []

        if tile.is_honor:  # honors cannot form a Sequence
            return []

        results = []
        for i in range(-2, 1):  # Check -2, -1, 0 three cases
            needed_ranks = [tile.rank + i, tile.rank + i + 1, tile.rank + i + 2]
            if all(1 <= r <= 9 for r in needed_ranks):
                sequence = []
                for rank in needed_ranks:
                    if rank == tile.rank:
                        continue
                    needed_tile = Tile(tile.suit, rank)
                    if needed_tile not in self._tiles:
                        continue
                    sequence.append(needed_tile)
                if len(sequence) == 2:
                    results.append(sequence)

        return results

    def chi(self, tile: Tile, sequence: List[Tile]) -> Meld:
        """
        Execute chi.

        Args:
            tile (Tile): The tile being called.
            sequence (List[Tile]): Two tiles from hand (forming a sequence with the called tile).

        Returns:
            Meld: Created Meld object.

        Raises:
            ValueError: If chi is not possible.
        """
        if not self.can_chi(tile, 0):
            raise ValueError("不能吃這張牌")

        for t in sequence:
            self._tiles.remove(t)

        all_tiles = sequence + [tile]
        meld = Meld(MeldType.CHI_MELD, all_tiles, called_tile=tile)
        self._melds.append(meld)
        self._tile_counts_cache = None
        self._tenpai_discards = self.calculate_tenpai_discards()
        self._last_drawn_tile = None
        return meld

    def can_pon(self, tile: Tile) -> bool:
        """
        Check if pon is possible.

        Args:
            tile (Tile): The tile being called.

        Returns:
            bool: Whether pon is possible.
        """

        count = self._tiles.count(tile)
        return count >= 2

    def pon(self, tile: Tile) -> Meld:
        """
        Execute pon.

        Args:
            tile (Tile): The tile being called.

        Returns:
            Meld: Created Meld object.

        Raises:
            ValueError: If pon is not possible.
        """
        if not self.can_pon(tile):
            raise ValueError("不能碰這張牌")

        removed = 0
        tiles_to_remove = []
        for t in self._tiles:
            if t == tile and removed < 2:
                tiles_to_remove.append(t)
                removed += 1

        for t in tiles_to_remove:
            self._tiles.remove(t)

        meld_tiles = tiles_to_remove + [tile]
        meld = Meld(MeldType.PON_MELD, meld_tiles, called_tile=tile)
        self._melds.append(meld)
        self._tile_counts_cache = None
        self._tenpai_discards = self.calculate_tenpai_discards()
        self._last_drawn_tile = None
        return meld

    def can_kan(self, tile: Optional[Tile] = None) -> List[Meld]:
        """
        Check if kan is possible.

        Args:
            tile (Optional[Tile]): The tile being called (required for open_kan, None for closed_kan/open_kan).

        Returns:
            List[Meld]: List of possible kan combinations.
        """
        results = []

        if tile is None:
            tile_counts = self._get_tile_counts(self._tiles)
            for tile, count in tile_counts.items():
                if count == 4:
                    kan_tiles = [t for t in self._tiles if t == tile]
                    results.append(Meld(MeldType.CLOSED_KAN, kan_tiles))
            for meld in self._melds:
                if (
                    meld.type == MeldType.PON_MELD
                    and meld.called_tile is not None
                    and self._tiles.count(meld.called_tile) > 0
                ):
                    kan_tiles = meld.tiles + [meld.called_tile]
                    results.append(
                        Meld(MeldType.OPEN_KAN, kan_tiles, called_tile=meld.called_tile)
                    )
        elif self._tiles.count(tile) == 3:
            kan_tiles = []
            for t in self._tiles:
                if t == tile and len(kan_tiles) < 3:
                    kan_tiles.append(t)
            kan_tiles.append(tile)
            results.append(Meld(MeldType.OPEN_KAN, kan_tiles, called_tile=tile))
        elif self._tiles.count(tile) == 4:
            # closed_kan of specific tile
            kan_tiles = [t for t in self._tiles if t == tile]
            results.append(Meld(MeldType.CLOSED_KAN, kan_tiles))
        elif self._tiles.count(tile) == 1:
            # open_kan of specific tile
            for meld in self._melds:
                if (
                    meld.type == MeldType.PON_MELD
                    and meld.called_tile is not None
                    and meld.called_tile == tile
                ):
                    kan_tiles = meld.tiles + [tile]
                    results.append(Meld(MeldType.OPEN_KAN, kan_tiles, called_tile=tile))

        return results

    def kan(self, tile: Optional[Tile]) -> Meld:
        """
        Execute kan.

        Args:
            tile (Optional[Tile]): The tile being called (required for open_kan, None for closed_kan/open_kan).

        Returns:
            Meld: Created Meld object.

        Raises:
            ValueError: If kan is not possible.
        """
        possible_kan = self.can_kan(tile)
        if not possible_kan:
            raise ValueError("不能槓這張牌")

        # Use the first possible kan combination
        meld = possible_kan[0]

        if meld.type == MeldType.CLOSED_KAN:
            for t in meld.tiles:
                self._tiles.remove(t)
        elif meld.type == MeldType.OPEN_KAN:
            if tile is None:
                called_tile = meld.called_tile
                if called_tile is None or self._tiles.count(called_tile) == 0:
                    raise ValueError("沒有可用的牌升級為加槓")
                for existing_meld in self._melds:
                    if (
                        existing_meld.type == MeldType.PON_MELD
                        and existing_meld.called_tile == called_tile
                    ):
                        self._melds.remove(existing_meld)
                        self._tiles.remove(called_tile)
                        break
            else:
                for t in meld.tiles:
                    if t in self._tiles:
                        self._tiles.remove(t)

        self._melds.append(meld)
        self._tile_counts_cache = None
        self._tenpai_discards = self.calculate_tenpai_discards()
        self._last_drawn_tile = None
        return meld

    @property
    def tiles(self) -> List[Tile]:
        """Get current hand tiles"""
        return self._tiles.copy()

    @property
    def melds(self) -> List[Meld]:
        """Get all melds"""
        return self._melds.copy()

    @property
    def discards(self) -> List[Tile]:
        """Get all discards"""
        return self._discards.copy()

    @property
    def is_concealed(self) -> bool:
        """Is menzen (Concealed, no open melds)"""
        return len(self._melds) == 0

    @property
    def is_riichi(self) -> bool:
        """Is riichi"""
        return self._is_riichi

    @property
    def tenpai_discards(self) -> List[Tile]:
        """Get tiles that can be discarded to reach tenpai"""
        return [] if self._tenpai_discards is None else self._tenpai_discards.copy()

    def set_riichi(self, is_riichi: bool = True, turn: Optional[int] = None) -> None:
        """
        Set riichi state.

        Args:
            is_riichi (bool): Whether riichi.
            turn (Optional[int]): Turn number of riichi.
        """
        self._is_riichi = is_riichi
        self._riichi_turn = turn

    @property
    def last_drawn_tile(self) -> Optional[Tile]:
        """Get the last drawn tile"""
        return self._last_drawn_tile

    def reset_last_drawn_tile(self) -> None:
        """Reset the last drawn tile"""
        self._last_drawn_tile = None

    def _get_tile_counts(self, tiles: Optional[List[Tile]] = None) -> dict[Tile, int]:
        """
        Get tile count dictionary.

        Args:
            tiles (Optional[List[Tile]]): List of tiles (if None, use current hand and cache).

        Returns:
            Dict[Tile, int]: Tile count dictionary {Tile: count}.
        """
        # If using current hand and cache exists, return cache
        if tiles is None:
            if self._tile_counts_cache is not None:
                return self._tile_counts_cache
            tiles = self._tiles

        counts = {}
        for tile in tiles:
            counts[tile] = counts.get(tile, 0) + 1

        # If using current hand, update cache
        if tiles is self._tiles:
            self._tile_counts_cache = counts

        return counts

    def _remove_triplet(self, counts: dict[Tile, int], tile: Tile, count: int) -> bool:
        """
        Remove a triplet (three identical tiles) from counts.

        Args:
            counts (Dict[Tile, int]): Tile count dictionary.
            tile (Tile): Tile.
            count (int): Tile count.

        Returns:
            bool: Whether removal was successful.
        """
        if counts.get(tile, 0) >= count:
            counts[tile] -= count
            return True
        return False

    def _remove_sequence(self, counts: dict[Tile, int], suit: Suit, rank: int) -> bool:
        """
        Remove a sequence (three consecutive tiles) from counts.

        Args:
            counts (Dict[Tile, int]): Tile count dictionary.
            suit (Suit): Suit.
            rank (int): Start rank of the sequence.

        Returns:
            bool: Whether removal was successful.
        """
        if suit == Suit.HONORS:  # honors cannot form a Sequence
            return False

        for i in range(3):
            r = rank + i
            tile = Tile(suit, r)
            if counts.get(tile, 0) == 0:
                return False

        for i in range(3):
            r = rank + i
            tile = Tile(suit, r)
            counts[tile] -= 1
        return True

    def _remove_pair(self, counts: dict[Tile, int], tile: Tile) -> bool:
        """
        Remove a pair (two identical tiles) from counts.

        Args:
            counts (Dict[Tile, int]): Tile count dictionary.
            tile (Tile): Tile.

        Returns:
            bool: Whether removal was successful.
        """
        if counts.get(tile, 0) >= 2:
            counts[tile] -= 2
            return True
        return False

    def _is_standard_winning(
        self, tiles: List[Tile], existing_melds: Optional[List[Combination]] = None
    ) -> Tuple[bool, List[List[Combination]]]:
        """
        Check standard winning hand (4 Melds + 1 Pair).

        Args:
            tiles (List[Tile]): List of tiles (Concealed part).
            existing_melds (Optional[List[Combination]]): List of existing melds (Open melds).

        Returns:
            Tuple[bool, List[List[Combination]]]: (Is winning, List of all possible winning combinations).
        """
        melds = existing_melds or []
        total_tiles_count = len(tiles) + sum(len(m.tiles) for m in melds)
        if total_tiles_count < 14:
            return False, []

        counts = self._get_tile_counts(tiles)
        combinations = []

        for _, count in counts.items():
            if count > 4:
                return False, []

        # Try all possible pairs
        pair_candidates = [tile for tile, count in counts.items() if count >= 2]

        for pair_tile in pair_candidates:
            test_counts = counts.copy()

            if not self._remove_pair(test_counts, pair_tile):
                continue

            # Recursively find remaining melds
            # Note: existing_melds already occupy some meld slots
            if results := self._find_melds(
                test_counts,
                melds,
                Combination(CombinationType.PAIR, [pair_tile, pair_tile]),
            ):
                combinations.extend(results)

        return len(combinations) > 0, combinations

    def _find_melds(
        self,
        counts: dict[Tile, int],
        current_combinations: List[Combination],
        pair_combination: Combination,
    ) -> List[List[Combination]]:
        """
        Recursively find all possible meld combinations.

        Args:
            counts (Dict[Tile, int]): Dictionary of remaining tile counts.
            current_combinations (List[Combination]): List of found melds.
            pair_combination (Combination): Pair combination.

        Returns:
            List[List[Combination]]: List of all possible meld combinations.
        """

        remaining_count = sum(counts.values())
        if remaining_count == 0:
            return (
                [current_combinations + [pair_combination]]
                if len(current_combinations) == 4
                else []
            )

        # If 4 melds found but tiles remain, it's a mismatch
        if len(current_combinations) == 4:
            return []

        # If remaining tiles are not enough to form more melds, return
        if remaining_count < 3:
            return []

        results = []
        results.extend(
            self._search_triplet_melds(counts, current_combinations, pair_combination)
        )
        results.extend(
            self._search_sequence_melds(counts, current_combinations, pair_combination)
        )
        return results

    def _search_triplet_melds(
        self,
        counts: dict[Tile, int],
        current_combinations: List[Combination],
        pair_combination: Combination,
    ) -> List[List[Combination]]:
        results = []
        for tile, count in counts.items():
            if count < 3 or not self._remove_triplet(counts, tile, count):
                continue
            if count == 3:
                combination = Combination(CombinationType.TRIPLET, [tile, tile, tile])
            elif count == 4:
                combination = Combination(CombinationType.KAN, [tile, tile, tile, tile])
            else:
                raise ValueError(f"Invalid count: {count} for tile: {tile}")
            new_combinations = current_combinations + [combination]
            if result := self._find_melds(counts, new_combinations, pair_combination):
                results.extend(result)
            counts[tile] += count
        return results

    def _search_sequence_melds(
        self,
        counts: dict[Tile, int],
        current_combinations: List[Combination],
        pair_combination: Combination,
    ) -> List[List[Combination]]:
        results = []
        for suit in [Suit.MANZU, Suit.PINZU, Suit.SOUZU]:
            for rank in range(1, 8):
                if any(counts.get(Tile(suit, rank + i), 0) <= 0 for i in range(3)):
                    continue
                original_values = {
                    Tile(suit, rank + i): counts.get(Tile(suit, rank + i), 0)
                    for i in range(3)
                }
                if not self._remove_sequence(counts, suit, rank):
                    continue
                new_combinations = current_combinations + [
                    Combination(
                        CombinationType.SEQUENCE,
                        [Tile(suit, rank), Tile(suit, rank + 1), Tile(suit, rank + 2)],
                    )
                ]
                if result := self._find_melds(
                    counts, new_combinations, pair_combination
                ):
                    results.extend(result)
                for i in range(3):
                    counts[Tile(suit, rank + i)] = original_values[Tile(suit, rank + i)]
        return results

    def _is_seven_pairs(self, tiles: List[Tile]) -> bool:
        """
        Check if chiitoitsu.

        Args:
            tiles (List[Tile]): List of tiles (14 tiles).

        Returns:
            bool: Whether it is Seven Pairs.
        """
        if len(tiles) != 14:
            return False

        counts = self._get_tile_counts(tiles)
        pairs = 0

        for count in counts.values():
            if count == 2:
                pairs += 1
            elif count != 0:
                return False  # Count is not 2

        return pairs == 7

    def _is_kokushi_musou(self, tiles: List[Tile]) -> bool:
        """
        Check if kokushi_musou.

        Args:
            tiles (List[Tile]): List of tiles (14 tiles).

        Returns:
            bool: Whether it is kokushi_musou.
        """
        if len(tiles) != 14:
            return False

        # 13 terminals and honors required for kokushi_musou
        required_tiles = [
            (Suit.MANZU, 1),
            (Suit.MANZU, 9),
            (Suit.PINZU, 1),
            (Suit.PINZU, 9),
            (Suit.SOUZU, 1),
            (Suit.SOUZU, 9),
            (Suit.HONORS, 1),
            (Suit.HONORS, 2),
            (Suit.HONORS, 3),
            (Suit.HONORS, 4),
            (Suit.HONORS, 5),
            (Suit.HONORS, 6),
            (Suit.HONORS, 7),
        ]

        found_tiles = set()
        duplicate = None

        for tile in tiles:
            key = (tile.suit, tile.rank)
            if key in required_tiles and key in found_tiles and duplicate is None:
                duplicate = key
            elif (
                key in required_tiles
                and key in found_tiles
                and duplicate != key
                or key not in required_tiles
            ):
                return False  # Multiple duplicates
            elif key not in found_tiles:
                found_tiles.add(key)
        # Must have one of each of the 13 types, plus one duplicate
        return len(found_tiles) == 13 and duplicate is not None

    def is_tenpai(self) -> bool:
        """
        Check if tenpai (Optimized: only check potentially relevant tiles).

        Returns:
            bool: Whether tenpai.
        """
        return len(self.get_waiting_tiles()) > 0

    def calculate_tenpai_discards(self) -> List[Tile]:
        """
        Get list of tiles that can be discarded to reach tenpai.

        Returns:
            List[Tile]: List of tiles that can be discarded to reach tenpai.
        """

        valid_discards = []
        original_tiles = list(self._tiles)
        unique_tiles = set(original_tiles)

        for tile_to_discard in unique_tiles:
            # Temporarily remove a tile
            try:
                self._tiles.remove(tile_to_discard)
                self._tile_counts_cache = None

                if self.is_tenpai():
                    valid_discards.append(tile_to_discard)

                # Restore hand
                self._tiles.append(tile_to_discard)
                self._tile_counts_cache = None
            except ValueError:
                continue

        return valid_discards

    def get_waiting_tiles(self) -> List[Tile]:
        """
        Get waiting tiles (Optimized: only check potentially relevant tiles).

        Returns:
            List[Tile]: List of all winning tiles.
        """
        # Collect all possible waiting candidates (tiles related to hand)
        candidates = set[Tile]()

        for tile in self._tiles:
            suit, rank = tile.suit, tile.rank
            # Add same tile
            candidates.add(tile)
            # If number tile, add adjacent tiles
            if suit != Suit.HONORS:
                if rank > 1:
                    candidates.add(Tile(suit, rank - 1))
                if rank < 9:
                    candidates.add(Tile(suit, rank + 1))
                # For sequence, also check tiles further away
                if rank > 2:
                    candidates.add(Tile(suit, rank - 2))
                if rank < 8:
                    candidates.add(Tile(suit, rank + 2))

        # If too few candidates, fallback to checking all tiles (ensure no misses)
        if len(candidates) < 10:
            for suit in Suit:
                max_rank = 7 if suit == Suit.HONORS else 9
                for rank in range(1, max_rank + 1):
                    candidates.add(Tile(suit, rank))

        for suit in [Suit.MANZU, Suit.PINZU, Suit.SOUZU]:
            for rank in [1, 9]:
                candidates.add(Tile(suit, rank))
        for rank in range(1, 8):
            candidates.add(Tile(Suit.HONORS, rank))

        return [
            test_tile for test_tile in candidates if self.is_winning_hand(test_tile)
        ]

    def is_winning_hand(self, winning_tile: Tile, is_tsumo: bool = False) -> bool:
        """
        Check if it is a winning hand.

        Args:
            winning_tile (Tile): Winning tile.
            is_tsumo (bool): Is tsumo (default False).

        Returns:
            bool: Whether it is a winning hand.
        """

        concealed_tiles = self._tiles.copy()

        if not is_tsumo:
            concealed_tiles.append(winning_tile)

        existing_melds = []
        for meld in self._melds:
            combo_type = CombinationType.SEQUENCE
            if meld.type == MeldType.PON_MELD:
                combo_type = CombinationType.TRIPLET
            elif meld.type in [MeldType.OPEN_KAN, MeldType.CLOSED_KAN]:
                combo_type = CombinationType.KAN

            combo = Combination(combo_type, meld.tiles)
            combo.set_open(meld.is_open())
            existing_melds.append(combo)

        # Check standard winning hand
        is_winning, _ = self._is_standard_winning(concealed_tiles, existing_melds)
        if is_winning:
            return True

        # Check Seven Pairs (Must be menzen)
        # chiitoitsu does not allow any melds (including closed_kan)
        if self.is_concealed:
            if self._is_seven_pairs(concealed_tiles):
                return True
            if self._is_kokushi_musou(concealed_tiles):
                return True

        return False

    def get_winning_combinations(
        self, winning_tile: Tile, is_tsumo: bool = False
    ) -> List[List[Combination]]:
        """
        Get winning combinations (for yaku determination).

        Args:
            winning_tile (Tile): Winning tile.
            is_tsumo (bool): Is tsumo (default False).

        Returns:
            List[List[Combination]]: All possible winning combinations (each combination contains 4 Melds and 1 Pair).
        """
        # Add winning tile (Concealed part)
        concealed_tiles = self._tiles.copy()

        if not is_tsumo:
            concealed_tiles.append(winning_tile)

        # Convert melds to Combination
        existing_melds = []
        for meld in self._melds:
            combo_type = CombinationType.SEQUENCE
            if meld.type == MeldType.PON_MELD:
                combo_type = CombinationType.TRIPLET
            elif meld.type in [MeldType.OPEN_KAN, MeldType.CLOSED_KAN]:
                combo_type = CombinationType.KAN

            combo = Combination(combo_type, meld.tiles)
            combo.set_open(meld.is_open())
            existing_melds.append(combo)

        # Check standard winning hand
        is_winning, combinations = self._is_standard_winning(
            concealed_tiles, existing_melds
        )

        return combinations if is_winning else []
