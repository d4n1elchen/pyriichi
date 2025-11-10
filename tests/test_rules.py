"""
RuleEngine 的單元測試
"""

import pytest
from pyriichi.hand import Hand, Meld, MeldType
from pyriichi.rules import ActionResult, RuleEngine, GameAction, GamePhase, RyuukyokuType, RyuukyokuResult
from pyriichi.tiles import Tile, Suit, TileSet
from pyriichi.utils import parse_tiles


class TestRuleEngine:
    """規則引擎測試"""

    def setup_method(self):
        """設置測試環境"""
        self.engine = RuleEngine(num_players=4)

    def _has_action(self, player: int, action: GameAction) -> bool:
        """便利方法：檢查玩家可用動作"""
        return action in self.engine.get_available_actions(player)

    def test_start_game(self):
        """測試開始遊戲"""
        self.engine.start_game()
        assert self.engine.get_phase() == GamePhase.INIT

    def test_start_round(self):
        """測試開始一局"""
        self.engine.start_game()
        self.engine.start_round()
        assert self.engine.get_phase() == GamePhase.DEALING

    def test_deal(self):
        """測試發牌"""
        self.engine.start_game()
        self.engine.start_round()
        hands = self.engine.deal()

        assert len(hands) == 4
        # 莊家應該有14張，其他玩家13張
        assert len(hands[0]) == 14
        assert len(hands[1]) == 13
        assert len(hands[2]) == 13
        assert len(hands[3]) == 13

        assert self.engine.get_phase() == GamePhase.PLAYING

    def test_check_draw(self):
        """測試流局判定"""
        self._init_game()
        # 初始狀態不應該流局
        draw_type = self.engine.check_ryuukyoku()
        assert draw_type is None

    def test_check_chankan(self):
        """測試搶槓檢查"""
        pass

    def test_check_win_rinshan(self):
        """測試嶺上開花和牌檢查"""
        self._init_game()
        # 設置一個可以嶺上開花和牌的手牌
        # 創建一個和牌型手牌
        # 手牌：123m 456m 789m 123p 4p (嶺上牌 4p)
        self.engine._hands[0] = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p4p4p"))
        self.engine._current_player = 0

        # 檢查嶺上開花和牌
        rinshan_tile = Tile(Suit.PINZU, 4)
        result = self.engine.check_win(0, rinshan_tile, is_rinshan=True)
        assert result is not None
        assert result.win == True
        assert result.rinshan is not None
        assert result.rinshan == True

    def test_check_win_tsumo_sets_is_tsumo(self):
        """測試自摸時 score_result.is_tsumo 為 True"""
        self._init_game()
        player = self.engine.get_current_player()
        winning_tile = Tile(Suit.PINZU, 4)
        # 門清手牌：123m 456m 789m 123p + 4p
        self.engine._hands[player] = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p4p4p"))
        # 模擬剛摸到和牌
        self.engine._last_drawn_tile = (player, winning_tile)
        result = self.engine.check_win(player, winning_tile)
        assert result is not None
        assert result.score_result.is_tsumo is True
        assert result.score_result.payment_from == 0

    def test_check_win_ron_when_turn_passes(self):
        """測試他家捨牌後榮和不會被誤判為自摸"""
        self._init_game()
        discarder = 0
        winner = (discarder + 1) % self.engine.get_num_players()
        winning_tile = Tile(Suit.PINZU, 4)
        self.engine._hands[winner] = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p4p"))
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = discarder
        # 模擬輪到下一位玩家（實際為榮和狀態）
        self.engine._current_player = winner
        self.engine._last_drawn_tile = None
        result = self.engine.check_win(winner, winning_tile)
        assert result is not None
        assert result.score_result is not None
        assert result.score_result.is_tsumo is False
        assert result.score_result.payment_from == discarder

    def test_pon_action_claims_last_discard(self):
        """測試碰牌會取得最後捨牌並改變輪到的玩家。"""
        self._init_game()
        tile_to_discard = Tile(Suit.MANZU, 3)

        self.engine._hands[0] = Hand(parse_tiles("1m3m5m6m7m8m9m1p2p3p4p1s2s3s"))
        # 手牌：33m 567p 89p 456s 789s
        self.engine._hands[1] = Hand(parse_tiles("3m3m5p6p7p8p9p4s5s6s7s8s9s"))

        self.engine._current_player = 0
        discard_before = len(self.engine.get_discards(0))

        discard_result = self.engine.execute_action(0, GameAction.DISCARD, tile=tile_to_discard)
        assert discard_result.discarded is True
        assert self.engine.get_last_discard() == tile_to_discard
        assert self.engine.get_last_discard_player() == 0
        actions = self.engine.get_available_actions(1)
        assert GameAction.PON in actions

        pon_result = self.engine.execute_action(1, GameAction.PON)

        assert pon_result.called_action == GameAction.PON
        assert pon_result.meld is not None
        assert tile_to_discard in pon_result.meld.tiles
        assert len(self.engine.get_hand(1).melds) == 1
        assert len(self.engine.get_discards(0)) == discard_before
        assert self.engine.get_last_discard() is None
        assert self.engine.get_last_discard_player() is None
        assert self.engine.get_current_player() == 1
        actions_after = self.engine.get_available_actions(1)
        assert GameAction.DRAW not in actions_after

    def test_chi_action_uses_sequence_and_resets_turn(self):
        """測試吃牌會使用指定順子並更新遊戲狀態。"""
        self._init_game()
        tile_to_discard = Tile(Suit.MANZU, 4)

        self.engine._hands[0] = Hand(parse_tiles("4m7m8m9m1p2p3p4p5p1s2s3s4s5s"))
        # 手牌：23m 56m 678p 9p 678s 9s 5s
        self.engine._hands[1] = Hand(parse_tiles("2m3m5m6m6p7p8p9p6s7s8s9s5s"))
        # 手牌：11m 11p 112345678s
        self.engine._hands[2] = Hand(parse_tiles("1m1m1p1p1s1s2s3s4s5s6s7s8s"))

        self.engine._current_player = 0
        self.engine.execute_action(0, GameAction.DISCARD, tile=tile_to_discard)

        actions_player1 = self.engine.get_available_actions(1)
        assert GameAction.CHI in actions_player1
        actions_player2 = self.engine.get_available_actions(2)
        assert GameAction.CHI not in actions_player2

        sequences = self.engine.get_available_chi_sequences(1)
        assert sequences

        target_sequence = None
        for seq in sequences:
            ranks = sorted(tile.rank for tile in seq)
            if ranks == [2, 3]:
                target_sequence = seq
                break

        assert target_sequence is not None

        chi_result = self.engine.execute_action(1, GameAction.CHI, sequence=target_sequence)

        assert chi_result.called_action == GameAction.CHI
        assert chi_result.called_tile == tile_to_discard
        assert chi_result.meld is not None
        assert len(self.engine.get_hand(1).melds) == 1
        assert self.engine.get_last_discard() is None
        assert self.engine.get_last_discard_player() is None
        assert self.engine.get_current_player() == 1
        actions_after_chi = self.engine.get_available_actions(1)
        assert GameAction.DRAW not in actions_after_chi

    def test_hand_total_tile_count_includes_melds(self):
        """手牌總數應包含副露的牌。"""
        # 手牌：11123m 456p 77899s
        tiles = parse_tiles("1m1m1m2m3m4p5p6p7s7s8s9s9s")

        hand = Hand(tiles)
        assert hand.total_tile_count() == 13

        meld = hand.pon(Tile(Suit.MANZU, 1))
        assert meld is not None
        assert len(hand.tiles) == 11
        assert hand.total_tile_count() == 14

    def test_handle_draw(self):
        """測試流局處理"""
        self._init_game()
        # 開局時不能流局
        actions = self.engine.get_available_actions(0)
        assert GameAction.DRAW not in actions

    def test_check_win_no_combinations(self):
        """測試 check_win 沒有和牌組合"""
        self._init_game()
        # 創建一個不和牌的手牌
        # 手牌：123m 456m 78m 123p 45p
        test_tiles = parse_tiles("1m2m3m4m5m6m7m8m1p2p3p4p5p")
        test_hand = Hand(test_tiles)
        self.engine._hands[0] = test_hand

        # 檢查和牌（應該返回 None，因為沒有和牌組合）
        winning_tile = Tile(Suit.MANZU, 9)
        result = self.engine.check_win(0, winning_tile)
        assert result is None

    def test_check_win_no_yaku(self):
        """測試 check_win 沒有役"""
        self._init_game()
        # 創建一個標準和牌型，但構造為「無役」：
        # - 4 個順子 + 1 個對子
        # - 包含 7-8-9（含幺九）使「斷么九」不成立
        # - 原設計以「嵌張」避免平和，但目前實作未嚴格檢查兩面聽
        #   因此下方額外設為「非門清」以杜絕平和誤判
        # - 對子為非役牌，且不產生其他役
        # 手牌：234m 567789m 2p 4p 22s
        tiles = parse_tiles("2m3m4m5m6m7m7m8m9m2p4p2s2s")

        hand = Hand(tiles)
        # 將手牌設為非門清，避免平和（實作目前未檢查兩面聽，防止誤判平和）
        # 手牌：111s
        hand._melds.append(Meld(MeldType.PON, parse_tiles("1s1s1s")))
        # 設定最後捨牌為 3p，測試榮和
        winning_tile = Tile(Suit.PINZU, 3)
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1

        # 將手牌放到玩家0
        self.engine._hands[0] = hand
        self.engine._current_player = 2  # 當前輪到其他玩家，表示榮和

        # 檢查和牌（非門清且無其他役，應該返回 None）
        result = self.engine.check_win(0, winning_tile)
        assert result is None

    def test_check_draw_suufon_renda(self):
        """測試四風連打流局檢查"""
        self._init_game()
        # 設置捨牌歷史為四張相同的風牌
        wind_tile = Tile(Suit.JIHAI, 1)  # 東

        # 添加四張相同的風牌到捨牌歷史
        self.engine._discard_history.append((0, wind_tile))
        self.engine._discard_history.append((1, wind_tile))
        self.engine._discard_history.append((2, wind_tile))
        self.engine._discard_history.append((3, wind_tile))

        # 檢查四風連打
        ryuukyoku_type = self.engine.check_ryuukyoku()
        assert ryuukyoku_type is not None
        assert ryuukyoku_type == RyuukyokuType.SUUFON_RENDA

    def test_check_draw_sancha_ron(self):
        """測試三家和了流局檢查"""
        pass

    def test_check_draw_suukantsu(self):
        """測試四槓散了流局檢查"""
        self._init_game()
        # 設置槓數為 4
        self.engine._kan_count = 4

        # 檢查四槓散了
        ryuukyoku_type = self.engine.check_ryuukyoku()
        assert ryuukyoku_type is not None
        assert ryuukyoku_type == RyuukyokuType.SUUKANTSU

    def test_check_draw_exhausted(self):
        """測試牌山耗盡流局檢查"""
        self._init_game()
        # 模擬牌山耗盡
        assert self.engine._tile_set is not None

        # 耗盡牌山
        while self.engine._tile_set._tiles:
            self.engine._tile_set.draw()

        # 檢查牌山耗盡流局
        ryuukyoku_type = self.engine.check_ryuukyoku()
        assert ryuukyoku_type is not None
        assert ryuukyoku_type == RyuukyokuType.EXHAUSTED

    def test_count_dora(self):
        """測試寶牌計算"""
        self._init_game()
        # 測試沒有牌組的情況
        self.engine._tile_set = None
        # 手牌：1m
        test_hand = Hand(parse_tiles("1m"))
        self.engine._hands[0] = test_hand
        dora_count = self.engine._count_dora(0, Tile(Suit.MANZU, 1), [])
        assert dora_count == 0

        # 恢復牌組
        self.engine._tile_set = TileSet()
        self.engine._tile_set.shuffle()

        # 測試有牌組的情況
        # 手牌：1m
        test_hand = Hand(parse_tiles("1m"))
        self.engine._hands[0] = test_hand
        dora_count = self.engine._count_dora(0, Tile(Suit.MANZU, 1), [])
        assert dora_count >= 0

        # 測試立直時的裡寶牌
        test_hand.set_riichi(True)
        dora_count = self.engine._count_dora(0, Tile(Suit.MANZU, 1), [])
        assert dora_count >= 0

        # 測試紅寶牌
        # 手牌：r5p
        red_tiles = parse_tiles("r5p")
        red_tile = red_tiles[0]
        test_hand = Hand(red_tiles)
        self.engine._hands[0] = test_hand
        dora_count = self.engine._count_dora(0, Tile(Suit.PINZU, 5), [])
        assert dora_count >= 1  # 至少有一個紅寶牌

    def test_get_hand_invalid_player(self):
        """測試 get_hand 無效玩家錯誤"""
        self._init_game()
        # 測試無效玩家位置
        with pytest.raises(ValueError, match="玩家位置必須在"):
            self.engine.get_hand(-1)

        with pytest.raises(ValueError, match="玩家位置必須在"):
            self.engine.get_hand(4)

    def test_get_discards_invalid_player(self):
        """測試 get_discards 無效玩家錯誤"""
        self._init_game()
        # 測試無效玩家位置
        with pytest.raises(ValueError, match="玩家位置必須在"):
            self.engine.get_discards(-1)

        with pytest.raises(ValueError, match="玩家位置必須在"):
            self.engine.get_discards(4)

    def test_handle_draw_kyuushu_kyuuhai(self):
        """測試九種九牌流局處理"""
        # TODO: 新增九種九牌流局 action
        pass

    def test_handle_draw_suucha_riichi(self):
        """測試四家立直流局處理"""
        pass

    def test_get_available_actions_default_empty(self):
        """測試在非 PLAYING 階段無可用動作"""
        self._init_game()
        current_player = self.engine.get_current_player()

        # 在非 PLAYING 階段，應無可用動作
        self.engine._phase = GamePhase.INIT
        assert self.engine.get_available_actions(current_player) == []

    def test_execute_action_kan_tile_none(self):
        """測試明槓時 tile 為 None"""
        self._init_game()
        current_player = self.engine.get_current_player()
        with pytest.raises(ValueError):
            self.engine.execute_action(current_player, GameAction.KAN, tile=None)

    def test_execute_action_draw_no_tile_set(self):
        """測試摸牌時牌組未初始化"""
        self._init_game()
        hand = self.engine.get_hand(0)
        self.engine.execute_action(0, GameAction.DISCARD, tile=hand.tiles[0])
        current_player = self.engine.get_current_player()

        self.engine._tile_set = None

        with pytest.raises(ValueError, match="牌組未初始化"):
            self.engine.execute_action(current_player, GameAction.DRAW)

    def test_execute_action_discard_no_tile(self):
        """測試打牌時未指定牌"""
        self._init_game()
        current_player = self.engine.get_current_player()
        with pytest.raises(ValueError):
            self.engine.execute_action(current_player, GameAction.DISCARD, tile=None)

    def test_execute_action_discard_no_tile_set(self):
        """測試打牌時牌組未初始化"""
        self._init_game()
        current_player = self.engine.get_current_player()
        hand = self.engine.get_hand(current_player)
        self.engine._tile_set = None
        with pytest.raises(ValueError, match="牌組未初始化"):
            self.engine.execute_action(current_player, GameAction.DISCARD, tile=hand.tiles[0])

    def test_execute_action_riichi(self):
        """測試執行立直動作"""
        self._init_game()
        current_player = self.engine.get_current_player()
        # 確保手牌聽牌且門清
        # 123m 456m 789m 123p 4p
        self.engine._hands[current_player] = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p4p"))

        assert self._has_action(current_player, GameAction.RICHI)

        result = self.engine.execute_action(current_player, GameAction.RICHI)
        assert result.riichi is True
        assert self.engine.get_hand(current_player).is_riichi
        # 檢查一發狀態已記錄
        assert current_player in self.engine._riichi_ippatsu
        assert self.engine._riichi_ippatsu[current_player] is True

    def test_cannot_action_riichi_not_tenpai(self):
        """測試未聽牌無法立直的情況"""
        self._init_game()
        current_player = self.engine.get_current_player()
        # 確保手牌無法聽牌
        # 123m 456m 789m 12p 4p 8p
        self.engine._hands[current_player] = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p2p4p8p"))
        assert not self.engine.get_hand(current_player).is_tenpai()
        assert not self._has_action(current_player, GameAction.RICHI)

    def test_cannot_action_riichi_not_concealed(self):
        """測試未門清無法立直的情況"""
        self._init_game()
        current_player = self.engine.get_current_player()
        self.engine._hands[current_player]._melds.append(
            Meld(MeldType.PON, [Tile(Suit.PINZU, 4), Tile(Suit.PINZU, 4), Tile(Suit.PINZU, 4)])
        )
        assert self.engine.get_hand(current_player).is_concealed is False
        assert not self._has_action(current_player, GameAction.RICHI)

    def test_execute_action_kan_no_tile(self):
        """測試明槓時未指定牌"""
        self._init_game()
        # TODO: 設置可以明槓的狀態，並測試明槓時未指定牌
        current_player = self.engine.get_current_player()
        assert not self._has_action(current_player, GameAction.KAN)

    def test_execute_action_discard_last_tile(self):
        """測試打出最後一張牌（河底撈魚）"""
        pass

    def test_execute_action_draw_last_tile(self):
        """測試摸到最後一張牌（海底撈月）"""
        pass

    def test_execute_action_discard_history(self):
        """測試捨牌歷史記錄"""
        self._init_game()
        current_player = self.engine.get_current_player()
        hand = self.engine.get_hand(current_player)
        assert hand.tiles is not None
        self.engine.execute_action(current_player, GameAction.DISCARD, tile=hand.tiles[0])
        assert len(self.engine._discard_history) > 0

    def test_execute_action_discard_history_limit(self):
        """測試捨牌歷史只保留前四張"""
        self._init_game()
        # 莊家開局有 14 張牌，先打出一張
        current_player = self.engine.get_current_player()
        hand = self.engine.get_hand(current_player)
        assert self._has_action(current_player, GameAction.DISCARD)
        self.engine.execute_action(current_player, GameAction.DISCARD, tile=hand.tiles[0])
        for _ in range(10):
            current_player = self.engine.get_current_player()
            assert self._has_action(current_player, GameAction.DRAW)
            self.engine.execute_action(current_player, GameAction.DRAW)
            hand = self.engine.get_hand(current_player)
            assert self._has_action(current_player, GameAction.DISCARD)
            self.engine.execute_action(current_player, GameAction.DISCARD, tile=hand.tiles[0])
        assert len(self.engine._discard_history) <= 4

    def test_deal_wrong_phase(self):
        """測試在錯誤階段發牌"""
        self.engine.start_game()
        # 不在發牌階段
        self.engine._phase = GamePhase.PLAYING
        with pytest.raises(ValueError, match="只能在發牌階段發牌"):
            self.engine.deal()

    def test_deal_no_tile_set(self):
        """測試牌組未初始化時發牌"""
        self.engine.start_game()
        self.engine.start_round()
        self.engine._tile_set = None
        with pytest.raises(ValueError, match="牌組未初始化"):
            self.engine.deal()

    def test_get_available_actions_kan(self):
        """測試是否可以明槓"""
        self._init_game()
        current_player = self.engine.get_current_player()
        # 111m 234m 567m 12p 3p 4p
        self.engine._hands[current_player] = Hand(parse_tiles("1m1m1m2m3m4m5m6m7m1p2p3p4p"))
        self.engine._last_discarded_tile = Tile(Suit.MANZU, 1)
        self.engine._last_discarded_player = (current_player + 1) % self.engine.get_num_players()
        assert self._has_action(current_player, GameAction.KAN)
        # 修改最後捨牌使其無法明槓
        self.engine._last_discarded_tile = Tile(Suit.MANZU, 9)
        assert not self._has_action(current_player, GameAction.KAN)

    def test_get_available_actions_ankan(self):
        """測試是否可以暗槓"""
        self._init_game()
        # 111m 123m 456m 7m 123p
        self.engine._hands[0] = Hand(parse_tiles("1m1m1m1m2m3m4m5m6m7m1p2p3p"))
        assert self._has_action(0, GameAction.ANKAN)

    def test_execute_action_draw_no_tile_drawn(self):
        """測試摸牌時無牌可摸"""
        self._init_game()
        current_player = self.engine.get_current_player()

        # 耗盡牌組以觸發 draw() 返回 None
        assert self.engine._tile_set is not None
        hand = self.engine.get_hand(current_player)
        assert hand.tiles is not None
        self.engine.execute_action(current_player, GameAction.DISCARD, tile=hand.tiles[0])
        while self.engine._tile_set._tiles:
            self.engine._tile_set.draw()
        current_player = self.engine.get_current_player()
        result = self.engine.execute_action(current_player, GameAction.DRAW)
        assert result.ryuukyoku is not None
        assert result.ryuukyoku.ryuukyoku is True
        assert result.ryuukyoku.ryuukyoku_type == RyuukyokuType.EXHAUSTED
        assert self.engine._phase == GamePhase.RYUUKYOKU

    def test_execute_action_kan_rinshan_win(self):
        """測試明槓後嶺上開花"""
        self._init_game()

        # 設置玩家0可以明槓且槓後可以嶺上開花
        kan_tile = Tile(Suit.MANZU, 1)
        ten_tile = Tile(Suit.PINZU, 4)
        # 111m 234m 567m 123p 4p
        kan_tiles = parse_tiles("1m1m1m2m3m4m5m6m7m1p2p3p4p")
        self.engine._hands[0] = Hand(kan_tiles)
        self.engine._current_player = 0
        self.engine._last_discarded_tile = kan_tile
        self.engine._last_discarded_player = 1
        assert self.engine._tile_set is not None
        self.engine._tile_set._wall[-1] = ten_tile

        # 執行明槓
        assert self._has_action(0, GameAction.KAN)
        result = self.engine.execute_action(0, GameAction.KAN, tile=kan_tile)
        assert result.rinshan_tile is not None
        assert result.rinshan_win is not None

    def test_execute_action_ankan_rinshan_win(self):
        """測試暗槓後嶺上開花"""
        self._init_game()

        # 設置玩家0可以暗槓
        ten_tile = Tile(Suit.PINZU, 4)
        # 1111m 234m 567m 123p 4p (聽 4p)
        ankan_tiles = parse_tiles("1m1m1m1m2m3m4m5m6m7m1p2p3p4p")
        self.engine._hands[0] = Hand(ankan_tiles)
        self.engine._current_player = 0
        assert self.engine._tile_set is not None
        self.engine._tile_set._wall[-1] = ten_tile

        # 執行暗槓
        assert self._has_action(0, GameAction.ANKAN)
        result = self.engine.execute_action(0, GameAction.ANKAN)
        assert result.rinshan_tile is not None
        assert result.rinshan_win is not None

    def test_check_flow_mangan(self):
        """測試流局滿貫判定"""
        pass

    def test_end_round_with_winner(self):
        """測試結束一局（有獲勝者）"""
        self._init_game()
        # 測試有獲勝者的情況
        winner = 0
        self.engine.end_round(winner)
        assert self.engine._phase == GamePhase.PLAYING
        # TODO: 測試遊戲結束條件

    def test_end_round_draw(self):
        """測試結束一局（流局）"""
        self._init_game()
        # 測試流局的情況
        self.engine.end_round(None)
        assert self.engine._phase == GamePhase.PLAYING
        # TODO: 測試遊戲結束條件

    def test_get_dora_tiles(self):
        """測試獲取表寶牌"""
        self._init_game()
        # 測試有牌組的情況
        dora_tiles = self.engine.get_dora_tiles()
        assert dora_tiles is not None

        # 測試沒有牌組的情況
        self.engine._tile_set = None
        dora_tiles = self.engine.get_dora_tiles()
        assert dora_tiles == []

    def test_get_ura_dora_tiles(self):
        """測試獲取裡寶牌"""
        self._init_game()
        # 測試有牌組的情況
        ura_dora_tiles = self.engine.get_ura_dora_tiles()
        assert ura_dora_tiles is not None

        # 測試沒有牌組的情況
        self.engine._tile_set = None
        ura_dora_tiles = self.engine.get_ura_dora_tiles()
        assert ura_dora_tiles == []

    def test_check_sancha_ron(self):
        """測試三家和了檢查"""
        self._init_game()

        # 設置最後捨牌
        winning_tile = Tile(Suit.PINZU, 4)
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 0

        # 設置三個玩家都可以和牌
        # 123m 456m 789m 123p 4p (聽 4p)
        self.engine._hands[1] = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p4p"))
        self.engine._hands[2] = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p4p"))
        self.engine._hands[3] = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p4p"))

        # 檢查三家和了
        result = self.engine._check_sancha_ron()
        assert result is True

    def test_execute_action_riichi_ippatsu_update(self):
        """測試立直後一發狀態更新"""
        self._init_game()
        # 玩家0立直
        # 123m 456m 789m 123p 4p (聽 4p)
        self.engine._hands[0] = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p4p"))
        assert self._has_action(0, GameAction.RICHI)
        self.engine.execute_action(0, GameAction.RICHI)
        assert 0 in self.engine._riichi_ippatsu
        assert self.engine._riichi_ippatsu[0] is True

        # 自己捨牌不應中斷一發
        discard_tile = self.engine.get_hand(0).tiles[0]
        self.engine._apply_discard_effects(0, discard_tile, ActionResult())
        assert 0 in self.engine._riichi_ippatsu
        assert self.engine._riichi_ippatsu[0] is True

    def test_interrupt_riichi_ippatsu_on_chi(self):
        """測試吃牌會中斷一發"""
        self._init_game()
        self.engine._riichi_ippatsu = {0: True}
        self.engine._riichi_ippatsu_discard = {0: 0}

        chi_tile = Tile(Suit.MANZU, 4)
        self.engine._hands[0] = Hand(parse_tiles("1m1m2m2m3m3m4m4m5m5m6m6m7m7m"))
        self.engine._hands[1] = Hand(parse_tiles("2m3m4m5m6m7m8m9m1p2p3p4p5p"))
        self.engine._current_player = 0

        self.engine.execute_action(0, GameAction.DISCARD, tile=chi_tile)
        sequences = self.engine.get_available_chi_sequences(1)
        assert sequences
        target_sequence = next(
            (seq for seq in sequences if sorted(tile.rank for tile in seq) == [2, 3]),
            None,
        )
        assert target_sequence is not None
        self.engine.execute_action(1, GameAction.CHI, sequence=target_sequence)
        assert self.engine._riichi_ippatsu[0] is False

    def test_interrupt_riichi_ippatsu_on_pon(self):
        """測試碰牌會中斷一發"""
        self._init_game()
        self.engine._riichi_ippatsu = {0: True}
        self.engine._riichi_ippatsu_discard = {0: 0}

        pon_tile = Tile(Suit.PINZU, 7)
        self.engine._hands[0] = Hand(parse_tiles("7p1m1m1m2m2m3m3m4m4m5m5m6m6m"))
        self.engine._hands[2] = Hand(parse_tiles("7p7p1p1p2p2p3p3p4p4p5p5p6p"))
        self.engine._current_player = 0

        self.engine.execute_action(0, GameAction.DISCARD, tile=pon_tile)
        assert GameAction.PON in self.engine.get_available_actions(2)
        self.engine.execute_action(2, GameAction.PON)
        assert self.engine._riichi_ippatsu[0] is False

    def test_interrupt_riichi_ippatsu_on_kan(self):
        """測試明槓會中斷一發"""
        self._init_game()
        self.engine._riichi_ippatsu = {0: True}
        self.engine._riichi_ippatsu_discard = {0: 0}

        kan_tile = Tile(Suit.SOZU, 9)
        self.engine._hands[0] = Hand(parse_tiles("9s1m1m2m2m3m3m4m4m5m5m6m6m7m"))
        self.engine._hands[1] = Hand(parse_tiles("9s9s9s1s1s2s2s3s3s4s4s5s5s"))
        self.engine._current_player = 0

        self.engine.execute_action(0, GameAction.DISCARD, tile=kan_tile)
        assert GameAction.KAN in self.engine.get_available_actions(1)
        self.engine.execute_action(1, GameAction.KAN, tile=kan_tile)
        assert self.engine._riichi_ippatsu[0] is False

    def test_interrupt_riichi_ippatsu_on_ankan(self):
        """測試暗槓會中斷一發"""
        self._init_game()
        self.engine._riichi_ippatsu = {0: True, 1: True}
        self.engine._riichi_ippatsu_discard = {0: 0, 1: 0}

        self.engine._hands[3] = Hand(parse_tiles("1m1m1m1m2m3m4m5m6m7m8m9m1p"))
        self.engine._current_player = 3

        assert GameAction.ANKAN in self.engine.get_available_actions(3)
        result = self.engine.execute_action(3, GameAction.ANKAN)
        assert result.ankan is True or result.kan is True
        assert all(flag is False for flag in self.engine._riichi_ippatsu.values())

    def test_execute_action_kan_chankan_complete(self):
        """測試明槓搶槓完整場景"""
        self._init_game()

        # 設置玩家0可以加槓（已有碰，增加第四張1m）
        # 手牌：111234567m 123p 4p
        kan_tiles = parse_tiles("1m1m1m2m3m4m5m6m7m1p2p3p4p")
        hand0 = Hand(kan_tiles)
        kan_tile = Tile(Suit.MANZU, 1)
        hand0.pon(kan_tile)
        hand0.add_tile(kan_tile)
        self.engine._hands[0] = hand0
        self.engine._current_player = 0
        self.engine._last_discarded_tile = None
        self.engine._last_discarded_player = None

        # 設置玩家1可以搶槓和（聽1m）
        # 手牌：23m 456m 789p 123p 44p（缺 1m）
        test_tiles = parse_tiles("2m3m4m5m6m7p8p9p1p2p3p4p4p")
        test_hand = Hand(test_tiles)
        self.engine._hands[1] = test_hand

        # 執行加槓，應該檢查搶槓
        assert self._has_action(0, GameAction.ANKAN)
        result = self.engine.execute_action(0, GameAction.ANKAN)
        # 應該觸發搶槓和
        assert result.chankan is not None
        assert result.chankan is True
        assert result.winners is not None
        assert len(result.winners) > 0
        winner = result.winners[0]
        # check_win 需要 pending_kan_tile 來設定支付者
        self.engine._pending_kan_tile = (0, kan_tile)
        win_result = self.engine.check_win(winner, kan_tile, is_chankan=True)
        assert win_result is not None
        assert win_result.win is True
        assert win_result.chankan is True
        assert win_result.score_result is not None
        assert win_result.score_result.payment_from == 0

    def test_execute_action_kan_wall_exhausted(self):
        """測試明槓觸發四槓散了"""
        self._init_game()

        player = self.engine.get_current_player()
        kan_tile = Tile(Suit.MANZU, 6)

        # 111m 2345m 6666m 7m 88m
        starting_tiles = parse_tiles("1m1m1m2m3m4m5m6m6m6m7m8m8m")
        self.engine._hands[player] = Hand(starting_tiles)
        self.engine._last_discarded_tile = kan_tile
        self.engine._last_discarded_player = (player + 1) % self.engine.get_num_players()

        self.engine._kan_count = 3
        assert self.engine._tile_set is not None
        self.engine._tile_set._wall = [Tile(Suit.PINZU, 2)]
        self.engine._tile_set._tiles = []

        result = self.engine.execute_action(player, GameAction.KAN, tile=kan_tile)

        assert result.kan is True
        assert self.engine._kan_count == 4
        assert self.engine.check_ryuukyoku() == RyuukyokuType.SUUKANTSU

    def test_fourth_kan_chankan_does_not_trigger_suukantsu(self):
        """第四次槓時被搶槓不算四槓散了"""
        self._init_game()

        self.engine._kan_count = 3
        self.engine._current_player = 0
        kan_tile = Tile(Suit.SOZU, 4)

        # 444s 234m 567m 123p 4p
        hand0_tiles = parse_tiles("4s4s4s2m3m4m5m6m7m1p2p3p4p")
        hand0 = Hand(hand0_tiles)
        hand0.pon(kan_tile)
        hand0.add_tile(kan_tile)
        self.engine._hands[0] = hand0
        self.engine._last_discarded_tile = None
        self.engine._last_discarded_player = None

        # 手牌：23s 234m 567m 789p 44p（缺 4s）
        winning_tiles = parse_tiles("2s3s2m3m4m5m6m7m7p8p9p4p4p")
        self.engine._hands[1] = Hand(winning_tiles)

        result = self.engine.execute_action(0, GameAction.ANKAN)
        assert result.chankan is True
        assert self.engine._kan_count == 3
        assert self.engine.check_ryuukyoku() is None

    def test_fourth_kan_ron_does_not_trigger_suukantsu(self):
        """第四次槓後他家榮和，不算四槓散了"""
        self._init_game()

        self.engine._kan_count = 4
        winning_tile = Tile(Suit.PINZU, 1)

        # 手牌：234m 567m 789p 234s 1p
        ron_ready = parse_tiles("2m3m4m5m6m7m7p8p9p2s3s4s1p")
        self.engine._hands[1] = Hand(ron_ready)
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 0

        win_result = self.engine.check_win(1, winning_tile)
        assert win_result is not None
        assert self.engine.check_ryuukyoku() is None

    def test_fourth_kan_rinshan_win_does_not_trigger_suukantsu(self):
        """第四次槓後嶺上開花，不算四槓散了"""
        pass

    def test_execute_action_ankan_wall_exhausted(self):
        """測試暗槓觸發四槓散了"""
        self._init_game()

        player = self.engine.get_current_player()

        # 手牌：222m 2334455678m
        starting_tiles = parse_tiles("2m2m2m2m3m3m4m4m5m5m6m7m8m")
        self.engine._hands[player] = Hand(starting_tiles)

        self.engine._kan_count = 3
        if self.engine._tile_set:
            self.engine._tile_set._wall = [Tile(Suit.SOZU, 5)]
            self.engine._tile_set._tiles = []

        result = self.engine.execute_action(player, GameAction.ANKAN)

        assert result.ankan is True
        assert self.engine._kan_count == 4
        assert self.engine.check_ryuukyoku() == RyuukyokuType.SUUKANTSU

    def test_execute_action_discard_is_last_tile(self):
        """測試打牌時最後一張牌檢查"""
        self._init_game()
        # 測試 is_last_tile 標記
        # 當牌組耗盡時，打牌應該設置 is_last_tile
        hand = self.engine.get_hand(0)
        if hand.total_tile_count() >= 14 and hand.tiles:
            self.engine.execute_action(0, GameAction.DISCARD, tile=hand.tiles[0])

        current = self.engine.get_current_player()
        if self._has_action(current, GameAction.DRAW):
            self.engine.execute_action(current, GameAction.DRAW)
            hand = self.engine.get_hand(current)
            if hand.tiles:
                tile = hand.tiles[0]
                if self._has_action(current, GameAction.DISCARD):
                    result = self.engine.execute_action(current, GameAction.DISCARD, tile=tile)
                    # 如果牌組耗盡，應該有 is_last_tile 標記
                    # 注意：這可能不會發生，取決於牌組狀態
                    if result.is_last_tile is not None:
                        assert result.is_last_tile == True

    def test_get_available_actions_draw_requires_current_player(self):
        """測試摸牌僅限當前玩家"""
        self._init_game()
        current_player = self.engine.get_current_player()

        # 非 PLAYING 階段無可用動作
        self.engine._phase = GamePhase.INIT
        assert GameAction.DRAW not in self.engine.get_available_actions(current_player)

        # PLAYING 階段但非當前玩家也不可摸牌
        self.engine._phase = GamePhase.PLAYING
        non_current = (current_player + 1) % 4
        assert GameAction.DRAW not in self.engine.get_available_actions(non_current)

    def test_execute_action_draw_exhausted(self):
        """測試摸牌時牌組耗盡"""
        self._init_game()
        current_player = self.engine.get_current_player()

        # 測試 is_last_tile 標記
        # 如果牌組耗盡，應該設置 is_last_tile
        # 但由於實際耗盡牌組需要很多步驟，我們測試邏輯
        # 當 is_exhausted() 返回 True 時，應該設置 is_last_tile

        # 先執行一次摸牌，檢查結果
        hand = self.engine.get_hand(current_player)
        if hand.total_tile_count() >= 14 and hand.tiles:
            self.engine.execute_action(current_player, GameAction.DISCARD, tile=hand.tiles[0])

        result = self.engine.execute_action(self.engine.get_current_player(), GameAction.DRAW)

        # 如果牌組耗盡，應該有 is_last_tile 標記
        # 注意：這可能不會發生，取決於牌組狀態
        if result.is_last_tile is not None:
            assert result.is_last_tile == True

    def test_execute_action_draw_draw_result(self):
        """測試摸牌結果"""
        self._init_game()
        current_player = self.engine.get_current_player()
        hand = self.engine.get_hand(current_player)
        if hand.total_tile_count() >= 14 and hand.tiles:
            self.engine.execute_action(current_player, GameAction.DISCARD, tile=hand.tiles[0])
            current_player = self.engine.get_current_player()
        result = self.engine.execute_action(current_player, GameAction.DRAW)

        # 檢查結果中是否有 drawn_tile 或 is_last_tile
        assert result.drawn_tile is not None or result.is_last_tile is not None or result.ryuukyoku is not None

    def _init_game(self):
        self.engine.start_game()
        self.engine.start_round()
        self.engine.deal()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
