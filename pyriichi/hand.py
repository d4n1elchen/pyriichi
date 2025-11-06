"""
手牌管理系統 - Hand and Meld implementation

提供手牌操作、副露管理和和牌判定功能。
"""

from enum import Enum
from typing import List, Optional, Tuple
from pyriichi.tiles import Tile, Suit


class MeldType(Enum):
    """副露類型"""

    CHI = "chi"  # 吃
    PON = "pon"  # 碰
    KAN = "kan"  # 明槓
    ANKAN = "ankan"  # 暗槓


class Meld:
    """副露（明刻、明順、明槓、暗槓）"""

    def __init__(self, meld_type: MeldType, tiles: List[Tile], called_tile: Optional[Tile] = None):
        """
        初始化副露

        Args:
            meld_type: 副露類型
            tiles: 副露的牌列表
            called_tile: 被鳴的牌（吃/碰時需要）

        Raises:
            ValueError: 如果牌數不符合要求
        """
        if meld_type == MeldType.CHI and len(tiles) != 3:
            raise ValueError("吃必須是 3 張牌")
        if meld_type == MeldType.PON and len(tiles) != 3:
            raise ValueError("碰必須是 3 張牌")
        if meld_type in [MeldType.KAN, MeldType.ANKAN] and len(tiles) != 4:
            raise ValueError("槓必須是 4 張牌")

        self._meld_type = meld_type
        self._tiles = sorted(tiles)
        self._called_tile = called_tile

    @property
    def meld_type(self) -> MeldType:
        """獲取副露類型"""
        return self._meld_type

    @property
    def tiles(self) -> List[Tile]:
        """獲取副露的牌列表"""
        return self._tiles.copy()

    @property
    def called_tile(self) -> Optional[Tile]:
        """獲取被鳴的牌"""
        return self._called_tile

    def is_concealed(self) -> bool:
        """是否為暗槓"""
        return self._meld_type == MeldType.ANKAN

    def is_open(self) -> bool:
        """是否為明副露"""
        return not self.is_concealed()

    def __str__(self) -> str:
        """字符串表示"""
        tiles_str = "".join(str(t) for t in self._tiles)
        return f"{self._meld_type.value}({tiles_str})"

    def __repr__(self) -> str:
        """對象表示"""
        return f"Meld({self._meld_type.value}, {self._tiles})"


class Hand:
    """手牌管理器"""

    def __init__(self, tiles: List[Tile]):
        """
        初始化手牌

        Args:
            tiles: 初始手牌列表（13 或 14 張）
        """
        self._tiles = sorted(tiles.copy())
        self._melds: List[Meld] = []
        self._discards: List[Tile] = []
        self._is_riichi = False
        self._riichi_turn: Optional[int] = None
        self._tile_counts_cache: Optional[dict] = None  # 緩存牌計數結果

    def add_tile(self, tile: Tile) -> None:
        """添加一張牌（摸牌）"""
        self._tiles.append(tile)
        self._tiles.sort()
        self._tile_counts_cache = None  # 清除緩存

    def discard(self, tile: Tile) -> bool:
        """
        打出一張牌

        Args:
            tile: 要打出的牌

        Returns:
            是否成功打出
        """
        try:
            self._tiles.remove(tile)
            self._discards.append(tile)
            self._tile_counts_cache = None  # 清除緩存
            return True
        except ValueError:
            return False

    def can_chi(self, tile: Tile, from_player: int) -> List[List[Tile]]:
        """
        檢查是否可以吃

        Args:
            tile: 被吃的牌
            from_player: 出牌玩家位置（0=上家，1=對家，2=下家）

        Returns:
            可以組成的順子列表（每個順子包含 3 張牌）
        """
        if from_player != 0:  # 只能吃上家的牌
            return []

        if tile.is_honor:  # 字牌不能組成順子
            return []

        results = []
        # 檢查是否可以組成順子
        for i in range(-2, 1):  # 檢查 -2, -1, 0 三種情況
            needed_ranks = [tile.rank + i, tile.rank + i + 1, tile.rank + i + 2]
            if all(1 <= r <= 9 for r in needed_ranks):
                # 檢查手牌中是否有對應的牌
                sequence = []
                for rank in needed_ranks:
                    if rank == tile.rank:
                        continue
                    needed_tile = Tile(tile.suit, rank)
                    if needed_tile in self._tiles:
                        # 檢查是否有重複（需要移除）
                        if needed_tile in sequence:
                            break
                        sequence.append(needed_tile)
                    else:
                        break
                else:
                    if len(sequence) == 2:
                        results.append(sequence)

        return results

    def chi(self, tile: Tile, sequence: List[Tile]) -> Meld:
        """
        執行吃操作

        Args:
            tile: 被吃的牌
            sequence: 手牌中的兩張牌（與被吃的牌組成順子）

        Returns:
            創建的 Meld 對象

        Raises:
            ValueError: 如果不能吃
        """
        if not self.can_chi(tile, 0):
            raise ValueError("不能吃這張牌")

        # 從手牌中移除用於組順子的牌
        for t in sequence:
            self._tiles.remove(t)

        all_tiles = sequence + [tile]
        meld = Meld(MeldType.CHI, all_tiles, called_tile=tile)
        self._melds.append(meld)
        self._tile_counts_cache = None  # 清除緩存
        return meld

    def can_pon(self, tile: Tile) -> bool:
        """
        檢查是否可以碰

        Args:
            tile: 被碰的牌

        Returns:
            是否可以碰
        """
        # 檢查手牌中是否有兩張相同的牌
        count = self._tiles.count(tile)
        return count >= 2

    def pon(self, tile: Tile) -> Meld:
        """
        執行碰操作

        Args:
            tile: 被碰的牌

        Returns:
            創建的 Meld 對象

        Raises:
            ValueError: 如果不能碰
        """
        if not self.can_pon(tile):
            raise ValueError("不能碰這張牌")

        # 從手牌中移除兩張相同的牌
        removed = 0
        tiles_to_remove = []
        for t in self._tiles:
            if t == tile and removed < 2:
                tiles_to_remove.append(t)
                removed += 1

        for t in tiles_to_remove:
            self._tiles.remove(t)

        meld_tiles = tiles_to_remove + [tile]
        meld = Meld(MeldType.PON, meld_tiles, called_tile=tile)
        self._melds.append(meld)
        self._tile_counts_cache = None  # 清除緩存
        return meld

    def can_kan(self, tile: Optional[Tile] = None) -> List[Meld]:
        """
        檢查是否可以槓

        Args:
            tile: 被槓的牌（明槓時需要，暗槓時為 None）

        Returns:
            可以槓的組合列表
        """
        results = []

        if tile is None:
            # 暗槓：檢查手牌中是否有四張相同的牌
            tile_counts = self._get_tile_counts(self._tiles)
            for (suit, rank), count in tile_counts.items():
                if count == 4:
                    # 找到四張相同的牌
                    kan_tiles = [t for t in self._tiles if t.suit == suit and t.rank == rank]
                    results.append(Meld(MeldType.ANKAN, kan_tiles))
        else:
            # 明槓：檢查是否可以加槓（之前碰過，現在摸到第四張）
            # 檢查是否有碰過這張牌
            for meld in self._melds:
                if meld.meld_type == MeldType.PON and meld.called_tile == tile:
                    # 可以加槓
                    kan_tiles = meld.tiles + [tile]
                    results.append(Meld(MeldType.KAN, kan_tiles, called_tile=tile))
                    break

            # 明槓：手牌中有三張相同牌，碰別人打出的第四張
            count = self._tiles.count(tile)
            if count >= 3:
                # 找到三張相同的牌
                kan_tiles = []
                for t in self._tiles:
                    if t == tile and len(kan_tiles) < 3:
                        kan_tiles.append(t)
                kan_tiles.append(tile)  # 加上被槓的牌
                results.append(Meld(MeldType.KAN, kan_tiles, called_tile=tile))

        return results

    def kan(self, tile: Optional[Tile], kan_tiles: Optional[List[Tile]] = None) -> Meld:
        """
        執行槓操作

        Args:
            tile: 被槓的牌（明槓時需要，暗槓時為 None）
            kan_tiles: 手牌中的牌（可選，如果不提供則自動查找）

        Returns:
            創建的 Meld 對象

        Raises:
            ValueError: 如果不能槓
        """
        possible_kan = self.can_kan(tile)
        if not possible_kan:
            raise ValueError("不能槓這張牌")

        # 使用第一個可能的槓組合
        meld = possible_kan[0]

        if meld.meld_type == MeldType.ANKAN:
            # 暗槓：從手牌中移除四張牌
            for t in meld.tiles:
                self._tiles.remove(t)
        elif meld.meld_type == MeldType.KAN:
            # 明槓：檢查是否為加槓（升級已有的碰為槓）
            if tile is not None:
                for existing_meld in self._melds:
                    if existing_meld.meld_type == MeldType.PON and existing_meld.called_tile == tile:
                        # 加槓：移除舊的碰，添加新的槓
                        self._melds.remove(existing_meld)
                        # 從手牌中移除新摸到的牌
                        if tile in self._tiles:
                            self._tiles.remove(tile)
                        break
                else:
                    # 普通明槓：從手牌中移除三張牌
                    for t in meld.tiles:
                        if t != tile and t in self._tiles:
                            self._tiles.remove(t)

        self._melds.append(meld)
        self._tile_counts_cache = None  # 清除緩存
        return meld

    @property
    def tiles(self) -> List[Tile]:
        """獲取當前手牌"""
        return self._tiles.copy()

    @property
    def melds(self) -> List[Meld]:
        """獲取所有副露"""
        return self._melds.copy()

    @property
    def discards(self) -> List[Tile]:
        """獲取所有舍牌"""
        return self._discards.copy()

    @property
    def is_concealed(self) -> bool:
        """是否門清（無副露）"""
        return len(self._melds) == 0

    @property
    def is_riichi(self) -> bool:
        """是否立直"""
        return self._is_riichi

    def set_riichi(self, is_riichi: bool = True, turn: Optional[int] = None) -> None:
        """
        設置立直狀態

        Args:
            is_riichi: 是否立直
            turn: 立直的回合數
        """
        self._is_riichi = is_riichi
        self._riichi_turn = turn

    def _get_tile_counts(self, tiles: Optional[List[Tile]] = None) -> dict:
        """
        獲取牌的計數字典

        Args:
            tiles: 牌列表（如果為 None，則使用當前手牌並使用緩存）

        Returns:
            牌計數字典 {(suit, rank): count}
        """
        # 如果使用當前手牌且緩存存在，直接返回緩存
        if tiles is None:
            if self._tile_counts_cache is not None:
                return self._tile_counts_cache
            tiles = self._tiles

        counts = {}
        for tile in tiles:
            key = (tile.suit, tile.rank)
            counts[key] = counts.get(key, 0) + 1

        # 如果使用當前手牌，更新緩存
        if tiles is self._tiles:
            self._tile_counts_cache = counts

        return counts

    def _remove_triplet(self, counts: dict, suit, rank: int) -> bool:
        """
        從計數中移除一個刻子（三張相同）

        Args:
            counts: 牌計數字典
            suit: 花色
            rank: 數字

        Returns:
            是否成功移除
        """
        key = (suit, rank)
        if counts.get(key, 0) >= 3:
            counts[key] -= 3
            return True
        return False

    def _remove_sequence(self, counts: dict, suit, rank: int) -> bool:
        """
        從計數中移除一個順子（三張連續）

        Args:
            counts: 牌計數字典
            suit: 花色
            rank: 順子的起始數字

        Returns:
            是否成功移除
        """
        if suit == Suit.JIHAI:  # 字牌不能組成順子
            return False

        for i in range(3):
            r = rank + i
            key = (suit, r)
            if counts.get(key, 0) == 0:
                return False

        # 移除順子
        for i in range(3):
            r = rank + i
            key = (suit, r)
            counts[key] -= 1
        return True

    def _remove_pair(self, counts: dict, suit, rank: int) -> bool:
        """
        從計數中移除一個對子（兩張相同）

        Args:
            counts: 牌計數字典
            suit: 花色
            rank: 數字

        Returns:
            是否成功移除
        """
        key = (suit, rank)
        if counts.get(key, 0) >= 2:
            counts[key] -= 2
            return True
        return False

    def _is_standard_winning(self, tiles: List[Tile]) -> Tuple[bool, List[Tuple]]:
        """
        檢查標準和牌型（4組面子 + 1對子）

        Args:
            tiles: 牌列表（14張）

        Returns:
            (是否和牌, 所有可能的和牌組合列表)
        """
        if len(tiles) != 14:
            return False, []

        counts = self._get_tile_counts(tiles)
        combinations = []

        # 嘗試所有可能的對子
        pair_candidates = [key for key, count in counts.items() if count >= 2]

        for pair_key in pair_candidates:
            # 複製計數
            test_counts = counts.copy()

            # 移除對子
            if not self._remove_pair(test_counts, pair_key[0], pair_key[1]):
                continue

            # 遞迴尋找4組面子
            result = self._find_melds(test_counts, [], pair_key)
            if result:
                combinations.extend(result)

        return len(combinations) > 0, combinations

    def _find_melds(self, counts: dict, current_melds: List[Tuple], pair: Tuple) -> List[List[Tuple]]:
        """
        遞迴尋找所有可能的面子組合（優化版本：使用回溯減少字典複製）

        Args:
            counts: 剩餘牌的計數字典
            current_melds: 已找到的面子列表
            pair: 對子

        Returns:
            所有可能的面子組合列表
        """
        # 檢查是否所有牌都已用完
        remaining_count = sum(counts.values())
        if remaining_count == 0:
            if len(current_melds) == 4:
                return [current_melds + [("pair", pair)]]
            return []

        # 如果已經找到4個面子但還有剩餘牌，說明不匹配
        if len(current_melds) == 4:
            return []

        # 如果剩餘牌數不足以組成更多面子，返回
        if remaining_count < 3:
            return []

        results = []

        # 嘗試所有可能的刻子（使用回溯，減少字典複製）
        for (suit, rank), count in list(counts.items()):
            if count >= 3:
                # 原地修改並回溯
                if self._remove_triplet(counts, suit, rank):
                    new_melds = current_melds + [("triplet", (suit, rank))]
                    result = self._find_melds(counts, new_melds, pair)
                    if result:
                        results.extend(result)
                    # 回溯：恢復計數
                    counts[(suit, rank)] += 3

        # 嘗試所有可能的順子（僅對數牌，使用回溯）
        for suit in [Suit.MANZU, Suit.PINZU, Suit.SOZU]:
            for rank in range(1, 8):  # 順子最多到 7（7-8-9）
                # 檢查是否可以組成順子（快速檢查）
                can_form_sequence = all(counts.get((suit, rank + i), 0) > 0 for i in range(3))
                if can_form_sequence:
                    # 記錄原始值以便回溯
                    original_values = {(suit, rank + i): counts.get((suit, rank + i), 0) for i in range(3)}
                    # 原地修改並回溯
                    if self._remove_sequence(counts, suit, rank):
                        new_melds = current_melds + [("sequence", (suit, rank))]
                        result = self._find_melds(counts, new_melds, pair)
                        if result:
                            results.extend(result)
                        # 回溯：恢復計數
                        for i in range(3):
                            counts[(suit, rank + i)] = original_values[(suit, rank + i)]

        return results

    def _is_seven_pairs(self, tiles: List[Tile]) -> bool:
        """
        檢查是否為七對子

        Args:
            tiles: 牌列表（14張）

        Returns:
            是否為七對子
        """
        if len(tiles) != 14:
            return False

        counts = self._get_tile_counts(tiles)
        pairs = 0

        for count in counts.values():
            if count == 2:
                pairs += 1
            elif count != 0:
                return False  # 有不是2的數量

        return pairs == 7

    def _is_kokushi_musou(self, tiles: List[Tile]) -> bool:
        """
        檢查是否為國士無雙

        Args:
            tiles: 牌列表（14張）

        Returns:
            是否為國士無雙
        """
        if len(tiles) != 14:
            return False

        # 國士無雙需要的13種幺九牌
        required_tiles = [
            (Suit.MANZU, 1),
            (Suit.MANZU, 9),
            (Suit.PINZU, 1),
            (Suit.PINZU, 9),
            (Suit.SOZU, 1),
            (Suit.SOZU, 9),
            (Suit.JIHAI, 1),
            (Suit.JIHAI, 2),
            (Suit.JIHAI, 3),
            (Suit.JIHAI, 4),
            (Suit.JIHAI, 5),
            (Suit.JIHAI, 6),
            (Suit.JIHAI, 7),
        ]

        counts = self._get_tile_counts(tiles)
        found_tiles = set()
        duplicate = None

        for tile in tiles:
            key = (tile.suit, tile.rank)
            if key in required_tiles:
                if key in found_tiles:
                    # 找到重複的牌
                    if duplicate is None:
                        duplicate = key
                    elif duplicate != key:
                        return False  # 有多個重複
                else:
                    found_tiles.add(key)
            else:
                return False  # 有非幺九牌

        # 必須有13種各1張，加上1張重複
        return len(found_tiles) == 13 and duplicate is not None

    def is_tenpai(self) -> bool:
        """
        是否聽牌（優化版本：只檢查可能相關的牌）

        Returns:
            是否聽牌
        """
        if len(self._tiles) != 13:
            return False

        # 獲取當前手牌的計數，只檢查可能相關的牌
        counts = self._get_tile_counts()

        # 優化：只檢查與手牌相關的牌（相鄰或相同）
        from pyriichi.tiles import Suit

        # 收集所有可能的聽牌候選（與手牌相關的牌）
        candidates = set()

        for tile in self._tiles:
            suit, rank = tile.suit, tile.rank
            # 添加相同牌
            candidates.add((suit, rank))
            # 如果是數牌，添加相鄰牌
            if suit != Suit.JIHAI:
                if rank > 1:
                    candidates.add((suit, rank - 1))
                if rank < 9:
                    candidates.add((suit, rank + 1))
                # 對於順子，還需要檢查更遠的牌
                if rank > 2:
                    candidates.add((suit, rank - 2))
                if rank < 8:
                    candidates.add((suit, rank + 2))

        # 如果候選太少，回退到檢查所有牌
        if len(candidates) < 10:
            for suit in Suit:
                if suit == Suit.JIHAI:
                    max_rank = 7
                else:
                    max_rank = 9
                for rank in range(1, max_rank + 1):
                    candidates.add((suit, rank))

        # 只檢查候選牌
        for suit, rank in candidates:
            test_tile = Tile(suit, rank)
            if self.is_winning_hand(test_tile):
                return True

        return False

    def get_waiting_tiles(self) -> List[Tile]:
        """
        獲取聽牌列表（優化版本：只檢查可能相關的牌）

        Returns:
            所有可以和的牌列表
        """
        if len(self._tiles) != 13:
            return []

        # 獲取當前手牌的計數，只檢查可能相關的牌
        counts = self._get_tile_counts()

        # 優化：只檢查與手牌相關的牌（相鄰或相同）
        from pyriichi.tiles import Suit

        # 收集所有可能的聽牌候選（與手牌相關的牌）
        candidates = set()

        for tile in self._tiles:
            suit, rank = tile.suit, tile.rank
            # 添加相同牌
            candidates.add((suit, rank))
            # 如果是數牌，添加相鄰牌
            if suit != Suit.JIHAI:
                if rank > 1:
                    candidates.add((suit, rank - 1))
                if rank < 9:
                    candidates.add((suit, rank + 1))
                # 對於順子，還需要檢查更遠的牌
                if rank > 2:
                    candidates.add((suit, rank - 2))
                if rank < 8:
                    candidates.add((suit, rank + 2))

        # 如果候選太少，回退到檢查所有牌（確保不遺漏）
        if len(candidates) < 10:
            for suit in Suit:
                if suit == Suit.JIHAI:
                    max_rank = 7
                else:
                    max_rank = 9
                for rank in range(1, max_rank + 1):
                    candidates.add((suit, rank))

        waiting_tiles = []
        # 只檢查候選牌
        for suit, rank in candidates:
            test_tile = Tile(suit, rank)
            if self.is_winning_hand(test_tile):
                waiting_tiles.append(test_tile)

        return waiting_tiles

    def is_winning_hand(self, winning_tile: Tile) -> bool:
        """
        檢查是否可以和牌

        Args:
            winning_tile: 和牌牌

        Returns:
            是否可以和牌
        """
        # 手牌應該有13張，加上和牌牌共14張
        if len(self._tiles) != 13:
            return False

        # 加上和牌牌
        all_tiles = self._tiles + [winning_tile]

        # 檢查特殊和牌型
        if self._is_seven_pairs(all_tiles):
            return True

        if self._is_kokushi_musou(all_tiles):
            return True

        # 檢查標準和牌型
        is_winning, _ = self._is_standard_winning(all_tiles)
        return is_winning

    def get_winning_combinations(self, winning_tile: Tile) -> List[Tuple]:
        """
        獲取和牌組合（用於役種判定）

        Args:
            winning_tile: 和牌牌

        Returns:
            所有可能的和牌組合（每種組合包含 4 組面子和 1 對子）
        """
        if len(self._tiles) != 13:
            return []

        # 加上和牌牌
        all_tiles = self._tiles + [winning_tile]

        # 檢查標準和牌型
        is_winning, combinations = self._is_standard_winning(all_tiles)

        if is_winning:
            return combinations

        # 特殊和牌型不返回組合（因為不需要用於役種判定）
        return []
