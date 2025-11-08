"""
役種判定系統 - YakuChecker implementation

提供所有役種的判定功能。
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pyriichi.enum_utils import TranslatableEnum
from pyriichi.hand import Hand, CombinationType
from pyriichi.tiles import Tile, Suit
from pyriichi.game_state import GameState, Wind
from pyriichi.rules_config import RenhouPolicy


__all__ = ["Yaku", "YakuResult", "YakuChecker"]


class Yaku(TranslatableEnum):
    """所有役種枚舉"""

    RIICHI = ("riichi", "立直", "立直", "Riichi")
    IPPATSU = ("ippatsu", "一發", "一発", "Ippatsu")
    MENZEN_TSUMO = ("menzen_tsumo", "門清自摸", "門前清自摸和", "Menzen Tsumo")
    TANYAO = ("tanyao", "斷么九", "断么九", "Tanyao")
    PINFU = ("pinfu", "平和", "平和", "Pinfu")
    IIPEIKOU = ("iipeikou", "一盃口", "一盃口", "Iipeikou")
    RYANPEIKOU = ("ryanpeikou", "二盃口", "二盃口", "Ryanpeikou")
    TOITOI = ("toitoi", "對對和", "対々和", "Toitoi")
    SANANKOU = ("sanankou", "三暗刻", "三暗刻", "Sanankou")
    SANKANTSU = ("sankantsu", "三槓子", "三槓子", "Sankantsu")
    SANSHOKU_DOUJUN = ("sanshoku_doujun", "三色同順", "三色同順", "Sanshoku Doujun")
    SANSHOKU_DOUKOU = ("sanshoku_doukou", "三色同刻", "三色同刻", "Sanshoku Doukou")
    ITTSU = ("ittsu", "一氣通貫", "一気通貫", "Ittsu")
    HONITSU = ("honitsu", "混一色", "混一色", "Honitsu")
    CHINITSU = ("chinitsu", "清一色", "清一色", "Chinitsu")
    JUNCHAN = ("junchan", "純全帶么九", "純全帯么九", "Junchan")
    CHANTA = ("chanta", "全帶么九", "全帯么九", "Chanta")
    HONROUTOU = ("honroutou", "混老頭", "混老頭", "Honroutou")
    SHOUSANGEN = ("shousangen", "小三元", "小三元", "Shousangen")
    DAISANGEN = ("daisangen", "大三元", "大三元", "Daisangen")
    SUUANKOU = ("suuankou", "四暗刻", "四暗刻", "Suuankou")
    SUUANKOU_TANKI = ("suuankou_tanki", "四暗刻單騎", "四暗刻単騎", "Suuankou Tanki")
    SUUKANTSU = ("suukantsu", "四槓子", "四槓子", "Suukantsu")
    SHOUSUUSHI = ("shousuushi", "小四喜", "小四喜", "Shousuushi")
    DAISUUSHI = ("daisuushi", "大四喜", "大四喜", "Daisuushi")
    CHINROUTOU = ("chinroutou", "清老頭", "清老頭", "Chinroutou")
    TSUUIISOU = ("tsuuiisou", "字一色", "字一色", "Tsuuiisou")
    RYUIISOU = ("ryuiisou", "綠一色", "綠一色", "Ryuuiisou")
    CHUUREN_POUTOU = ("chuuren_poutou", "九蓮寶燈", "九蓮宝燈", "Chuuren Poutou")
    CHUUREN_POUTOU_PURE = ("chuuren_poutou_pure", "純正九蓮寶燈", "純正九蓮寶燈", "Pure Chuuren Poutou")
    KOKUSHI_MUSOU = ("kokushi_musou", "國士無雙", "國士無双", "Kokushi Musou")
    KOKUSHI_MUSOU_JUUSANMEN = ("kokushi_musou_juusanmen", "國士無雙十三面", "國士無双十三面", "Kokushi Musou Juusanmen")
    TENHOU = ("tenhou", "天和", "天和", "Tenhou")
    CHIHOU = ("chihou", "地和", "地和", "Chihou")
    RENHOU = ("renhou", "人和", "人和", "Renhou")
    HAITEI = ("haitei", "海底撈月", "海底撈月", "Haitei")
    HOUTEI = ("houtei", "河底撈魚", "河底撈魚", "Houtei")
    RINSHAN = ("rinshan", "嶺上開花", "嶺上開花", "Rinshan Kaihou")
    CHIITOITSU = ("chiitoitsu", "七對子", "七対子", "Chiitoitsu")
    HAKU = ("haku", "白", "白", "Haku")
    HATSU = ("hatsu", "發", "發", "Hatsu")
    CHUN = ("chun", "中", "中", "Chun")
    ROUND_WIND_EAST = ("round_wind_east", "場風東", "場風東", "Round Wind East")
    ROUND_WIND_SOUTH = ("round_wind_south", "場風南", "場風南", "Round Wind South")
    ROUND_WIND_WEST = ("round_wind_west", "場風西", "場風西", "Round Wind West")
    ROUND_WIND_NORTH = ("round_wind_north", "場風北", "場風北", "Round Wind North")
    SEAT_WIND_EAST = ("seat_wind_east", "自風東", "自風東", "Seat Wind East")
    SEAT_WIND_SOUTH = ("seat_wind_south", "自風南", "自風南", "Seat Wind South")
    SEAT_WIND_WEST = ("seat_wind_west", "自風西", "自風西", "Seat Wind West")
    SEAT_WIND_NORTH = ("seat_wind_north", "自風北", "自風北", "Seat Wind North")


class WaitingType(Enum):
    """聽牌類型"""

    RYANMEN = "ryanmen"
    PENCHAN = "penchan"
    KANCHAN = "kanchan"
    TANKI = "tanki"
    SHABO = "shabo"


@dataclass(frozen=True)
class YakuResult:
    """役種判定結果"""

    yaku: Yaku
    han: int
    is_yakuman: bool

    def __eq__(self, other):
        return self.yaku == other.yaku if isinstance(other, YakuResult) else False

    def __hash__(self):
        return hash(self.yaku)


class YakuChecker:
    """役種判定器"""

    def check_all(
        self,
        hand: Hand,
        winning_tile: Tile,
        winning_combination: List,
        game_state: GameState,
        is_tsumo: bool = False,
        turns_after_riichi: int = -1,
        is_first_turn: bool = False,
        is_last_tile: bool = False,
        player_position: int = 0,
        is_rinshan: bool = False,
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

        # 天和、地和、人和判定（優先檢查，因為是役滿）
        if result := self.check_tenhou(hand, is_tsumo, is_first_turn, player_position, game_state):
            return [result]
        if result := self.check_chihou(hand, is_tsumo, is_first_turn, player_position, game_state):
            return [result]
        if result := self.check_renhou(hand, is_tsumo, is_first_turn, player_position, game_state):
            return [result]

        # 國士無雙判定（優先檢查，因為是役滿）
        if result := self.check_kokushi_musou(hand, all_tiles):
            results = [result]
            # 檢查是否為十三面聽牌
            if self.check_kokushi_musou_juusanmen(hand, all_tiles):
                results[0] = YakuResult(Yaku.KOKUSHI_MUSOU_JUUSANMEN, 26, True)
            # 國士無雙可以與立直複合（但天和、地和、人和不能與立直複合）
            if hand.is_riichi:
                results.insert(0, YakuResult(Yaku.RIICHI, 1, False))
            return results

        # 七對子判定
        if result := self.check_chiitoitsu(hand, all_tiles):
            results = [result]
            if hand.is_riichi:
                results.insert(0, YakuResult(Yaku.RIICHI, 1, False))
            return results

        results = []

        # 基本役
        if result := self.check_riichi(hand, game_state):
            results.append(result)
        if result := self.check_ippatsu(hand, game_state, turns_after_riichi):
            results.append(result)
        if result := self.check_menzen_tsumo(hand, game_state, is_tsumo):
            results.append(result)
        if result := self.check_haitei_raoyue(hand, is_tsumo, is_last_tile):
            results.append(result)
        if result := self.check_rinshan_kaihou(hand, is_rinshan):
            results.append(result)
        if result := self.check_tanyao(hand, winning_combination):
            results.append(result)
        if result := self.check_pinfu(hand, winning_combination, game_state, winning_tile):
            results.append(result)
        if result := self.check_iipeikou(hand, winning_combination):
            results.append(result)
        if result := self.check_toitoi(hand, winning_combination):
            results.append(result)
        if result := self.check_sankantsu(hand, winning_combination):
            results.append(result)

        # 役牌（可能有多個）
        yakuhai_results = self.check_yakuhai(hand, winning_combination, game_state, player_position)
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
        if result := self.check_sanshoku_doukou(hand, winning_combination):
            results.append(result)
        if result := self.check_shousangen(hand, winning_combination):
            results.append(result)
        if result := self.check_honroutou(hand, winning_combination):
            results.append(result)

        # 高級役（3翻以上）
        if result := self.check_junchan(hand, winning_combination, game_state):
            results.append(result)
        if result := self.check_honchan(hand, winning_combination, game_state):
            results.append(result)
        if result := self.check_ryanpeikou(hand, winning_combination):
            results.append(result)

        # 役滿檢查（優先檢查，因為役滿會覆蓋其他役種）
        # 注意：某些役滿可以同時存在（如四暗刻+字一色）
        yakuman_results = []
        if result := self.check_daisangen(hand, winning_combination):
            yakuman_results.append(result)
        if result := self.check_suukantsu(hand, winning_combination):
            yakuman_results.append(result)
        if result := self.check_suuankou(hand, winning_combination, winning_tile, game_state):
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
        if result := self.check_chuuren_poutou(hand, all_tiles, game_state):
            yakuman_results.append(result)

        # 如果有役滿，只返回役滿（役滿不與其他役種複合，但可以多個役滿複合）
        if yakuman_results:
            # 役滿可以與立直複合
            if hand.is_riichi:
                yakuman_results.insert(0, YakuResult(Yaku.RIICHI, 1, False))
            return yakuman_results

        # 役種衝突檢測和過濾
        results = self._filter_conflicting_yaku(results, winning_combination, game_state)

        return results

    def _filter_conflicting_yaku(
        self, results: List[YakuResult], winning_combination: List, game_state: GameState
    ) -> List[YakuResult]:
        """
        過濾衝突的役種

        Args:
            results: 役種結果列表
            winning_combination: 和牌組合
            game_state: 遊戲狀態

        Returns:
            過濾後的役種列表
        """
        filtered = []
        yaku_set = {r.yaku for r in results}

        for result in results:
            should_include = True

            # 1. 平和與役牌衝突
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
                # 包含幺九的役種
                terminal_yaku = {
                    Yaku.ITTSU,  # 包含1和9的順子
                    Yaku.JUNCHAN,
                    Yaku.CHANTA,
                    Yaku.HONROUTOU,
                    Yaku.CHINROUTOU,
                }
                if yaku_set & terminal_yaku:
                    should_include = False

            # 4. 一盃口與二盃口互斥
            if result.yaku == Yaku.IIPEIKOU and Yaku.RYANPEIKOU in yaku_set:
                should_include = False

            # 5. 清一色與混一色互斥
            if result.yaku == Yaku.CHINITSU and Yaku.HONITSU in yaku_set:
                should_include = False
            if result.yaku == Yaku.HONITSU and Yaku.CHINITSU in yaku_set:
                should_include = False

            # 6. 純全帶与混全帶互斥
            if result.yaku == Yaku.JUNCHAN and Yaku.CHANTA in yaku_set:
                should_include = False
            if result.yaku == Yaku.CHANTA and Yaku.JUNCHAN in yaku_set:
                should_include = False

            # 7. 平和與對對和衝突（結構上互斥）
            if result.yaku == Yaku.PINFU and Yaku.TOITOI in yaku_set:
                should_include = False
            if result.yaku == Yaku.TOITOI and Yaku.PINFU in yaku_set:
                should_include = False

            # 8. 平和與一盃口、二盃口衝突（平和只能有一個對子）
            if result.yaku == Yaku.PINFU and (Yaku.IIPEIKOU in yaku_set or Yaku.RYANPEIKOU in yaku_set):
                should_include = False

            if should_include:
                filtered.append(result)

        return filtered

    def check_riichi(self, hand: Hand, game_state: GameState) -> Optional[YakuResult]:
        """檢查立直"""
        return YakuResult(Yaku.RIICHI, 1, False) if hand.is_riichi else None

    def check_ippatsu(self, hand: Hand, game_state: GameState, turns_after_riichi: int = -1) -> Optional[YakuResult]:
        """
        檢查一發

        一發：立直後一巡內和牌（立直後的第一個自己的回合）
        """
        if not hand.is_riichi:
            return None

        # 如果 turns_after_riichi 為 -1，表示未追蹤，無法判定
        if turns_after_riichi < 0:
            return None

        # 一發：立直後一巡內和牌（turns_after_riichi == 0）
        return YakuResult(Yaku.IPPATSU, 1, False) if turns_after_riichi == 0 else None

    def check_menzen_tsumo(self, hand: Hand, game_state: GameState, is_tsumo: bool = False) -> Optional[YakuResult]:
        """
        檢查門清自摸

        門清自摸：門清狀態下自摸和牌
        """
        if not hand.is_concealed:
            return None

        return YakuResult(Yaku.MENZEN_TSUMO, 1, False) if is_tsumo else None

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
                if meld_type == CombinationType.PAIR:
                    all_tiles.extend([Tile(suit, rank), Tile(suit, rank)])
                elif meld_type == CombinationType.TRIPLET:
                    all_tiles.extend([Tile(suit, rank), Tile(suit, rank), Tile(suit, rank)])
                elif meld_type == CombinationType.SEQUENCE:
                    all_tiles.extend(Tile(suit, rank + i) for i in range(3))
        # 檢查是否有幺九牌或字牌
        for tile in all_tiles:
            if tile.is_honor or tile.is_terminal:
                return None

        return YakuResult(Yaku.TANYAO, 1, False)

    def check_pinfu(
        self,
        hand: Hand,
        winning_combination: List,
        game_state: Optional[GameState] = None,
        winning_tile: Optional[Tile] = None,
    ) -> Optional[YakuResult]:
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
                if meld_type == CombinationType.PAIR:
                    pair = (suit, rank)
                elif meld_type == CombinationType.SEQUENCE:
                    sequences += 1
                elif meld_type == CombinationType.TRIPLET:
                    # 有刻子就不是平和
                    return None

        # 必須有4個順子和1個對子
        if sequences != 4 or pair is None:
            return None

        # 對子不能是役牌（檢查場風、自風、三元牌）
        pair_suit, pair_rank = pair
        if pair_suit == Suit.JIHAI:
            # 檢查是否是三元牌
            sangen = [5, 6, 7]  # 白、發、中
            if pair_rank in sangen:
                return None  # 三元牌對子，不能是平和

            # 檢查是否是場風（需要game_state）
            if game_state is not None:
                round_wind = game_state.round_wind
                wind_mapping = {
                    1: Wind.EAST,
                    2: Wind.SOUTH,
                    3: Wind.WEST,
                    4: Wind.NORTH,
                }
                if round_wind == wind_mapping.get(pair_rank):
                    return None  # 場風對子，不能是平和

            # 檢查是否是自風（需要玩家位置，這裡先跳過）
            # TODO: 需要完善玩家位置邏輯來檢查自風

        # 檢查聽牌類型（兩面聽）- 根據規則配置
        ruleset = game_state.ruleset if game_state else None
        if ruleset and ruleset.pinfu_require_ryanmen and winning_tile is not None:
            waiting_type = self._determine_waiting_type(winning_tile, winning_combination)
            if waiting_type != WaitingType.RYANMEN:
                return None  # 不是兩面聽，不能是平和

        return YakuResult(Yaku.PINFU, 1, False)

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
                if meld_type == CombinationType.SEQUENCE:
                    sequences.append((suit, rank))

        # 檢查是否有兩組相同的順子
        if len(sequences) >= 2:
            for i in range(len(sequences)):
                for j in range(i + 1, len(sequences)):
                    if sequences[i] == sequences[j]:
                        return YakuResult(Yaku.IIPEIKOU, 1, False)

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
                if meld_type == CombinationType.PAIR:
                    pair = (suit, rank)
                elif meld_type == CombinationType.SEQUENCE:
                    # 有順子就不是對對和
                    return None

                elif meld_type == CombinationType.TRIPLET:
                    triplets += 1
        # 必須有4個刻子和1個對子
        if triplets == 4 and pair is not None:
            return YakuResult(Yaku.TOITOI, 2, False)

        return None

    def check_sankantsu(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查三槓子

        三槓子：有三組槓子
        """
        if not winning_combination:
            return None

        kan_count = 0
        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                if meld_type == CombinationType.KAN:
                    kan_count += 1

        # 三個槓子
        return YakuResult(Yaku.SANKANTSU, 2, False) if kan_count == 3 else None

    def check_yakuhai(
        self, hand: Hand, winning_combination: List, game_state: GameState, player_position: int = 0
    ) -> List[YakuResult]:
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
        wind_rank_mapping = {
            1: (Wind.EAST, Yaku.ROUND_WIND_EAST, Yaku.SEAT_WIND_EAST),
            2: (Wind.SOUTH, Yaku.ROUND_WIND_SOUTH, Yaku.SEAT_WIND_SOUTH),
            3: (Wind.WEST, Yaku.ROUND_WIND_WEST, Yaku.SEAT_WIND_WEST),
            4: (Wind.NORTH, Yaku.ROUND_WIND_NORTH, Yaku.SEAT_WIND_NORTH),
        }
        round_wind = game_state.round_wind
        player_wind = game_state.player_winds[0] if game_state.player_winds else None

        # 檢查刻子
        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                if meld_type in {CombinationType.TRIPLET, CombinationType.KAN} and suit == Suit.JIHAI:
                    if rank in sangen:
                        if rank == 5:
                            results.append(YakuResult(Yaku.HAKU, 1, False))
                        elif rank == 6:
                            results.append(YakuResult(Yaku.HATSU, 1, False))
                        elif rank == 7:
                            results.append(YakuResult(Yaku.CHUN, 1, False))

                    # 場風和自風
                    if rank in wind_rank_mapping:
                        target_wind, round_yaku, seat_yaku = wind_rank_mapping[rank]
                        if round_wind == target_wind:
                            results.append(YakuResult(round_yaku, 1, False))

                    # 自風（需要根據玩家位置）
                    # 自風：與玩家位置對應的風牌刻子
                    if player_position < len(game_state.player_winds):
                        player_wind = game_state.player_winds[player_position]
                        if rank in wind_rank_mapping:
                            target_wind, _, seat_yaku = wind_rank_mapping[rank]
                            if player_wind == target_wind:
                                results.append(YakuResult(seat_yaku, 1, False))

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
                if meld_type == CombinationType.SEQUENCE and suit in sequences_by_suit:
                    sequences_by_suit[suit].append(rank)

        # 檢查三種花色是否有相同數字的順子
        for rank in range(1, 8):  # 順子最多到7
            has_manzu = rank in sequences_by_suit[Suit.MANZU]
            has_pinzu = rank in sequences_by_suit[Suit.PINZU]
            has_sozu = rank in sequences_by_suit[Suit.SOZU]

            if has_manzu and has_pinzu and has_sozu:
                return YakuResult(Yaku.SANSHOKU_DOUJUN, 2, False)

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
                if meld_type == CombinationType.SEQUENCE and suit in sequences_by_suit:
                    sequences_by_suit[suit].append(rank)

        # 檢查每種花色是否有一氣通貫
        for suit in [Suit.MANZU, Suit.PINZU, Suit.SOZU]:
            sequences = sequences_by_suit[suit]
            # 需要 1-3、4-6、7-9 各一個順子
            has_123 = 1 in sequences
            has_456 = 4 in sequences
            has_789 = 7 in sequences

            if has_123 and has_456 and has_789:
                return YakuResult(Yaku.ITTSU, 2, False)

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
                if meld_type == CombinationType.TRIPLET:
                    triplets += 1

        return YakuResult(Yaku.SANANKOU, 2, False) if triplets >= 3 else None

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
        return YakuResult(Yaku.CHINITSU, 6, False) if len(suits) == 1 else None

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
            return YakuResult(Yaku.HONITSU, 3, False)

        return None

    def check_chiitoitsu(self, hand: Hand, all_tiles: List[Tile]) -> Optional[YakuResult]:
        """
        檢查七對子

        七對子：七組對子（特殊和牌型）
        注意：七對子不會有標準的和牌組合，需要特殊處理
        """
        if not hand.is_concealed or len(all_tiles) != 14:
            return None

        counts: Dict[Tuple[Suit, int], int] = {}
        for tile in all_tiles:
            key = (tile.suit, tile.rank)
            counts[key] = counts.get(key, 0) + 1
            if counts[key] > 2:
                return None

        pairs = [count for count in counts.values() if count == 2]
        return None if len(pairs) != 7 else YakuResult(Yaku.CHIITOITSU, 2, False)

    def check_junchan(
        self, hand: Hand, winning_combination: List, game_state: Optional[GameState] = None
    ) -> Optional[YakuResult]:
        """
        檢查純全帶么九

        純全帶么九：全部由順子組成，且每個順子都包含1或9
        無字牌，對子可以是任何數牌（但實際上通常是1或9）
        根據門清/副露狀態決定翻數（標準競技規則）
        """
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
                if meld_type == CombinationType.SEQUENCE:
                    sequences_count += 1
                    # 順子必須包含1或9（1-2-3 或 7-8-9）
                    if rank not in [1, 7]:
                        return None

                elif meld_type == CombinationType.TRIPLET:
                    return None

        # 必須有4個順子
        if sequences_count == 4:
            # 根據規則配置決定翻數
            ruleset = game_state.ruleset if game_state else None
            if ruleset:
                han = ruleset.junchan_closed_han if hand.is_concealed else ruleset.junchan_open_han
            else:
                # 默認：門清3翻，副露2翻
                han = 3 if hand.is_concealed else 2
            return YakuResult(Yaku.JUNCHAN, han, False)

        return None

    def check_honchan(
        self, hand: Hand, winning_combination: List, game_state: Optional[GameState] = None
    ) -> Optional[YakuResult]:
        """
        檢查全帶么九（Chanta）

        全帶么九：全部由順子和對子組成，且每個面子都包含1或9或字牌
        可以有字牌，根據門清/副露狀態決定翻數（標準競技規則）
        """
        ruleset = game_state.ruleset if game_state else None
        if ruleset and not ruleset.chanta_enabled:
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
                elif (
                    meld_type == CombinationType.SEQUENCE
                    and rank not in [1, 7]
                    or meld_type != CombinationType.SEQUENCE
                    and meld_type in {CombinationType.TRIPLET, CombinationType.PAIR}
                    and rank not in [1, 9]
                ):
                    all_terminals = False
                    break

        # 必須有字牌，且所有數牌都是幺九牌
        if has_honor and all_terminals:
            # 根據規則配置決定翻數
            if ruleset:
                han = ruleset.chanta_closed_han if hand.is_concealed else ruleset.chanta_open_han
            else:
                # 默認：門清2翻，副露1翻
                han = 2 if hand.is_concealed else 1
            return YakuResult(Yaku.CHANTA, han, False)

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
                if meld_type == CombinationType.SEQUENCE:
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
            return YakuResult(Yaku.RYANPEIKOU, 3, False)

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
                if meld_type == CombinationType.TRIPLET and suit in triplets_by_suit:
                    triplets_by_suit[suit].append(rank)

        # 檢查三種花色是否有相同數字的刻子
        for rank in range(1, 10):
            has_manzu = rank in triplets_by_suit[Suit.MANZU]
            has_pinzu = rank in triplets_by_suit[Suit.PINZU]
            has_sozu = rank in triplets_by_suit[Suit.SOZU]

            if has_manzu and has_pinzu and has_sozu:
                return YakuResult(Yaku.SANSHOKU_DOUKOU, 2, False)

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
                    if meld_type in {CombinationType.TRIPLET, CombinationType.KAN}:
                        sangen_triplets.append(rank)
                    elif meld_type == CombinationType.PAIR:
                        sangen_pair = rank

        # 兩個三元牌刻子 + 一個三元牌對子
        if len(sangen_triplets) == 2 and sangen_pair is not None:
            return YakuResult(Yaku.SHOUSANGEN, 2, False)

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

        return YakuResult(Yaku.HONROUTOU, 2, False)

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
                if (
                    suit == Suit.JIHAI
                    and rank in sangen
                    and meld_type in {CombinationType.TRIPLET, CombinationType.KAN}
                ):
                    sangen_triplets.append(rank)

        # 三個三元牌刻子
        if len(sangen_triplets) == 3:
            return YakuResult(Yaku.DAISANGEN, 13, True)

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
                if meld_type == CombinationType.KAN:
                    kan_count += 1

        # 四個槓子
        return YakuResult(Yaku.SUUKANTSU, 13, True) if kan_count == 4 else None

    def check_suuankou(
        self,
        hand: Hand,
        winning_combination: List,
        winning_tile: Optional[Tile] = None,
        game_state: Optional[GameState] = None,
    ) -> Optional[YakuResult]:
        """
        檢查四暗刻

        四暗刻：門清狀態下，有四組暗刻（或四暗刻單騎）
        根據規則配置，四暗刻單騎可能為雙倍役滿
        """
        if not hand.is_concealed:
            return None

        if not winning_combination:
            return None

        # 統計刻子（在門清狀態下，所有刻子都是暗刻）
        triplets = 0
        is_tanki = False
        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                if meld_type == CombinationType.TRIPLET:
                    triplets += 1
                elif meld_type == CombinationType.PAIR and winning_tile:
                    # 檢查是否為單騎聽
                    if suit == winning_tile.suit and rank == winning_tile.rank:
                        is_tanki = True

        # 四個暗刻
        if triplets == 4:
            ruleset = game_state.ruleset if game_state else None
            if ruleset and ruleset.suuankou_tanki_double and is_tanki:
                return YakuResult(Yaku.SUUANKOU_TANKI, 26, True)
            return YakuResult(Yaku.SUUANKOU, 13, True)

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
        return YakuResult(Yaku.KOKUSHI_MUSOU, 13, True) if pairs == 1 else None

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
                    if meld_type in {CombinationType.TRIPLET, CombinationType.KAN}:
                        kaze_triplets.append(rank)
                    elif meld_type == CombinationType.PAIR:
                        kaze_pair = rank

        # 三個風牌刻子 + 一個風牌對子
        if len(kaze_triplets) == 3 and kaze_pair is not None:
            return YakuResult(Yaku.SHOUSUUSHI, 13, True)

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
                if suit == Suit.JIHAI and rank in kaze and meld_type in {CombinationType.TRIPLET, CombinationType.KAN}:
                    kaze_triplets.append(rank)

        # 四個風牌刻子
        if len(kaze_triplets) == 4:
            return YakuResult(Yaku.DAISUUSHI, 13, True)

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
                if (
                    meld_type in {CombinationType.TRIPLET, CombinationType.KAN, CombinationType.PAIR}
                    and not tile.is_terminal
                    or meld_type not in {CombinationType.TRIPLET, CombinationType.KAN, CombinationType.PAIR}
                    and meld_type == CombinationType.SEQUENCE
                ):
                    return None
        return YakuResult(Yaku.CHINROUTOU, 13, True)

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

        return YakuResult(Yaku.TSUUIISOU, 13, True)

    def check_ryuuiisou(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查綠一色

        綠一色：全部由綠牌組成（2、3、4、6、8條、發）
        """
        if not winning_combination:
            return None

        # 綠牌：2、3、4、6、8條、發
        green_tiles = [
            (Suit.SOZU, 2),
            (Suit.SOZU, 3),
            (Suit.SOZU, 4),
            (Suit.SOZU, 6),
            (Suit.SOZU, 8),
            (Suit.JIHAI, 6),  # 發
        ]

        # 檢查所有牌是否都是綠牌
        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                tile_key = (suit, rank)

                # 檢查順子
                if meld_type == CombinationType.SEQUENCE:
                    # 順子中的每張牌都必須是綠牌
                    for i in range(3):
                        seq_tile = (suit, rank + i)
                        if seq_tile not in green_tiles:
                            return None

                # 檢查刻子、槓子、對子
                elif meld_type in {CombinationType.TRIPLET, CombinationType.KAN, CombinationType.PAIR}:
                    if tile_key not in green_tiles:
                        return None

        return YakuResult(Yaku.RYUIISOU, 13, True)

    def check_chuuren_poutou(
        self, hand: Hand, all_tiles: List[Tile], game_state: Optional[GameState] = None
    ) -> Optional[YakuResult]:
        """
        檢查九蓮寶燈

        九蓮寶燈：同一種花色（萬、筒、條）有 1112345678999 + 任意一張相同花色
        純正九蓮寶燈：九蓮寶燈且聽牌為九面聽
        根據規則配置，純正九蓮寶燈可能為雙倍役滿
        """
        if not hand.is_concealed:
            return None

        if len(all_tiles) != 14:
            return None

        # 檢查是否為同一種數牌花色
        suits = set()
        for tile in all_tiles:
            if tile.suit != Suit.JIHAI:  # 只檢查數牌
                suits.add(tile.suit)
            else:
                return None  # 有字牌就不是九蓮寶燈

        # 必須只有一種花色
        if len(suits) != 1:
            return None

        suit = list(suits)[0]

        # 統計該花色的牌數
        counts = {}
        for tile in all_tiles:
            if tile.suit == suit:
                counts[tile.rank] = counts.get(tile.rank, 0) + 1

        # 檢查是否符合九蓮寶燈模式：1112345678999 + 任意一張
        # 必須有：1（至少3張）、2（至少1張）、3（至少1張）、4（至少1張）、
        #         5（至少1張）、6（至少1張）、7（至少1張）、8（至少1張）、9（至少3張）
        required = {
            1: 3,  # 至少3張
            2: 1,
            3: 1,
            4: 1,
            5: 1,
            6: 1,
            7: 1,
            8: 1,
            9: 3,  # 至少3張
        }

        # 檢查是否符合要求
        for rank, min_count in required.items():
            if rank not in counts or counts[rank] < min_count:
                return None

        # 檢查總數是否為14張（1-9各至少要求的數量，加上額外的1張）
        total = sum(counts.values())
        if total != 14:
            return None

        # 檢查是否為純正九蓮寶燈（聽牌為九面聽）
        # 純正九蓮寶燈：1112345678999 + 任意一張，且該張牌是聽牌
        # 簡化處理：如果多出的那張牌是1-9中的任意一張且數量為2，則為純正
        # TODO: 需要更精確的判定
        for rank in range(1, 10):
            if counts.get(rank, 0) == 4:
                # 有4張相同的牌，可能是純正九蓮寶燈
                # 根據規則配置決定是否為雙倍役滿
                ruleset = game_state.ruleset if game_state else None
                if ruleset and ruleset.chuuren_pure_double:
                    return YakuResult(Yaku.CHUUREN_POUTOU_PURE, 26, True)
                else:
                    return YakuResult(Yaku.CHUUREN_POUTOU_PURE, 13, True)

        return YakuResult(Yaku.CHUUREN_POUTOU, 13, True)

    def check_tenhou(
        self, hand: Hand, is_tsumo: bool, is_first_turn: bool, player_position: int, game_state: GameState
    ) -> Optional[YakuResult]:
        """
        檢查天和

        天和：莊家在第一巡自摸和牌
        條件：
        1. 莊家（player_position == dealer）
        2. 第一巡（is_first_turn）
        3. 自摸（is_tsumo）
        4. 門清（hand.is_concealed）
        """
        # 必須是莊家
        if player_position != game_state.dealer:
            return None

        # 必須是第一巡
        if not is_first_turn:
            return None

        # 必須是自摸
        if not is_tsumo:
            return None

        # 必須是門清
        return YakuResult(Yaku.TENHOU, 13, True) if hand.is_concealed else None

    def check_chihou(
        self, hand: Hand, is_tsumo: bool, is_first_turn: bool, player_position: int, game_state: GameState
    ) -> Optional[YakuResult]:
        """
        檢查地和

        地和：閒家在第一巡自摸和牌
        條件：
        1. 閒家（player_position != dealer）
        2. 第一巡（is_first_turn）
        3. 自摸（is_tsumo）
        4. 門清（hand.is_concealed）
        """
        # 必須是閒家
        if player_position == game_state.dealer:
            return None

        # 必須是第一巡
        if not is_first_turn:
            return None

        # 必須是自摸
        if not is_tsumo:
            return None

        # 必須是門清
        return YakuResult(Yaku.CHIHOU, 13, True) if hand.is_concealed else None

    def check_renhou(
        self, hand: Hand, is_tsumo: bool, is_first_turn: bool, player_position: int, game_state: GameState
    ) -> Optional[YakuResult]:
        """
        檢查人和

        人和：閒家在第一巡榮和
        條件：
        1. 閒家（player_position != dealer）
        2. 第一巡（is_first_turn）
        3. 榮和（not is_tsumo）
        4. 門清（hand.is_concealed）

        根據規則配置決定翻數：
        - RenhouPolicy.YAKUMAN: 役滿（13翻）
        - RenhouPolicy.TWO_HAN: 2翻（標準競技規則）
        - RenhouPolicy.OFF: 不啟用
        """
        ruleset = game_state.ruleset

        # 檢查是否啟用
        if ruleset.renhou_policy == RenhouPolicy.OFF:
            return None

        # 必須是閒家
        if player_position == game_state.dealer:
            return None

        # 必須是第一巡
        if not is_first_turn:
            return None

        # 必須是榮和
        if is_tsumo:
            return None

        # 必須是門清
        if not hand.is_concealed:
            return None

        # 根據規則配置返回不同的翻數
        if ruleset.renhou_policy == RenhouPolicy.YAKUMAN:
            return YakuResult(Yaku.RENHOU, 13, True)
        elif ruleset.renhou_policy == RenhouPolicy.TWO_HAN:
            return YakuResult(Yaku.RENHOU, 2, False)
        else:
            return None

    def check_haitei_raoyue(self, hand: Hand, is_tsumo: bool, is_last_tile: bool) -> Optional[YakuResult]:
        """
        檢查海底撈月/河底撈魚

        海底撈月：自摸最後一張牌和牌（1翻）
        河底撈魚：榮和最後一張牌和牌（1翻）
        """
        if not is_last_tile:
            return None

        if is_tsumo:
            return YakuResult(Yaku.HAITEI, 1, False)
        else:
            return YakuResult(Yaku.HOUTEI, 1, False)

    def check_rinshan_kaihou(self, hand: Hand, is_rinshan: bool) -> Optional[YakuResult]:
        """
        檢查嶺上開花

        嶺上開花：槓後從嶺上摸牌和牌（1翻）
        """
        return YakuResult(Yaku.RINSHAN, 1, False) if is_rinshan else None

    def check_kokushi_musou_juusanmen(self, hand: Hand, all_tiles: List[Tile]) -> bool:
        """
        檢查國士無雙十三面

        國士無雙十三面：13種幺九牌各一張，再有一張幺九牌，且該牌為聽牌
        實際上，如果重複的牌正好是13種中的任意一種，且該牌可以是聽牌，則為十三面
        """
        if not hand.is_concealed:
            return False

        if len(all_tiles) != 14:
            return False

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

        # 檢查是否包含所有需要的牌，且每種牌至少1張
        for req in required_tiles:
            if req not in counts or counts[req] == 0:
                return False

        # 檢查是否只有一張重複，且重複的牌是13種中的一種
        pairs = 0
        for key, count in counts.items():
            if key in required_tiles and count == 2:
                pairs += 1
            elif key not in required_tiles:
                return False  # 有非幺九牌

        # 必須有且只有一張重複，且該重複牌是13種中的一種
        # 在這種情況下，任何一張幺九牌都可以和，所以是十三面聽牌
        return pairs == 1

    def _determine_waiting_type(self, winning_tile: Tile, winning_combination: List) -> WaitingType:
        """
        判定聽牌類型

        Args:
            winning_tile: 和牌牌
            winning_combination: 和牌組合

        Returns:
            聽牌類型：ryanmen（兩面）、penchan（邊張）、kanchan（嵌張）、tanki（單騎）、shabo（雙碰）
        """
        if not winning_combination:
            return WaitingType.RYANMEN  # 默認為兩面聽

        # 檢查和牌牌是否在順子中
        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                if (
                    meld_type == CombinationType.SEQUENCE
                    and suit == winning_tile.suit
                    and rank <= winning_tile.rank <= rank + 2
                ):
                    if (
                        winning_tile.rank == rank == 1
                        or winning_tile.rank != rank
                        and winning_tile.rank != rank + 1
                        and winning_tile.rank == rank + 2
                        and rank == 7
                    ):
                        return WaitingType.PENCHAN
                    elif (
                        winning_tile.rank == rank
                        or winning_tile.rank != rank + 1
                        and winning_tile.rank == rank + 2
                        or winning_tile.rank == rank + 1
                    ):
                        return WaitingType.KANCHAN
                    break

        # 檢查是否為單騎聽（對子的一部分）
        for meld in winning_combination:
            if isinstance(meld, tuple) and len(meld) == 2:
                meld_type, (suit, rank) = meld
                if meld_type == CombinationType.PAIR and (suit == winning_tile.suit and rank == winning_tile.rank):
                    return WaitingType.TANKI

        # 默認為兩面聽
        return WaitingType.RYANMEN
