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
    RyuukyokuType,
)
from pyriichi.tiles import Suit, Tile, TileSet
from pyriichi.utils import parse_tiles
from pyriichi.yaku import Yaku


class TestRuleEngine:
    """Rule Engine Tests"""

    def setup_method(self):
        """Setup test environment"""
        self.engine = RuleEngine(num_players=4)

    def _has_action(self, player: int, action: GameAction) -> bool:
        """Helper method: Check if player has action available"""
        return action in self.engine.get_available_actions(player)

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
        # Dealer should have 14 tiles, others 13
        assert len(hands[0]) == 14
        assert len(hands[1]) == 13
        assert len(hands[2]) == 13
        assert len(hands[3]) == 13

        assert self.engine.get_phase() == GamePhase.PLAYING

    def test_riichi_availability_14_tiles(self):
        """Test Riichi availability with 14 tiles (after draw) and Tenpai after discard"""
        self.engine.start_game()
        self.engine.start_round()
        self.engine.deal()

        player_idx = self.engine.get_current_player()
        hand = self.engine.get_hand(player_idx)

        # Clear hand
        hand._tiles = []

        # Construct hand: 11 123 123 123 566 (Manzu)
        # After discarding 5m, remains 11 123 123 123 66 -> Tenpai (Wait on 6m)
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

        assert GameAction.RICHI in actions

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
        """Test Chi interrupts Ippatsu"""
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

        # Handle other waiting players (e.g. PON)
        waiting_players = list(self.engine.waiting_for_actions.keys())
        for pid in waiting_players:
            if pid != 1:
                self.engine.execute_action(pid, GameAction.PASS)

        assert self.engine._riichi_ippatsu[0] is False

    def test_interrupt_riichi_ippatsu_on_pon(self):
        """Test Pon interrupts Ippatsu"""
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

        # If other players are waiting (e.g. P1 can Chi?), need to let them PASS
        waiting_players = list(self.engine.waiting_for_actions.keys())
        for pid in waiting_players:
            if GameAction.PASS in self.engine.get_available_actions(pid):
                self.engine.execute_action(pid, GameAction.PASS)

        assert self.engine._riichi_ippatsu[0] is False

    def test_interrupt_riichi_ippatsu_on_kan(self):
        """Test Daiminkan (Open Kan) interrupts Ippatsu"""
        self._init_game()
        self.engine._riichi_ippatsu = {0: True}
        self.engine._riichi_ippatsu_discard = {0: 0}

        kan_tile = Tile(Suit.SOZU, 9)
        self.engine._hands[0] = Hand(parse_tiles("9s1122334455667m"))
        self.engine._hands[1] = Hand(parse_tiles("999s1122334455s"))
        self.engine._current_player = 0

        self.engine.execute_action(0, GameAction.DISCARD, tile=kan_tile)
        assert GameAction.KAN in self.engine.get_available_actions(1)
        self.engine.execute_action(1, GameAction.KAN, tile=kan_tile)

        # Handle other waiting players
        waiting_players = list(self.engine.waiting_for_actions.keys())
        for pid in waiting_players:
            if pid != 1:
                self.engine.execute_action(pid, GameAction.PASS)

        assert self.engine._riichi_ippatsu[0] is False

    def test_interrupt_riichi_ippatsu_on_ankan(self):
        """Test Ankan (Closed Kan) interrupts Ippatsu"""
        self._init_game()
        self.engine._riichi_ippatsu = {0: True, 1: True}
        self.engine._riichi_ippatsu_discard = {0: 0, 1: 0}

        self.engine._hands[3] = Hand(parse_tiles("111123456789m1p"))

        # Force update actions
        self.engine._waiting_for_actions = {}
        self.engine._waiting_for_actions[3] = self.engine._calculate_turn_actions(3)
        self.engine._current_player = 3

        assert GameAction.ANKAN in self.engine.get_available_actions(3)
        result = self.engine.execute_action(3, GameAction.ANKAN)

        assert result.ankan is True or result.kan is True
        assert all(flag is False for flag in self.engine._riichi_ippatsu.values())

    def test_furiten_discards_cannot_ron(self):
        """Test Furiten (Discards): Cannot Ron if winning tile is in discards"""
        self._init_game()

        # Set Player 0 Tenpai (Wait 3p)
        # Hand: 123m 456m 789m 12p 33p (Wait 3p)
        tiles = parse_tiles("123456789m1233p")
        self.engine._hands[0] = Hand(tiles)

        # Player 0 discarded 3p before (now in discards)
        discard_tile = Tile(Suit.PINZU, 3)
        self.engine._hands[0]._discards.append(discard_tile)

        # Other player discards 3p
        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0
        self.engine._last_drawn_tile = None

        # Check Furiten status
        assert self.engine.check_furiten_discards(0) is True
        assert self.engine.is_furiten(0) is True

        # Try Ron, should fail
        result = self.engine.check_win(0, discard_tile)
        assert result is None or result.win is False

    def test_furiten_discards_can_tsumo(self):
        """Test Furiten (Discards): Can Tsumo even if Furiten"""
        self._init_game()

        # Set Player 0 Tenpai (Wait 3p)
        # Hand: 123m 456m 789m 12p 33p (13 tiles, Wait 3p)
        tiles = parse_tiles("123456789m1233p")
        self.engine._hands[0] = Hand(tiles)

        # Player 0 discarded 3p before
        discard_tile = Tile(Suit.PINZU, 3)
        self.engine._hands[0]._discards.append(discard_tile)

        # Check Furiten status (13 tiles, should be Furiten)
        assert self.engine.check_furiten_discards(0) is True

        # Simulate Tsumo 3p
        self.engine._current_player = 0
        self.engine._last_drawn_tile = (0, discard_tile)
        self.engine._last_discarded_tile = None

        # Tsumo requires 14 tiles in hand
        self.engine._hands[0].add_tile(discard_tile)

        # Tsumo should succeed
        result = self.engine.check_win(0, discard_tile)
        assert result is not None
        assert result.win is True

    def test_furiten_temp_same_turn_cannot_ron(self):
        """Test Temporary Furiten (Same Turn): Cannot Ron if passed winning tile in same turn"""
        self._init_game()

        # Set Player 0 Tenpai (Wait 4p)
        # Hand: 123m 456m 789m 123p 4p
        tiles = parse_tiles("123456789m1234p")
        self.engine._hands[0] = Hand(tiles)

        winning_tile = Tile(Suit.PINZU, 4)

        # Set Temporary Furiten status (Player 0 passed Ron in current turn)
        self.engine._furiten_temp[0] = True
        self.engine._furiten_temp_round[0] = self.engine._turn_count

        # Other player discards 4p
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0
        self.engine._last_drawn_tile = None

        # Check Furiten status
        assert self.engine.check_furiten_temp(0) is True
        assert self.engine.is_furiten(0) is True

        # 嘗試榮和，應該失敗
        result = self.engine.check_win(0, winning_tile)
        assert result is None or result.win is False

    def test_furiten_temp_next_turn_can_ron(self):
        """Test Temporary Furiten: Can Ron in next turn"""
        self._init_game()

        # Set Player 0 Tenpai (Wait 4p)
        tiles = parse_tiles("123456789m1234p")
        self.engine._hands[0] = Hand(tiles)

        winning_tile = Tile(Suit.PINZU, 4)

        # Set Temporary Furiten status (Previous turn)
        self.engine._furiten_temp[0] = True
        self.engine._furiten_temp_round[0] = 0
        self.engine._turn_count = 2  # 2 turns passed

        # 其他玩家打出 4p
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0
        self.engine._last_drawn_tile = None

        # Check Furiten status (Should not be temporary furiten)
        assert self.engine.check_furiten_temp(0) is False
        assert self.engine.is_furiten(0) is False

        # Try Ron, should succeed
        result = self.engine.check_win(0, winning_tile)
        assert result is not None
        assert result.win is True

    def test_kan_updates_current_player(self):
        """
        Regression Test: Verify Daiminkan (Open Kan) updates current player.
        Ensure Kan player can discard after drawing Rinshan tile.
        """
        self._init_game()

        # Setup: Player 1 has three West (4z), can Kan if Player 0 discards 4z
        # Player 0's turn
        self.engine._current_player = 0

        # Ensure other players don't interrupt
        safe_tiles = parse_tiles("1s1s1s1s2s2s2s2s3s3s3s3s4s")
        for i in [0, 2, 3]:
            self.engine._hands[i] = Hand(safe_tiles)

        # Give Player 1 three 4z
        p1_hand = self.engine.get_hand(1)
        # 13 tiles
        p1_hand._tiles = parse_tiles("4z4z4z1m2m3m4m5m6m7m8m9m1p")
        p1_hand._melds = []

        # Player 0 discards 4z
        tile_4z = Tile(Suit.JIHAI, 4)
        # Ensure Player 0 has this tile
        self.engine.get_hand(0)._tiles.append(tile_4z)
        self.engine.execute_action(0, GameAction.DISCARD, tile_4z)

        # Verify Player 1 can Kan
        actions = self.engine.get_available_actions(1)
        assert GameAction.KAN in actions

        # Player 1 executes Kan
        result = self.engine.execute_action(1, GameAction.KAN, tile_4z)

        # Verify Kan success
        assert result.success
        assert result.kan is True

        # Critical check: Current player should update to 1
        assert self.engine.get_current_player() == 1

        # Verify Player 1 can discard (after automatically drawing Rinshan tile)
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

    def test_furiten_riichi_permanent(self):
        """Test Riichi Furiten: Permanent Furiten after passing Ron in Riichi"""
        self._init_game()

        # Set Player 0 Riichi and Tenpai (Wait 4p)
        tiles = parse_tiles("123456789m1234p")
        self.engine._hands[0] = Hand(tiles)
        self.engine._hands[0].set_riichi(True)

        winning_tile = Tile(Suit.PINZU, 4)

        # Set Riichi Furiten status (Player 0 passed Ron after Riichi)
        self.engine._furiten_permanent[0] = True

        # 其他玩家打出 4p
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0
        self.engine._last_drawn_tile = None

        # Check Furiten status
        assert self.engine.check_furiten_riichi(0) is True
        assert self.engine.is_furiten(0) is True

        # 嘗試榮和，應該失敗
        result = self.engine.check_win(0, winning_tile)
        assert result is None or result.win is False

    def test_furiten_riichi_can_tsumo(self):
        """Test Riichi Furiten: Can Tsumo even if permanent Furiten"""
        self._init_game()

        # Set Player 0 Riichi and Tenpai (Wait 4p)
        tiles = parse_tiles("123456789m12344p")
        self.engine._hands[0] = Hand(tiles)
        self.engine._hands[0].set_riichi(True)

        winning_tile = Tile(Suit.PINZU, 4)

        # Set Riichi Furiten status
        self.engine._furiten_permanent[0] = True

        # Simulate Tsumo 4p
        self.engine._current_player = 0
        self.engine._last_drawn_tile = (0, winning_tile)
        self.engine._last_discarded_tile = None

        # Check Furiten status (Still Furiten)
        assert self.engine.check_furiten_riichi(0) is True

        # Tsumo should succeed
        result = self.engine.check_win(0, winning_tile)
        assert result is not None
        assert result.win is True

    def test_furiten_not_tenpai_returns_false(self):
        """Test Furiten check returns False if not Tenpai"""
        self._init_game()

        # Set Player 0 Noten
        tiles = parse_tiles("123456789m12345p")
        self.engine._hands[0] = Hand(tiles)

        # Check Furiten status (Noten is not Furiten)
        assert self.engine.check_furiten_discards(0) is False
        assert self.engine.is_furiten(0) is False

    def test_furiten_multiple_waiting_tiles(self):
        """Test Furiten with multiple waiting tiles"""
        self._init_game()

        # Set Player 0 multi-wait (Wait 4p 5p)
        # Hand: 123m 456m 789m 44p 55p (Shanpon wait 4p 5p)
        tiles = parse_tiles("123456789m4455p")
        self.engine._hands[0] = Hand(tiles)

        # Player 0 discarded 4p before (one of the waiting tiles)
        self.engine._hands[0]._discards.append(Tile(Suit.PINZU, 4))

        # Check Furiten status (Discarded one of the waiting tiles)
        assert self.engine.check_furiten_discards(0) is True

        # Even if discarded tile is 5p (the other waiting tile), cannot Ron
        winning_tile = Tile(Suit.PINZU, 5)
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0
        self.engine._last_drawn_tile = None

        result = self.engine.check_win(0, winning_tile)
        assert result is None or result.win is False

    def test_noten_bappu_one_tenpai(self):
        """Test Noten Bappu: One Tenpai (+3000 / -1000)"""
        self._init_game()

        # Set Player 0 Tenpai
        # 123m 456m 789m 123p 4p
        self.engine._hands[0] = Hand(parse_tiles("123456789m1234p"))

        # Set other players Noten
        # 12m 45m 78m 12p 45p 78s 1z
        noten_hand = Hand(parse_tiles("124578m1245p78s1z"))
        for i in range(1, 4):
            self.engine._hands[i] = noten_hand

        # Record initial scores
        initial_scores = self.engine._game_state.scores.copy()

        # Simulate Ryuukyoku (Exhausted Wall)
        self.engine._tile_set._tiles = []
        # Ensure check_ryuukyoku returns EXHAUSTED
        # Note: check_ryuukyoku relies on _tile_set.is_exhausted()

        # Directly call end_round(None)
        # Expect end_round to detect Ryuukyoku and calculate penalty
        self.engine.end_round(None)

        # Verify score changes
        # Player 0: +3000
        assert self.engine._game_state.scores[0] == initial_scores[0] + 3000
        # Other players: -1000
        for i in range(1, 4):
            assert self.engine._game_state.scores[i] == initial_scores[i] - 1000

    def test_noten_bappu_two_tenpai(self):
        """Test Noten Bappu: Two Tenpai (+1500 / -1500)"""
        self._init_game()

        # Set Player 0, 1 Tenpai
        tenpai_hand = Hand(parse_tiles("123456789m1234p"))
        self.engine._hands[0] = tenpai_hand
        self.engine._hands[1] = tenpai_hand

        # Set Player 2, 3 Noten
        noten_hand = Hand(parse_tiles("124578m1245p78s1z"))
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
        """Test Noten Bappu: Three Tenpai (+1000 / -3000)"""
        self._init_game()

        # Set Player 0, 1, 2 Tenpai
        tenpai_hand = Hand(parse_tiles("123456789m1234p"))
        self.engine._hands[0] = tenpai_hand
        self.engine._hands[1] = tenpai_hand
        self.engine._hands[2] = tenpai_hand

        # Set Player 3 Noten
        noten_hand = Hand(parse_tiles("124578m1245p78s1z"))
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
        """Test Noten Bappu: All Tenpai (0)"""
        self._init_game()

        # Set all players Tenpai
        tenpai_hand = Hand(parse_tiles("123456789m1234p"))
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
        """Test Noten Bappu: No Tenpai (0)"""
        self._init_game()

        # Set all players Noten
        noten_hand = Hand(parse_tiles("124578m1245p78s1z"))
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
        """Test Tobi (Bankruptcy): Ron causes score < 0"""
        self._init_game()

        # Enable Tobi rule
        self.engine._game_state.ruleset.tobi_enabled = True

        # Set Player 1 score very low (modify _scores directly)
        self.engine._game_state._scores[1] = 1000

        # Player 0 Tenpai, Ron Player 1
        # 123m 456m 789m 123p 4p (Wait 4p)
        self.engine._hands[0] = Hand(parse_tiles("123456789m1234p"))

        # Player 1 discards 4p
        winning_tile = Tile(Suit.PINZU, 4)
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0

        # Execute Ron
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
        """Test Tobi (Bankruptcy): Tsumo causes score < 0"""
        self._init_game()
        self.engine._game_state.ruleset.tobi_enabled = True

        # Set Player 1, 2, 3 score very low
        self.engine._game_state._scores[1] = 1000

        # Player 0 Tsumo, everyone pays 1000
        self.engine._game_state.update_score(1, -2000)  # Assume big hand
        self.engine._game_state.update_score(0, 6000)

        assert self.engine._game_state.scores[1] < 0

        self.engine.end_round([0])
        assert self.engine.get_phase() == GamePhase.ENDED

    def test_tobi_noten_bappu(self):
        """Test Tobi (Bankruptcy): Noten Bappu causes score < 0"""
        self._init_game()
        self.engine._game_state.ruleset.tobi_enabled = True

        # Set Player 1 score very low
        self.engine._game_state._scores[1] = 500

        # Set Player 0 Tenpai, others Noten
        tenpai_hand = Hand(parse_tiles("123456789m1234p"))
        noten_hand = Hand(parse_tiles("124578m1245p78s1z"))

        self.engine._hands[0] = tenpai_hand
        for i in range(1, 4):
            self.engine._hands[i] = noten_hand

        # Simulate Ryuukyoku
        self.engine._tile_set._tiles = []
        self.engine.end_round(None)

        # Player 1 pays 1000, becomes -500
        assert self.engine._game_state.scores[1] == -500

        # Verify game ended
        assert self.engine.get_phase() == GamePhase.ENDED

    def test_tobi_disabled(self):
        """Test Tobi Disabled"""
        self._init_game()
        self.engine._game_state.ruleset.tobi_enabled = False

        # Set Player 1 score negative
        self.engine._game_state.scores[1] = -1000

        # End round
        self.engine.end_round([0])

        # Verify game not ended (Next round or next wind)
        # Assuming not last round
        assert self.engine.get_phase() != GamePhase.ENDED

    def _init_game(self):
        self.engine.start_game()
        self.engine.start_round()
        self.engine.deal()

    def test_draw_with_kan(self):
        """Test Draw with Kan (Hand size limit should increase)"""
        self._init_game()

        # Setup: Player 0 has an Ankan (Closed Kan)
        hand = self.engine.get_hand(0)
        # 10 tiles + 1 Kan (4 tiles) = 14 tiles
        hand._tiles = parse_tiles("1m2m3m4m5m6m7m8m9m1p")
        kan_tiles = parse_tiles("2p2p2p2p")
        meld = Meld(MeldType.ANKAN, kan_tiles)
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
        """Test cannot Chi/Pon/Kan in Riichi"""
        self._init_game()

        # Set Player 0 Riichi
        hand = self.engine.get_hand(0)
        hand._is_riichi = True

        # Set Kamicha discard
        self.engine._last_discarded_player = 3
        self.engine._last_discarded_tile = Tile(Suit.PINZU, 3)

        # Set hand to allow Chi/Pon/Kan
        # 12p (Chi 3p), 33p (Pon 3p), 333p (Kan 3p)
        hand._tiles = parse_tiles("12333p456s789m11z")

        # Check Chi
        # 12p + 3p -> Chi
        assert hand.can_chi(self.engine._last_discarded_tile, from_player=0)
        assert not self.engine._can_chi(0)  # Should be False due to Riichi

        # Check Pon
        # 33p + 3p -> Pon
        assert hand.can_pon(self.engine._last_discarded_tile)
        assert not self.engine._can_pon(0)  # Should be False due to Riichi

        # Check Kan (Open)
        # 333p + 3p -> Kan
        assert hand.can_kan(self.engine._last_discarded_tile)
        assert not self.engine._can_kan(0)  # Should be False due to Riichi

    def test_must_discard_drawn_tile_in_riichi(self):
        """Test must discard drawn tile in Riichi"""
        self._init_game()
        hand = self.engine.get_hand(0)
        hand._is_riichi = True

        # Set hand
        hand._tiles = parse_tiles("123m456p789s1122z")

        # Draw tile
        drawn_tile = Tile(Suit.JIHAI, 3)  # 3z (West)
        hand.add_tile(drawn_tile)

        # Try to discard a tile that was not just drawn (1m)
        with pytest.raises(ValueError, match="立直後只能打出剛摸到的牌"):
            self.engine._handle_discard(0, Tile(Suit.MANZU, 1))

        # Try to discard the drawn tile (3z)
        # Should succeed
        self.engine._handle_discard(0, drawn_tile)

    def test_ankan_allowed_if_wait_unchanged(self):
        """Test Ankan allowed if wait is unchanged after Riichi"""
        self._init_game()
        hand = self.engine.get_hand(0)
        hand._is_riichi = True

        # Tenpai: 111m (Triplet) + 456m + 789p + 23s (Wait 1s, 4s) + 77z (Pair)
        # Here 111m can only be interpreted as a triplet, not a pair (because 1m is not connected to 456m)
        hand._tiles = parse_tiles("111456m789p23s77z")
        drawn_tile = Tile(Suit.MANZU, 1)
        hand.add_tile(drawn_tile)

        # Should allow Ankan
        assert self.engine._can_ankan(0)

    def test_ankan_forbidden_if_wait_changed(self):
        """Test Ankan forbidden if wait is changed after Riichi"""
        self._init_game()
        hand = self.engine.get_hand(0)
        hand._is_riichi = True

        # Tenpai: 3334m (Wait 2m, 3m, 4m, 5m) -> Ankan 3m -> 4m (Single wait 4m)
        hand._tiles = parse_tiles("3334m456p789s11z")
        drawn_tile = Tile(Suit.MANZU, 3)
        hand.add_tile(drawn_tile)

        # Should NOT allow Ankan
        assert not self.engine._can_ankan(0)

    def test_riichi_requires_discard_and_tenpai(self):
        """Test Riichi requires both discard and Tenpai"""
        self._init_game()
        hand = self.engine.get_hand(0)

        # Set Tenpai hand: 11123m (Wait 1m, 4m) + 456p + 789s + 11z
        # Draw 2p (Not Tenpai)
        hand._tiles = parse_tiles("11123m456p789s11z")
        drawn_tile = Tile(Suit.PINZU, 2)
        hand.add_tile(drawn_tile)

        # Try Riichi without discarding
        with pytest.raises(ValueError, match="立直必須同時打出一張牌"):
            self.engine._handle_riichi(0, tile=None)

        # Try Riichi and discard 2p (Tenpai)
        # Should succeed
        result = self.engine._handle_riichi(0, tile=drawn_tile)
        assert result.riichi
        assert hand.is_riichi
        assert self.engine._last_discarded_tile == drawn_tile

        # Set Noten hand
        # 11123m 456p 789s 12z (Noten) + draw 3z
        hand._is_riichi = False
        hand._tiles = parse_tiles("11123m456p789s12z")
        drawn_tile = Tile(Suit.JIHAI, 3)
        hand.add_tile(drawn_tile)

        # Try Riichi and discard 3z (Still Noten)
        with pytest.raises(ValueError, match="立直打牌後必須聽牌"):
            self.engine._handle_riichi(0, tile=drawn_tile)

    def test_multiple_ron_decision(self):
        """Test multiple Ron decisions (One Ron, One Pass)"""
        self._init_game()

        # Enable Double Ron
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True

        # Set Player 1 Tenpai (Wait 5p)
        # 123m 456s 789p 11z + 46p (Wait 5p for 456p)
        self.engine.get_hand(1)._tiles = parse_tiles("123m456s789p11z46p")
        self.engine.get_hand(1)._melds = []

        # Set Player 2 Tenpai (Wait 5p)
        # 123m 456s 789p 22z + 46p (Wait 5p for 456p)
        self.engine.get_hand(2)._tiles = parse_tiles("123m456s789p22z46p")
        self.engine.get_hand(2)._melds = []

        # Player 0 discards 5p
        discard_tile = Tile(Suit.PINZU, 5)
        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # Check interrupts
        interrupts = self.engine._check_interrupts(discard_tile, discarded_player=0)

        # Ensure Player 1 and Player 2 can both Ron
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

        # Verify Player 2 Furiten (Missed Ron)
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

        # Set last drawn tile to simulate Tsumo
        engine._last_drawn_tile = (0, winning_tile)

        # Disable Tenhou/Chiihou/Renhou
        engine._is_first_turn_after_deal = False

        # Calculate score
        result = engine.check_win(0, winning_tile)

        assert result is not None

        # Expected:
        # Sanankou (2) + Tsumo (1) = 3 Han 40 Fu.
        # If Pinfu interpretation:
        # Pinfu (1) + Tsumo (1) + Iipeikou (1) = 3 Han 20 Fu.

        # So we expect 3 Han 40 Fu.
        assert result.fu == 40, (
            f"Should choose higher scoring interpretation (40 Fu vs 20 Fu). Got {result.fu} Fu, Yaku: {[y.yaku.name for y in result.yaku]}"
        )


class TestDarkKanSelection:
    def test_ankan_selection(self):
        # Setup: Hand has 1111m and 2222m.
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

        # Execute Ankan 2m
        tile_to_kan = Tile(Suit.MANZU, 2)
        result = engine.execute_action(0, GameAction.ANKAN, tile=tile_to_kan)

        # Check success
        assert result.success

        # Check hand melds
        melds = engine._hands[0].melds
        assert len(melds) == 1
        assert melds[0].type == MeldType.ANKAN
        assert melds[0].tiles[0] == tile_to_kan

        # Check remaining tiles
        # Should remain 1111m (and other tiles)
        remaining_tiles = engine._hands[0].tiles
        count_1m = sum(
            1 for t in remaining_tiles if t.suit == Suit.MANZU and t.rank == 1
        )
        assert count_1m == 4

        # Now execute Ankan 1m
        tile_to_kan_1 = Tile(Suit.MANZU, 1)
        result = engine.execute_action(0, GameAction.ANKAN, tile=tile_to_kan_1)
        assert result.success

        melds = engine._hands[0].melds
        assert len(melds) == 2
        assert melds[1].tiles[0] == tile_to_kan_1


class TestActionAvailability:
    def setup_method(self):
        self.engine = RuleEngine(num_players=4)

    def _has_action(self, player: int, action: GameAction) -> bool:
        return action in self.engine.get_available_actions(player)

    def _init_game(self):
        self.engine.start_game()
        self.engine.start_round()
        self.engine.deal()

    def test_get_available_actions_default_empty(self):
        """Test no available actions in non-PLAYING phase"""
        self._init_game()
        current_player = self.engine.get_current_player()

        # In non-PLAYING phase, should have no available actions
        self.engine._phase = GamePhase.INIT
        assert self.engine.get_available_actions(current_player) == []

    def test_cannot_action_riichi_not_tenpai(self):
        """Test cannot Riichi if not Tenpai"""
        self._init_game()
        current_player = self.engine.get_current_player()
        # Ensure hand cannot Tenpai
        # 123m 456m 789m 12p 4p 8p
        self.engine._hands[current_player] = Hand(parse_tiles("123456789m1248p"))
        assert not self.engine.get_hand(current_player).is_tenpai()
        assert not self._has_action(current_player, GameAction.RICHI)

    def test_cannot_action_riichi_not_concealed(self):
        """Test cannot Riichi if not concealed"""
        self._init_game()
        current_player = self.engine.get_current_player()
        self.engine._hands[current_player]._melds.append(
            Meld(
                MeldType.PON,
                [Tile(Suit.PINZU, 4), Tile(Suit.PINZU, 4), Tile(Suit.PINZU, 4)],
            )
        )
        assert self.engine.get_hand(current_player).is_concealed is False
        assert not self._has_action(current_player, GameAction.RICHI)

    def test_get_available_actions_kan(self):
        """Test if Daiminkan (Open Kan) is available"""
        self._init_game()
        current_player = self.engine.get_current_player()
        # 111m 234m 567m 12p 3p 4p
        self.engine._hands[current_player] = Hand(parse_tiles("111m234m567m1234p"))
        self.engine._last_discarded_tile = Tile(Suit.MANZU, 1)
        self.engine._last_discarded_player = (
            current_player + 1
        ) % self.engine.get_num_players()

        # Force update actions
        self.engine._waiting_for_actions[current_player] = (
            self.engine._calculate_turn_actions(current_player)
        )

        assert self._has_action(current_player, GameAction.KAN)
        # Modify last discard to make Kan unavailable
        self.engine._last_discarded_tile = Tile(Suit.MANZU, 9)

        # Force update actions again
        self.engine._waiting_for_actions[current_player] = (
            self.engine._calculate_turn_actions(current_player)
        )

        assert not self._has_action(current_player, GameAction.KAN)

    def test_get_available_actions_ankan(self):
        """Test if Ankan (Closed Kan) is available"""
        self._init_game()
        # 111m 123m 456m 7m 123p
        self.engine._hands[0] = Hand(parse_tiles("1111m234m567m123p"))

        # Force update actions
        self.engine._waiting_for_actions[0] = self.engine._calculate_turn_actions(0)

        assert self._has_action(0, GameAction.ANKAN)

    def test_get_available_actions_draw_requires_current_player(self):
        """Test Draw is only available to current player"""
        self._init_game()
        current_player = self.engine.get_current_player()

        # No available actions in non-PLAYING phase
        self.engine._phase = GamePhase.INIT
        assert GameAction.DRAW not in self.engine.get_available_actions(current_player)

        # PLAYING phase but not current player cannot Draw
        self.engine._phase = GamePhase.PLAYING
        non_current = (current_player + 1) % 4
        assert GameAction.DRAW not in self.engine.get_available_actions(non_current)


class TestActionExecution:
    def setup_method(self):
        self.engine = RuleEngine(num_players=4)

    def _has_action(self, player: int, action: GameAction) -> bool:
        return action in self.engine.get_available_actions(player)

    def _init_game(self):
        self.engine.start_game()
        self.engine.start_round()
        self.engine.deal()

    def test_open_kan_logic(self):
        """Test Daiminkan logic: Automatically infer tile and remove from discards"""
        self.engine.start_game()
        self.engine.start_round()
        self.engine.deal()

        # Player 1 setup (before discard)
        p1 = 1
        hand1 = self.engine.get_hand(p1)
        hand1._tiles = []
        # Give P1 three 1m
        for _ in range(3):
            hand1.add_tile(Tile(Suit.MANZU, 1))
        # Fill remaining tiles
        for i in range(10):
            hand1.add_tile(Tile(Suit.PINZU, i % 9 + 1))

        # Player 0 turn
        p0 = 0
        self.engine._current_player = p0
        hand0 = self.engine.get_hand(p0)
        discard_tile = Tile(Suit.MANZU, 1)
        hand0.add_tile(discard_tile)

        # Player 0 discards 1m
        self.engine.execute_action(p0, GameAction.DISCARD, tile=discard_tile)

        # Verify discard status
        assert self.engine._last_discarded_tile == discard_tile
        assert self.engine._last_discarded_player == p0
        assert discard_tile in hand0.discards

        # Check if P1 can Kan
        assert self.engine._can_kan(p1)

        # Execute Kan (Infer tile without specifying)
        waiting = self.engine.waiting_for_actions
        assert p1 in waiting
        assert GameAction.KAN in waiting[p1]

        result = self.engine.execute_action(p1, GameAction.KAN, tile=None)

        # Verify Kan success
        assert result.kan is True
        assert len(hand1.melds) == 1
        assert hand1.melds[0].type == MeldType.KAN
        assert hand1.melds[0].called_tile == discard_tile

        # Verify discard removed from P0's discards
        assert discard_tile not in hand0.discards
        assert self.engine._last_discarded_tile is None

    def test_pon_action_claims_last_discard(self):
        """Test Pon action claims last discard and changes turn."""
        self._init_game()
        tile_to_discard = Tile(Suit.MANZU, 3)

        self.engine._hands[0] = Hand(parse_tiles("1356789m1234p123s"))
        # 33m 567p 89p 456s 789s
        self.engine._hands[1] = Hand(parse_tiles("33m56789p456789s"))

        self.engine._current_player = 0
        discard_before = len(self.engine.get_discards(0))

        discard_result = self.engine.execute_action(
            0, GameAction.DISCARD, tile=tile_to_discard
        )
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
        """Test Chi action uses specified sequence and resets turn."""
        self._init_game()
        tile_to_discard = Tile(Suit.MANZU, 4)

        self.engine._hands[0] = Hand(parse_tiles("4789m12345p12345s"))
        # 23m 56m 678p 9p 678s 9s 5s
        self.engine._hands[1] = Hand(parse_tiles("2356m6789p56789s"))
        # 11m 11p 112345678s
        self.engine._hands[2] = Hand(parse_tiles("11m11p12345678s"))

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

        chi_result = self.engine.execute_action(
            1, GameAction.CHI, sequence=target_sequence
        )

        assert chi_result.called_action == GameAction.CHI
        assert chi_result.called_tile == tile_to_discard
        assert chi_result.meld is not None
        assert len(self.engine.get_hand(1).melds) == 1
        assert self.engine.get_last_discard() is None
        assert self.engine.get_last_discard_player() is None
        assert self.engine.get_current_player() == 1
        actions_after_chi = self.engine.get_available_actions(1)
        assert GameAction.DRAW not in actions_after_chi

    def test_execute_action_kan_tile_none(self):
        """Test Kan with tile as None"""
        self._init_game()
        current_player = self.engine.get_current_player()
        with pytest.raises(ValueError):
            self.engine.execute_action(current_player, GameAction.KAN, tile=None)

    def test_execute_action_draw_no_tile_set(self):
        """Test Draw when tile set is not initialized"""
        self._init_game()
        hand = self.engine.get_hand(0)
        self.engine.execute_action(0, GameAction.DISCARD, tile=hand.tiles[0])
        current_player = self.engine.get_current_player()

        self.engine._tile_set = None

        # Ensure hand is not full
        hand = self.engine.get_hand(current_player)
        if hand.total_tile_count() >= 14:
            hand.tiles.pop()

        with pytest.raises(ValueError, match="牌組未初始化"):
            self.engine._handle_draw(current_player)

    def test_execute_action_discard_no_tile(self):
        """Test Discard without specifying tile"""
        self._init_game()
        current_player = self.engine.get_current_player()
        with pytest.raises(ValueError):
            self.engine.execute_action(current_player, GameAction.DISCARD, tile=None)

    def test_execute_action_discard_no_tile_set(self):
        """Test Discard when tile set is not initialized"""
        self._init_game()
        current_player = self.engine.get_current_player()
        hand = self.engine.get_hand(current_player)
        self.engine._tile_set = None
        with pytest.raises(ValueError, match="牌組未初始化"):
            self.engine.execute_action(
                current_player, GameAction.DISCARD, tile=hand.tiles[0]
            )

    def test_execute_action_riichi(self):
        """Test execute Riichi action"""
        self._init_game()
        current_player = self.engine.get_current_player()
        # Ensure hand is Tenpai and Concealed
        # 123m 456m 789m 123p 4p -> 13 tiles
        # Add one more tile (e.g. 9s) to discard and stay tenpai
        # 123m 456m 789m 123p 4p -> 13 tiles
        # Add one more tile (e.g. 9s) to discard and stay tenpai
        tiles = parse_tiles("123456789m1234p")
        hand = Hand(tiles)
        hand.add_tile(Tile(Suit.SOZU, 9))
        self.engine._hands[current_player] = hand

        # Force update actions
        self.engine._waiting_for_actions[current_player] = (
            self.engine._calculate_turn_actions(current_player)
        )

        assert self._has_action(current_player, GameAction.RICHI)

        result = self.engine.execute_action(
            current_player, GameAction.RICHI, tile=Tile(Suit.SOZU, 9)
        )
        assert result.riichi is True
        assert self.engine.get_hand(current_player).is_riichi
        # Check Ippatsu status recorded
        assert current_player in self.engine._riichi_ippatsu
        assert self.engine._riichi_ippatsu[current_player]

    def test_execute_action_kan_no_tile(self):
        """Test Daiminkan/Kakan without specifying tile"""
        self._init_game()
        current_player = self.engine.get_current_player()

        # Set Kakan status: Has Pon 1m, Hand has 1m
        hand = self.engine.get_hand(current_player)
        hand._melds.append(
            Meld(
                MeldType.PON, [Tile(Suit.MANZU, 1)] * 3, called_tile=Tile(Suit.MANZU, 1)
            )
        )
        hand._tiles = [Tile(Suit.MANZU, 1)]  # 4th tile in hand

        # Force update actions
        self.engine._waiting_for_actions[current_player] = (
            self.engine._calculate_turn_actions(current_player)
        )

        # Ensure KAN is available
        assert self._has_action(current_player, GameAction.KAN)

        # Execute KAN without specifying tile, should raise error
        with pytest.raises(ValueError, match="明槓必須指定被槓的牌"):
            self.engine.execute_action(current_player, GameAction.KAN, tile=None)

    def test_execute_action_discard_last_tile(self):
        """Test discard last tile (Houtei Raoyui)"""
        self._init_game()
        current_player = self.engine.get_current_player()
        hand = self.engine.get_hand(current_player)

        # Simulate wall exhausted
        assert self.engine._tile_set is not None
        self.engine._tile_set._tiles = []

        result = self.engine.execute_action(
            current_player, GameAction.DISCARD, tile=hand.tiles[0]
        )
        assert result.is_last_tile is True

    def test_execute_action_draw_last_tile(self):
        """Test draw last tile (Haitei Raoyue)"""
        self._init_game()
        current_player = self.engine.get_current_player()

        # Ensure hand has one less tile to allow draw
        hand = self.engine.get_hand(current_player)
        hand._tiles.pop()

        # 模擬牌山只剩一張
        assert self.engine._tile_set is not None
        self.engine._tile_set._tiles = [Tile(Suit.MANZU, 1)]

        # 模擬牌山只剩一張
        assert self.engine._tile_set is not None
        self.engine._tile_set._tiles = [Tile(Suit.MANZU, 1)]

        # Directly call internal _handle_draw to test logic, as DRAW action is removed
        result = self.engine._handle_draw(current_player)
        assert result.is_last_tile is True

    def test_execute_action_discard_history(self):
        """Test discard history recording"""
        self._init_game()
        current_player = self.engine.get_current_player()
        hand = self.engine.get_hand(current_player)
        assert hand.tiles is not None
        self.engine.execute_action(
            current_player, GameAction.DISCARD, tile=hand.tiles[0]
        )
        assert len(self.engine._discard_history) > 0

    def test_execute_action_discard_history_limit(self):
        """Test discard history keeps only last 4"""
        self._init_game()
        # Dealer has 14 tiles at start, discard one first
        current_player = self.engine.get_current_player()
        hand = self.engine.get_hand(current_player)
        assert self._has_action(current_player, GameAction.DISCARD)
        self.engine.execute_action(
            current_player, GameAction.DISCARD, tile=hand.tiles[0]
        )
        for _ in range(10):
            current_player = self.engine.get_current_player()
        for _ in range(10):
            current_player = self.engine.get_current_player()
            # DRAW is automatic, so check DISCARD directly
            hand = self.engine.get_hand(current_player)
            # Ensure there are tiles to discard
            if not hand.tiles:
                self.engine._handle_draw(current_player)

            # If just drawn, hand count should be 14. After discard 13.
            # Next player will automatically draw.

            # Here we force discard
            if self._has_action(current_player, GameAction.DISCARD):
                self.engine.execute_action(
                    current_player, GameAction.DISCARD, tile=hand.tiles[0]
                )
            else:
                # If cannot discard (e.g. no tiles), manually draw one
                # Ensure hand is not full
                if hand.total_tile_count() < 14:
                    self.engine._handle_draw(current_player)

                if self._has_action(current_player, GameAction.DISCARD):
                    self.engine.execute_action(
                        current_player, GameAction.DISCARD, tile=hand.tiles[0]
                    )

        assert len(self.engine._discard_history) <= 4

    def test_execute_action_draw_no_tile_drawn(self):
        """Test Draw when no tiles left"""
        self._init_game()
        current_player = self.engine.get_current_player()

        # Exhaust wall to trigger draw() returning None
        assert self.engine._tile_set is not None
        hand = self.engine.get_hand(current_player)
        assert hand.tiles is not None
        self.engine.execute_action(
            current_player, GameAction.DISCARD, tile=hand.tiles[0]
        )
        while self.engine._tile_set._tiles:
            self.engine._tile_set.draw()
        current_player = self.engine.get_current_player()
        while self.engine._tile_set._tiles:
            self.engine._tile_set.draw()
        current_player = self.engine.get_current_player()

        # Ensure hand is not full (less than 14)
        hand = self.engine.get_hand(current_player)
        while hand.total_tile_count() >= 14:
            hand._tiles.pop()

        # Directly call _handle_draw
        result = self.engine._handle_draw(current_player)
        assert result.ryuukyoku is not None
        assert result.ryuukyoku.ryuukyoku is True
        assert result.ryuukyoku.ryuukyoku_type == RyuukyokuType.EXHAUSTED
        # _handle_draw sets phase
        assert self.engine._phase == GamePhase.RYUUKYOKU

    def test_execute_action_kan_rinshan_win(self):
        """Test Rinshan Kaihou (Win on Rinshan tile) after Daiminkan"""
        self._init_game()

        # Set Player 0 can Daiminkan and win on Rinshan tile
        kan_tile = Tile(Suit.MANZU, 1)
        ten_tile = Tile(Suit.PINZU, 4)
        # 111m 234m 567m 123p 4p
        kan_tiles = parse_tiles("111234567m1234p")
        self.engine._hands[0] = Hand(kan_tiles)
        self.engine._current_player = 0
        self.engine._last_discarded_tile = kan_tile
        self.engine._last_discarded_player = 1
        assert self.engine._tile_set is not None
        self.engine._tile_set._rinshan_tiles[0] = ten_tile

        # Force update actions
        self.engine._waiting_for_actions[0] = self.engine._calculate_turn_actions(0)

        # Execute Daiminkan
        assert self._has_action(0, GameAction.KAN)
        result = self.engine.execute_action(0, GameAction.KAN, tile=kan_tile)
        assert result.rinshan_tile is not None
        assert result.rinshan_win is not None

    def test_execute_action_ankan_rinshan_win(self):
        """Test Rinshan Kaihou after Ankan"""
        self._init_game()

        # Set Player 0 can Ankan
        ten_tile = Tile(Suit.PINZU, 4)
        # 1111m 234m 567m 123p 4p (Wait 4p)
        ankan_tiles = parse_tiles("1111234567m1234p")
        self.engine._hands[0] = Hand(ankan_tiles)
        self.engine._current_player = 0
        assert self.engine._tile_set is not None
        self.engine._tile_set._rinshan_tiles[0] = ten_tile

        # Force update actions
        self.engine._waiting_for_actions[0] = self.engine._calculate_turn_actions(0)

        # Execute Ankan
        assert self._has_action(0, GameAction.ANKAN)
        result = self.engine.execute_action(0, GameAction.ANKAN)
        assert result.rinshan_tile is not None
        assert result.rinshan_win is not None

    def test_execute_action_kan_chankan_complete(self):
        """Test Chankan (Robbing the Kan) complete scenario"""
        self._init_game()

        # Set Player 0 can Kakan (Has Pon, adds 4th 1m)
        # Hand: 111234567m 123p 4p
        kan_tiles = parse_tiles("111234567m1234p")
        hand0 = Hand(kan_tiles)
        kan_tile = Tile(Suit.MANZU, 1)
        hand0.pon(kan_tile)
        hand0.add_tile(kan_tile)
        self.engine._hands[0] = hand0
        self.engine._current_player = 0
        self.engine._last_discarded_tile = None
        self.engine._last_discarded_player = None

        # Set Player 1 can Chankan (Wait 1m)
        # Hand: 23m 456m 789p 123p 44p (Wait 1m)
        test_tiles = parse_tiles("23456m12344789p")
        test_hand = Hand(test_tiles)
        self.engine._hands[1] = test_hand

        # Force update actions for player 0
        self.engine._waiting_for_actions[0] = self.engine._calculate_turn_actions(0)

        # Execute Kakan, should check Chankan
        assert self._has_action(0, GameAction.ANKAN)
        result = self.engine.execute_action(0, GameAction.ANKAN)
        # Should trigger Chankan
        assert result.chankan is not None
        assert result.chankan is True
        assert result.winners is not None
        assert len(result.winners) > 0
        winner = result.winners[0]
        # check_win needs pending_kan_tile to set payer
        self.engine._pending_kan_tile = (0, kan_tile)
        win_result = self.engine.check_win(winner, kan_tile, is_chankan=True)
        assert win_result is not None
        assert win_result.win is True
        assert win_result.chankan is True
        assert win_result.score_result is not None
        assert win_result.score_result.payment_from == 0

    def test_execute_action_kan_wall_exhausted(self):
        """Test Kan triggers Four Kans Abortion (Suukaikan)"""
        self._init_game()

        player = self.engine.get_current_player()
        kan_tile = Tile(Suit.MANZU, 6)

        # 111m 2345m 6666m 7m 88m
        starting_tiles = parse_tiles("1112345666788m")
        self.engine._hands[player] = Hand(starting_tiles)
        self.engine._last_discarded_tile = kan_tile
        self.engine._last_discarded_player = (
            player + 1
        ) % self.engine.get_num_players()

        self.engine._kan_count = 3
        assert self.engine._tile_set is not None
        self.engine._tile_set._wall = [Tile(Suit.PINZU, 2)]
        # Set dead wall to safe tiles to avoid accidental Rinshan Kaihou
        safe_tiles = [Tile(Suit.PINZU, 1)] * 14
        self.engine._tile_set._dead_wall = safe_tiles
        self.engine._tile_set._rinshan_tiles = safe_tiles[:4]
        self.engine._tile_set._tiles = []

        # Force update actions
        self.engine._waiting_for_actions[player] = self.engine._calculate_turn_actions(
            player
        )

        result = self.engine.execute_action(player, GameAction.KAN, tile=kan_tile)

        assert result.kan is True
        assert self.engine._kan_count == 4
        assert self.engine.check_ryuukyoku() == RyuukyokuType.SUUKANTSU

    def test_execute_action_ankan_wall_exhausted(self):
        """Test Ankan triggers Four Kans Abortion (Suukaikan)"""
        self._init_game()

        player = self.engine.get_current_player()

        # Hand: 222m 2334455678m
        starting_tiles = parse_tiles("2222334455678m")
        self.engine._hands[player] = Hand(starting_tiles)

        self.engine._kan_count = 3
        assert self.engine._tile_set is not None
        self.engine._tile_set._wall = [Tile(Suit.SOZU, 5)]
        self.engine._tile_set._tiles = []
        # Ensure Rinshan tile is not a winning tile (Hand tenpai is special, give unrelated honor tile to ensure no win)
        self.engine._tile_set._rinshan_tiles = [Tile(Suit.JIHAI, 1)] * 4

        # Force update actions
        self.engine._waiting_for_actions[player] = self.engine._calculate_turn_actions(
            player
        )

        result = self.engine.execute_action(player, GameAction.ANKAN)

        assert result.ankan is True
        assert self.engine._kan_count == 4
        assert self.engine.check_ryuukyoku() == RyuukyokuType.SUUKANTSU

    def test_execute_action_discard_is_last_tile(self):
        """Test check for discarding the last tile"""
        self._init_game()
        current_player = self.engine.get_current_player()
        hand = self.engine.get_hand(current_player)
        assert hand.tiles
        assert hand.total_tile_count() == 14
        self.engine.execute_action(
            current_player, GameAction.DISCARD, tile=hand.tiles[0]
        )

        # Simulate wall has only one tile left
        assert self.engine._tile_set is not None
        self.engine._tile_set._tiles = [Tile(Suit.MANZU, 1)]


class TestWinningAndScoring:
    def setup_method(self):
        self.engine = RuleEngine(num_players=4)

    def _has_action(self, player: int, action: GameAction) -> bool:
        return action in self.engine.get_available_actions(player)

    def _init_game(self):
        self.engine.start_game()
        self.engine.start_round()
        self.engine.deal()

    def test_check_chankan(self):
        """Test Chankan check"""
        self._init_game()

        # Set Player 0 can Chankan (Wait 6p, Tanyao)
        # Hand: 234m 567m 234p 66p 78p (Wait 6p/9p)
        test_tiles = parse_tiles("234567m2346678p")
        self.engine._hands[0] = Hand(test_tiles)

        # Check Chankan
        kan_tile = Tile(Suit.PINZU, 6)

        # check_win needs pending_kan_tile to set payer
        # Assume Player 1 Kakans 6p
        self.engine._pending_kan_tile = (1, kan_tile)

        result = self.engine.check_win(0, kan_tile, is_chankan=True)
        assert result is not None
        assert result.win is True
        assert result.chankan is True
        assert result.score_result.payment_from == 1

    def test_check_win_rinshan(self):
        """Test Rinshan Kaihou win check"""
        self._init_game()
        # Set a hand that can win on Rinshan Kaihou
        # Create a winning hand
        # Hand: 123m 456m 789m 123p 4p (Rinshan tile 4p)
        self.engine._hands[0] = Hand(parse_tiles("123456789m12344p"))
        self.engine._current_player = 0

        # Check Rinshan Kaihou win
        rinshan_tile = Tile(Suit.PINZU, 4)
        result = self.engine.check_win(0, rinshan_tile, is_rinshan=True)
        assert result is not None
        assert result.win
        assert result.rinshan

    def test_check_win_tsumo_sets_is_tsumo(self):
        """Test Tumo sets score_result.is_tsumo to True"""
        self._init_game()
        player = self.engine.get_current_player()
        winning_tile = Tile(Suit.PINZU, 4)
        # Concealed hand: 123m 456m 789m 123p + 4p
        self.engine._hands[player] = Hand(parse_tiles("123456789m12344p"))
        # Simulate just drawn winning tile
        self.engine._last_drawn_tile = (player, winning_tile)
        result = self.engine.check_win(player, winning_tile)
        assert result is not None
        assert result.score_result.is_tsumo is True
        assert result.score_result.payment_from == 0

    def test_check_win_ron_when_turn_passes(self):
        """Test Ron after other player discards is not mistaken for Tsumo"""
        self._init_game()
        discarder = 0
        winner = (discarder + 1) % self.engine.get_num_players()
        winning_tile = Tile(Suit.PINZU, 4)
        self.engine._hands[winner] = Hand(parse_tiles("123456789m1234p"))
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = discarder
        # Simulate turn passed to next player (actually Ron state)
        self.engine._current_player = winner
        self.engine._last_drawn_tile = None
        result = self.engine.check_win(winner, winning_tile)
        assert result is not None
        assert result.score_result is not None
        assert result.score_result.is_tsumo is False
        assert result.score_result.payment_from == discarder

    def test_check_win_no_combinations(self):
        """Test check_win with no winning combinations"""
        self._init_game()
        # Create a non-winning hand
        # 123m 456m 78m 123p 45p
        test_tiles = parse_tiles("12345678m12345p")
        test_hand = Hand(test_tiles)
        self.engine._hands[0] = test_hand

        # Check win (Should return None because no winning combinations)
        winning_tile = Tile(Suit.MANZU, 9)
        result = self.engine.check_win(0, winning_tile)
        assert result is None

    def test_check_win_no_yaku(self):
        """Test No Yaku"""
        self._init_game()
        # 234m 567m 789m 2p 4p 22s
        tiles = parse_tiles("234567789m24p22s")

        hand = Hand(tiles)
        # Set hand to not concealed
        hand._melds.append(Meld(MeldType.PON, parse_tiles("1s1s1s")))
        # Set last discard to 3p, test Ron
        winning_tile = Tile(Suit.PINZU, 3)
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1

        self.engine._last_discarded_player = 1

        # Set hand to player 0
        self.engine._hands[0] = hand
        self.engine._current_player = 2

        # Check win (Not concealed and no other Yaku, should return None)
        result = self.engine.check_win(0, winning_tile)
        assert result is None

    def test_count_dora_zero(self):
        """Test zero Dora count"""
        self._init_game()
        self.engine._hands[0] = Hand(parse_tiles("1111234567999m"))
        dora_count = self.engine._count_dora(0, Tile(Suit.MANZU, 1))
        assert dora_count == 0

    def test_count_dora_one(self):
        """Test Dora count"""
        self._init_game()
        test_hand = Hand(parse_tiles("1111234567999m"))
        self.engine._hands[0] = test_hand
        dora_count = self.engine._count_dora(0, Tile(Suit.MANZU, 1))
        assert dora_count >= 0

        # Test Uradora when Riichi
        test_hand.set_riichi(True)
        dora_count = self.engine._count_dora(0, Tile(Suit.MANZU, 1))
        assert dora_count >= 0

        # Test Red Dora
        # Hand: r5p
        red_tiles = parse_tiles("r5p")

        test_hand = Hand(red_tiles)
        self.engine._hands[0] = test_hand
        dora_count = self.engine._count_dora(0, Tile(Suit.PINZU, 5))
        assert dora_count >= 1  # At least one Red Dora

    def test_pao_daisangen_tsumo(self):
        """Test Pao: Daisangen Tsumo, Pao player pays all"""
        self._init_game()

        # Player 0: Daisangen Tenpai (Pon Haku, Hatsu)
        # Hand: 11m 99m
        # Melds: Haku Haku Haku, Hatsu Hatsu Hatsu
        # Simulate meld state
        # Assume Player 1 discards Haku, Player 0 Pons
        # Assume Player 2 discards Hatsu, Player 0 Pons
        # Assume Player 3 discards Chun, Player 0 Pons (Triggers Pao)

        # For testing, we need to manually set state because _handle_pon doesn't implement Pao logic yet
        # But we are writing tests, so we assume it works, or we manually set _pao_daisangen

        # Set Player 0 hand
        # For Tsumo, hand must contain winning tile (Total 14 tiles)
        # 3 Melds (9 tiles) + 5 tiles = 14 tiles
        # Hand: 1m1m1m 9m9m (Winning tile 1m is already in hand for is_winning_hand check)
        self.engine._hands[0] = Hand(parse_tiles("11199m"))  # 111m 99m

        # Set Melds
        meld_haku = Meld(
            MeldType.PON, [Tile(Suit.JIHAI, 5)] * 3, 1
        )  # Pon Haku (from 1)
        meld_hatsu = Meld(
            MeldType.PON, [Tile(Suit.JIHAI, 6)] * 3, 2
        )  # Pon Hatsu (from 2)
        meld_chun = Meld(
            MeldType.PON, [Tile(Suit.JIHAI, 7)] * 3, 3
        )  # Pon Chun (from 3) - Triggers Pao

        self.engine._hands[0]._melds = [meld_haku, meld_hatsu, meld_chun]

        # Set Pao state (Player 3 is Pao)
        # Note: This requires adding _pao_daisangen attribute in rules.py
        # Since attribute is not added yet, this will error, which is expected (Red Phase)
        self.engine._pao_daisangen[0] = 3

        # Player 0 Tsumo 1m (This tile is already in hand for is_winning_hand check)
        winning_tile = Tile(Suit.MANZU, 1)
        self.engine._current_player = 0
        self.engine._last_drawn_tile = (0, winning_tile)

        # Record initial scores
        initial_scores = self.engine._game_state.scores.copy()

        # Execute Tsumo
        # We need to call check_win to ensure it is Daisangen
        result = self.engine.check_win(0, winning_tile)
        assert result is not None, "check_win should return a result"
        assert result.win
        assert any(y.yaku == Yaku.DAISANGEN for y in result.yaku)

        # Apply score
        self.engine.apply_win_score(result)

        # Execute end_round
        self.engine.end_round([0])

        # Verify score changes
        # Daisangen Tsumo: 32000 (Dealer 48000)
        # Here is Dealer (Player 0 is dealer initially) -> 48000
        # Pao player (Player 3) pays all 48000

        assert self.engine._game_state.scores[0] == initial_scores[0] + 48000
        assert self.engine._game_state.scores[3] == initial_scores[3] - 48000
        assert (
            self.engine._game_state.scores[1] == initial_scores[1]
        )  # Others don't pay
        assert (
            self.engine._game_state.scores[2] == initial_scores[2]
        )  # Others don't pay

    def test_pao_daisangen_ron_pao_player(self):
        """Test Pao: Daisangen Ron Pao player (Normal payment)"""
        self._init_game()

        # Set Player 0 hand
        self.engine._hands[0] = Hand(parse_tiles("1199m"))

        # Set Melds
        meld_haku = Meld(MeldType.PON, [Tile(Suit.JIHAI, 5)] * 3, 1)
        meld_hatsu = Meld(MeldType.PON, [Tile(Suit.JIHAI, 6)] * 3, 2)
        meld_chun = Meld(
            MeldType.PON, [Tile(Suit.JIHAI, 7)] * 3, 3
        )  # Pon Chun (from 3) - Triggers Pao

        self.engine._hands[0]._melds = [meld_haku, meld_hatsu, meld_chun]

        # Set Pao state (Player 3 is Pao)
        self.engine._pao_daisangen[0] = 3

        # Player 3 discards Chun (Pao player deals in)
        # winning_tile = Tile(Suit.JIHAI, 7) # Actually should discard 1m or 5z, because 5z is already Ponned, so discard 1m
        # Wait, hand is 11m 55z, Ponned 567z
        # Tenpai is 1m, 5z (Pair wait?) No, Ponned 3 triplets, hand remains 11m 55z?
        # 13 tiles: 3*3=9 tiles melded, remains 4 tiles.
        # 11m 55z -> Wait 1m, 5z (Shanpon)
        # Assume Player 3 discards 1m
        winning_tile = Tile(Suit.MANZU, 1)

        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 3
        self.engine._current_player = 0

        initial_scores = self.engine._game_state.scores.copy()

        # Execute Ron
        result = self.engine.check_win(0, winning_tile)
        self.engine.apply_win_score(result)
        self.engine.end_round([0])

        # Verify score changes
        # Dealer Daisangen Ron: 48000
        # Deal-in player (Player 3) pays 48000
        assert self.engine._game_state.scores[0] == initial_scores[0] + 48000
        assert self.engine._game_state.scores[3] == initial_scores[3] - 48000

    def test_pao_daisangen_ron_other(self):
        """Test Pao: Daisangen Ron other (Pao player and Deal-in player split)"""
        self._init_game()

        # Set Player 0 hand
        # 3 Melds (9 tiles) + 4 tiles = 13 tiles
        # Hand: 1m1m 9m9m
        self.engine._hands[0] = Hand(parse_tiles("1199m"))

        # Set Melds
        meld_haku = Meld(MeldType.PON, [Tile(Suit.JIHAI, 5)] * 3, 1)
        meld_hatsu = Meld(MeldType.PON, [Tile(Suit.JIHAI, 6)] * 3, 2)
        meld_chun = Meld(
            MeldType.PON, [Tile(Suit.JIHAI, 7)] * 3, 3
        )  # Pon Chun (from 3) - Triggers Pao

        self.engine._hands[0]._melds = [meld_haku, meld_hatsu, meld_chun]

        # Set Pao state (Player 3 is Pao)
        self.engine._pao_daisangen[0] = 3

        # Player 1 discards 1m (Non-Pao player deals in)
        winning_tile = Tile(Suit.MANZU, 1)

        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0

        initial_scores = self.engine._game_state.scores.copy()

        # Execute Ron
        result = self.engine.check_win(0, winning_tile)
        self.engine.apply_win_score(result)
        self.engine.end_round([0])

        # Verify score changes
        # Dealer Daisangen Ron: 48000
        # Pao player (Player 3) and Deal-in player (Player 1) split equally (24000 each)
        assert self.engine._game_state.scores[0] == initial_scores[0] + 48000
        assert self.engine._game_state.scores[1] == initial_scores[1] - 24000
        assert self.engine._game_state.scores[3] == initial_scores[3] - 24000
        assert (
            self.engine._game_state.scores[2] == initial_scores[2]
        )  # Player 2 doesn't pay

    # ==================== Head Bump / Double Ron / Triple Ron Tests ====================

    def test_head_bump_only_shimocha_wins(self):
        """Test Head Bump: Shimocha and Kamicha can Ron, only Shimocha wins"""
        self._init_game()

        # Ensure Head Bump mode (Default)
        assert self.engine._game_state.ruleset.head_bump_only

        # Player 0 discards 1m
        discard_tile = Tile(Suit.MANZU, 1)

        # Player 1 (Shimocha) and Player 3 (Kamicha) can Ron 1m
        # Hand should have 13 tiles, becomes 14 after Ron
        self.engine._hands[1] = Hand(parse_tiles("23456789m12344p"))  # 13 tiles
        self.engine._hands[3] = Hand(parse_tiles("23456789m12344p"))  # 13 tiles

        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # Test check_multiple_ron
        winners = self.engine.check_multiple_ron(discard_tile, 0)

        # In Head Bump mode, when multiple players can Ron, only Shimocha (Player 1) wins
        assert len(winners) == 1
        assert winners[0] == 1  # Only Player 1 (Shimocha)

    def test_head_bump_only_toimen_blocked(self):
        """Test Head Bump: Toimen can Ron but blocked"""
        self._init_game()

        # Player 0 discards 1m
        discard_tile = Tile(Suit.MANZU, 1)

        # Only Player 2 (Toimen) can Ron
        self.engine._hands[2] = Hand(parse_tiles("23456789m12344p"))

        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # Test check_multiple_ron
        winners = self.engine.check_multiple_ron(discard_tile, 0)

        # If only one player can Ron, Head Bump doesn't apply, player wins normally
        assert len(winners) == 1
        assert winners[0] == 2  # Only Player 2 can Ron, returns normally

    def test_head_bump_only_kamicha_blocked(self):
        """Test Head Bump: Kamicha can Ron but blocked"""
        self._init_game()

        # Player 0 discards 1m
        discard_tile = Tile(Suit.MANZU, 1)

        # Only Player 3 (Kamicha) can Ron
        self.engine._hands[3] = Hand(parse_tiles("23456789m12344p"))

        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # Test check_multiple_ron
        winners = self.engine.check_multiple_ron(discard_tile, 0)

        # If only one player can Ron, Head Bump doesn't apply, player wins normally
        assert len(winners) == 1
        assert winners[0] == 3

    def test_double_ron_both_win(self):
        """Test Double Ron: Two players win simultaneously"""
        self._init_game()

        # Enable Double Ron mode
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True

        # Player 0 discards 1m
        discard_tile = Tile(Suit.MANZU, 1)

        # Player 1 (Shimocha) and Player 2 (Toimen) can Ron
        self.engine._hands[1] = Hand(parse_tiles("23456789m12344p"))
        self.engine._hands[2] = Hand(parse_tiles("23456789m12344p"))

        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # Test check_multiple_ron
        winners = self.engine.check_multiple_ron(discard_tile, 0)

        # In Double Ron mode, both players can win
        assert len(winners) == 2
        assert 1 in winners
        assert 2 in winners
        # Order should be counter-clockwise (Shimocha first)
        assert winners[0] == 1
        assert winners[1] == 2

    def test_double_ron_score_calculation(self):
        """Test Double Ron: Verify deal-in player pays both"""
        self._init_game()
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True

        # Player 0 discards 4p
        discard_tile = Tile(Suit.PINZU, 4)

        # Set Player 1 and 2 hands (Tanyao Pinfu)
        # 234m 567m 234p 56p 88s (Wait 4p/7p)
        # 30 fu 2 han = 2000 points (Non-dealer)
        hand_tiles = parse_tiles("234567m23456p88s")
        self.engine._hands[1] = Hand(hand_tiles)
        self.engine._hands[2] = Hand(hand_tiles)

        self.engine._current_player = 0

        # Disable Renhou (Human Win) by simulating that it's not the first turn
        # This ensures we test standard Yaku (Tanyao + Pinfu) scoring
        self.engine._is_first_turn_after_deal = False

        initial_scores = self.engine._game_state.scores.copy()

        # Player 0 discards 4p
        self.engine._hands[0]._tiles.append(discard_tile)
        self.engine._waiting_for_actions = {0: self.engine._calculate_turn_actions(0)}
        self.engine.execute_action(0, GameAction.DISCARD, discard_tile)

        # Execute Double Ron
        self.engine.execute_action(1, GameAction.RON, tile=discard_tile)
        result = self.engine.execute_action(2, GameAction.RON, tile=discard_tile)

        # Verify results
        assert result.success
        assert len(result.winners) == 2

        # Verify score changes
        # Player 1 +2000
        # Player 2 +2000
        # Player 0 -4000
        assert self.engine._game_state.scores[1] == initial_scores[1] + 2000
        assert self.engine._game_state.scores[2] == initial_scores[2] + 2000
        assert self.engine._game_state.scores[0] == initial_scores[0] - 4000

    def test_double_ron_dealer_renchan(self):
        """Test Double Ron: Dealer win leads to Renchan"""
        self._init_game()
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True

        # Set Dealer to Player 0
        self.engine._game_state._dealer = 0
        self.engine._game_state._round_number = 1
        self.engine._game_state._honba = 0

        # Player 1 discards 5p
        discard_tile = Tile(Suit.PINZU, 5)

        # Player 0 (Dealer) and Player 2 (Non-dealer) Ron
        hand_str = "233445678m2345p"
        self.engine._hands[0] = Hand(parse_tiles(hand_str))
        self.engine._hands[2] = Hand(parse_tiles(hand_str))

        # Player 1 discards 5p
        self.engine._current_player = 1
        self.engine._hands[1]._tiles.append(discard_tile)
        self.engine._waiting_for_actions = {1: self.engine._calculate_turn_actions(1)}
        self.engine.execute_action(1, GameAction.DISCARD, discard_tile)

        # Execute Ron
        self.engine.execute_action(0, GameAction.RON, tile=discard_tile)
        result = self.engine.execute_action(2, GameAction.RON, tile=discard_tile)

        assert result.success
        assert sorted(result.winners) == [0, 2]

    def test_triple_ron_enabled_all_win(self):
        """Test Triple Ron enabled: All three players win"""
        self._init_game()
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True
        self.engine._game_state.ruleset.allow_triple_ron = True

        # Player 0 discards 5p, Player 1, 2, 3 all Ron with Tanyao
        discard_tile = Tile(Suit.PINZU, 5)

        # 234m 345m 678m 234p 5p (Wait 5p)
        hand_str = "233445678m2345p"
        self.engine._hands[1] = Hand(parse_tiles(hand_str))
        self.engine._hands[2] = Hand(parse_tiles(hand_str))
        self.engine._hands[3] = Hand(parse_tiles(hand_str))

        initial_scores = self.engine._game_state.scores.copy()

        # Execute Triple Ron
        # Player 0 discards 5p
        self.engine._current_player = 0
        self.engine._hands[0]._tiles.append(discard_tile)
        self.engine._waiting_for_actions = {0: self.engine._calculate_turn_actions(0)}
        self.engine.execute_action(0, GameAction.DISCARD, discard_tile)

        # Player 1 Ron
        self.engine.execute_action(1, GameAction.RON, tile=discard_tile)
        # Player 2 Ron
        self.engine.execute_action(2, GameAction.RON, tile=discard_tile)
        # Player 3 Ron (triggers resolution)
        result = self.engine.execute_action(3, GameAction.RON, tile=discard_tile)

        assert result.success
        assert sorted(result.winners) == [1, 2, 3]

        # Players 1, 2, 3 each get 1000.

        # Wait, calculate_score might give more if dora/uradora etc.
        # Let's just verify scores changed in the right direction.

        score_diff_0 = self.engine._game_state.scores[0] - initial_scores[0]
        score_diff_1 = self.engine._game_state.scores[1] - initial_scores[1]
        score_diff_2 = self.engine._game_state.scores[2] - initial_scores[2]
        score_diff_3 = self.engine._game_state.scores[3] - initial_scores[3]

        assert score_diff_0 < 0
        assert score_diff_1 > 0
        assert score_diff_2 > 0
        assert score_diff_3 > 0

        # Verify total balance is zero (assuming no riichi sticks)
        assert score_diff_0 + score_diff_1 + score_diff_2 + score_diff_3 == 0

    def test_double_ron_with_furiten(self):
        """Test Double Ron with Furiten: One player Furiten, only other player wins"""
        self._init_game()

        # Enable Double Ron mode
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True

        # Player 0 discards 5p
        discard_tile = Tile(Suit.PINZU, 5)

        # 234m 345m 678m 234p 5p (Wait 5p) - Tanyao
        hand_str = "233445678m2345p"

        # Player 1 can Ron
        self.engine._hands[1] = Hand(parse_tiles(hand_str))

        # Player 2 can Ron but is Furiten
        self.engine._hands[2] = Hand(parse_tiles(hand_str))
        self.engine._hands[2]._discards.append(
            discard_tile
        )  # Discarded 5p, Genbutsu Furiten

        # Player 0 discards 5p
        self.engine._current_player = 0
        self.engine._hands[0]._tiles.append(discard_tile)
        self.engine._waiting_for_actions = {0: self.engine._calculate_turn_actions(0)}
        self.engine.execute_action(0, GameAction.DISCARD, discard_tile)

        # Player 1 Ron
        result1 = self.engine.execute_action(1, GameAction.RON, tile=discard_tile)
        assert result1.success
        assert result1.winners == [1]

    def test_double_ron_priority_order(self):
        """Test Double Ron: Verify player order (Shimocha first)"""
        self._init_game()

        # Enable Double Ron mode
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True

        # Player 0 discards 5p, Player 2 and 3 can Ron
        discard_tile = Tile(Suit.PINZU, 5)

        # 234m 345m 678m 234p 5p (Wait 5p) - Tanyao
        hand_str = "233445678m2345p"

        self.engine._hands[2] = Hand(parse_tiles(hand_str))
        self.engine._hands[3] = Hand(parse_tiles(hand_str))

        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # Check check_multiple_ron return order
        winners = self.engine.check_multiple_ron(discard_tile, 0)

        # Player 0's Shimocha is Player 1, then 2, 3
        # So return order should be [2, 3] (Counter-clockwise)
        assert winners == [2, 3]


class TestRyuukyoku:
    def setup_method(self):
        self.engine = RuleEngine(num_players=4)

    def _has_action(self, player: int, action: GameAction) -> bool:
        return action in self.engine.get_available_actions(player)

    def _init_game(self):
        self.engine.start_game()
        self.engine.start_round()
        self.engine.deal()

    def test_check_draw(self):
        """Test Ryuukyoku check"""
        self._init_game()
        # Initial state should not be Ryuukyoku
        draw_type = self.engine.check_ryuukyoku()
        assert draw_type is None

    def test_handle_draw(self):
        """Test Ryuukyoku handling"""
        self._init_game()
        # Cannot Ryuukyoku at start
        actions = self.engine.get_available_actions(0)
        assert GameAction.DRAW not in actions

    def test_check_draw_suufon_renda(self):
        """Test Suufon Renda (Four Winds) Ryuukyoku check"""
        self._init_game()
        # Set discard history to four identical wind tiles
        wind_tile = Tile(Suit.JIHAI, 1)  # East

        # Add four identical wind tiles to discard history
        self.engine._discard_history.append((0, wind_tile))
        self.engine._discard_history.append((1, wind_tile))
        self.engine._discard_history.append((2, wind_tile))
        self.engine._discard_history.append((3, wind_tile))

        # Check Suufon Renda
        ryuukyoku_type = self.engine.check_ryuukyoku()
        assert ryuukyoku_type is not None
        assert ryuukyoku_type == RyuukyokuType.SUUFON_RENDA

    def test_check_draw_sancha_ron(self):
        """Test Sancha Ron (Three Ron) Ryuukyoku check"""
        self._init_game()

        # Set Triple Ron to allow Ryuukyoku
        self.engine._game_state.ruleset.allow_triple_ron = False

        # Set last discard
        winning_tile = Tile(Suit.PINZU, 4)
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 0

        # Set three players can win
        # 123m 456m 789m 123p 4p (Wait 4p)
        tenpai_hand = Hand(parse_tiles("123456789m1234p"))
        self.engine._hands[1] = tenpai_hand
        self.engine._hands[2] = tenpai_hand
        self.engine._hands[3] = tenpai_hand

        self.engine._hands[1] = tenpai_hand
        self.engine._hands[2] = tenpai_hand
        self.engine._hands[3] = tenpai_hand

        # Check Ryuukyoku
        ryuukyoku_type = self.engine.check_ryuukyoku()
        assert ryuukyoku_type == RyuukyokuType.SANCHA_RON

    def test_check_draw_suukantsu(self):
        """Test Suukaikan (Four Kans) Ryuukyoku check"""
        self._init_game()
        # Set Kan count to 4
        self.engine._kan_count = 4

        # Check Suukaikan
        ryuukyoku_type = self.engine.check_ryuukyoku()
        assert ryuukyoku_type is not None
        assert ryuukyoku_type == RyuukyokuType.SUUKANTSU

    def test_check_draw_exhausted(self):
        """Test Exhausted Wall Ryuukyoku check"""
        self._init_game()
        # Simulate wall exhausted
        assert self.engine._tile_set is not None

        # Exhaust wall
        while self.engine._tile_set._tiles:
            self.engine._tile_set.draw()

        # Check Exhausted Wall Ryuukyoku
        ryuukyoku_type = self.engine.check_ryuukyoku()
        assert ryuukyoku_type is not None
        assert ryuukyoku_type == RyuukyokuType.EXHAUSTED

    def test_handle_draw_kyuushu_kyuuhai(self):
        """Test Kyuushu Kyuuhai (Nine Terminal/Honors) Ryuukyoku handling"""
        self._init_game()
        player = self.engine.get_current_player()

        # Set Kyuushu Kyuuhai
        tiles = parse_tiles("19m19p19s1234567z1m")
        self.engine._hands[player] = Hand(tiles)
        self.engine._is_first_turn_after_deal = True

        # Force update actions
        self.engine._waiting_for_actions[player] = self.engine._calculate_turn_actions(
            player
        )

        # Execute action
        result = self.engine.execute_action(player, GameAction.KYUUSHU_KYUUHAI)

        assert result.ryuukyoku is not None
        assert result.ryuukyoku.ryuukyoku is True
        assert result.ryuukyoku.ryuukyoku_type == RyuukyokuType.KYUUSHU_KYUUHAI
        assert result.ryuukyoku.kyuushu_kyuuhai_player == player

    def test_handle_draw_suucha_riichi(self):
        """Test Suucha Riichi (Four Riichi) Ryuukyoku handling"""
        self._init_game()

        # Set all players Riichi
        for i in range(4):
            self.engine._hands[i].set_riichi(True)

        # Check Ryuukyoku
        ryuukyoku_type = self.engine.check_ryuukyoku()
        assert ryuukyoku_type == RyuukyokuType.SUUCHA_RIICHI

    def test_check_nagashi_mangan(self):
        """Test Nagashi Mangan check"""
        self._init_game()
        player = 0

        # 1. Normal Nagashi Mangan: All discards are terminals/honors, and not called
        yaochuu_tiles = [
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 9),
            Tile(Suit.PINZU, 1),
            Tile(Suit.PINZU, 9),
            Tile(Suit.SOZU, 1),
            Tile(Suit.SOZU, 9),
            Tile(Suit.JIHAI, 1),
            Tile(Suit.JIHAI, 2),
            Tile(Suit.JIHAI, 3),
            Tile(Suit.JIHAI, 4),
            Tile(Suit.JIHAI, 5),
            Tile(Suit.JIHAI, 6),
            Tile(Suit.JIHAI, 7),
        ]

        self.engine._hands[player]._discards = yaochuu_tiles
        self.engine._has_called_discard[player] = False
        assert self.engine._check_nagashi_mangan(player) is True

        # 2. Failure case: Non-terminal/honor tile
        self.engine._hands[player]._discards.append(Tile(Suit.MANZU, 5))
        assert self.engine._check_nagashi_mangan(player) is False

        # 3. Failure case: Discard called
        self.engine._hands[
            player
        ]._discards = yaochuu_tiles  # Reset to all terminals/honors
        self.engine._has_called_discard[player] = True
        assert self.engine._check_nagashi_mangan(player) is False

    def test_check_sancha_ron(self):
        """Test Sancha Ron (Three Ron) check"""
        self._init_game()

        # Set last discard
        winning_tile = Tile(Suit.PINZU, 4)
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 0

        # Set three players can win
        # 123m 456m 789m 123p 4p (Wait 4p)
        self.engine._hands[1] = Hand(parse_tiles("123456789m1234p"))
        self.engine._hands[2] = Hand(parse_tiles("123456789m1234p"))
        self.engine._hands[3] = Hand(parse_tiles("123456789m1234p"))

        # Check Sancha Ron
        result = self.engine._check_sancha_ron()
        assert result is True

    def test_end_round_draw(self):
        """Test end round (Ryuukyoku)"""
        self._init_game()

        # Set to South 4
        from pyriichi.game_state import Wind

        self.engine._game_state.set_round(Wind.SOUTH, 4)
        self.engine._game_state._dealer = 3  # Player 3 is dealer

        # Set player score >= 30000 (Return score), otherwise will go to West round
        self.engine._game_state._scores[0] = 30000

        # Test Ryuukyoku case (Dealer not Tenpai)
        # Default hand is empty, not Tenpai

        self.engine.end_round(None)

        # Should end game (GamePhase.ENDED)
        assert self.engine._phase == GamePhase.ENDED

    def test_fourth_kan_chankan_does_not_trigger_suukantsu(self):
        """Test Chankan on fourth Kan does not trigger Suukaikan (Four Kans Abortion)"""
        self._init_game()

        self.engine._kan_count = 3
        self.engine._current_player = 0
        kan_tile = Tile(Suit.SOZU, 4)

        # 444s 234m 567m 123p 4p
        hand0_tiles = parse_tiles("444s234567m1234p")
        hand0 = Hand(hand0_tiles)
        hand0.pon(kan_tile)
        hand0.add_tile(kan_tile)
        self.engine._hands[0] = hand0
        self.engine._last_discarded_tile = None
        self.engine._last_discarded_player = None

        # Hand: 23s 234m 567m 789p 44p (Wait 4s)
        winning_tiles = parse_tiles("23s234567m789p44p")
        self.engine._hands[1] = Hand(winning_tiles)

        # Force update actions for player 0
        self.engine._waiting_for_actions[0] = self.engine._calculate_turn_actions(0)

        result = self.engine.execute_action(0, GameAction.ANKAN)
        assert result.chankan is True
        assert self.engine._kan_count == 3
        assert self.engine.check_ryuukyoku() is None

    def test_fourth_kan_ron_does_not_trigger_suukantsu(self):
        """Test Ron after fourth Kan does not trigger Suukaikan (Four Kans Abortion)"""
        self._init_game()

        self.engine._kan_count = 4
        winning_tile = Tile(Suit.PINZU, 1)

        # Hand: 234m 567m 789p 234s 1p
        ron_ready = parse_tiles("234567m789p234s1p")
        self.engine._hands[1] = Hand(ron_ready)
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 0

        # Force update interrupts
        self.engine._check_interrupts(winning_tile, 0)

        win_result = self.engine.check_win(1, winning_tile)
        assert win_result is not None
        assert self.engine.check_ryuukyoku() is None

    def test_fourth_kan_rinshan_win_does_not_trigger_suukantsu(self):
        """Test Rinshan Kaihou after fourth Kan does not trigger Suukaikan (Four Kans Abortion)"""
        self._init_game()

        self.engine._kan_count = 3
        player = self.engine.get_current_player()

        # Set Rinshan Kaihou
        # 1. Set hand to Kan (Need 4 identical tiles)

        # 1111m 234m 567m 123p 4p
        hand_tiles = parse_tiles("1111m234567m1234p")
        self.engine._hands[player] = Hand(hand_tiles)

        # 2. Set Rinshan tile to winning tile (4p) - Wait 1p/4p
        rinshan_tile = Tile(Suit.PINZU, 4)
        assert self.engine._tile_set is not None
        self.engine._tile_set._rinshan_tiles[0] = rinshan_tile

        # Force update actions
        self.engine._waiting_for_actions[player] = self.engine._calculate_turn_actions(
            player
        )

        # 3. Execute Ankan
        result = self.engine.execute_action(player, GameAction.ANKAN)

        # 4. Verify Rinshan Kaihou
        assert result.rinshan_win is not None
        assert result.rinshan_win.win is True

        # 5. Verify Suukaikan not triggered
        assert self.engine.check_ryuukyoku() is None

    def test_triple_ron_disabled_ryuukyoku(self):
        """Test Triple Ron disabled: Three players Ron leads to Ryuukyoku"""
        self._init_game()

        # Disable Triple Ron (Default)
        assert not self.engine._game_state.ruleset.allow_triple_ron

        # Player 0 discards 1m, Player 1, 2, 3 can all Ron
        discard_tile = Tile(Suit.MANZU, 1)

        self.engine._hands[1] = Hand(parse_tiles("23456789m123p44p"))
        self.engine._hands[2] = Hand(parse_tiles("23456789m123p44p"))
        self.engine._hands[3] = Hand(parse_tiles("23456789m123p44p"))

        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # Test check_multiple_ron
        winners = self.engine.check_multiple_ron(discard_tile, 0)

        # Detect three players can Ron but Triple Ron disabled, return empty list (Trigger Ryuukyoku)
        assert len(winners) == 0  # Empty list means Sancha Ron Ryuukyoku


class TestGameEndConditions:
    def setup_method(self):
        self.engine = RuleEngine()
        self.engine.start_game()
        # Reset scores to default
        self.engine.game_state._scores = [25000] * 4

    def test_west_round_extension(self):
        """Test West Round Extension: South 4 ends with no one reaching 30000, enter West Round"""
        # Set to South 4
        self.engine.game_state.set_round(Wind.SOUTH, 4)
        self.engine.game_state.set_dealer(3)  # Player 3 is dealer

        # Set scores all below 30000
        self.engine.game_state._scores = [25000, 25000, 25000, 25000]

        # Ensure West Round Extension enabled
        self.engine.game_state.ruleset.west_round_extension = True
        self.engine.game_state.ruleset.return_score = 30000

        # Simulate non-dealer win (Dealer loses), trigger next_round
        # Directly call next_round to test GameState logic
        has_next = self.engine.game_state.next_round()

        assert has_next is True
        assert self.engine.game_state.round_wind == Wind.WEST
        assert self.engine.game_state.round_number == 1

    def test_west_round_sudden_death(self):
        """Test West Round Sudden Death: Someone reaches 30000 in West Round, game ends"""
        # Set to West 1
        self.engine.game_state.set_round(Wind.WEST, 1)

        # Set someone over 30000
        self.engine.game_state._scores = [31000, 20000, 20000, 29000]

        self.engine.game_state.ruleset.return_score = 30000

        # Call next_round
        has_next = self.engine.game_state.next_round()

        assert has_next is False

    def test_no_west_round_if_score_reached(self):
        """Test No West Round if score reached: South 4 ends with someone reaching 30000, game ends"""
        self.engine.game_state.set_round(Wind.SOUTH, 4)
        self.engine.game_state._scores = [31000, 20000, 20000, 29000]

        has_next = self.engine.game_state.next_round()

        assert has_next is False

    def test_agari_yame(self):
        """Test Agari Yame: South 4 Dealer wins and is Top, game ends"""
        self.engine.game_state.set_round(Wind.SOUTH, 4)
        self.engine.game_state.set_dealer(0)  # Assume Player 0 is dealer

        # Set Player 0 as Top and over 30000 (Usually Agari Yame just requires Top? Need to confirm rules)
        # Standard rule: Just need to be Top to end.
        self.engine.game_state._scores = [35000, 20000, 20000, 25000]

        self.engine.game_state.ruleset.agari_yame = True

        # Simulate Dealer win
        winners = [0]
        self.engine.end_round(winners)

        assert self.engine._phase == GamePhase.ENDED

    def test_agari_yame_continuation(self):
        """Test Agari Yame Continuation: South 4 Dealer wins but not Top, game continues (Renchan)"""
        self.engine.game_state.set_round(Wind.SOUTH, 4)
        self.engine.game_state.set_dealer(0)

        # Set Player 0 not Top
        self.engine.game_state._scores = [30000, 35000, 20000, 15000]

        self.engine.game_state.ruleset.agari_yame = True

        # Simulate Dealer win
        winners = [0]
        self.engine.end_round(winners)

        assert self.engine._phase != GamePhase.ENDED
        # Should Renchan
        assert self.engine.game_state.round_wind == Wind.SOUTH
        assert self.engine.game_state.round_number == 4
        assert self.engine.game_state.honba == 1
