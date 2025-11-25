"""
RuleEngine 的單元測試
"""

import pytest
from pyriichi.hand import Hand, Meld, MeldType
from pyriichi.rules import ActionResult, RuleEngine, GameAction, GamePhase, RyuukyokuType, RyuukyokuResult
from pyriichi.tiles import Tile, Suit
from pyriichi.yaku import Yaku
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
        self._init_game()

        # 設置玩家0可以搶槓和（聽6p，斷么九）
        # 手牌：234m 567m 234p 66p 78p（聽 6p/9p）
        test_tiles = parse_tiles("2m3m4m5m6m7m2p3p4p6p6p7p8p")
        self.engine._hands[0] = Hand(test_tiles)

        # 檢查搶槓
        kan_tile = Tile(Suit.PINZU, 6)

        # check_win 需要 pending_kan_tile 來設定支付者
        # 假設玩家1加槓 6p
        self.engine._pending_kan_tile = (1, kan_tile)

        result = self.engine.check_win(0, kan_tile, is_chankan=True)
        assert result is not None
        assert result.win is True
        assert result.chankan is True
        assert result.score_result.payment_from == 1

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
        # 33m 567p 89p 456s 789s
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
        # 23m 56m 678p 9p 678s 9s 5s
        self.engine._hands[1] = Hand(parse_tiles("2m3m5m6m6p7p8p9p6s7s8s9s5s"))
        # 11m 11p 112345678s
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
        # 11m 123m 456p 77s 8s 99s
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
        # 123m 456m 78m 123p 45p
        test_tiles = parse_tiles("1m2m3m4m5m6m7m8m1p2p3p4p5p")
        test_hand = Hand(test_tiles)
        self.engine._hands[0] = test_hand

        # 檢查和牌（應該返回 None，因為沒有和牌組合）
        winning_tile = Tile(Suit.MANZU, 9)
        result = self.engine.check_win(0, winning_tile)
        assert result is None

    def test_check_win_no_yaku(self):
        """測試無役"""
        self._init_game()
        # 234m 567m 789m 2p 4p 22s
        tiles = parse_tiles("2m3m4m5m6m7m7m8m9m2p4p2s2s")

        hand = Hand(tiles)
        # 將手牌設為非門清
        hand._melds.append(Meld(MeldType.PON, parse_tiles("1s1s1s")))
        # 設定最後捨牌為 3p，測試榮和
        winning_tile = Tile(Suit.PINZU, 3)
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1

        # 將手牌放到玩家0
        self.engine._hands[0] = hand
        self.engine._current_player = 2

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
        self._init_game()

        # 設置三家和了允許流局
        self.engine._game_state.ruleset.allow_triple_ron = False

        # 設置最後捨牌
        winning_tile = Tile(Suit.PINZU, 4)
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 0

        # 設置三個玩家都可以和牌
        # 123m 456m 789m 123p 4p (聽 4p)
        tenpai_hand = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p4p"))
        self.engine._hands[1] = tenpai_hand
        self.engine._hands[2] = tenpai_hand
        self.engine._hands[3] = tenpai_hand

        # 檢查流局
        ryuukyoku_type = self.engine.check_ryuukyoku()
        assert ryuukyoku_type == RyuukyokuType.SANCHA_RON

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

    def test_count_dora_zero(self):
        """測試無寶牌計算"""
        self._init_game()
        self.engine._hands[0] = Hand(parse_tiles("1m1m1m1m2m3m4m5m6m7m9m9m9m"))
        dora_count = self.engine._count_dora(0, Tile(Suit.MANZU, 1))
        assert dora_count == 0

    def test_count_dora_one(self):
        """測試有寶牌計算"""
        self._init_game()
        test_hand = Hand(parse_tiles("1m1m1m1m2m3m4m5m6m7m9m9m9m"))
        self.engine._hands[0] = test_hand
        dora_count = self.engine._count_dora(0, Tile(Suit.MANZU, 1))
        assert dora_count >= 0

        # 測試立直時的裡寶牌
        test_hand.set_riichi(True)
        dora_count = self.engine._count_dora(0, Tile(Suit.MANZU, 1))
        assert dora_count >= 0

        # 測試紅寶牌
        # 手牌：r5p
        red_tiles = parse_tiles("r5p")
        red_tile = red_tiles[0]
        test_hand = Hand(red_tiles)
        self.engine._hands[0] = test_hand
        dora_count = self.engine._count_dora(0, Tile(Suit.PINZU, 5))
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
        self._init_game()
        player = self.engine.get_current_player()

        # 設置九種九牌
        tiles = parse_tiles("1m9m1p9p1s9s1z2z3z4z5z6z7z1m")
        self.engine._hands[player] = Hand(tiles)
        self.engine._is_first_turn_after_deal = True

        # 執行動作
        result = self.engine.execute_action(player, GameAction.KYUUSHU_KYUUHAI)

        assert result.ryuukyoku is not None
        assert result.ryuukyoku.ryuukyoku is True
        assert result.ryuukyoku.ryuukyoku_type == RyuukyokuType.KYUUSHU_KYUUHAI
        assert result.ryuukyoku.kyuushu_kyuuhai_player == player

    def test_handle_draw_suucha_riichi(self):
        """測試四家立直流局處理"""
        self._init_game()

        # 設置所有玩家立直
        for i in range(4):
            self.engine._hands[i].set_riichi(True)

        # 檢查流局
        ryuukyoku_type = self.engine.check_ryuukyoku()
        assert ryuukyoku_type == RyuukyokuType.SUUCHA_RIICHI

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
        self._init_game()
        current_player = self.engine.get_current_player()
        hand = self.engine.get_hand(current_player)

        # 模擬牌山耗盡
        assert self.engine._tile_set is not None
        self.engine._tile_set._tiles = []

        result = self.engine.execute_action(current_player, GameAction.DISCARD, tile=hand.tiles[0])
        assert result.is_last_tile is True

    def test_execute_action_draw_last_tile(self):
        """測試摸到最後一張牌（海底撈月）"""
        self._init_game()
        current_player = self.engine.get_current_player()

        # 確保手牌少一張，以便可以摸牌
        hand = self.engine.get_hand(current_player)
        hand._tiles.pop()

        # 模擬牌山只剩一張
        assert self.engine._tile_set is not None
        self.engine._tile_set._tiles = [Tile(Suit.MANZU, 1)]

        result = self.engine.execute_action(current_player, GameAction.DRAW)
        assert result.is_last_tile is True

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
        self.engine._tile_set._rinshan_tiles[0] = ten_tile

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
        self.engine._tile_set._rinshan_tiles[0] = ten_tile

        # 執行暗槓
        assert self._has_action(0, GameAction.ANKAN)
        result = self.engine.execute_action(0, GameAction.ANKAN)
        assert result.rinshan_tile is not None
        assert result.rinshan_win is not None

    def test_check_nagashi_mangan(self):
        """測試流局滿貫判定"""
        self._init_game()
        player = 0

        # 1. 正常流局滿貫：捨牌全為幺九牌，且未被鳴牌
        yaochuu_tiles = [
            Tile(Suit.MANZU, 1), Tile(Suit.MANZU, 9),
            Tile(Suit.PINZU, 1), Tile(Suit.PINZU, 9),
            Tile(Suit.SOZU, 1), Tile(Suit.SOZU, 9),
            Tile(Suit.JIHAI, 1), Tile(Suit.JIHAI, 2),
            Tile(Suit.JIHAI, 3), Tile(Suit.JIHAI, 4),
            Tile(Suit.JIHAI, 5), Tile(Suit.JIHAI, 6),
            Tile(Suit.JIHAI, 7)
        ]

        self.engine._hands[player]._discards = yaochuu_tiles
        self.engine._has_called_discard[player] = False
        assert self.engine._check_nagashi_mangan(player) is True

        # 2. 失敗情況：有非幺九牌
        self.engine._hands[player]._discards.append(Tile(Suit.MANZU, 5))
        assert self.engine._check_nagashi_mangan(player) is False

        # 3. 失敗情況：捨牌被鳴牌
        self.engine._hands[player]._discards = yaochuu_tiles  # 重置為全幺九
        self.engine._has_called_discard[player] = True
        assert self.engine._check_nagashi_mangan(player) is False

    def test_end_round_with_winner(self):
        """測試結束一局（有獲勝者）"""
        self._init_game()
        # 測試有獲勝者的情況
        winner = 0
        self.engine.end_round([winner])
        assert self.engine._phase == GamePhase.PLAYING
        # TODO: 測試遊戲結束條件

    def test_end_round_draw(self):
        """測試結束一局（流局）"""
        self._init_game()
        # 測試流局的情況
        self.engine.end_round(None)
        assert self.engine._phase == GamePhase.PLAYING
        # TODO: 測試遊戲結束條件

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
        self._init_game()

        self.engine._kan_count = 3
        player = self.engine.get_current_player()

        # 設置嶺上開花
        # 1. 設置手牌可以槓 (需要4張相同的牌)
        kan_tile = Tile(Suit.MANZU, 1)
        # 1111m 234m 567m 123p 4p
        hand_tiles = parse_tiles("1m1m1m1m2m3m4m5m6m7m1p2p3p4p")
        self.engine._hands[player] = Hand(hand_tiles)

        # 2. 設置嶺上牌為和牌牌 (4p) - 聽 1p/4p
        rinshan_tile = Tile(Suit.PINZU, 4)
        assert self.engine._tile_set is not None
        self.engine._tile_set._rinshan_tiles[0] = rinshan_tile

        # 3. 執行暗槓
        result = self.engine.execute_action(player, GameAction.ANKAN)

        # 4. 驗證嶺上開花
        assert result.rinshan_win is not None
        assert result.rinshan_win.win is True

        # 5. 驗證不觸發四槓散了
        assert self.engine.check_ryuukyoku() is None

    def test_execute_action_ankan_wall_exhausted(self):
        """測試暗槓觸發四槓散了"""
        self._init_game()

        player = self.engine.get_current_player()

        # 手牌：222m 2334455678m
        starting_tiles = parse_tiles("2m2m2m2m3m3m4m4m5m5m6m7m8m")
        self.engine._hands[player] = Hand(starting_tiles)

        self.engine._kan_count = 3
        assert self.engine._tile_set is not None
        self.engine._tile_set._wall = [Tile(Suit.SOZU, 5)]
        self.engine._tile_set._tiles = []
        # 確保嶺上牌不是和牌牌（手牌聽牌型比較特殊，給一個無關的字牌確保不和）
        self.engine._tile_set._rinshan_tiles = [Tile(Suit.JIHAI, 1)] * 4

        result = self.engine.execute_action(player, GameAction.ANKAN)

        assert result.ankan is True
        assert self.engine._kan_count == 4
        assert self.engine.check_ryuukyoku() == RyuukyokuType.SUUKANTSU

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

    def test_execute_action_discard_is_last_tile(self):
        """測試摸牌最後一張牌檢查"""
        self._init_game()
        current_player = self.engine.get_current_player()
        hand = self.engine.get_hand(current_player)
        assert hand.tiles
        assert hand.total_tile_count() == 14
        self.engine.execute_action(current_player, GameAction.DISCARD, tile=hand.tiles[0])

        # 模擬牌山只剩一張牌
        assert self.engine._tile_set is not None
        self.engine._tile_set._tiles = [Tile(Suit.MANZU, 1)]

        current_player = self.engine.get_current_player()
        result = self.engine.execute_action(current_player, GameAction.DRAW)
        assert result.is_last_tile is True

    def test_execute_action_draw_exhausted(self):
        """測試捨牌時牌組耗盡"""
        self._init_game()

        # 模擬牌山耗盡
        assert self.engine._tile_set is not None
        self.engine._tile_set._tiles = []

        current_player = self.engine.get_current_player()
        hand = self.engine.get_hand(current_player)
        assert hand.tiles
        assert hand.total_tile_count() == 14
        result = self.engine.execute_action(current_player, GameAction.DISCARD, tile=hand.tiles[0])
        assert result.is_last_tile is True

    def test_furiten_discards_cannot_ron(self):
        """測試現物振聽：玩家打過的牌在聽牌牌中，不能榮和"""
        self._init_game()

        # 設置玩家0聽牌（聽 3p）
        # 手牌：123m 456m 789m 12p 33p (聽3p)
        tiles = parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p3p")
        self.engine._hands[0] = Hand(tiles)

        # 玩家0之前打過 3p（現在在捨牌堆中）
        discard_tile = Tile(Suit.PINZU, 3)
        self.engine._hands[0]._discards.append(discard_tile)

        # 其他玩家打出 3p
        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0
        self.engine._last_drawn_tile = None

        # 檢查振聽狀態
        assert self.engine.check_furiten_discards(0) is True
        assert self.engine.is_furiten(0) is True

        # 嘗試榮和，應該失敗
        result = self.engine.check_win(0, discard_tile)
        assert result is None or result.win is False

    def test_furiten_discards_can_tsumo(self):
        """測試現物振聽：雖然振聽，但可以自摸"""
        self._init_game()

        # 設置玩家0聽牌（聽 3p）
        # 手牌：123m 456m 789m 12p 33p (13張，聽3p)
        tiles = parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p3p")
        self.engine._hands[0] = Hand(tiles)

        # 玩家0之前打過 3p
        discard_tile = Tile(Suit.PINZU, 3)
        self.engine._hands[0]._discards.append(discard_tile)

        # 檢查振聽狀態（此時是13張，應該是振聽）
        assert self.engine.check_furiten_discards(0) is True

        # 模擬自摸 3p
        self.engine._current_player = 0
        self.engine._last_drawn_tile = (0, discard_tile)
        self.engine._last_discarded_tile = None

        # 自摸需要手牌有14張
        self.engine._hands[0].add_tile(discard_tile)

        # 自摸應該成功
        result = self.engine.check_win(0, discard_tile)
        assert result is not None
        assert result.win is True

    def test_furiten_temp_same_turn_cannot_ron(self):
        """測試同巡振聽：同巡內放過和牌機會後不能榮和"""
        self._init_game()

        # 設置玩家0聽牌（聽 4p）
        # 手牌：123m 456m 789m 123p 4p
        tiles = parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p4p")
        self.engine._hands[0] = Hand(tiles)

        winning_tile = Tile(Suit.PINZU, 4)

        # 設置同巡振聽狀態（玩家0在當前回合放過榮和）
        self.engine._furiten_temp[0] = True
        self.engine._furiten_temp_round[0] = self.engine._turn_count

        # 其他玩家打出 4p
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0
        self.engine._last_drawn_tile = None

        # 檢查振聽狀態
        assert self.engine.check_furiten_temp(0) is True
        assert self.engine.is_furiten(0) is True

        # 嘗試榮和，應該失敗
        result = self.engine.check_win(0, winning_tile)
        assert result is None or result.win is False

    def test_furiten_temp_next_turn_can_ron(self):
        """測試同巡振聽：下一巡可以榮和"""
        self._init_game()

        # 設置玩家0聽牌（聽 4p）
        tiles = parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p4p")
        self.engine._hands[0] = Hand(tiles)

        winning_tile = Tile(Suit.PINZU, 4)

        # 設置同巡振聽狀態（上一回合）
        self.engine._furiten_temp[0] = True
        self.engine._furiten_temp_round[0] = 0
        self.engine._turn_count = 2  # 已經過了兩巡

        # 其他玩家打出 4p
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0
        self.engine._last_drawn_tile = None

        # 檢查振聽狀態（不應該是同巡振聽）
        assert self.engine.check_furiten_temp(0) is False

        # 應該可以榮和（如果沒有其他振聽）
        # 注意：這裡只測試同巡振聽被解除，實際榮和還需要檢查其他條件

    def test_furiten_riichi_permanent(self):
        """測試立直振聽：立直後放過榮和，永久振聽"""
        self._init_game()

        # 設置玩家0立直且聽牌（聽 4p）
        tiles = parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p4p")
        self.engine._hands[0] = Hand(tiles)
        self.engine._hands[0].set_riichi(True)

        winning_tile = Tile(Suit.PINZU, 4)

        # 設置立直振聽狀態（玩家0在立直後放過榮和）
        self.engine._furiten_permanent[0] = True

        # 其他玩家打出 4p
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0
        self.engine._last_drawn_tile = None

        # 檢查振聽狀態
        assert self.engine.check_furiten_riichi(0) is True
        assert self.engine.is_furiten(0) is True

        # 嘗試榮和，應該失敗
        result = self.engine.check_win(0, winning_tile)
        assert result is None or result.win is False

    def test_furiten_riichi_can_tsumo(self):
        """測試立直振聽：雖然永久振聽，但可以自摸"""
        self._init_game()

        # 設置玩家0立直且聽牌（聽 4p）
        tiles = parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p4p4p")
        self.engine._hands[0] = Hand(tiles)
        self.engine._hands[0].set_riichi(True)

        winning_tile = Tile(Suit.PINZU, 4)

        # 設置立直振聽狀態
        self.engine._furiten_permanent[0] = True

        # 模擬自摸 4p
        self.engine._current_player = 0
        self.engine._last_drawn_tile = (0, winning_tile)
        self.engine._last_discarded_tile = None

        # 檢查振聽狀態（還是振聽）
        assert self.engine.check_furiten_riichi(0) is True

        # 自摸應該成功
        result = self.engine.check_win(0, winning_tile)
        assert result is not None
        assert result.win is True

    def test_furiten_not_tenpai_returns_false(self):
        """測試未聽牌時振聽檢查返回 False"""
        self._init_game()

        # 設置玩家0不聽牌
        tiles = parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p4p5p")
        self.engine._hands[0] = Hand(tiles)

        # 檢查振聽狀態（未聽牌不算振聽）
        assert self.engine.check_furiten_discards(0) is False
        assert self.engine.is_furiten(0) is False

    def test_furiten_multiple_waiting_tiles(self):
        """測試多面聽牌時的現物振聽"""
        self._init_game()

        # 設置玩家0多面聽（聽 4p 5p）
        # 手牌：123m 456m 789m 44p 55p (雙碰聽 4p 5p)
        tiles = parse_tiles("1m2m3m4m5m6m7m8m9m4p5p4p5p")
        self.engine._hands[0] = Hand(tiles)

        # 玩家0之前打過 4p（聽牌牌之一）
        self.engine._hands[0]._discards.append(Tile(Suit.PINZU, 4))

        # 檢查振聽狀態（打過其中一個聽牌牌）
        assert self.engine.check_furiten_discards(0) is True

        # 即使打出的是另一個聽牌牌 5p，也不能榮和
        winning_tile = Tile(Suit.PINZU, 5)
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0
        self.engine._last_drawn_tile = None

        result = self.engine.check_win(0, winning_tile)
        assert result is None or result.win is False


    def test_noten_bappu_one_tenpai(self):
        """測試不聽罰符：一人聽牌 (+3000 / -1000)"""
        self._init_game()

        # 設置玩家0聽牌
        # 123m 456m 789m 123p 4p
        self.engine._hands[0] = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p4p"))

        # 設置其他玩家不聽牌
        # 12m 45m 78m 12p 45p 78s 1z
        noten_hand = Hand(parse_tiles("1m2m4m5m7m8m1p2p4p5p7s8s1z"))
        for i in range(1, 4):
            self.engine._hands[i] = noten_hand

        # 記錄初始分數
        initial_scores = self.engine._game_state.scores.copy()

        # 模擬流局（牌山耗盡）
        self.engine._tile_set._tiles = []
        # 確保 check_ryuukyoku 返回 EXHAUSTED
        # 注意：check_ryuukyoku 依賴於 _tile_set.is_exhausted()

        # 我們直接調用 end_round(None)
        # 預期 end_round 會檢測到流局並計算罰符
        self.engine.end_round(None)

        # 驗證分數變化
        # 玩家0: +3000
        assert self.engine._game_state.scores[0] == initial_scores[0] + 3000
        # 其他玩家: -1000
        for i in range(1, 4):
            assert self.engine._game_state.scores[i] == initial_scores[i] - 1000

    def test_noten_bappu_two_tenpai(self):
        """測試不聽罰符：兩人聽牌 (+1500 / -1500)"""
        self._init_game()

        # 設置玩家0, 1聽牌
        tenpai_hand = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p4p"))
        self.engine._hands[0] = tenpai_hand
        self.engine._hands[1] = tenpai_hand

        # 設置玩家2, 3不聽牌
        noten_hand = Hand(parse_tiles("1m2m4m5m7m8m1p2p4p5p7s8s1z"))
        self.engine._hands[2] = noten_hand
        self.engine._hands[3] = noten_hand

        initial_scores = self.engine._game_state.scores.copy()

        # 模擬流局
        self.engine._tile_set._tiles = []
        self.engine.end_round(None)

        # 驗證分數變化
        assert self.engine._game_state.scores[0] == initial_scores[0] + 1500
        assert self.engine._game_state.scores[1] == initial_scores[1] + 1500
        assert self.engine._game_state.scores[2] == initial_scores[2] - 1500
        assert self.engine._game_state.scores[3] == initial_scores[3] - 1500

    def test_noten_bappu_three_tenpai(self):
        """測試不聽罰符：三人聽牌 (+1000 / -3000)"""
        self._init_game()

        # 設置玩家0, 1, 2聽牌
        tenpai_hand = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p4p"))
        self.engine._hands[0] = tenpai_hand
        self.engine._hands[1] = tenpai_hand
        self.engine._hands[2] = tenpai_hand

        # 設置玩家3不聽牌
        noten_hand = Hand(parse_tiles("1m2m4m5m7m8m1p2p4p5p7s8s1z"))
        self.engine._hands[3] = noten_hand

        initial_scores = self.engine._game_state.scores.copy()

        # 模擬流局
        self.engine._tile_set._tiles = []
        self.engine.end_round(None)

        # 驗證分數變化
        assert self.engine._game_state.scores[0] == initial_scores[0] + 1000
        assert self.engine._game_state.scores[1] == initial_scores[1] + 1000
        assert self.engine._game_state.scores[2] == initial_scores[2] + 1000
        assert self.engine._game_state.scores[3] == initial_scores[3] - 3000

    def test_noten_bappu_all_tenpai(self):
        """測試不聽罰符：全員聽牌 (0)"""
        self._init_game()

        # 設置所有玩家聽牌
        tenpai_hand = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p4p"))
        for i in range(4):
            self.engine._hands[i] = tenpai_hand

        initial_scores = self.engine._game_state.scores.copy()

        # 模擬流局
        self.engine._tile_set._tiles = []
        self.engine.end_round(None)

        # 驗證分數無變化
        for i in range(4):
            assert self.engine._game_state.scores[i] == initial_scores[i]

    def test_noten_bappu_no_tenpai(self):
        """測試不聽罰符：無人聽牌 (0)"""
        self._init_game()

        # 設置所有玩家不聽牌
        noten_hand = Hand(parse_tiles("1m2m4m5m7m8m1p2p4p5p7s8s1z"))
        for i in range(4):
            self.engine._hands[i] = noten_hand

        initial_scores = self.engine._game_state.scores.copy()

        # 模擬流局
        self.engine._tile_set._tiles = []
        self.engine.end_round(None)

        # 驗證分數無變化
        for i in range(4):
            assert self.engine._game_state.scores[i] == initial_scores[i]


    def test_tobi_ron(self):
        """測試擊飛：榮和導致點數 < 0"""
        self._init_game()

        # 啟用擊飛規則
        self.engine._game_state.ruleset.tobi_enabled = True

        # 設置玩家1點數很少 (直接修改 _scores)
        self.engine._game_state._scores[1] = 1000

        # 玩家0聽牌，榮和玩家1
        # 123m 456m 789m 123p 4p (聽 4p)
        self.engine._hands[0] = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p4p"))

        # 玩家1打出 4p
        winning_tile = Tile(Suit.PINZU, 4)
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0

        # 執行榮和
        # 模擬分數更新：玩家1支付 2000 點（假設）
        self.engine._game_state.update_score(1, -2000)
        self.engine._game_state.update_score(0, 2000)

        # 玩家1現在是 -1000 點
        assert self.engine._game_state.scores[1] == -1000

        # 調用 end_round (傳入 winner=0)
        self.engine.end_round([0])

        # 驗證遊戲結束
        assert self.engine.get_phase() == GamePhase.ENDED

    def test_tobi_tsumo(self):
        """測試擊飛：自摸導致點數 < 0"""
        self._init_game()
        self.engine._game_state.ruleset.tobi_enabled = True

        # 設置玩家1, 2, 3點數很少
        self.engine._game_state._scores[1] = 1000

        # 玩家0自摸，每人支付 1000
        self.engine._game_state.update_score(1, -2000) # 假設大牌
        self.engine._game_state.update_score(0, 6000)

        assert self.engine._game_state.scores[1] < 0

        self.engine.end_round([0])
        assert self.engine.get_phase() == GamePhase.ENDED

    def test_tobi_noten_bappu(self):
        """測試擊飛：不聽罰符導致點數 < 0"""
        self._init_game()
        self.engine._game_state.ruleset.tobi_enabled = True

        # 設置玩家1點數很少
        self.engine._game_state._scores[1] = 500

        # 設置玩家0聽牌，其他人不聽
        tenpai_hand = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p4p"))
        noten_hand = Hand(parse_tiles("1m2m4m5m7m8m1p2p4p5p7s8s1z"))

        self.engine._hands[0] = tenpai_hand
        for i in range(1, 4):
            self.engine._hands[i] = noten_hand

        # 模擬流局
        self.engine._tile_set._tiles = []
        self.engine.end_round(None)

        # 玩家1支付 1000，變成 -500
        assert self.engine._game_state.scores[1] == -500

        # 驗證遊戲結束
        assert self.engine.get_phase() == GamePhase.ENDED

    def test_tobi_disabled(self):
        """測試擊飛：禁用擊飛規則"""
        self._init_game()
        self.engine._game_state.ruleset.tobi_enabled = False

        # 設置玩家1點數為負
        self.engine._game_state.scores[1] = -1000

        # 結束回合
        self.engine.end_round([0])

        # 驗證遊戲未結束（進入下一局或下一風）
        # 這裡假設不是最後一局
        assert self.engine.get_phase() != GamePhase.ENDED


    def test_pao_daisangen_tsumo(self):
        """測試包牌：大三元自摸，包牌者全付"""
        self._init_game()

        # 玩家0：大三元聽牌 (已碰白、發)
        # 手牌：11m 99m
        # 副露：白白白 發發發

        # 模擬副露狀態
        # 假設玩家1打出白，玩家0碰
        # 假設玩家2打出發，玩家0碰
        # 假設玩家3打出中，玩家0碰 (觸發包牌)

        # 為了測試，我們需要手動設置狀態，因為 _handle_pon 還沒實現包牌邏輯
        # 但我們正在寫測試，所以我們假設它會工作，或者我們手動設置 _pao_daisangen

        # 設置玩家0手牌
        # For tsumo, hand must include the winning tile (14 tiles total)
        # 3 melds (9 tiles) + 5 tiles in hand = 14 tiles
        # Hand: 1m1m1m 9m9m (winning tile 1m already in hand for is_winning_hand check)
        self.engine._hands[0] = Hand(parse_tiles("1m1m1m9m9m")) # 111m 99m

        # 設置副露
        meld_haku = Meld(MeldType.PON, [Tile(Suit.JIHAI, 5)] * 3, 1) # 碰白 (from 1)
        meld_hatsu = Meld(MeldType.PON, [Tile(Suit.JIHAI, 6)] * 3, 2) # 碰發 (from 2)
        meld_chun = Meld(MeldType.PON, [Tile(Suit.JIHAI, 7)] * 3, 3) # 碰中 (from 3) - 觸發包牌

        self.engine._hands[0]._melds = [meld_haku, meld_hatsu, meld_chun]

        # 設置包牌狀態 (玩家3包牌)
        # 注意：這需要我們在 rules.py 中添加 _pao_daisangen 屬性
        # 由於屬性還沒添加，這裡會報錯，這是預期的 (Red Phase)
        self.engine._pao_daisangen[0] = 3

        # 玩家0自摸1m (此牌已在手牌中，用於 is_winning_hand 檢查)
        winning_tile = Tile(Suit.MANZU, 1)
        self.engine._current_player = 0
        self.engine._last_drawn_tile = (0, winning_tile)

        # 記錄初始分數
        initial_scores = self.engine._game_state.scores.copy()

        # 執行自摸
        # 我們需要調用 check_win 確保它是大三元
        result = self.engine.check_win(0, winning_tile)
        assert result is not None, "check_win should return a result"
        assert result.win
        assert any(y.yaku == Yaku.DAISANGEN for y in result.yaku)

        # 應用分數
        self.engine.apply_win_score(result)

        # 執行 end_round
        self.engine.end_round([0])

        # 驗證分數變化
        # 大三元自摸：32000 (莊家48000)
        # 這裡是親家 (Player 0 is dealer initially) -> 48000
        # 包牌者 (Player 3) 支付全部 48000

        assert self.engine._game_state.scores[0] == initial_scores[0] + 48000
        assert self.engine._game_state.scores[3] == initial_scores[3] - 48000
        assert self.engine._game_state.scores[1] == initial_scores[1] # 其他人不付
        assert self.engine._game_state.scores[2] == initial_scores[2] # 其他人不付

    def test_pao_daisangen_ron_pao_player(self):
        """測試包牌：大三元榮和包牌者（正常支付）"""
        self._init_game()

        # 設置玩家0手牌
        self.engine._hands[0] = Hand(parse_tiles("1m1m9m9m"))

        # 設置副露
        meld_haku = Meld(MeldType.PON, [Tile(Suit.JIHAI, 5)] * 3, 1)
        meld_hatsu = Meld(MeldType.PON, [Tile(Suit.JIHAI, 6)] * 3, 2)
        meld_chun = Meld(MeldType.PON, [Tile(Suit.JIHAI, 7)] * 3, 3) # 碰中 (from 3) - 觸發包牌

        self.engine._hands[0]._melds = [meld_haku, meld_hatsu, meld_chun]

        # 設置包牌狀態 (玩家3包牌)
        self.engine._pao_daisangen[0] = 3

        # 玩家3打出中 (包牌者放銃)
        # winning_tile = Tile(Suit.JIHAI, 7) # 實際上應該是打出 1m 或 5z，因為 5z 已經碰了，所以打出 1m
        # 等等，手牌是 11m 55z，碰了 567z
        # 聽牌是 1m, 5z (單騎?) 不對，碰了三個刻子，手牌剩 11m 55z?
        # 13張牌：3*3=9張副露，剩4張。
        # 11m 55z -> 聽 1m, 5z (雙碰)
        # 假設玩家3打出 1m
        winning_tile = Tile(Suit.MANZU, 1)

        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 3
        self.engine._current_player = 0

        initial_scores = self.engine._game_state.scores.copy()

        # 執行榮和
        result = self.engine.check_win(0, winning_tile)
        self.engine.apply_win_score(result)
        self.engine.end_round([0])

        # 驗證分數變化
        # 莊家大三元榮和：48000
        # 放銃者 (Player 3) 支付 48000
        assert self.engine._game_state.scores[0] == initial_scores[0] + 48000
        assert self.engine._game_state.scores[3] == initial_scores[3] - 48000

    def test_pao_daisangen_ron_other(self):
        """測試包牌：大三元榮和其他人（包牌者與放銃者分擔）"""
        self._init_game()

        # 設置玩家0手牌
        # 3副露 (9張) + 4張手牌 = 13張
        # 手牌: 1m1m 9m9m
        self.engine._hands[0] = Hand(parse_tiles("1m1m9m9m"))

        # 設置副露
        meld_haku = Meld(MeldType.PON, [Tile(Suit.JIHAI, 5)] * 3, 1)
        meld_hatsu = Meld(MeldType.PON, [Tile(Suit.JIHAI, 6)] * 3, 2)
        meld_chun = Meld(MeldType.PON, [Tile(Suit.JIHAI, 7)] * 3, 3) # 碰中 (from 3) - 觸發包牌

        self.engine._hands[0]._melds = [meld_haku, meld_hatsu, meld_chun]

        # 設置包牌狀態 (玩家3包牌)
        self.engine._pao_daisangen[0] = 3

        # 玩家1打出 1m (非包牌者放銃)
        winning_tile = Tile(Suit.MANZU, 1)

        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0

        initial_scores = self.engine._game_state.scores.copy()

        # 執行榮和
        result = self.engine.check_win(0, winning_tile)
        self.engine.apply_win_score(result)
        self.engine.end_round([0])

        # 驗證分數變化
        # 莊家大三元榮和：48000
        # 包牌者 (Player 3) 和 放銃者 (Player 1) 各支付一半 (24000)
        assert self.engine._game_state.scores[0] == initial_scores[0] + 48000
        assert self.engine._game_state.scores[1] == initial_scores[1] - 24000
        assert self.engine._game_state.scores[3] == initial_scores[3] - 24000
        assert self.engine._game_state.scores[2] == initial_scores[2] # 玩家2不付

    # ==================== 頭跳 / 雙響 / 三響 測試 ====================

    def test_head_bump_only_shimocha_wins(self):
        """測試頭跳：下家和上家都能榮和，只有下家和牌"""
        self._init_game()

        # 確保使用頭跳模式（預設）
        assert self.engine._game_state.ruleset.head_bump_only == True

        # 玩家0打出1m
        discard_tile = Tile(Suit.MANZU, 1)

        # 玩家1（下家）和玩家3（上家）都能榮和1m
        # 手牌應該有13張，榮和1張後變成14張
        self.engine._hands[1] = Hand(parse_tiles("2m3m4m5m6m7m8m9m1p2p3p4p4p"))  # 13張
        self.engine._hands[3] = Hand(parse_tiles("2m3m4m5m6m7m8m9m1p2p3p4p4p"))  # 13張

        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # 測試 check_multiple_ron
        winners = self.engine.check_multiple_ron(discard_tile, 0)

        # 在頭跳模式下，當多個玩家能榮和時，只有下家（玩家1）能榮和
        assert len(winners) == 1
        assert winners[0] == 1  # 只有玩家1（下家）

    def test_head_bump_only_toimen_blocked(self):
        """測試頭跳：對面能榮和但被阻擋"""
        self._init_game()

        # 玩家0打出1m
        discard_tile = Tile(Suit.MANZU, 1)

        # 只有玩家2（對面）能榮和
        self.engine._hands[2] = Hand(parse_tiles("2m3m4m5m6m7m8m9m1p2p3p4p4p"))

        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # 測試 check_multiple_ron
        winners = self.engine.check_multiple_ron(discard_tile, 0)

        # 如果只有一個玩家能榮和，則頭跳規則不適用於阻擋，該玩家正常榮和
        assert len(winners) == 1
        assert winners[0] == 2  # 只有玩家2能榮和，正常返回

    def test_head_bump_only_kamicha_blocked(self):
        """測試頭跳：上家能榮和但被阻擋"""
        self._init_game()

        # 玩家0打出1m
        discard_tile = Tile(Suit.MANZU, 1)

        # 只有玩家3（上家）能榮和
        self.engine._hands[3] = Hand(parse_tiles("2m3m4m5m6m7m8m9m1p2p3p4p4p"))

        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # 測試 check_multiple_ron
        winners = self.engine.check_multiple_ron(discard_tile, 0)

        # 如果只有一個玩家能榮和，則頭跳規則不適用於阻擋，該玩家正常榮和
        assert len(winners) == 1
        assert winners[0] == 3

    def test_double_ron_both_win(self):
        """測試雙響：兩家同時榮和"""
        self._init_game()

        # 啟用雙響模式
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True

        # 玩家0打出1m
        discard_tile = Tile(Suit.MANZU, 1)

        # 玩家1（下家）和玩家2（對面）都能榮和
        self.engine._hands[1] = Hand(parse_tiles("2m3m4m5m6m7m8m9m1p2p3p4p4p"))
        self.engine._hands[2] = Hand(parse_tiles("2m3m4m5m6m7m8m9m1p2p3p4p4p"))

        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # 測試 check_multiple_ron
        winners = self.engine.check_multiple_ron(discard_tile, 0)

        # 在雙響模式下，兩家都能榮和
        assert len(winners) == 2
        assert 1 in winners
        assert 2 in winners
        # 順序應該按逆時針（下家優先）
        assert winners[0] == 1
        assert winners[1] == 2


    def test_double_ron_score_calculation(self):
        """測試雙響：驗證放銃者支付兩份分數"""
        self._init_game()
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True

        # 玩家0打出4p
        discard_tile = Tile(Suit.PINZU, 4)

        # 設置玩家1和2的手牌（斷么九 平和）
        # 234m 567m 234p 56p 88s (聽4p/7p)
        # 30符 2翻 = 2000點 (閒家)
        hand_tiles = parse_tiles("2m3m4m5m6m7m2p3p4p5p6p8s8s")
        self.engine._hands[1] = Hand(hand_tiles)
        self.engine._hands[2] = Hand(hand_tiles)

        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0
        self.engine._current_player = 0

        # Disable Renhou (Human Win) by simulating that it's not the first turn
        # This ensures we test standard Yaku (Tanyao + Pinfu) scoring
        self.engine._is_first_turn_after_deal = False

        initial_scores = self.engine._game_state.scores.copy()

        # 執行雙響榮和
        result = self.engine.execute_action(1, GameAction.RON)

        # 驗證結果
        assert len(result.winners) == 2

        # 驗證分數變化
        # 玩家1 +2000
        # 玩家2 +2000
        # 玩家0 -4000
        assert self.engine._game_state.scores[1] == initial_scores[1] + 2000
        assert self.engine._game_state.scores[2] == initial_scores[2] + 2000
        assert self.engine._game_state.scores[0] == initial_scores[0] - 4000


    def test_double_ron_dealer_renchan(self):
        """測試雙響：任一贏家是莊家則連莊"""
        self._init_game()

        # 啟用雙響模式
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True

        # 玩家0是莊家
        assert self.engine._game_state.dealer == 0

        # 玩家1打出1m
        discard_tile = Tile(Suit.MANZU, 1)

        # 設置玩家0（莊家）手牌：役牌東
        # 23m 456m 789m 111z 22z (聽1m/4m)
        self.engine._hands[0] = Hand(parse_tiles("2m3m4m5m6m7m8m9m1z1z1z2z2z"))

        # 設置玩家2手牌：役牌中
        # 23m 456m 789m 555z 66z (聽1m/4m)
        self.engine._hands[2] = Hand(parse_tiles("2m3m4m5m6m7m8m9m5z5z5z6z6z"))

        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 1

        # 執行雙響
        result = self.engine.execute_action(0, GameAction.RON)

        # 驗證贏家
        assert 0 in result.winners
        assert 2 in result.winners

        # 執行回合結束
        self.engine.end_round(winners=result.winners)

        # 驗證莊家連莊（玩家0仍是莊家）
        assert self.engine._game_state.dealer == 0

    def test_triple_ron_disabled_ryuukyoku(self):
        """測試三響禁用：三家可榮和導致流局"""
        self._init_game()

        # 禁用三響（預設）
        assert self.engine._game_state.ruleset.allow_triple_ron == False

        # 玩家0打出1m，玩家1、2、3都能榮和
        discard_tile = Tile(Suit.MANZU, 1)

        self.engine._hands[1] = Hand(parse_tiles("2m3m4m5m6m7m8m9m1p2p3p4p4p"))
        self.engine._hands[2] = Hand(parse_tiles("2m3m4m5m6m7m8m9m1p2p3p4p4p"))
        self.engine._hands[3] = Hand(parse_tiles("2m3m4m5m6m7m8m9m1p2p3p4p4p"))

        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # 測試 check_multiple_ron
        winners = self.engine.check_multiple_ron(discard_tile, 0)

        # 檢測到三家能榮和但禁用三響，返回空列表（觸發流局）
        assert len(winners) == 0  # 空列表表示三家和了流局

    def test_triple_ron_enabled_all_win(self):
        """測試三響啟用：三家都和牌"""
        self._init_game()
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True
        self.engine._game_state.ruleset.allow_triple_ron = True

        # 玩家0打出4p，玩家1、2、3都滿貫榮和
        discard_tile = Tile(Suit.PINZU, 4)

        self.engine._hands[1] = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p4p4p"))
        self.engine._hands[2] = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p4p4p"))
        self.engine._hands[3] = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p4p4p"))

        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        initial_scores = self.engine._game_state.scores.copy()

        # TODO: 執行三響榮和
        # TODO: 驗證玩家0支付三份滿貫（8000 * 3 = 24000）
        # assert self.engine._game_state.scores[0] == initial_scores[0] - 24000
        # assert self.engine._game_state.scores[1] == initial_scores[1] + 8000
        # assert self.engine._game_state.scores[2] == initial_scores[2] + 8000
        # assert self.engine._game_state.scores[3] == initial_scores[3] + 8000

    def test_double_ron_with_furiten(self):
        """測試雙響與振聽：一人振聽，只有另一人榮和"""
        self._init_game()

        # 啟用雙響模式
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True

        # 玩家0打出1m
        discard_tile = Tile(Suit.MANZU, 1)

        # 玩家1能榮和
        self.engine._hands[1] = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p2p2p"))

        # 玩家2能榮和但處於振聽狀態
        self.engine._hands[2] = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p2p2p"))
        self.engine._hands[2]._discards.append(discard_tile)  # 打過1m，現物振聽

        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # TODO: 檢查多人榮和，應該只有玩家1能榮和
        # TODO: 驗證 check_multiple_ron 返回 [1] （不包含2）

    def test_double_ron_priority_order(self):
        """測試雙響：驗證玩家順序正確（下家優先）"""
        self._init_game()

        # 啟用雙響模式
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True

        # 玩家0打出1m，玩家2和3都能榮和
        discard_tile = Tile(Suit.MANZU, 1)

        self.engine._hands[2] = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p2p2p"))
        self.engine._hands[3] = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p2p2p"))

        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # TODO: 檢查 check_multiple_ron 返回的順序
        # 玩家0的下家是玩家1，然後是2、3
        # 所以返回順序應該是 [2, 3]（按逆時針順序）


    def _init_game(self):
        self.engine.start_game()
        self.engine.start_round()
        self.engine.deal()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
