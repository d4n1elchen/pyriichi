"""
Unit tests for RuleEngine
"""

import pytest

from pyriichi.game_state import Wind
from pyriichi.hand import Hand, Meld, MeldType
from pyriichi.rules import (
    GameAction,
    GamePhase,
    RuleEngine,
)
from pyriichi.tiles import Suit, Tile, TileSet
from pyriichi.utils import parse_tiles
from pyriichi.yaku import Yaku
from tests.helpers import (
    RuleEngineTestMixin,
    set_non_matching_scoring_dora,
)


class TestRuleEngine(RuleEngineTestMixin):
    """Rule Engine Tests"""

    def test_start_game(self):
        """Test start game"""
        self.engine.start_game()
        assert self.engine.get_phase() == GamePhase.INIT

    def test_start_round(self):
        """Test start round"""
        self.engine.start_game()
        self.engine.start_round()
        assert self.engine.get_phase() == GamePhase.DEALING

    def test_deal(self):
        """Test deal"""
        self.engine.start_game()
        self.engine.start_round()
        hands = self.engine.deal()

        assert len(hands) == 4
        # dealer should have 14 tiles, others 13
        assert len(hands[0]) == 14
        assert len(hands[1]) == 13
        assert len(hands[2]) == 13
        assert len(hands[3]) == 13

        assert self.engine.get_phase() == GamePhase.PLAYING

    def test_deal_uses_current_dealer(self):
        """Test deal uses current dealer."""
        self.engine.start_game()
        self.engine.game_state.set_dealer(2)
        self.engine.start_round()
        hands = self.engine.deal()

        assert len(hands) == 4
        assert len(hands[0]) == 13
        assert len(hands[1]) == 13
        assert len(hands[2]) == 14
        assert len(hands[3]) == 13
        assert self.engine.get_current_player() == 2
        assert self.engine.get_available_actions(2)
        assert not self.engine.get_available_actions(0)

    def test_check_win_allows_kokushi_musou_ron(self):
        """Test check_win allows kokushi_musou ron."""
        self._init_game()
        winning_tile = Tile(Suit.HONORS, 1)
        self.engine._hands[1] = Hand(parse_tiles("19m19p19s22z3z4z5z6z7z"))
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 0
        self.engine._is_first_turn_after_deal = False

        result = self.engine.check_win(1, winning_tile)

        assert result is not None
        assert result.win
        assert any(yaku.yaku == Yaku.KOKUSHI_MUSOU for yaku in result.yaku)

    def test_check_win_allows_kokushi_musou_tsumo(self):
        """Test check_win allows kokushi_musou tsumo."""
        self._init_game()
        winning_tile = Tile(Suit.HONORS, 7)
        self.engine._hands[1] = Hand(parse_tiles("19m19p19s1z2z3z4z5z6z77z"))
        self.engine._last_drawn_tile = (1, winning_tile)
        self.engine._is_first_turn_after_deal = False

        result = self.engine.check_win(1, winning_tile)

        assert result is not None
        assert result.win
        assert any(yaku.yaku == Yaku.KOKUSHI_MUSOU for yaku in result.yaku)

    def test_check_win_uses_non_dealer_payment_context(self):
        """Test check_win uses non-dealer payment context."""
        self._init_game()
        winning_tile = Tile(Suit.SOUZU, 5)
        hand = Hand(parse_tiles("123m456m789m123p5s"))
        hand.set_riichi(True)
        self.engine._hands[1] = hand
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 0
        self.engine._is_first_turn_after_deal = False
        set_non_matching_scoring_dora(self.engine)

        result = self.engine.check_win(1, winning_tile)

        assert result is not None
        assert result.score_result.payment_to == 1
        assert result.score_result.payment_from == 0
        assert result.score_result.total_points == 5200

    def test_riichi_availability_14_tiles(self):
        """Test riichi availability with 14 tiles (after draw) and tenpai after discard"""
        self.engine.start_game()
        self.engine.start_round()
        self.engine.deal()

        player_idx = self.engine.get_current_player()
        hand = self.engine.get_hand(player_idx)

        # Clear hand
        hand._tiles = []

        # Construct hand: 11 123 123 123 566 (manzu)
        # After discarding 5m, remains 11 123 123 123 66 -> tenpai (machi on 6m)
        tiles = []
        tiles.extend([Tile(Suit.MANZU, 1) for _ in range(2)])
        tiles.extend([Tile(Suit.MANZU, 2) for _ in range(3)])
        tiles.extend([Tile(Suit.MANZU, 3) for _ in range(3)])
        tiles.extend([Tile(Suit.MANZU, 4) for _ in range(3)])
        tiles.append(Tile(Suit.MANZU, 5))
        tiles.append(Tile(Suit.MANZU, 6))
        tiles.append(Tile(Suit.MANZU, 6))

        for t in tiles:
            hand.add_tile(t)

        # Force recalculate actions (bypass cache)
        actions = self.engine._calculate_turn_actions(player_idx)

        assert GameAction.DECLARE_RIICHI in actions

    def test_hand_total_tile_count_includes_melds(self):
        """Total tile count should include melded tiles."""
        # 11m 123m 456p 77s 8s 99s
        tiles = parse_tiles("11123m456p77899s")

        hand = Hand(tiles)
        assert hand.total_tile_count() == 13

        meld = hand.pon(Tile(Suit.MANZU, 1))
        assert meld is not None
        assert len(hand.tiles) == 11
        assert hand.total_tile_count() == 14

    def test_get_hand_invalid_player(self):
        """Test get_hand invalid player error"""
        self._init_game()
        # Test invalid player index
        with pytest.raises(ValueError, match="玩家位置必須在"):
            self.engine.get_hand(-1)

        with pytest.raises(ValueError, match="玩家位置必須在"):
            self.engine.get_hand(4)

    def test_get_discards_invalid_player(self):
        """Test get_discards invalid player error"""
        self._init_game()
        # Test invalid player index
        with pytest.raises(ValueError, match="玩家位置必須在"):
            self.engine.get_discards(-1)

        with pytest.raises(ValueError, match="玩家位置必須在"):
            self.engine.get_discards(4)

    def test_deal_wrong_phase(self):
        """Test deal in wrong phase"""
        self.engine.start_game()
        # Not in dealing phase
        self.engine._phase = GamePhase.PLAYING
        with pytest.raises(ValueError, match="只能在發牌階段發牌"):
            self.engine.deal()

    def test_deal_no_tile_set(self):
        self.engine.start_game()
        self.engine.start_round()
        # Manually initialize hands because deal() was not called
        self.engine._hands = [Hand([]) for _ in range(4)]
        self.engine._tile_set = None
        # Directly call _handle_draw
        # Ensure hand is not full
        hand = self.engine.get_hand(0)
        if hand.total_tile_count() >= 14:
            hand.tiles.pop()

        # Error message might be "Tile set not initialized" or similar, loose check here
        with pytest.raises(ValueError):
            self.engine._handle_draw(0)

    def test_end_round_with_winner(self):
        """Test end round (with winner)"""
        self._init_game()

        # Set to South 4 Round
        from pyriichi.game_state import Wind

        self.engine._game_state.set_round(Wind.SOUTH, 4)
        self.engine._game_state._dealer = 3  # Player 3 is dealer

        # Set player score >= 30000 (Return point), otherwise will go into West round
        self.engine._game_state._scores[0] = 30000

        # Test with winner (Player 0 wins, non-dealer)
        winner = 0
        self.engine.end_round([winner])

        # Should end game (GamePhase.ENDED)
        assert self.engine._phase == GamePhase.ENDED

    def test_interrupt_riichi_ippatsu_on_chi(self):
        """Test chi interrupts ippatsu"""
        self._init_game()
        self.engine._riichi_ippatsu = {0: True}
        self.engine._riichi_ippatsu_discard = {0: 0}

        chi_tile = Tile(Suit.MANZU, 4)
        self.engine._hands[0] = Hand(parse_tiles("11223344556677m"))
        self.engine._hands[1] = Hand(parse_tiles("23456789m12345p"))
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

        # handle other waiting players (e.g. PON)
        waiting_players = list(self.engine.waiting_for_actions.keys())
        for pid in waiting_players:
            if pid != 1:
                self.engine.execute_action(pid, GameAction.PASS)

        assert self.engine._riichi_ippatsu[0] is False

    def test_interrupt_riichi_ippatsu_on_pon(self):
        """Test pon interrupts ippatsu"""
        self._init_game()
        self.engine._riichi_ippatsu = {0: True}
        self.engine._riichi_ippatsu_discard = {0: 0}

        pon_tile = Tile(Suit.PINZU, 7)
        self.engine._hands[0] = Hand(parse_tiles("7p1112233445566m"))
        self.engine._hands[2] = Hand(parse_tiles("77p11223344556p"))
        self.engine._current_player = 0

        self.engine.execute_action(0, GameAction.DISCARD, tile=pon_tile)
        assert GameAction.PON in self.engine.get_available_actions(2)
        self.engine.execute_action(2, GameAction.PON)

        # If other players are waiting (e.g. P1 can chi?), need to let them PASS
        waiting_players = list(self.engine.waiting_for_actions.keys())
        for pid in waiting_players:
            if GameAction.PASS in self.engine.get_available_actions(pid):
                self.engine.execute_action(pid, GameAction.PASS)

        assert self.engine._riichi_ippatsu[0] is False

    def test_interrupt_riichi_ippatsu_on_kan(self):
        """Test open_kan interrupts ippatsu"""
        self._init_game()
        self.engine._riichi_ippatsu = {0: True}
        self.engine._riichi_ippatsu_discard = {0: 0}

        kan_tile = Tile(Suit.SOUZU, 9)
        self.engine._hands[0] = Hand(parse_tiles("9s1122334455667m"))
        self.engine._hands[1] = Hand(parse_tiles("999s1122334455s"))
        self.engine._current_player = 0

        self.engine.execute_action(0, GameAction.DISCARD, tile=kan_tile)
        assert GameAction.KAN in self.engine.get_available_actions(1)
        self.engine.execute_action(1, GameAction.KAN, tile=kan_tile)

        # handle other waiting players
        waiting_players = list(self.engine.waiting_for_actions.keys())
        for pid in waiting_players:
            if pid != 1:
                self.engine.execute_action(pid, GameAction.PASS)

        assert self.engine._riichi_ippatsu[0] is False

    def test_interrupt_riichi_ippatsu_on_declare_ankan(self):
        """Test declare_ankan interrupts ippatsu"""
        self._init_game()
        self.engine._riichi_ippatsu = {0: True, 1: True}
        self.engine._riichi_ippatsu_discard = {0: 0, 1: 0}

        self.engine._hands[3] = Hand(parse_tiles("111123456789m1p"))

        # Force update actions
        self.engine._waiting_for_actions = {}
        self.engine._waiting_for_actions[3] = self.engine._calculate_turn_actions(3)
        self.engine._current_player = 3

        assert GameAction.DECLARE_ANKAN in self.engine.get_available_actions(3)
        result = self.engine.execute_action(3, GameAction.DECLARE_ANKAN)

        assert result.closed_kan is True or result.kan is True
        assert all(flag is False for flag in self.engine._riichi_ippatsu.values())





    def test_kan_updates_current_player(self):
        """
        Regression Test: Verify open_kan updates current player.
        Ensure kan player can discard after drawing rinshan tile.
        """
        self._init_game()

        # Setup: Player 1 has three West (4z), can kan if Player 0 discards 4z
        # Player 0's turn
        self.engine._current_player = 0

        # Ensure other players don't interrupt
        non_interrupt_tiles = parse_tiles("1s1s1s1s2s2s2s2s3s3s3s3s4s")
        for i in [0, 2, 3]:
            self.engine._hands[i] = Hand(non_interrupt_tiles)

        # Give Player 1 three 4z
        p1_hand = self.engine.get_hand(1)
        # 13 tiles
        p1_hand._tiles = parse_tiles("4z4z4z1m2m3m4m5m6m7m8m9m1p")
        p1_hand._melds = []

        # Player 0 discards 4z
        tile_4z = Tile(Suit.HONORS, 4)
        # Ensure Player 0 has this tile
        self.engine.get_hand(0)._tiles.append(tile_4z)
        self.engine.execute_action(0, GameAction.DISCARD, tile_4z)

        # Verify Player 1 can kan
        actions = self.engine.get_available_actions(1)
        assert GameAction.KAN in actions

        # Player 1 executes kan
        result = self.engine.execute_action(1, GameAction.KAN, tile_4z)

        # Verify kan success
        assert result.success
        assert result.kan is True

        # Critical check: Current player should update to 1
        assert self.engine.get_current_player() == 1

        # Verify Player 1 can discard (after automatically drawing rinshan tile)
        # _handle_kan calls _draw_rinshan_tile to add a tile
        p1_actions = self.engine.get_available_actions(1)
        assert GameAction.DISCARD in p1_actions

        # Player 1 discards to finish turn
        tile_to_discard = p1_hand.tiles[0]
        result_discard = self.engine.execute_action(
            1, GameAction.DISCARD, tile_to_discard
        )
        assert result_discard.success

        # Turn should rotate to Player 2
        assert self.engine.get_current_player() == 2
        assert self.engine.check_furiten_temp(0) is False






    def test_noten_bappu_one_tenpai(self):
        """Test noten_bappu: One tenpai (+3000 / -1000)"""
        self._init_game()

        # Set Player 0 tenpai
        # 123m 456m 789m 123p 4p
        self.engine._hands[0] = Hand(parse_tiles("123456789m1234p"))

        # Set other players noten
        # 12m 45m 78m 12p 45p 78s 1z
        noten_hand = Hand(parse_tiles("124578m1245p78s1z"))
        for i in range(1, 4):
            self.engine._hands[i] = noten_hand

        # Record initial scores
        initial_scores = self.engine._game_state.scores.copy()

        # Simulate ryuukyoku (exhaustive_draw)
        self.engine._tile_set._tiles = []
        # Ensure check_ryuukyoku returns EXHAUSTED
        # Note: check_ryuukyoku relies on _tile_set.is_exhausted()

        # Directly call end_round(None)
        # Expect end_round to detect ryuukyoku and calculate penalty
        self.engine.end_round(None)

        # Verify score changes
        # Player 0: +3000
        assert self.engine._game_state.scores[0] == initial_scores[0] + 3000
        # Other players: -1000
        for i in range(1, 4):
            assert self.engine._game_state.scores[i] == initial_scores[i] - 1000

    def test_noten_bappu_two_tenpai(self):
        """Test noten_bappu: Two tenpai (+1500 / -1500)"""
        self._init_game()

        # Set Player 0, 1 tenpai
        tenpai_hand = Hand(parse_tiles("123456789m1234p"))
        self.engine._hands[0] = tenpai_hand
        self.engine._hands[1] = tenpai_hand

        # Set Player 2, 3 noten
        noten_hand = Hand(parse_tiles("124578m1245p78s1z"))
        self.engine._hands[2] = noten_hand
        self.engine._hands[3] = noten_hand

        initial_scores = self.engine._game_state.scores.copy()

        self.engine._tile_set._tiles = []
        self.engine.end_round(None)

        assert self.engine._game_state.scores[0] == initial_scores[0] + 1500
        assert self.engine._game_state.scores[1] == initial_scores[1] + 1500
        assert self.engine._game_state.scores[2] == initial_scores[2] - 1500
        assert self.engine._game_state.scores[3] == initial_scores[3] - 1500

    def test_noten_bappu_three_tenpai(self):
        """Test noten_bappu: Three tenpai (+1000 / -3000)"""
        self._init_game()

        # Set Player 0, 1, 2 tenpai
        tenpai_hand = Hand(parse_tiles("123456789m1234p"))
        self.engine._hands[0] = tenpai_hand
        self.engine._hands[1] = tenpai_hand
        self.engine._hands[2] = tenpai_hand

        # Set Player 3 noten
        noten_hand = Hand(parse_tiles("124578m1245p78s1z"))
        self.engine._hands[3] = noten_hand

        initial_scores = self.engine._game_state.scores.copy()

        self.engine._tile_set._tiles = []
        self.engine.end_round(None)

        assert self.engine._game_state.scores[0] == initial_scores[0] + 1000
        assert self.engine._game_state.scores[1] == initial_scores[1] + 1000
        assert self.engine._game_state.scores[2] == initial_scores[2] + 1000
        assert self.engine._game_state.scores[3] == initial_scores[3] - 3000

    def test_noten_bappu_all_tenpai(self):
        """Test noten_bappu: All tenpai (0)"""
        self._init_game()

        # Set all players tenpai
        tenpai_hand = Hand(parse_tiles("123456789m1234p"))
        for i in range(4):
            self.engine._hands[i] = tenpai_hand

        initial_scores = self.engine._game_state.scores.copy()

        self.engine._tile_set._tiles = []
        self.engine.end_round(None)

        for i in range(4):
            assert self.engine._game_state.scores[i] == initial_scores[i]

    def test_noten_bappu_no_tenpai(self):
        """Test noten_bappu: No tenpai (0)"""
        self._init_game()

        # Set all players noten
        noten_hand = Hand(parse_tiles("124578m1245p78s1z"))
        for i in range(4):
            self.engine._hands[i] = noten_hand

        initial_scores = self.engine._game_state.scores.copy()

        self.engine._tile_set._tiles = []
        self.engine.end_round(None)

        for i in range(4):
            assert self.engine._game_state.scores[i] == initial_scores[i]

    def test_exhaustive_draw_dealer_tenpai_renchan(self):
        """Test exhaustive_draw dealer tenpai renchan."""
        self._init_game()
        self.engine._game_state.set_dealer(0)
        self.engine._game_state.set_round(Wind.EAST, 1)
        self.engine._game_state._honba = 0
        self.engine._hands[0] = Hand(parse_tiles("123456789m1234p"))
        noten_hand = Hand(parse_tiles("124578m1245p78s1z"))
        for i in range(1, 4):
            self.engine._hands[i] = noten_hand
        self.engine._tile_set._tiles = []

        self.engine.end_round(None)

        assert self.engine._game_state.dealer == 0
        assert self.engine._game_state.round_wind == Wind.EAST
        assert self.engine._game_state.round_number == 1
        assert self.engine._game_state.honba == 1

    def test_exhaustive_draw_dealer_noten_rotates(self):
        """Test exhaustive_draw dealer noten rotates."""
        self._init_game()
        self.engine._game_state.set_dealer(0)
        self.engine._game_state.set_round(Wind.EAST, 1)
        self.engine._hands[0] = Hand(parse_tiles("124578m1245p78s1z"))
        self.engine._hands[1] = Hand(parse_tiles("123456789m1234p"))
        for i in range(2, 4):
            self.engine._hands[i] = Hand(parse_tiles("124578m1245p78s1z"))
        self.engine._tile_set._tiles = []

        self.engine.end_round(None)

        assert self.engine._game_state.dealer == 1
        assert self.engine._game_state.round_wind == Wind.EAST
        assert self.engine._game_state.round_number == 2
        assert self.engine._game_state.honba == 1

    def test_tobi_ron(self):
        """Test tobi (Bankruptcy): ron causes score < 0"""
        self._init_game()

        # Enable tobi rule
        self.engine._game_state.ruleset.tobi_enabled = True

        # Set Player 1 score very low (modify _scores directly)
        self.engine._game_state._scores[1] = 1000

        # Player 0 tenpai, ron Player 1
        # 123m 456m 789m 123p 4p (machi 4p)
        self.engine._hands[0] = Hand(parse_tiles("123456789m1234p"))

        # Player 1 discards 4p
        winning_tile = Tile(Suit.PINZU, 4)
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0

        # Execute ron
        # Simulate score update: Player 1 pays 2000 (assumed)
        self.engine._game_state.update_score(1, -2000)
        self.engine._game_state.update_score(0, 2000)

        # Player 1 is now -1000
        assert self.engine._game_state.scores[1] == -1000

        # Call end_round (pass winner=0)
        self.engine.end_round([0])

        # Verify game ended
        assert self.engine.get_phase() == GamePhase.ENDED

    def test_tobi_tsumo(self):
        """Test tobi (Bankruptcy): tsumo causes score < 0"""
        self._init_game()
        self.engine._game_state.ruleset.tobi_enabled = True

        # Set Player 1, 2, 3 score very low
        self.engine._game_state._scores[1] = 1000

        # Player 0 tsumo, everyone pays 1000
        self.engine._game_state.update_score(1, -2000)  # Assume big hand
        self.engine._game_state.update_score(0, 6000)

        assert self.engine._game_state.scores[1] < 0

        self.engine.end_round([0])
        assert self.engine.get_phase() == GamePhase.ENDED

    def test_tobi_noten_bappu(self):
        """Test tobi (Bankruptcy): noten_bappu causes score < 0"""
        self._init_game()
        self.engine._game_state.ruleset.tobi_enabled = True

        # Set Player 1 score very low
        self.engine._game_state._scores[1] = 500

        # Set Player 0 tenpai, others noten
        tenpai_hand = Hand(parse_tiles("123456789m1234p"))
        noten_hand = Hand(parse_tiles("124578m1245p78s1z"))

        self.engine._hands[0] = tenpai_hand
        for i in range(1, 4):
            self.engine._hands[i] = noten_hand

        # Simulate ryuukyoku
        self.engine._tile_set._tiles = []
        self.engine.end_round(None)

        # Player 1 pays 1000, becomes -500
        assert self.engine._game_state.scores[1] == -500

        # Verify game ended
        assert self.engine.get_phase() == GamePhase.ENDED

    def test_tobi_disabled(self):
        """Test tobi Disabled"""
        self._init_game()
        self.engine._game_state.ruleset.tobi_enabled = False

        # Set Player 1 score negative
        self.engine._game_state.scores[1] = -1000

        # End round
        self.engine.end_round([0])

        # Verify game not ended (Next round or next wind)
        # Assuming not last round
        assert self.engine.get_phase() != GamePhase.ENDED

    def test_draw_with_kan(self):
        """Test Draw with kan (hand size limit should increase)"""
        self._init_game()

        # Setup: Player 0 has a closed_kan
        hand = self.engine.get_hand(0)
        # 10 tiles + 1 kan (4 tiles) = 14 tiles
        hand._tiles = parse_tiles("1m2m3m4m5m6m7m8m9m1p")
        kan_tiles = parse_tiles("2p2p2p2p")
        meld = Meld(MeldType.CLOSED_KAN, kan_tiles)
        hand._melds = [meld]

        # Ensure Player 0's turn
        self.engine._current_player = 0

        # Execute Draw
        # Directly call _handle_draw to bypass execute_action checks
        # Should allow draw (becomes 15 tiles)
        # If limit is fixed at 14, this will fail
        self.engine._handle_draw(0)

        assert hand.total_tile_count() == 15
        assert len(hand.melds) == 1

    def test_cannot_chi_pon_kan_in_riichi(self):
        """Test cannot chi/pon/kan in riichi"""
        self._init_game()

        # Set Player 0 riichi
        hand = self.engine.get_hand(0)
        hand._is_riichi = True

        # Set kamicha discard
        self.engine._last_discarded_player = 3
        self.engine._last_discarded_tile = Tile(Suit.PINZU, 3)

        # Set hand to allow chi/pon/kan
        # 12p (chi 3p), 33p (pon 3p), 333p (kan 3p)
        hand._tiles = parse_tiles("12333p456s789m11z")

        # Check chi
        # 12p + 3p -> chi
        assert hand.can_chi(self.engine._last_discarded_tile, from_player=0)
        assert not self.engine._can_chi(0)  # Should be False due to riichi

        # Check pon
        # 33p + 3p -> pon
        assert hand.can_pon(self.engine._last_discarded_tile)
        assert not self.engine._can_pon(0)  # Should be False due to riichi

        # Check kan (Open)
        # 333p + 3p -> kan
        assert hand.can_kan(self.engine._last_discarded_tile)
        assert not self.engine._can_kan(0)  # Should be False due to riichi

    def test_must_discard_drawn_tile_in_riichi(self):
        """Test must discard drawn tile in riichi"""
        self._init_game()
        hand = self.engine.get_hand(0)
        hand._is_riichi = True

        # Set hand
        hand._tiles = parse_tiles("123m456p789s1122z")

        # Draw tile
        drawn_tile = Tile(Suit.HONORS, 3)  # 3z (West)
        hand.add_tile(drawn_tile)

        # Try to discard a tile that was not just drawn (1m)
        with pytest.raises(ValueError, match="立直後只能打出剛摸到的牌"):
            self.engine._handle_discard(0, Tile(Suit.MANZU, 1))

        # Try to discard the drawn tile (3z)
        # Should succeed
        self.engine._handle_discard(0, drawn_tile)

    def test_closed_kan_allowed_if_wait_unchanged(self):
        """Test declare_ankan allowed if machi is unchanged after riichi"""
        self._init_game()
        hand = self.engine.get_hand(0)
        hand._is_riichi = True

        # tenpai: 111m (Triplet) + 456m + 789p + 23s (machi 1s, 4s) + 77z (Pair)
        # Here 111m can only be interpreted as a triplet, not a pair (because 1m is not connected to 456m)
        hand._tiles = parse_tiles("111456m789p23s77z")
        drawn_tile = Tile(Suit.MANZU, 1)
        hand.add_tile(drawn_tile)

        # Should allow declare_ankan
        assert self.engine._can_declare_ankan(0)

    def test_closed_kan_forbidden_if_wait_changed(self):
        """Test declare_ankan forbidden if machi is changed after riichi"""
        self._init_game()
        hand = self.engine.get_hand(0)
        hand._is_riichi = True

        # tenpai: 3334m (machi 2m, 3m, 4m, 5m) -> closed_kan 3m -> 4m (tanki 4m)
        hand._tiles = parse_tiles("3334m456p789s11z")
        drawn_tile = Tile(Suit.MANZU, 3)
        hand.add_tile(drawn_tile)

        # Should NOT allow declare_ankan
        assert not self.engine._can_declare_ankan(0)

    def test_riichi_requires_discard_and_tenpai(self):
        """Test riichi requires both discard and tenpai"""
        self._init_game()
        hand = self.engine.get_hand(0)

        # Set tenpai hand: 11123m (machi 1m, 4m) + 456p + 789s + 11z
        # Draw 2p (Not tenpai)
        hand._tiles = parse_tiles("11123m456p789s11z")
        drawn_tile = Tile(Suit.PINZU, 2)
        hand.add_tile(drawn_tile)

        # Try riichi without discarding
        with pytest.raises(ValueError, match="立直必須同時打出一張牌"):
            self.engine._handle_riichi(0, tile=None)

        # Try riichi and discard 2p (tenpai)
        # Should succeed
        result = self.engine._handle_riichi(0, tile=drawn_tile)
        assert result.riichi
        assert hand.is_riichi
        assert self.engine._last_discarded_tile == drawn_tile

        # Set noten hand
        # 11123m 456p 789s 12z (noten) + draw 3z
        hand._is_riichi = False
        hand._tiles = parse_tiles("11123m456p789s12z")
        drawn_tile = Tile(Suit.HONORS, 3)
        hand.add_tile(drawn_tile)
        self.engine._game_state.ruleset.chombo_penalty_enabled = False

        # Try riichi and discard 3z (Still noten)
        with pytest.raises(ValueError, match="立直打牌後必須聽牌"):
            self.engine._handle_riichi(0, tile=drawn_tile)

    def test_multiple_ron_decision(self):
        """Test multiple ron decisions (One ron, One Pass)"""
        self._init_game()

        # Enable double_ron
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True

        # Set Player 1 tenpai (machi 5p)
        # 123m 456s 789p 11z + 46p (machi 5p for 456p)
        self.engine.get_hand(1)._tiles = parse_tiles("123m456s789p11z46p")
        self.engine.get_hand(1)._melds = []

        # Set Player 2 tenpai (machi 5p)
        # 123m 456s 789p 22z + 46p (machi 5p for 456p)
        self.engine.get_hand(2)._tiles = parse_tiles("123m456s789p22z46p")
        self.engine.get_hand(2)._melds = []

        # Player 0 discards 5p
        discard_tile = Tile(Suit.PINZU, 5)
        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # Check interrupts
        interrupts = self.engine._check_interrupts(discard_tile, discarded_player=0)

        # Ensure Player 1 and Player 2 can both ron
        assert 1 in interrupts
        assert GameAction.RON in interrupts[1]
        assert 2 in interrupts
        assert GameAction.RON in interrupts[2]

        # Set waiting for actions
        self.engine._waiting_for_actions = interrupts
        self.engine._incoming_actions = {}
        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # Player 1 chooses RON
        self.engine.execute_action(1, GameAction.RON)

        # Player 2 chooses PASS
        result = self.engine.execute_action(2, GameAction.PASS)

        # Verify result
        # Only Player 1 should win
        assert result.success
        assert len(result.winners) == 1
        assert result.winners[0] == 1

        # Verify Player 2 furiten (Missed ron)
        assert self.engine._furiten_temp[2]


class TestHighScoringMethod:
    def test_ambiguous_hand_pinfu_vs_triplet(self):
        # 111222333m.
        # 111 222 333 (Triplet).
        # 123 123 123 (Sequence).
        # This is a classic case!

        tiles = parse_tiles("111m222m333m678p55s")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 1)  # Win on 1m

        combinations = hand.get_winning_combinations(winning_tile, is_tsumo=True)

        assert len(combinations) >= 2, "Should have at least 2 interpretations"

        engine = RuleEngine()
        engine.start_game()
        engine.start_round()
        engine.deal()

        # Simulate game state
        engine._hands[0] = hand

        # Set last drawn tile to simulate tsumo
        engine._last_drawn_tile = (0, winning_tile)

        # Disable tenhou/chihou/renhou
        engine._is_first_turn_after_deal = False

        # Calculate score
        result = engine.check_win(0, winning_tile)

        assert result is not None

        # Expected:
        # sanankou (2) + tsumo (1) = 3 han 40 fu.
        # If pinfu interpretation:
        # pinfu (1) + tsumo (1) + iipeikou (1) = 3 han 20 fu.

        # So we expect 3 han 40 fu.
        assert (
            result.fu == 40
        ), f"Should choose higher scoring interpretation (40 Fu vs 20 Fu). Got {result.fu} Fu, Yaku: {[y.yaku.name for y in result.yaku]}"


class TestClosedKanSelection:
    def test_closed_kan_selection(self):
        # Setup: hand has 1111m and 2222m.
        tiles = parse_tiles("1111m2222m567p89s")
        hand = Hand(tiles)

        engine = RuleEngine(num_players=1)
        # Manually initialize hands
        engine._hands = [hand]
        # Manually initialize tile set

        engine._tile_set = TileSet()
        # Remove tiles in hand from tile set to avoid duplicates
        for t in tiles:
            if t in engine._tile_set._tiles:
                engine._tile_set._tiles.remove(t)
        engine._tile_set.shuffle()

        # Set game state
        engine._phase = GamePhase.PLAYING
        engine._current_player = 0
        engine._riichi_ippatsu = {}

        # Force update actions
        engine._waiting_for_actions[0] = engine._calculate_turn_actions(0)

        # Execute declare_ankan 2m
        tile_to_kan = Tile(Suit.MANZU, 2)
        result = engine.execute_action(0, GameAction.DECLARE_ANKAN, tile=tile_to_kan)

        # Check success
        assert result.success

        # Check hand melds
        melds = engine._hands[0].melds
        assert len(melds) == 1
        assert melds[0].type == MeldType.CLOSED_KAN
        assert melds[0].tiles[0] == tile_to_kan

        # Check remaining tiles
        # Should remain 1111m (and other tiles)
        remaining_tiles = engine._hands[0].tiles
        count_1m = sum(
            1 for t in remaining_tiles if t.suit == Suit.MANZU and t.rank == 1
        )
        assert count_1m == 4

        # Now execute declare_ankan 1m
        tile_to_kan_1 = Tile(Suit.MANZU, 1)
        result = engine.execute_action(0, GameAction.DECLARE_ANKAN, tile=tile_to_kan_1)
        assert result.success

        melds = engine._hands[0].melds
        assert len(melds) == 2
        assert melds[1].tiles[0] == tile_to_kan_1
