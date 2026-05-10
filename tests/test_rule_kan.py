"""Kan rule tests for RuleEngine."""

import pytest

from pyriichi.hand import Hand, Meld, MeldType
from pyriichi.rules import GameAction, GamePhase, RuleEngine, RyuukyokuType
from pyriichi.tiles import Suit, Tile, TileSet
from pyriichi.utils import parse_tiles
from tests.helpers import RuleEngineTestMixin, no_response_hand


class TestKanBehavior(RuleEngineTestMixin):
    def test_open_kan_logic(self):
        """Test open_kan logic: Automatically infer tile and remove from discards."""
        self.engine.start_game()
        self.engine.start_round()
        self.engine.deal()

        p1 = 1
        hand1 = self.engine.get_hand(p1)
        hand1._tiles = []
        for _ in range(3):
            hand1.add_tile(Tile(Suit.MANZU, 1))
        for i in range(10):
            hand1.add_tile(Tile(Suit.PINZU, i % 9 + 1))
        self.engine._hands[2] = no_response_hand()
        self.engine._hands[3] = no_response_hand()

        p0 = 0
        self.engine._current_player = p0
        hand0 = self.engine.get_hand(p0)
        discard_tile = Tile(Suit.MANZU, 1)
        hand0.add_tile(discard_tile)

        self.engine.execute_action(p0, GameAction.DISCARD, tile=discard_tile)

        assert self.engine._last_discarded_tile == discard_tile
        assert self.engine._last_discarded_player == p0
        assert discard_tile in hand0.discards
        assert self.engine._can_kan(p1)

        waiting = self.engine.waiting_for_actions
        assert p1 in waiting
        assert GameAction.KAN in waiting[p1]

        result = self.engine.execute_action(p1, GameAction.KAN, tile=None)

        assert result.kan is True
        assert len(hand1.melds) == 1
        assert hand1.melds[0].type == MeldType.OPEN_KAN
        assert hand1.melds[0].called_tile == discard_tile
        assert discard_tile not in hand0.discards
        assert self.engine._last_discarded_tile is None

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

    def test_execute_action_kan_tile_none(self):
        """Test kan with tile as None."""
        self._init_game()
        current_player = self.engine.get_current_player()

        with pytest.raises(ValueError):
            self.engine.execute_action(current_player, GameAction.KAN, tile=None)

    def test_execute_action_kan_no_tile(self):
        """Test open_kan without specifying tile."""
        self._init_game()
        current_player = self.engine.get_current_player()
        hand = self.engine.get_hand(current_player)
        hand._melds.append(
            Meld(
                MeldType.PON_MELD,
                [Tile(Suit.MANZU, 1)] * 3,
                called_tile=Tile(Suit.MANZU, 1),
            )
        )
        hand._tiles = [Tile(Suit.MANZU, 1)]
        self.engine._waiting_for_actions[current_player] = (
            self.engine._calculate_turn_actions(current_player)
        )

        assert self._has_action(current_player, GameAction.KAN)
        with pytest.raises(ValueError, match="明槓必須指定被槓的牌"):
            self.engine.execute_action(current_player, GameAction.KAN, tile=None)

    def test_execute_action_kan_rinshan_win(self):
        """Test rinshan after open_kan."""
        self._init_game()

        kan_tile = Tile(Suit.MANZU, 1)
        ten_tile = Tile(Suit.PINZU, 4)
        kan_tiles = parse_tiles("111234567m1234p")
        self.engine._hands[0] = Hand(kan_tiles)
        self.engine._current_player = 0
        self.engine._last_discarded_tile = kan_tile
        self.engine._last_discarded_player = 1
        assert self.engine._tile_set is not None
        self.engine._tile_set._rinshan_tiles[0] = ten_tile
        self.engine._waiting_for_actions[0] = self.engine._calculate_turn_actions(0)

        assert self._has_action(0, GameAction.KAN)
        result = self.engine.execute_action(0, GameAction.KAN, tile=kan_tile)

        assert result.rinshan_tile is not None
        assert result.rinshan_win is not None

    def test_execute_action_declare_ankan_rinshan_win(self):
        """Test rinshan after declare_ankan."""
        self._init_game()

        ten_tile = Tile(Suit.PINZU, 4)
        closed_kan_tiles = parse_tiles("1111234567m1234p")
        self.engine._hands[0] = Hand(closed_kan_tiles)
        self.engine._current_player = 0
        assert self.engine._tile_set is not None
        self.engine._tile_set._rinshan_tiles[0] = ten_tile
        self.engine._waiting_for_actions[0] = self.engine._calculate_turn_actions(0)

        assert self._has_action(0, GameAction.DECLARE_ANKAN)
        result = self.engine.execute_action(0, GameAction.DECLARE_ANKAN)

        assert result.rinshan_tile is not None
        assert result.rinshan_win is not None

    def test_execute_action_kan_chankan_complete(self):
        """Test chankan complete scenario."""
        self._init_game()

        kan_tiles = parse_tiles("111234567m1234p")
        hand0 = Hand(kan_tiles)
        kan_tile = Tile(Suit.MANZU, 1)
        hand0.pon(kan_tile)
        hand0.add_tile(kan_tile)
        self.engine._hands[0] = hand0
        self.engine._current_player = 0
        self.engine._last_discarded_tile = None
        self.engine._last_discarded_player = None

        test_tiles = parse_tiles("23456m12344789p")
        self.engine._hands[1] = Hand(test_tiles)
        self.engine._waiting_for_actions[0] = self.engine._calculate_turn_actions(0)

        assert self._has_action(0, GameAction.DECLARE_ANKAN)
        result = self.engine.execute_action(0, GameAction.DECLARE_ANKAN)

        assert result.chankan is True
        assert result.winners is not None
        assert len(result.winners) > 0
        winner = result.winners[0]
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
        starting_tiles = parse_tiles("1112345666788m")
        self.engine._hands[player] = Hand(starting_tiles)
        self.engine._last_discarded_tile = kan_tile
        self.engine._last_discarded_player = (
            player + 1
        ) % self.engine.get_num_players()
        self.engine._kan_count = 3
        assert self.engine._tile_set is not None
        self.engine._tile_set._wall = [Tile(Suit.PINZU, 2)]
        non_winning_tiles = [Tile(Suit.PINZU, 1)] * 14
        self.engine._tile_set._dead_wall = non_winning_tiles
        self.engine._tile_set._rinshan_tiles = non_winning_tiles[:4]
        self.engine._tile_set._tiles = []
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
        starting_tiles = parse_tiles("2222334455678m")
        self.engine._hands[player] = Hand(starting_tiles)
        self.engine._kan_count = 3
        assert self.engine._tile_set is not None
        self.engine._tile_set._wall = [Tile(Suit.SOUZU, 5)]
        self.engine._tile_set._tiles = []
        self.engine._tile_set._rinshan_tiles = [Tile(Suit.HONORS, 1)] * 4
        self.engine._waiting_for_actions[player] = self.engine._calculate_turn_actions(
            player
        )

        result = self.engine.execute_action(player, GameAction.DECLARE_ANKAN)

        assert result.closed_kan is True
        assert self.engine._kan_count == 4
        assert self.engine.check_ryuukyoku() == RyuukyokuType.SUUKAN_SANRA


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
