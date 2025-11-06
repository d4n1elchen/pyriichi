"""
役種判定系統 - YakuChecker implementation

提供所有役種的判定功能。
"""

from typing import List, Optional
from dataclasses import dataclass
from pyriichi.hand import Hand
from pyriichi.tiles import Tile, Suit
from pyriichi.game_state import GameState


@dataclass
class YakuResult:
    """役種判定結果"""

    name: str  # 役種名稱（日文）
    name_en: str  # 役種名稱（英文）
    name_cn: str  # 役種名稱（中文）
    han: int  # 翻數
    is_yakuman: bool  # 是否為役滿

    def __eq__(self, other):
        if not isinstance(other, YakuResult):
            return False
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)


class YakuChecker:
    """役種判定器"""

    def check_all(
        self, hand: Hand, winning_tile: Tile, winning_combination: List, game_state: GameState
    ) -> List[YakuResult]:
        """
        檢查所有符合的役種

        Args:
            hand: 手牌
            winning_tile: 和牌牌
            winning_combination: 和牌組合（標準型）或 None（特殊型如七對子）
            game_state: 遊戲狀態

        Returns:
            所有符合的役種列表
        """
        # 檢查特殊和牌型（七對子、國士無雙）
        all_tiles = hand.tiles + [winning_tile] if len(hand.tiles) == 13 else hand.tiles

        # 國士無雙判定（優先檢查，因為是役滿）
        if result := self.check_kokushi_musou(hand, all_tiles):
            results = [result]
            # 國士無雙可以與立直複合
            if hand.is_riichi:
                results.insert(0, YakuResult("立直", "Riichi", "立直", 1, False))
            return results

        # 七對子判定
        if hand.is_concealed and len(all_tiles) == 14:
            counts = {}
            for tile in all_tiles:
                key = (tile.suit, tile.rank)
                counts[key] = counts.get(key, 0) + 1

            # 檢查是否全部是對子
            pairs = sum(1 for count in counts.values() if count == 2)
            if pairs == 7:
                results = [YakuResult("七対子", "Chiitoitsu", "七對子", 2, False)]
                # 七對子不能和其他役種複合（除了立直），所以直接返回
                if hand.is_riichi:
                    results.insert(0, YakuResult("立直", "Riichi", "立直", 1, False))
                return results
        results = []

        # 基本役
        if result := self.check_riichi(hand, game_state):
            results.append(result)
        if result := self.check_ippatsu(hand, game_state):
            results.append(result)
        if result := self.check_menzen_tsumo(hand, game_state):
            results.append(result)
        if result := self.check_tanyao(hand, winning_combination):
            results.append(result)
        if result := self.check_pinfu(hand, winning_combination):
            results.append(result)
        if result := self.check_iipeikou(hand, winning_combination):
            results.append(result)
        if result := self.check_toitoi(hand, winning_combination):
            results.append(result)

        # 役牌（可能有多個）
        yakuhai_results = self.check_yakuhai(hand, winning_combination, game_state)
        results.extend(yakuhai_results)

        # 特殊役（2-3翻）
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
        # 七對子需要特殊處理（因為 winning_combination 為空）
        # 如果 winning_combination 為空且手牌是門清，檢查是否為七對子
        if not winning_combination and hand.is_concealed:
            # 檢查手牌是否為七對子型（需要和牌牌）
            # 這個檢查需要在調用時傳入完整的14張牌
            pass

        # 高級役（3翻以上）
        if result := self.check_junchan(hand, winning_combination):
            results.append(result)
        if result := self.check_honchan(hand, winning_combination):
            results.append(result)
        if result := self.check_ryanpeikou(hand, winning_combination):
            results.append(result)

        # 特殊役（2翻）
        if result := self.check_sanshoku_doukou(hand, winning_combination):
            results.append(result)
        if result := self.check_shousangen(hand, winning_combination):
            results.append(result)
        if result := self.check_honroutou(hand, winning_combination):
            results.append(result)

        # 役滿檢查（優先檢查，因為役滿會覆蓋其他役種）
        # 注意：某些役滿可以同時存在（如四暗刻+字一色）
        yakuman_results = []
        if result := self.check_daisangen(hand, winning_combination):
            yakuman_results.append(result)
        if result := self.check_suukantsu(hand, winning_combination):
            yakuman_results.append(result)
        if result := self.check_suuankou(hand, winning_combination):
            yakuman_results.append(result)
        # 國士無雙已在前面檢查，這裡跳過
        if result := self.check_shousuushi(hand, winning_combination):
            yakuman_results.append(result)
        if result := self.check_daisuushi(hand, winning_combination):
            yakuman_results.append(result)
        if result := self.check_chinroutou(hand, winning_combination):
            yakuman_results.append(result)
        if result := self.check_tsuuiisou(hand, winning_combination):
            yakuman_results.append(result)

        # 如果有役滿，只返回役滿（役滿不與其他役種複合，但可以多個役滿複合）
        if yakuman_results:
            # 役滿可以與立直複合
            if hand.is_riichi:
                yakuman_results.insert(0, YakuResult("立直", "Riichi", "立直", 1, False))
            return yakuman_results

        return results

    def check_riichi(self, hand: Hand, game_state: GameState) -> Optional[YakuResult]:
        """檢查立直"""
        if hand.is_riichi:
            return YakuResult("立直", "Riichi", "立直", 1, False)
        return None

    def check_ippatsu(self, hand: Hand, game_state: GameState) -> Optional[YakuResult]:
        """檢查一發"""
        # TODO: 需要記錄立直後的回合數
        return None

    def check_menzen_tsumo(self, hand: Hand, game_state: GameState) -> Optional[YakuResult]:
        """檢查門清自摸"""
        # TODO: 需要知道是否為自摸
        if hand.is_concealed:
            # 實際判定需要檢查是否為自摸
            pass
        return None

    def check_tanyao(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查斷么九

        斷么九：全部由中張牌（2-8）組成，無幺九牌（1、9、字牌）
        """
        if not winning_combination:
            return None

        # 檢查所有牌是否都是中張牌
        all_tiles = []
        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                if meld_type == "pair":
                    all_tiles.extend([Tile(suit, rank), Tile(suit, rank)])
                elif meld_type == "triplet":
                    all_tiles.extend([Tile(suit, rank), Tile(suit, rank), Tile(suit, rank)])
                elif meld_type == "sequence":
                    for i in range(3):
                        all_tiles.append(Tile(suit, rank + i))

        # 檢查是否有幺九牌或字牌
        for tile in all_tiles:
            if tile.is_honor or tile.is_terminal:
                return None

        return YakuResult("斷么九", "Tanyao", "斷么九", 1, False)

    def check_pinfu(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查平和

        平和：全部由順子和對子組成，無刻子，且聽牌是兩面聽
        門清狀態下，且對子不是役牌
        """
        if not hand.is_concealed:
            return None

        if not winning_combination:
            return None

        # 檢查是否全部是順子（4個順子 + 1個對子）
        sequences = 0
        pair = None

        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                if meld_type == "sequence":
                    sequences += 1
                elif meld_type == "pair":
                    pair = (suit, rank)
                elif meld_type == "triplet":
                    # 有刻子就不是平和
                    return None

        # 必須有4個順子和1個對子
        if sequences != 4 or pair is None:
            return None

        # 對子不能是役牌（這裡簡化處理，實際需要檢查場風、自風、三元牌）
        # TODO: 需要檢查聽牌類型（兩面聽）

        return YakuResult("平和", "Pinfu", "平和", 1, False)

    def check_iipeikou(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查一盃口

        一盃口：門清狀態下，有兩組相同的順子
        """
        if not hand.is_concealed:
            return None

        if not winning_combination:
            return None

        # 統計順子
        sequences = []
        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                if meld_type == "sequence":
                    sequences.append((suit, rank))

        # 檢查是否有兩組相同的順子
        if len(sequences) >= 2:
            for i in range(len(sequences)):
                for j in range(i + 1, len(sequences)):
                    if sequences[i] == sequences[j]:
                        return YakuResult("一盃口", "Iipeikou", "一盃口", 1, False)

        return None

    def check_toitoi(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查對對和

        對對和：全部由刻子組成（4個刻子 + 1個對子）
        """
        if not winning_combination:
            return None

        triplets = 0
        pair = None

        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                if meld_type == "triplet":
                    triplets += 1
                elif meld_type == "pair":
                    pair = (suit, rank)
                elif meld_type == "sequence":
                    # 有順子就不是對對和
                    return None

        # 必須有4個刻子和1個對子
        if triplets == 4 and pair is not None:
            return YakuResult("対々和", "Toitoi", "對對和", 2, False)

        return None

    def check_yakuhai(self, hand: Hand, winning_combination: List, game_state: GameState) -> List[YakuResult]:
        """
        檢查役牌（場風、自風、三元牌刻子）

        Returns:
            役牌列表（可能有多個）
        """
        results = []
        if not winning_combination:
            return results

        # 三元牌
        sangen = [5, 6, 7]  # 白、發、中
        round_wind = game_state.round_wind
        player_wind = game_state.player_winds[0] if game_state.player_winds else None

        # 檢查刻子
        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                if meld_type == "triplet" or meld_type == "kan":
                    if suit.value == "z":
                        # 三元牌
                        if rank in sangen:
                            if rank == 5:
                                results.append(YakuResult("白", "Haku", "白", 1, False))
                            elif rank == 6:
                                results.append(YakuResult("發", "Hatsu", "發", 1, False))
                            elif rank == 7:
                                results.append(YakuResult("中", "Chun", "中", 1, False))

                        # 場風和自風
                        if rank == 1 and round_wind.value == "e":  # 東
                            results.append(YakuResult("場風東", "Ton", "場風東", 1, False))
                        elif rank == 2 and round_wind.value == "s":  # 南
                            results.append(YakuResult("場風南", "Nan", "場風南", 1, False))
                        elif rank == 3 and round_wind.value == "w":  # 西
                            results.append(YakuResult("場風西", "Shaa", "場風西", 1, False))
                        elif rank == 4 and round_wind.value == "n":  # 北
                            results.append(YakuResult("場風北", "Pei", "場風北", 1, False))

                        # 自風（需要根據玩家位置）
                        # TODO: 完善自風判定

        return results

    def check_sanshoku_doujun(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查三色同順

        三色同順：三種數牌（萬、筒、條）都有相同數字的順子
        """
        if not winning_combination:
            return None

        # 統計順子
        sequences_by_suit = {Suit.MANZU: [], Suit.PINZU: [], Suit.SOZU: []}

        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                if meld_type == "sequence" and suit in sequences_by_suit:
                    sequences_by_suit[suit].append(rank)

        # 檢查三種花色是否有相同數字的順子
        for rank in range(1, 8):  # 順子最多到7
            has_manzu = rank in sequences_by_suit[Suit.MANZU]
            has_pinzu = rank in sequences_by_suit[Suit.PINZU]
            has_sozu = rank in sequences_by_suit[Suit.SOZU]

            if has_manzu and has_pinzu and has_sozu:
                return YakuResult("三色同順", "Sanshoku Doujun", "三色同順", 2, False)

        return None

    def check_ittsu(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查一氣通貫

        一氣通貫：同一花色有 1-3、4-6、7-9 的順子
        """
        if not winning_combination:
            return None

        # 按花色統計順子
        sequences_by_suit = {Suit.MANZU: [], Suit.PINZU: [], Suit.SOZU: []}

        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                if meld_type == "sequence" and suit in sequences_by_suit:
                    sequences_by_suit[suit].append(rank)

        # 檢查每種花色是否有一氣通貫
        for suit in [Suit.MANZU, Suit.PINZU, Suit.SOZU]:
            sequences = sequences_by_suit[suit]
            # 需要 1-3、4-6、7-9 各一個順子
            has_123 = 1 in sequences
            has_456 = 4 in sequences
            has_789 = 7 in sequences

            if has_123 and has_456 and has_789:
                return YakuResult("一気通貫", "Ittsu", "一氣通貫", 2, False)

        return None

    def check_sanankou(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查三暗刻

        三暗刻：有三組暗刻（門清狀態下的刻子）
        """
        if not hand.is_concealed:
            return None

        if not winning_combination:
            return None

        # 統計刻子（在門清狀態下，所有刻子都是暗刻）
        triplets = 0

        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                if meld_type == "triplet":
                    triplets += 1

        if triplets >= 3:
            return YakuResult("三暗刻", "Sanankou", "三暗刻", 2, False)

        return None

    def check_chinitsu(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查清一色

        清一色：全部由同一種數牌組成（萬、筒、條）
        """
        if not winning_combination:
            return None

        # 檢查所有牌是否為同一花色
        suits = set()

        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                if suit != Suit.JIHAI:  # 只檢查數牌
                    suits.add(suit)
                else:
                    # 有字牌就不是清一色
                    return None

        # 只有一種數牌花色
        if len(suits) == 1:
            return YakuResult("清一色", "Chinitsu", "清一色", 6, False)

        return None

    def check_honitsu(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查混一色

        混一色：由一種數牌和字牌組成
        """
        if not winning_combination:
            return None

        # 檢查數牌花色和字牌
        number_suits = set()
        has_honor = False

        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                if suit == Suit.JIHAI:
                    has_honor = True
                else:
                    number_suits.add(suit)

        # 只有一種數牌花色，且包含字牌
        if len(number_suits) == 1 and has_honor:
            return YakuResult("混一色", "Honitsu", "混一色", 3, False)

        return None

    def check_chiitoitsu(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查七對子

        七對子：七組對子（特殊和牌型）
        注意：七對子不會有標準的和牌組合，需要特殊處理
        """
        if not hand.is_concealed:
            return None

        # 七對子的和牌組合為空，所以我們需要檢查手牌本身
        # 但這裡我們無法直接訪問完整手牌（14張），所以需要通過其他方式判斷
        # 實際上，如果 winning_combination 為空且是門清，可能是七對子
        # 但這不準確，因為國士無雙也是空組合

        # 更好的方法：在 check_all 中，如果檢測到是七對子型，直接返回
        # 但這裡我們暫時返回 None，因為七對子的判定需要特殊處理
        return None

    def check_junchan(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查純全帶么九

        純全帶么九：全部由順子組成，且每個順子都包含1或9
        門清狀態，無字牌，對子可以是任何數牌（但實際上通常是1或9）
        """
        if not hand.is_concealed:
            return None

        if not winning_combination:
            return None

        # 檢查所有面子是否都包含1或9
        sequences_count = 0
        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                tile = Tile(suit, rank)

                # 有字牌就不是純全帶么九
                if tile.is_honor:
                    return None

                # 檢查順子
                if meld_type == "sequence":
                    sequences_count += 1
                    # 順子必須包含1或9（1-2-3 或 7-8-9）
                    if rank != 1 and rank != 7:
                        return None

                # 純全帶么九應該只有順子，不應該有刻子
                elif meld_type == "triplet":
                    return None

        # 必須有4個順子
        if sequences_count == 4:
            return YakuResult("純全帯么九", "Junchan", "純全帶么九", 3, False)

        return None

    def check_honchan(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查混全帶么九

        混全帶么九：全部由順子和對子組成，且每個面子都包含1或9或字牌
        門清狀態，可以有字牌
        """
        if not hand.is_concealed:
            return None

        if not winning_combination:
            return None

        # 檢查是否有字牌
        has_honor = False
        all_terminals = True

        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                tile = Tile(suit, rank)

                if tile.is_honor:
                    has_honor = True
                else:
                    # 檢查順子
                    if meld_type == "sequence":
                        # 順子必須包含1或9
                        if rank != 1 and rank != 7:
                            all_terminals = False
                            break

                    # 檢查刻子或對子
                    elif meld_type in ["triplet", "pair"]:
                        # 必須是1或9
                        if rank != 1 and rank != 9:
                            all_terminals = False
                            break

        # 必須有字牌，且所有數牌都是幺九牌
        if has_honor and all_terminals:
            return YakuResult("混全帯么九", "Honchan", "混全帶么九", 2, False)

        return None

    def check_ryanpeikou(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查二盃口

        二盃口：門清狀態下，有兩組不同的相同順子（兩組1-2-3和兩組4-5-6）
        注意：二盃口會覆蓋一盃口，所以需要先檢查二盃口
        """
        if not hand.is_concealed:
            return None

        if not winning_combination:
            return None

        # 統計順子
        sequences = []
        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                if meld_type == "sequence":
                    sequences.append((suit, rank))

        # 必須有4個順子
        if len(sequences) != 4:
            return None

        # 檢查是否有兩組不同的相同順子
        sequence_counts = {}
        for seq in sequences:
            sequence_counts[seq] = sequence_counts.get(seq, 0) + 1

        # 計算有多少組不同的順子各出現兩次
        paired_sequences = [seq for seq, count in sequence_counts.items() if count >= 2]

        # 二盃口需要兩組不同的順子各出現兩次（總共4個順子）
        if len(paired_sequences) == 2:
            # 檢查是否每組都恰好出現兩次
            for seq in paired_sequences:
                if sequence_counts[seq] != 2:
                    return None
            return YakuResult("二盃口", "Ryanpeikou", "二盃口", 3, False)

        return None

    def check_sanshoku_doukou(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查三色同刻

        三色同刻：三種數牌（萬、筒、條）都有相同數字的刻子
        """
        if not winning_combination:
            return None

        # 統計刻子
        triplets_by_suit = {Suit.MANZU: [], Suit.PINZU: [], Suit.SOZU: []}

        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                if meld_type == "triplet" and suit in triplets_by_suit:
                    triplets_by_suit[suit].append(rank)

        # 檢查三種花色是否有相同數字的刻子
        for rank in range(1, 10):
            has_manzu = rank in triplets_by_suit[Suit.MANZU]
            has_pinzu = rank in triplets_by_suit[Suit.PINZU]
            has_sozu = rank in triplets_by_suit[Suit.SOZU]

            if has_manzu and has_pinzu and has_sozu:
                return YakuResult("三色同刻", "Sanshoku Doukou", "三色同刻", 2, False)

        return None

    def check_shousangen(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查小三元

        小三元：有兩個三元牌刻子，一個三元牌對子
        """
        if not winning_combination:
            return None

        sangen = [5, 6, 7]  # 白、發、中
        sangen_triplets = []
        sangen_pair = None

        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                if suit == Suit.JIHAI and rank in sangen:
                    if meld_type in ["triplet", "kan"]:
                        sangen_triplets.append(rank)
                    elif meld_type == "pair":
                        sangen_pair = rank

        # 兩個三元牌刻子 + 一個三元牌對子
        if len(sangen_triplets) == 2 and sangen_pair is not None:
            return YakuResult("小三元", "Shousangen", "小三元", 2, False)

        return None

    def check_honroutou(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查混老頭

        混老頭：全部由幺九牌（1、9、字牌）組成
        """
        if not winning_combination:
            return None

        # 檢查所有牌是否都是幺九牌或字牌
        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                tile = Tile(suit, rank)

                # 檢查是否為幺九牌或字牌
                if not (tile.is_terminal or tile.is_honor):
                    return None

        return YakuResult("混老頭", "Honroutou", "混老頭", 2, False)

    def check_daisangen(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查大三元

        大三元：有三組三元牌刻子（白、發、中）
        """
        if not winning_combination:
            return None

        sangen = [5, 6, 7]  # 白、發、中
        sangen_triplets = []

        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                if suit == Suit.JIHAI and rank in sangen:
                    if meld_type in ["triplet", "kan"]:
                        sangen_triplets.append(rank)

        # 三個三元牌刻子
        if len(sangen_triplets) == 3:
            return YakuResult("大三元", "Daisangen", "大三元", 13, True)

        return None

    def check_suukantsu(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查四槓子

        四槓子：有四組槓子
        """
        if not winning_combination:
            return None

        kan_count = 0
        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                if meld_type == "kan":
                    kan_count += 1

        # 四個槓子
        if kan_count == 4:
            return YakuResult("四槓子", "Suukantsu", "四槓子", 13, True)

        return None

    def check_suuankou(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查四暗刻

        四暗刻：門清狀態下，有四組暗刻（或四暗刻單騎）
        """
        if not hand.is_concealed:
            return None

        if not winning_combination:
            return None

        # 統計刻子（在門清狀態下，所有刻子都是暗刻）
        triplets = 0
        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                if meld_type == "triplet":
                    triplets += 1

        # 四個暗刻
        if triplets == 4:
            return YakuResult("四暗刻", "Suuankou", "四暗刻", 13, True)

        return None

    def check_kokushi_musou(self, hand: Hand, all_tiles: List[Tile]) -> Optional[YakuResult]:
        """
        檢查國士無雙

        國士無雙：13種幺九牌各一張，再有一張幺九牌（13面聽）
        國士無雙十三面：13種幺九牌各一張，再有一張幺九牌，且該牌為聽牌
        """
        if not hand.is_concealed:
            return None

        if len(all_tiles) != 14:
            return None

        # 需要的13種幺九牌
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

        # 統計每種牌
        counts = {}
        for tile in all_tiles:
            key = (tile.suit, tile.rank)
            counts[key] = counts.get(key, 0) + 1

        # 檢查是否包含所有需要的牌
        has_all = True
        for req in required_tiles:
            if req not in counts or counts[req] == 0:
                has_all = False
                break

        if not has_all:
            return None

        # 檢查是否只有一張重複
        pairs = 0
        for key, count in counts.items():
            if key in required_tiles and count == 2:
                pairs += 1
            elif key not in required_tiles:
                return None  # 有非幺九牌

        # 必須有一張重複（且只有一張重複）
        if pairs == 1:
            # 檢查是否為十三面聽（重複的牌是聽牌）
            # 這裡簡化處理，如果重複的牌是聽牌，則為十三面
            # TODO: 需要更精確的判定
            return YakuResult("國士無雙", "Kokushi Musou", "國士無雙", 13, True)

        return None

    def check_shousuushi(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查小四喜

        小四喜：有三組風牌刻子，一個風牌對子
        """
        if not winning_combination:
            return None

        kaze = [1, 2, 3, 4]  # 東、南、西、北
        kaze_triplets = []
        kaze_pair = None

        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                if suit == Suit.JIHAI and rank in kaze:
                    if meld_type in ["triplet", "kan"]:
                        kaze_triplets.append(rank)
                    elif meld_type == "pair":
                        kaze_pair = rank

        # 三個風牌刻子 + 一個風牌對子
        if len(kaze_triplets) == 3 and kaze_pair is not None:
            return YakuResult("小四喜", "Shousuushi", "小四喜", 13, True)

        return None

    def check_daisuushi(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查大四喜

        大四喜：有四組風牌刻子
        """
        if not winning_combination:
            return None

        kaze = [1, 2, 3, 4]  # 東、南、西、北
        kaze_triplets = []

        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                if suit == Suit.JIHAI and rank in kaze:
                    if meld_type in ["triplet", "kan"]:
                        kaze_triplets.append(rank)

        # 四個風牌刻子
        if len(kaze_triplets) == 4:
            return YakuResult("大四喜", "Daisuushi", "大四喜", 13, True)

        return None

    def check_chinroutou(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查清老頭

        清老頭：全部由幺九牌刻子組成（無字牌）
        """
        if not winning_combination:
            return None

        # 檢查所有牌是否都是幺九牌刻子（無字牌）
        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                tile = Tile(suit, rank)

                # 有字牌就不是清老頭
                if tile.is_honor:
                    return None

                # 必須是刻子或對子，且是幺九牌
                if meld_type in ["triplet", "kan", "pair"]:
                    if not tile.is_terminal:
                        return None
                elif meld_type == "sequence":
                    # 清老頭不能有順子
                    return None

        return YakuResult("清老頭", "Chinroutou", "清老頭", 13, True)

    def check_tsuuiisou(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查字一色

        字一色：全部由字牌組成
        """
        if not winning_combination:
            return None

        # 檢查所有牌是否都是字牌
        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                tile = Tile(suit, rank)

                # 有數牌就不是字一色
                if not tile.is_honor:
                    return None

        return YakuResult("字一色", "Tsuuiisou", "字一色", 13, True)
