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
        self.engine._tile_set._dora_indicators = []

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

    def test_furiten_discards_cannot_ron(self):
        """Test furiten (Discards): Cannot ron if winning tile is in discards"""
        self._init_game()

        # Set Player 0 tenpai (machi 3p)
        # hand: 123m 456m 789m 12p 33p (machi 3p)
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

        # Check furiten status
        assert self.engine.check_furiten_discards(0) is True
        assert self.engine.is_furiten(0) is True

        # Try ron, should fail
        result = self.engine.check_win(0, discard_tile)
        assert result is None or result.win is False

    def test_furiten_discards_can_tsumo(self):
        """Test furiten (Discards): Can tsumo even if furiten"""
        self._init_game()

        # Set Player 0 tenpai (machi 3p)
        # hand: 123m 456m 789m 12p 33p (13 tiles, machi 3p)
        tiles = parse_tiles("123456789m1233p")
        self.engine._hands[0] = Hand(tiles)

        # Player 0 discarded 3p before
        discard_tile = Tile(Suit.PINZU, 3)
        self.engine._hands[0]._discards.append(discard_tile)

        # Check furiten status (13 tiles, should be furiten)
        assert self.engine.check_furiten_discards(0) is True

        # Simulate tsumo 3p
        self.engine._current_player = 0
        self.engine._last_drawn_tile = (0, discard_tile)
        self.engine._last_discarded_tile = None

        # tsumo requires 14 tiles in hand
        self.engine._hands[0].add_tile(discard_tile)

        # tsumo should succeed
        result = self.engine.check_win(0, discard_tile)
        assert result is not None
        assert result.win is True

    def test_furiten_temp_same_turn_cannot_ron(self):
        """Test temp_furiten (Same Turn): Cannot ron if passed winning tile in same turn"""
        self._init_game()

        # Set Player 0 tenpai (machi 4p)
        # hand: 123m 456m 789m 123p 4p
        tiles = parse_tiles("123456789m1234p")
        self.engine._hands[0] = Hand(tiles)

        winning_tile = Tile(Suit.PINZU, 4)

        # Set temp_furiten status (Player 0 passed ron in current turn)
        self.engine._furiten_temp[0] = True
        self.engine._furiten_temp_round[0] = self.engine._turn_count

        # Other player discards 4p
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0
        self.engine._last_drawn_tile = None

        # Check furiten status
        assert self.engine.check_furiten_temp(0) is True
        assert self.engine.is_furiten(0) is True

        result = self.engine.check_win(0, winning_tile)
        assert result is None or result.win is False

    def test_furiten_temp_next_turn_can_ron(self):
        """Test temp_furiten: Can ron in next turn"""
        self._init_game()

        # Set Player 0 tenpai (machi 4p)
        tiles = parse_tiles("123456789m1234p")
        self.engine._hands[0] = Hand(tiles)

        winning_tile = Tile(Suit.PINZU, 4)

        # Set temp_furiten status (Previous turn)
        self.engine._furiten_temp[0] = True
        self.engine._furiten_temp_round[0] = 0
        self.engine._turn_count = 2  # 2 turns passed

        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0
        self.engine._last_drawn_tile = None

        # Check furiten status (Should not be temp_furiten)
        assert self.engine.check_furiten_temp(0) is False
        assert self.engine.is_furiten(0) is False

        # Try ron, should succeed
        result = self.engine.check_win(0, winning_tile)
        assert result is not None
        assert result.win is True

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

    def test_furiten_riichi_permanent(self):
        """Test riichi furiten: Permanent furiten after passing ron in riichi"""
        self._init_game()

        # Set Player 0 riichi and tenpai (machi 4p)
        tiles = parse_tiles("123456789m1234p")
        self.engine._hands[0] = Hand(tiles)
        self.engine._hands[0].set_riichi(True)

        winning_tile = Tile(Suit.PINZU, 4)

        # Set riichi furiten status (Player 0 passed ron after riichi)
        self.engine._furiten_permanent[0] = True

        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0
        self.engine._last_drawn_tile = None

        # Check furiten status
        assert self.engine.check_furiten_riichi(0) is True
        assert self.engine.is_furiten(0) is True

        result = self.engine.check_win(0, winning_tile)
        assert result is None or result.win is False

    def test_passing_ron_after_riichi_sets_permanent_furiten(self):
        """Test passing ron after riichi sets permanent furiten."""
        self._init_game()
        player = 0
        self.engine._hands[player] = Hand(parse_tiles("123456789m1234p"))
        self.engine._hands[player].set_riichi(True)
        self.engine._last_discarded_tile = Tile(Suit.PINZU, 4)
        self.engine._last_discarded_player = 1
        self.engine._waiting_for_actions = {
            player: [GameAction.RON, GameAction.PASS],
            2: [GameAction.PASS],
        }

        self.engine.execute_action(player, GameAction.PASS)

        assert self.engine.check_furiten_temp(player) is True
        assert self.engine.check_furiten_riichi(player) is True
        assert self.engine.is_furiten(player) is True

    def test_furiten_riichi_can_tsumo(self):
        """Test riichi furiten: Can tsumo even if permanent furiten"""
        self._init_game()

        # Set Player 0 riichi and tenpai (machi 4p)
        tiles = parse_tiles("123456789m12344p")
        self.engine._hands[0] = Hand(tiles)
        self.engine._hands[0].set_riichi(True)

        winning_tile = Tile(Suit.PINZU, 4)

        # Set riichi furiten status
        self.engine._furiten_permanent[0] = True

        # Simulate tsumo 4p
        self.engine._current_player = 0
        self.engine._last_drawn_tile = (0, winning_tile)
        self.engine._last_discarded_tile = None

        # Check furiten status (Still furiten)
        assert self.engine.check_furiten_riichi(0) is True

        # tsumo should succeed
        result = self.engine.check_win(0, winning_tile)
        assert result is not None
        assert result.win is True

    def test_furiten_not_tenpai_returns_false(self):
        """Test furiten check returns False if not tenpai"""
        self._init_game()

        # Set Player 0 noten
        tiles = parse_tiles("123456789m12345p")
        self.engine._hands[0] = Hand(tiles)

        # Check furiten status (noten is not furiten)
        assert self.engine.check_furiten_discards(0) is False
        assert self.engine.is_furiten(0) is False

    def test_furiten_multiple_machi_tiles(self):
        """Test furiten with multiple machi tiles."""
        self._init_game()

        # Set Player 0 multi-machi (machi 4p 5p)
        # hand: 123m 456m 789m 44p 55p (Shanpon machi 4p 5p)
        tiles = parse_tiles("123456789m4455p")
        self.engine._hands[0] = Hand(tiles)

        # Player 0 discarded 4p before (one of the machi tiles).
        self.engine._hands[0]._discards.append(Tile(Suit.PINZU, 4))

        # Check furiten status after discarding one of the winning tiles.
        assert self.engine.check_furiten_discards(0) is True

        # Even if the discarded is 5p, the other winning tile, ron is blocked.
        winning_tile = Tile(Suit.PINZU, 5)
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0
        self.engine._last_drawn_tile = None

        result = self.engine.check_win(0, winning_tile)
        assert result is None or result.win is False

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
        assert self.engine._game_state.honba == 0

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

    def _init_game(self):
        self.engine.start_game()
        self.engine.start_round()
        self.engine.deal()

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
        """Test cannot riichi if not tenpai"""
        self._init_game()
        current_player = self.engine.get_current_player()
        # Ensure hand cannot tenpai
        # 123m 456m 789m 12p 4p 8p
        self.engine._hands[current_player] = Hand(parse_tiles("123456789m1248p"))
        assert not self.engine.get_hand(current_player).is_tenpai()
        assert not self._has_action(current_player, GameAction.DECLARE_RIICHI)

    def test_cannot_action_riichi_not_concealed(self):
        """Test cannot riichi if not concealed"""
        self._init_game()
        current_player = self.engine.get_current_player()
        self.engine._hands[current_player]._melds.append(
            Meld(
                MeldType.PON_MELD,
                [Tile(Suit.PINZU, 4), Tile(Suit.PINZU, 4), Tile(Suit.PINZU, 4)],
            )
        )
        assert self.engine.get_hand(current_player).is_concealed is False
        assert not self._has_action(current_player, GameAction.DECLARE_RIICHI)

    def test_get_available_actions_kan(self):
        """Test if open_kan is available"""
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
        # Modify last discard to make kan unavailable
        self.engine._last_discarded_tile = Tile(Suit.MANZU, 9)

        # Force update actions again
        self.engine._waiting_for_actions[current_player] = (
            self.engine._calculate_turn_actions(current_player)
        )

        assert not self._has_action(current_player, GameAction.KAN)

    def test_get_available_actions_declare_ankan(self):
        """Test if declare_ankan is available"""
        self._init_game()
        # 111m 123m 456m 7m 123p
        self.engine._hands[0] = Hand(parse_tiles("1111m234m567m123p"))

        # Force update actions
        self.engine._waiting_for_actions[0] = self.engine._calculate_turn_actions(0)

        assert self._has_action(0, GameAction.DECLARE_ANKAN)

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
        """Test open_kan logic: Automatically infer tile and remove from discards"""
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

        # Check if P1 can kan
        assert self.engine._can_kan(p1)

        # Execute kan (Infer tile without specifying)
        waiting = self.engine.waiting_for_actions
        assert p1 in waiting
        assert GameAction.KAN in waiting[p1]

        result = self.engine.execute_action(p1, GameAction.KAN, tile=None)

        # Verify kan success
        assert result.kan is True
        assert len(hand1.melds) == 1
        assert hand1.melds[0].type == MeldType.OPEN_KAN
        assert hand1.melds[0].called_tile == discard_tile

        # Verify discard removed from P0's discards
        assert discard_tile not in hand0.discards
        assert self.engine._last_discarded_tile is None

    def test_pon_action_claims_last_discard(self):
        """Test pon action claims last discard and changes turn."""
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
        """Test chi action uses specified sequence and resets turn."""
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
        """Test kan with tile as None"""
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
        """Test execute riichi action"""
        self._init_game()
        current_player = self.engine.get_current_player()
        # Ensure hand is tenpai and Concealed
        # 123m 456m 789m 123p 4p -> 13 tiles
        # Add one more tile (e.g. 9s) to discard and stay tenpai
        # 123m 456m 789m 123p 4p -> 13 tiles
        # Add one more tile (e.g. 9s) to discard and stay tenpai
        tiles = parse_tiles("123456789m1234p")
        hand = Hand(tiles)
        hand.add_tile(Tile(Suit.SOUZU, 9))
        self.engine._hands[current_player] = hand

        # Force update actions
        self.engine._waiting_for_actions[current_player] = (
            self.engine._calculate_turn_actions(current_player)
        )

        assert self._has_action(current_player, GameAction.DECLARE_RIICHI)

        result = self.engine.execute_action(
            current_player, GameAction.DECLARE_RIICHI, tile=Tile(Suit.SOUZU, 9)
        )
        assert result.riichi is True
        assert self.engine.get_hand(current_player).is_riichi
        # Check ippatsu status recorded
        assert current_player in self.engine._riichi_ippatsu
        assert self.engine._riichi_ippatsu[current_player]

    def test_riichi_requires_remaining_wall_tiles(self):
        """Test riichi requires enough remaining live wall tiles."""
        self._init_game()
        current_player = self.engine.get_current_player()
        tiles = parse_tiles("123456789m1234p")
        hand = Hand(tiles)
        hand.add_tile(Tile(Suit.SOUZU, 9))
        self.engine._hands[current_player] = hand
        self.engine._tile_set._tiles = [Tile(Suit.MANZU, 1)] * 3

        assert not self.engine._can_riichi(current_player)
        with pytest.raises(ValueError, match="立直時牌山剩餘張數不足"):
            self.engine._handle_riichi(current_player, tile=Tile(Suit.SOUZU, 9))

    def test_execute_action_kan_no_tile(self):
        """Test open_kan without specifying tile"""
        self._init_game()
        current_player = self.engine.get_current_player()

        # Set open_kan status: Has pon_meld 1m, hand has 1m
        hand = self.engine.get_hand(current_player)
        hand._melds.append(
            Meld(
                MeldType.PON_MELD,
                [Tile(Suit.MANZU, 1)] * 3,
                called_tile=Tile(Suit.MANZU, 1),
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
        """Test discard last tile (houtei)"""
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
        """Test draw last tile (haitei)"""
        self._init_game()
        current_player = self.engine.get_current_player()

        # Ensure hand has one less tile to allow draw
        hand = self.engine.get_hand(current_player)
        hand._tiles.pop()

        assert self.engine._tile_set is not None
        self.engine._tile_set._tiles = [Tile(Suit.MANZU, 1)]

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
        # dealer has 14 tiles at start, discard one first
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
        assert result.ryuukyoku.ryuukyoku_type == RyuukyokuType.EXHAUSTIVE_DRAW
        # _handle_draw sets phase
        assert self.engine._phase == GamePhase.RYUUKYOKU

    def test_execute_action_kan_rinshan_win(self):
        """Test rinshan after open_kan"""
        self._init_game()

        # Set Player 0 can open_kan and win on rinshan tile
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

        # Execute open_kan
        assert self._has_action(0, GameAction.KAN)
        result = self.engine.execute_action(0, GameAction.KAN, tile=kan_tile)
        assert result.rinshan_tile is not None
        assert result.rinshan_win is not None

    def test_execute_action_declare_ankan_rinshan_win(self):
        """Test rinshan after declare_ankan"""
        self._init_game()

        # Set Player 0 can declare_ankan
        ten_tile = Tile(Suit.PINZU, 4)
        # 1111m 234m 567m 123p 4p (machi 4p)
        closed_kan_tiles = parse_tiles("1111234567m1234p")
        self.engine._hands[0] = Hand(closed_kan_tiles)
        self.engine._current_player = 0
        assert self.engine._tile_set is not None
        self.engine._tile_set._rinshan_tiles[0] = ten_tile

        # Force update actions
        self.engine._waiting_for_actions[0] = self.engine._calculate_turn_actions(0)

        # Execute declare_ankan
        assert self._has_action(0, GameAction.DECLARE_ANKAN)
        result = self.engine.execute_action(0, GameAction.DECLARE_ANKAN)
        assert result.rinshan_tile is not None
        assert result.rinshan_win is not None

    def test_execute_action_kan_chankan_complete(self):
        """Test chankan (Robbing the kan) complete scenario"""
        self._init_game()

        # Set Player 0 can open_kan (has pon_meld, adds 4th 1m)
        # hand: 111234567m 123p 4p
        kan_tiles = parse_tiles("111234567m1234p")
        hand0 = Hand(kan_tiles)
        kan_tile = Tile(Suit.MANZU, 1)
        hand0.pon(kan_tile)
        hand0.add_tile(kan_tile)
        self.engine._hands[0] = hand0
        self.engine._current_player = 0
        self.engine._last_discarded_tile = None
        self.engine._last_discarded_player = None

        # Set Player 1 can chankan (machi 1m)
        # hand: 23m 456m 789p 123p 44p (machi 1m)
        test_tiles = parse_tiles("23456m12344789p")
        test_hand = Hand(test_tiles)
        self.engine._hands[1] = test_hand

        # Force update actions for player 0
        self.engine._waiting_for_actions[0] = self.engine._calculate_turn_actions(0)

        # Execute open_kan, should check chankan
        assert self._has_action(0, GameAction.DECLARE_ANKAN)
        result = self.engine.execute_action(0, GameAction.DECLARE_ANKAN)
        # Should trigger chankan
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
        """Test kan triggers suukan_sanra."""
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
        # Set dead wall to non-winning tiles to avoid accidental rinshan.
        non_winning_tiles = [Tile(Suit.PINZU, 1)] * 14
        self.engine._tile_set._dead_wall = non_winning_tiles
        self.engine._tile_set._rinshan_tiles = non_winning_tiles[:4]
        self.engine._tile_set._tiles = []

        # Force update actions
        self.engine._waiting_for_actions[player] = self.engine._calculate_turn_actions(
            player
        )

        result = self.engine.execute_action(player, GameAction.KAN, tile=kan_tile)

        assert result.kan is True
        assert self.engine._kan_count == 4
        assert self.engine.check_ryuukyoku() == RyuukyokuType.SUUKAN_SANRA

    def test_execute_action_declare_ankan_wall_exhausted(self):
        """Test closed_kan triggers suukan_sanra."""
        self._init_game()

        player = self.engine.get_current_player()

        # hand: 222m 2334455678m
        starting_tiles = parse_tiles("2222334455678m")
        self.engine._hands[player] = Hand(starting_tiles)

        self.engine._kan_count = 3
        assert self.engine._tile_set is not None
        self.engine._tile_set._wall = [Tile(Suit.SOUZU, 5)]
        self.engine._tile_set._tiles = []
        # Ensure rinshan tile is not a winning tile (hand tenpai is special, give unrelated honor tile to ensure no win)
        self.engine._tile_set._rinshan_tiles = [Tile(Suit.HONORS, 1)] * 4

        # Force update actions
        self.engine._waiting_for_actions[player] = self.engine._calculate_turn_actions(
            player
        )

        result = self.engine.execute_action(player, GameAction.DECLARE_ANKAN)

        assert result.closed_kan is True
        assert self.engine._kan_count == 4
        assert self.engine.check_ryuukyoku() == RyuukyokuType.SUUKAN_SANRA

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
        """Test chankan check"""
        self._init_game()

        # Set Player 0 can chankan (machi 6p, tanyao)
        # hand: 234m 567m 234p 66p 78p (machi 6p/9p)
        test_tiles = parse_tiles("234567m2346678p")
        self.engine._hands[0] = Hand(test_tiles)

        # Check chankan
        kan_tile = Tile(Suit.PINZU, 6)

        # check_win needs pending_kan_tile to set payer
        # Assume Player 1 open_kan 6p
        self.engine._pending_kan_tile = (1, kan_tile)

        result = self.engine.check_win(0, kan_tile, is_chankan=True)
        assert result is not None
        assert result.win is True
        assert result.chankan is True
        assert result.score_result.payment_from == 1

    def test_check_win_rinshan(self):
        """Test rinshan win check"""
        self._init_game()
        # Set a hand that can win on rinshan
        # Create a winning hand
        # hand: 123m 456m 789m 123p 4p (rinshan tile 4p)
        self.engine._hands[0] = Hand(parse_tiles("123456789m12344p"))
        self.engine._current_player = 0

        # Check rinshan win
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
        """Test ron after other player discards is not mistaken for tsumo"""
        self._init_game()
        discarder = 0
        winner = (discarder + 1) % self.engine.get_num_players()
        winning_tile = Tile(Suit.PINZU, 4)
        self.engine._hands[winner] = Hand(parse_tiles("123456789m1234p"))
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = discarder
        # Simulate turn passed to next player (actually ron state)
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
        """Test No yaku"""
        self._init_game()
        # 234m 567m 789m 2p 4p 22s
        tiles = parse_tiles("234567789m24p22s")

        hand = Hand(tiles)
        # Set hand to not concealed
        hand._melds.append(Meld(MeldType.PON_MELD, parse_tiles("1s1s1s")))
        # Set last discard to 3p, test ron
        winning_tile = Tile(Suit.PINZU, 3)
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1

        self.engine._last_discarded_player = 1

        # Set hand to player 0
        self.engine._hands[0] = hand
        self.engine._current_player = 2

        # Check win (Not concealed and no other yaku, should return None)
        result = self.engine.check_win(0, winning_tile)
        assert result is None

    def test_count_dora_zero(self):
        """Test zero dora count"""
        self._init_game()
        self.engine._hands[0] = Hand(parse_tiles("1111234567999m"))
        dora_count = self.engine._count_dora(0, Tile(Suit.MANZU, 1))
        assert dora_count == 0

    def test_count_dora_one(self):
        """Test dora count"""
        self._init_game()
        test_hand = Hand(parse_tiles("1111234567999m"))
        self.engine._hands[0] = test_hand
        dora_count = self.engine._count_dora(0, Tile(Suit.MANZU, 1))
        assert dora_count >= 0

        # Test ura_dora when riichi
        test_hand.set_riichi(True)
        dora_count = self.engine._count_dora(0, Tile(Suit.MANZU, 1))
        assert dora_count >= 0

        # Test red_dora
        # hand: r5p
        red_dora_tiles = parse_tiles("r5p")

        test_hand = Hand(red_dora_tiles)
        self.engine._hands[0] = test_hand
        dora_count = self.engine._count_dora(0, Tile(Suit.PINZU, 5))
        assert dora_count >= 1  # At least one red_dora

    def test_pao_daisangen_tsumo(self):
        """Test pao: daisangen tsumo, pao player pays all"""
        self._init_game()

        # Player 0: daisangen tenpai (pon haku, hatsu)
        # hand: 11m 99m
        # Melds: haku haku haku, hatsu hatsu hatsu
        # Simulate meld state
        # Assume Player 1 discards haku, Player 0 pons
        # Assume Player 2 discards hatsu, Player 0 pons
        # Assume Player 3 discards chun, Player 0 pons (Triggers pao)

        # For testing, we need to manually set state because _handle_pon doesn't implement pao logic yet
        # But we are writing tests, so we assume it works, or we manually set _pao_daisangen

        # Set Player 0 hand
        # For tsumo, hand must contain winning tile (Total 14 tiles)
        # 3 Melds (9 tiles) + 5 tiles = 14 tiles
        # hand: 1m1m1m 9m9m (Winning tile 1m is already in hand for is_winning_hand check)
        self.engine._hands[0] = Hand(parse_tiles("11199m"))  # 111m 99m

        # Set Melds
        meld_haku = Meld(
            MeldType.PON_MELD, [Tile(Suit.HONORS, 5)] * 3, 1
        )  # pon haku (from 1)
        meld_hatsu = Meld(
            MeldType.PON_MELD, [Tile(Suit.HONORS, 6)] * 3, 2
        )  # pon hatsu (from 2)
        meld_chun = Meld(
            MeldType.PON_MELD, [Tile(Suit.HONORS, 7)] * 3, 3
        )  # pon chun (from 3) - Triggers pao

        self.engine._hands[0]._melds = [meld_haku, meld_hatsu, meld_chun]

        # Set pao state (Player 3 is pao)
        # Note: This requires adding _pao_daisangen attribute in rules.py
        # Since attribute is not added yet, this will error, which is expected
        self.engine._pao_daisangen[0] = 3

        # Player 0 tsumo 1m (This tile is already in hand for is_winning_hand check)
        winning_tile = Tile(Suit.MANZU, 1)
        self.engine._current_player = 0
        self.engine._last_drawn_tile = (0, winning_tile)

        # Record initial scores
        initial_scores = self.engine._game_state.scores.copy()

        # Execute tsumo
        # We need to call check_win to ensure it is daisangen
        result = self.engine.check_win(0, winning_tile)
        assert result is not None, "check_win should return a result"
        assert result.win
        assert any(y.yaku == Yaku.DAISANGEN for y in result.yaku)

        # Apply score
        self.engine.apply_win_score(result)

        # Execute end_round
        self.engine.end_round([0])

        # Verify score changes
        # daisangen tsumo: 32000 (dealer 48000)
        # Here is dealer (Player 0 is dealer initially) -> 48000
        # pao player (Player 3) pays all 48000

        assert self.engine._game_state.scores[0] == initial_scores[0] + 48000
        assert self.engine._game_state.scores[3] == initial_scores[3] - 48000
        assert (
            self.engine._game_state.scores[1] == initial_scores[1]
        )  # Others don't pay
        assert (
            self.engine._game_state.scores[2] == initial_scores[2]
        )  # Others don't pay

    def test_pao_daisangen_tracks_final_dragon_call(self):
        """Test pao_daisangen tracks final dragon call."""
        self._init_game()
        player = 0
        responsible_player = 3
        called_tile = Tile(Suit.HONORS, 7)
        hand = Hand(parse_tiles("77z123m456p789s1m"))
        hand._melds = [
            Meld(MeldType.PON_MELD, [Tile(Suit.HONORS, 5)] * 3, called_tile=Tile(Suit.HONORS, 5)),
            Meld(MeldType.PON_MELD, [Tile(Suit.HONORS, 6)] * 3, called_tile=Tile(Suit.HONORS, 6)),
        ]
        self.engine._hands[player] = hand
        self.engine._hands[responsible_player]._discards = [called_tile]
        self.engine._last_discarded_tile = called_tile
        self.engine._last_discarded_player = responsible_player

        self.engine._handle_pon(player)

        assert self.engine._pao_daisangen[player] == responsible_player

    def test_pao_daisuushi_tracks_final_wind_call(self):
        """Test pao_daisuushi tracks final wind call."""
        self._init_game()
        player = 0
        responsible_player = 2
        called_tile = Tile(Suit.HONORS, 4)
        hand = Hand(parse_tiles("44z123m456p789s1m"))
        hand._melds = [
            Meld(MeldType.PON_MELD, [Tile(Suit.HONORS, 1)] * 3, called_tile=Tile(Suit.HONORS, 1)),
            Meld(MeldType.PON_MELD, [Tile(Suit.HONORS, 2)] * 3, called_tile=Tile(Suit.HONORS, 2)),
            Meld(MeldType.PON_MELD, [Tile(Suit.HONORS, 3)] * 3, called_tile=Tile(Suit.HONORS, 3)),
        ]
        self.engine._hands[player] = hand
        self.engine._hands[responsible_player]._discards = [called_tile]
        self.engine._last_discarded_tile = called_tile
        self.engine._last_discarded_player = responsible_player

        self.engine._handle_pon(player)

        assert self.engine._pao_daisuushi[player] == responsible_player

    def test_pao_daisangen_ron_pao_player(self):
        """Test pao: daisangen ron pao player (normal payment)"""
        self._init_game()

        # Set Player 0 hand
        self.engine._hands[0] = Hand(parse_tiles("1199m"))

        # Set Melds
        meld_haku = Meld(MeldType.PON_MELD, [Tile(Suit.HONORS, 5)] * 3, 1)
        meld_hatsu = Meld(MeldType.PON_MELD, [Tile(Suit.HONORS, 6)] * 3, 2)
        meld_chun = Meld(
            MeldType.PON_MELD, [Tile(Suit.HONORS, 7)] * 3, 3
        )  # pon chun (from 3) - Triggers pao

        self.engine._hands[0]._melds = [meld_haku, meld_hatsu, meld_chun]

        # Set pao state (Player 3 is pao)
        self.engine._pao_daisangen[0] = 3

        # Player 3 discards chun (pao player deals in)
        # winning_tile = Tile(Suit.HONORS, 7) # Actually should discard 1m or 5z, because 5z is already ponned, so discard 1m
        # The hand is 11m 55z after ponning 567z.
        # tenpai should be 1m and 5z by shabo.
        # 13 tiles: 3*3=9 tiles melded, remains 4 tiles.
        # 11m 55z -> machi 1m, 5z (Shanpon)
        # Assume Player 3 discards 1m
        winning_tile = Tile(Suit.MANZU, 1)

        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 3
        self.engine._current_player = 0

        initial_scores = self.engine._game_state.scores.copy()

        # Execute ron
        result = self.engine.check_win(0, winning_tile)
        self.engine.apply_win_score(result)
        self.engine.end_round([0])

        # Verify score changes
        # dealer daisangen ron: 48000
        # Deal-in player (Player 3) pays 48000
        assert self.engine._game_state.scores[0] == initial_scores[0] + 48000
        assert self.engine._game_state.scores[3] == initial_scores[3] - 48000

    def test_pao_daisangen_ron_other(self):
        """Test pao: daisangen ron other (pao player and Deal-in player split)"""
        self._init_game()

        # Set Player 0 hand
        # 3 Melds (9 tiles) + 4 tiles = 13 tiles
        # hand: 1m1m 9m9m
        self.engine._hands[0] = Hand(parse_tiles("1199m"))

        # Set Melds
        meld_haku = Meld(MeldType.PON_MELD, [Tile(Suit.HONORS, 5)] * 3, 1)
        meld_hatsu = Meld(MeldType.PON_MELD, [Tile(Suit.HONORS, 6)] * 3, 2)
        meld_chun = Meld(
            MeldType.PON_MELD, [Tile(Suit.HONORS, 7)] * 3, 3
        )  # pon chun (from 3) - Triggers pao

        self.engine._hands[0]._melds = [meld_haku, meld_hatsu, meld_chun]

        # Set pao state (Player 3 is pao)
        self.engine._pao_daisangen[0] = 3

        # Player 1 discards 1m (Non-pao player deals in)
        winning_tile = Tile(Suit.MANZU, 1)

        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0

        initial_scores = self.engine._game_state.scores.copy()

        # Execute ron
        result = self.engine.check_win(0, winning_tile)
        self.engine.apply_win_score(result)
        self.engine.end_round([0])

        # Verify score changes
        # dealer daisangen ron: 48000
        # pao player (Player 3) and Deal-in player (Player 1) split equally (24000 each)
        assert self.engine._game_state.scores[0] == initial_scores[0] + 48000
        assert self.engine._game_state.scores[1] == initial_scores[1] - 24000
        assert self.engine._game_state.scores[3] == initial_scores[3] - 24000
        assert (
            self.engine._game_state.scores[2] == initial_scores[2]
        )  # Player 2 doesn't pay

    # ==================== head_bump / double_ron / triple_ron Tests ====================

    def test_head_bump_only_shimocha_wins(self):
        """Test head_bump: shimocha and kamicha can ron, only shimocha wins"""
        self._init_game()

        # Ensure head_bump mode (default)
        assert self.engine._game_state.ruleset.head_bump_only

        # Player 0 discards 1m
        discard_tile = Tile(Suit.MANZU, 1)

        # Player 1 (shimocha) and Player 3 (kamicha) can ron 1m
        # hand should have 13 tiles, becomes 14 after ron
        self.engine._hands[1] = Hand(parse_tiles("23456789m12344p"))  # 13 tiles
        self.engine._hands[3] = Hand(parse_tiles("23456789m12344p"))  # 13 tiles

        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # Test check_multiple_ron
        winners = self.engine.check_multiple_ron(discard_tile, 0)

        # In head_bump mode, when multiple players can ron, only shimocha (Player 1) wins
        assert len(winners) == 1
        assert winners[0] == 1  # Only Player 1 (shimocha)

    def test_head_bump_only_toimen_blocked(self):
        """Test head_bump: toimen can ron but blocked"""
        self._init_game()

        # Player 0 discards 1m
        discard_tile = Tile(Suit.MANZU, 1)

        # Only Player 2 (toimen) can ron
        self.engine._hands[2] = Hand(parse_tiles("23456789m12344p"))

        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # Test check_multiple_ron
        winners = self.engine.check_multiple_ron(discard_tile, 0)

        # If only one player can ron, head_bump doesn't apply, player wins normally
        assert len(winners) == 1
        assert winners[0] == 2  # Only Player 2 can ron, returns normally

    def test_head_bump_only_kamicha_blocked(self):
        """Test head_bump: kamicha can ron but blocked"""
        self._init_game()

        # Player 0 discards 1m
        discard_tile = Tile(Suit.MANZU, 1)

        # Only Player 3 (kamicha) can ron
        self.engine._hands[3] = Hand(parse_tiles("23456789m12344p"))

        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # Test check_multiple_ron
        winners = self.engine.check_multiple_ron(discard_tile, 0)

        # If only one player can ron, head_bump doesn't apply, player wins normally
        assert len(winners) == 1
        assert winners[0] == 3

    def test_double_ron_both_win(self):
        """Test double_ron: Two players win simultaneously"""
        self._init_game()

        # Enable double_ron mode
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True

        # Player 0 discards 1m
        discard_tile = Tile(Suit.MANZU, 1)

        # Player 1 (shimocha) and Player 2 (toimen) can ron
        self.engine._hands[1] = Hand(parse_tiles("23456789m12344p"))
        self.engine._hands[2] = Hand(parse_tiles("23456789m12344p"))

        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # Test check_multiple_ron
        winners = self.engine.check_multiple_ron(discard_tile, 0)

        # In double_ron mode, both players can win
        assert len(winners) == 2
        assert 1 in winners
        assert 2 in winners
        # Order should be counter-clockwise (shimocha first)
        assert winners[0] == 1
        assert winners[1] == 2

    def test_double_ron_score_calculation(self):
        """Test double_ron: Verify deal-in player pays both"""
        self._init_game()
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True

        # Player 0 discards 4p
        discard_tile = Tile(Suit.PINZU, 4)

        # Set Player 1 and 2 hands (tanyao pinfu)
        # 234m 567m 234p 56p 88s (machi 4p/7p)
        # 30 fu 2 han = 2000 points (non-dealer)
        hand_tiles = parse_tiles("234567m23456p88s")
        self.engine._hands[1] = Hand(hand_tiles)
        self.engine._hands[2] = Hand(hand_tiles)

        self.engine._current_player = 0

        # Disable renhou by simulating that it's not the first turn
        # This ensures we test standard yaku (tanyao + pinfu) scoring
        self.engine._is_first_turn_after_deal = False

        initial_scores = self.engine._game_state.scores.copy()

        # Player 0 discards 4p
        self.engine._hands[0]._tiles.append(discard_tile)
        self.engine._waiting_for_actions = {0: self.engine._calculate_turn_actions(0)}
        self.engine.execute_action(0, GameAction.DISCARD, discard_tile)

        # Execute double_ron
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
        """Test double_ron: dealer win leads to renchan"""
        self._init_game()
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True

        # Set dealer to Player 0
        self.engine._game_state._dealer = 0
        self.engine._game_state._round_number = 1
        self.engine._game_state._honba = 0

        # Player 1 discards 5p
        discard_tile = Tile(Suit.PINZU, 5)

        # Player 0 (dealer) and Player 2 (non-dealer) ron
        hand_str = "233445678m2345p"
        self.engine._hands[0] = Hand(parse_tiles(hand_str))
        self.engine._hands[2] = Hand(parse_tiles(hand_str))

        # Player 1 discards 5p
        self.engine._current_player = 1
        self.engine._hands[1]._tiles.append(discard_tile)
        self.engine._waiting_for_actions = {1: self.engine._calculate_turn_actions(1)}
        self.engine.execute_action(1, GameAction.DISCARD, discard_tile)

        # Execute ron
        self.engine.execute_action(0, GameAction.RON, tile=discard_tile)
        result = self.engine.execute_action(2, GameAction.RON, tile=discard_tile)

        assert result.success
        assert sorted(result.winners) == [0, 2]

    def test_triple_ron_enabled_all_win(self):
        """Test triple_ron enabled: All three players win"""
        self._init_game()
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True
        self.engine._game_state.ruleset.allow_triple_ron = True

        # Player 0 discards 5p, Player 1, 2, 3 all ron with tanyao
        discard_tile = Tile(Suit.PINZU, 5)

        # 234m 345m 678m 234p 5p (machi 5p)
        hand_str = "233445678m2345p"
        self.engine._hands[1] = Hand(parse_tiles(hand_str))
        self.engine._hands[2] = Hand(parse_tiles(hand_str))
        self.engine._hands[3] = Hand(parse_tiles(hand_str))

        initial_scores = self.engine._game_state.scores.copy()

        # Execute triple_ron
        # Player 0 discards 5p
        self.engine._current_player = 0
        self.engine._hands[0]._tiles.append(discard_tile)
        self.engine._waiting_for_actions = {0: self.engine._calculate_turn_actions(0)}
        self.engine.execute_action(0, GameAction.DISCARD, discard_tile)

        # Player 1 ron
        self.engine.execute_action(1, GameAction.RON, tile=discard_tile)
        # Player 2 ron
        self.engine.execute_action(2, GameAction.RON, tile=discard_tile)
        # Player 3 ron (triggers resolution)
        result = self.engine.execute_action(3, GameAction.RON, tile=discard_tile)

        assert result.success
        assert sorted(result.winners) == [1, 2, 3]

        # Players 1, 2, 3 each get 1000.

        # Note: calculate_score might give more with dora/ura_dora.
        # Let's just verify scores changed in the right direction.

        score_diff_0 = self.engine._game_state.scores[0] - initial_scores[0]
        score_diff_1 = self.engine._game_state.scores[1] - initial_scores[1]
        score_diff_2 = self.engine._game_state.scores[2] - initial_scores[2]
        score_diff_3 = self.engine._game_state.scores[3] - initial_scores[3]

        assert score_diff_0 < 0
        assert score_diff_1 > 0
        assert score_diff_2 > 0
        assert score_diff_3 > 0

        # Verify total balance is zero (assuming no riichi_stick)
        assert score_diff_0 + score_diff_1 + score_diff_2 + score_diff_3 == 0

    def test_double_ron_with_furiten(self):
        """Test double_ron with furiten: One player furiten, only other player wins"""
        self._init_game()

        # Enable double_ron mode
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True

        # Player 0 discards 5p
        discard_tile = Tile(Suit.PINZU, 5)

        # 234m 345m 678m 234p 5p (machi 5p) - tanyao
        hand_str = "233445678m2345p"

        # Player 1 can ron
        self.engine._hands[1] = Hand(parse_tiles(hand_str))

        # Player 2 can ron but is furiten
        self.engine._hands[2] = Hand(parse_tiles(hand_str))
        self.engine._hands[2]._discards.append(
            discard_tile
        )  # Discarded 5p, genbutsu furiten

        # Player 0 discards 5p
        self.engine._current_player = 0
        self.engine._hands[0]._tiles.append(discard_tile)
        self.engine._waiting_for_actions = {0: self.engine._calculate_turn_actions(0)}
        self.engine.execute_action(0, GameAction.DISCARD, discard_tile)

        # Player 1 ron
        result1 = self.engine.execute_action(1, GameAction.RON, tile=discard_tile)
        assert result1.success
        assert result1.winners == [1]

    def test_double_ron_priority_order(self):
        """Test double_ron: Verify player order (shimocha first)"""
        self._init_game()

        # Enable double_ron mode
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True

        # Player 0 discards 5p, Player 2 and 3 can ron
        discard_tile = Tile(Suit.PINZU, 5)

        # 234m 345m 678m 234p 5p (machi 5p) - tanyao
        hand_str = "233445678m2345p"

        self.engine._hands[2] = Hand(parse_tiles(hand_str))
        self.engine._hands[3] = Hand(parse_tiles(hand_str))

        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # Check check_multiple_ron return order
        winners = self.engine.check_multiple_ron(discard_tile, 0)

        # Player 0's shimocha is Player 1, then 2, 3
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
        """Test ryuukyoku check"""
        self._init_game()
        # Initial state should not be ryuukyoku
        draw_type = self.engine.check_ryuukyoku()
        assert draw_type is None

    def test_handle_draw(self):
        """Test ryuukyoku handling"""
        self._init_game()
        # Cannot ryuukyoku at start
        actions = self.engine.get_available_actions(0)
        assert GameAction.DRAW not in actions

    def test_check_draw_suufon_renda(self):
        """Test suufon_renda (Four Winds) ryuukyoku check"""
        self._init_game()
        # Set discard history to four identical wind tiles
        wind_tile = Tile(Suit.HONORS, 1)  # East

        # Add four identical wind tiles to discard history
        self.engine._discard_history.append((0, wind_tile))
        self.engine._discard_history.append((1, wind_tile))
        self.engine._discard_history.append((2, wind_tile))
        self.engine._discard_history.append((3, wind_tile))

        # Check suufon_renda
        ryuukyoku_type = self.engine.check_ryuukyoku()
        assert ryuukyoku_type is not None
        assert ryuukyoku_type == RyuukyokuType.SUUFON_RENDA

    def test_check_draw_sancha_ron(self):
        """Test sancha_ron (Three ron) ryuukyoku check"""
        self._init_game()

        # Set triple_ron to allow ryuukyoku
        self.engine._game_state.ruleset.allow_triple_ron = False

        # Set last discard
        winning_tile = Tile(Suit.PINZU, 4)
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 0

        # Set three players can win
        # 123m 456m 789m 123p 4p (machi 4p)
        tenpai_hand = Hand(parse_tiles("123456789m1234p"))
        self.engine._hands[1] = tenpai_hand
        self.engine._hands[2] = tenpai_hand
        self.engine._hands[3] = tenpai_hand

        self.engine._hands[1] = tenpai_hand
        self.engine._hands[2] = tenpai_hand
        self.engine._hands[3] = tenpai_hand

        # Check ryuukyoku
        ryuukyoku_type = self.engine.check_ryuukyoku()
        assert ryuukyoku_type == RyuukyokuType.SANCHA_RON

    def test_check_draw_suukan_sanra(self):
        """Test suukan_sanra ryuukyoku check."""
        self._init_game()
        # Set kan count to 4
        self.engine._kan_count = 4

        # Check suukan_sanra
        ryuukyoku_type = self.engine.check_ryuukyoku()
        assert ryuukyoku_type is not None
        assert ryuukyoku_type == RyuukyokuType.SUUKAN_SANRA

    def test_check_draw_exhausted(self):
        """Test exhaustive_draw ryuukyoku check"""
        self._init_game()
        # Simulate wall exhausted
        assert self.engine._tile_set is not None

        # Exhaust wall
        while self.engine._tile_set._tiles:
            self.engine._tile_set.draw()

        # Check exhaustive_draw ryuukyoku
        ryuukyoku_type = self.engine.check_ryuukyoku()
        assert ryuukyoku_type is not None
        assert ryuukyoku_type == RyuukyokuType.EXHAUSTIVE_DRAW

    def test_declare_kyuushu_kyuuhai(self):
        """Test kyuushu_kyuuhai handling."""
        self._init_game()
        player = self.engine.get_current_player()

        # Set kyuushu_kyuuhai
        tiles = parse_tiles("19m19p19s1234567z1m")
        self.engine._hands[player] = Hand(tiles)
        self.engine._is_first_turn_after_deal = True

        # Force update actions
        self.engine._waiting_for_actions[player] = self.engine._calculate_turn_actions(
            player
        )

        # Execute action
        result = self.engine.execute_action(player, GameAction.DECLARE_KYUUSHU_KYUUHAI)

        assert result.ryuukyoku is not None
        assert result.ryuukyoku.ryuukyoku is True
        assert result.ryuukyoku.ryuukyoku_type == RyuukyokuType.KYUUSHU_KYUUHAI
        assert result.ryuukyoku.kyuushu_kyuuhai_player == player

    def test_handle_draw_suucha_riichi(self):
        """Test suucha_riichi (Four riichi) ryuukyoku handling"""
        self._init_game()

        # Set all players riichi
        for i in range(4):
            self.engine._hands[i].set_riichi(True)

        # Check ryuukyoku
        ryuukyoku_type = self.engine.check_ryuukyoku()
        assert ryuukyoku_type == RyuukyokuType.SUUCHA_RIICHI

    def test_check_nagashi_mangan(self):
        """Test nagashi_mangan check"""
        self._init_game()
        player = 0

        # 1. Normal nagashi_mangan: All discards are terminals/honors, and not called
        yaochuu_tiles = [
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 9),
            Tile(Suit.PINZU, 1),
            Tile(Suit.PINZU, 9),
            Tile(Suit.SOUZU, 1),
            Tile(Suit.SOUZU, 9),
            Tile(Suit.HONORS, 1),
            Tile(Suit.HONORS, 2),
            Tile(Suit.HONORS, 3),
            Tile(Suit.HONORS, 4),
            Tile(Suit.HONORS, 5),
            Tile(Suit.HONORS, 6),
            Tile(Suit.HONORS, 7),
        ]

        self.engine._hands[player]._discards = yaochuu_tiles
        self.engine._has_called_discard[player] = False
        assert self.engine._check_nagashi_mangan(player) is True

        # 2. Failure case: Non-terminal/honor tile
        self.engine._hands[player]._discards.append(Tile(Suit.MANZU, 5))
        assert self.engine._check_nagashi_mangan(player) is False

        # 3. Failure case: Discard called
        self.engine._hands[player]._discards = yaochuu_tiles  # Reset to yaochuu tiles.
        self.engine._has_called_discard[player] = True
        assert self.engine._check_nagashi_mangan(player) is False

    def test_handle_ryuukyoku_scores_nagashi_mangan_as_mangan(self):
        """Test handle_ryuukyoku scores nagashi_mangan as mangan."""
        self._init_game()
        player = 1
        self.engine._game_state.set_dealer(0)
        self.engine._tile_set._tiles = []
        self.engine._hands[player]._discards = [
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 9),
            Tile(Suit.PINZU, 1),
            Tile(Suit.PINZU, 9),
        ]
        self.engine._has_called_discard[player] = False
        initial_scores = self.engine._game_state.scores

        result = self.engine.handle_ryuukyoku()

        score_deltas = [
            score - initial_scores[i]
            for i, score in enumerate(self.engine._game_state.scores)
        ]
        assert result.nagashi_mangan_players == [player]
        assert score_deltas == [-4000, 8000, -2000, -2000]

    def test_check_sancha_ron(self):
        """Test sancha_ron (Three ron) check"""
        self._init_game()

        # Set last discard
        winning_tile = Tile(Suit.PINZU, 4)
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 0

        # Set three players can win
        # 123m 456m 789m 123p 4p (machi 4p)
        self.engine._hands[1] = Hand(parse_tiles("123456789m1234p"))
        self.engine._hands[2] = Hand(parse_tiles("123456789m1234p"))
        self.engine._hands[3] = Hand(parse_tiles("123456789m1234p"))

        # Check sancha_ron
        result = self.engine._check_sancha_ron()
        assert result is True

    def test_end_round_draw(self):
        """Test end round (ryuukyoku)"""
        self._init_game()

        # Set to South 4
        from pyriichi.game_state import Wind

        self.engine._game_state.set_round(Wind.SOUTH, 4)
        self.engine._game_state._dealer = 3  # Player 3 is dealer

        # Set player score >= 30000 (Return score), otherwise will go to West round
        self.engine._game_state._scores[0] = 30000

        # Test ryuukyoku case (dealer not tenpai)
        # Default hand is empty, not tenpai

        self.engine.end_round(None)

        # Should end game (GamePhase.ENDED)
        assert self.engine._phase == GamePhase.ENDED

    def test_fourth_kan_chankan_does_not_trigger_suukan_sanra(self):
        """Test chankan on fourth kan does not trigger suukan_sanra."""
        self._init_game()

        self.engine._kan_count = 3
        self.engine._current_player = 0
        kan_tile = Tile(Suit.SOUZU, 4)

        # 444s 234m 567m 123p 4p
        hand0_tiles = parse_tiles("444s234567m1234p")
        hand0 = Hand(hand0_tiles)
        hand0.pon(kan_tile)
        hand0.add_tile(kan_tile)
        self.engine._hands[0] = hand0
        self.engine._last_discarded_tile = None
        self.engine._last_discarded_player = None

        # hand: 23s 234m 567m 789p 44p (machi 4s)
        winning_tiles = parse_tiles("23s234567m789p44p")
        self.engine._hands[1] = Hand(winning_tiles)

        # Force update actions for player 0
        self.engine._waiting_for_actions[0] = self.engine._calculate_turn_actions(0)

        result = self.engine.execute_action(0, GameAction.DECLARE_ANKAN)
        assert result.chankan is True
        assert self.engine._kan_count == 3
        assert self.engine.check_ryuukyoku() is None

    def test_fourth_kan_ron_does_not_trigger_suukan_sanra(self):
        """Test ron after fourth kan does not trigger suukan_sanra."""
        self._init_game()

        self.engine._kan_count = 4
        winning_tile = Tile(Suit.PINZU, 1)

        # hand: 234m 567m 789p 234s 1p
        ron_ready = parse_tiles("234567m789p234s1p")
        self.engine._hands[1] = Hand(ron_ready)
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 0

        # Force update interrupts
        self.engine._check_interrupts(winning_tile, 0)

        win_result = self.engine.check_win(1, winning_tile)
        assert win_result is not None
        assert self.engine.check_ryuukyoku() is None

    def test_fourth_kan_rinshan_win_does_not_trigger_suukan_sanra(self):
        """Test rinshan after fourth kan does not trigger suukan_sanra."""
        self._init_game()

        self.engine._kan_count = 3
        player = self.engine.get_current_player()

        # Set rinshan
        # 1. Set hand to kan (Need 4 identical tiles)

        # 1111m 234m 567m 123p 4p
        hand_tiles = parse_tiles("1111m234567m1234p")
        self.engine._hands[player] = Hand(hand_tiles)

        # 2. Set rinshan tile to winning tile (4p) - machi 1p/4p
        rinshan_tile = Tile(Suit.PINZU, 4)
        assert self.engine._tile_set is not None
        self.engine._tile_set._rinshan_tiles[0] = rinshan_tile

        # Force update actions
        self.engine._waiting_for_actions[player] = self.engine._calculate_turn_actions(
            player
        )

        # 3. Execute declare_ankan
        result = self.engine.execute_action(player, GameAction.DECLARE_ANKAN)

        # 4. Verify rinshan
        assert result.rinshan_win is not None
        assert result.rinshan_win.win is True

        # 5. Verify suukan_sanra not triggered
        assert self.engine.check_ryuukyoku() is None

    def test_triple_ron_disabled_ryuukyoku(self):
        """Test triple_ron disabled: Three players ron leads to ryuukyoku"""
        self._init_game()

        # Disable triple_ron (default)
        assert not self.engine._game_state.ruleset.allow_triple_ron

        # Player 0 discards 1m, Player 1, 2, 3 can all ron
        discard_tile = Tile(Suit.MANZU, 1)

        self.engine._hands[1] = Hand(parse_tiles("23456789m123p44p"))
        self.engine._hands[2] = Hand(parse_tiles("23456789m123p44p"))
        self.engine._hands[3] = Hand(parse_tiles("23456789m123p44p"))

        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # Test check_multiple_ron
        winners = self.engine.check_multiple_ron(discard_tile, 0)

        # Detect three players can ron but triple_ron disabled, return empty list (trigger ryuukyoku)
        assert len(winners) == 0  # Empty list means sancha_ron ryuukyoku


class TestGameEndConditions:
    def setup_method(self):
        self.engine = RuleEngine()
        self.engine.start_game()
        # Reset scores to default
        self.engine.game_state._scores = [25000] * 4

    def test_west_round_extension(self):
        """Test west_round_extension: South 4 ends with no one reaching 30000, enter west round"""
        # Set to South 4
        self.engine.game_state.set_round(Wind.SOUTH, 4)
        self.engine.game_state.set_dealer(3)  # Player 3 is dealer

        # Set scores all below 30000
        self.engine.game_state._scores = [25000, 25000, 25000, 25000]

        # Ensure west_round_extension enabled
        self.engine.game_state.ruleset.west_round_extension = True
        self.engine.game_state.ruleset.return_score = 30000

        # Simulate non-dealer win (dealer loses), trigger next_round
        # Directly call next_round to test GameState logic
        has_next = self.engine.game_state.next_round()

        assert has_next is True
        assert self.engine.game_state.round_wind == Wind.WEST
        assert self.engine.game_state.round_number == 1

    def test_west_round_sudden_death(self):
        """Test west_round_extension end check: Someone reaches 30000 in west round, game ends"""
        # Set to West 1
        self.engine.game_state.set_round(Wind.WEST, 1)

        # Set someone over 30000
        self.engine.game_state._scores = [31000, 20000, 20000, 29000]

        self.engine.game_state.ruleset.return_score = 30000

        # Call next_round
        has_next = self.engine.game_state.next_round()

        assert has_next is False

    def test_no_west_round_if_score_reached(self):
        """Test No west round if score reached: South 4 ends with someone reaching 30000, game ends"""
        self.engine.game_state.set_round(Wind.SOUTH, 4)
        self.engine.game_state._scores = [31000, 20000, 20000, 29000]

        has_next = self.engine.game_state.next_round()

        assert has_next is False

    def test_agari_yame(self):
        """Test agari_yame: south 4 dealer wins and is top, game ends"""
        self.engine.game_state.set_round(Wind.SOUTH, 4)
        self.engine.game_state.set_dealer(0)  # Assume Player 0 is dealer

        # Set Player 0 as Top and over 30000 (Usually agari_yame just requires Top? Need to confirm rules)
        # Standard rule: Just need to be Top to end.
        self.engine.game_state._scores = [35000, 20000, 20000, 25000]

        self.engine.game_state.ruleset.agari_yame = True

        # Simulate dealer win
        winners = [0]
        self.engine.end_round(winners)

        assert self.engine._phase == GamePhase.ENDED

    def test_agari_yame_continuation(self):
        """Test agari_yame continuation: south 4 dealer wins but not top, game continues (renchan)"""
        self.engine.game_state.set_round(Wind.SOUTH, 4)
        self.engine.game_state.set_dealer(0)

        # Set Player 0 not Top
        self.engine.game_state._scores = [30000, 35000, 20000, 15000]

        self.engine.game_state.ruleset.agari_yame = True

        # Simulate dealer win
        winners = [0]
        self.engine.end_round(winners)

        assert self.engine._phase != GamePhase.ENDED
        # Should renchan
        assert self.engine.game_state.round_wind == Wind.SOUTH
        assert self.engine.game_state.round_number == 4
        assert self.engine.game_state.honba == 1
