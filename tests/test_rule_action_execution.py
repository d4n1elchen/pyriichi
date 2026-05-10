"""Action execution tests for RuleEngine."""

import pytest

from pyriichi.hand import Hand, Meld, MeldType
from pyriichi.rules import GameAction, GamePhase, RyuukyokuType
from pyriichi.tiles import Suit, Tile
from pyriichi.utils import parse_tiles
from tests.helpers import RuleEngineTestMixin, no_response_hand


class TestActionExecution(RuleEngineTestMixin):
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
        self.engine._hands[2] = no_response_hand()
        self.engine._hands[3] = no_response_hand()

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
        self.engine._hands[2] = no_response_hand()
        self.engine._hands[3] = no_response_hand()

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
