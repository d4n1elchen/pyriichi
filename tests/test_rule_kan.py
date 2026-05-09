"""Kan rule tests for RuleEngine."""

from pyriichi.hand import Hand, Meld, MeldType
from pyriichi.rules import GameAction, GamePhase, RuleEngine
from pyriichi.tiles import Suit, Tile, TileSet
from pyriichi.utils import parse_tiles
from tests.helpers import RuleEngineTestMixin


class TestKanBehavior(RuleEngineTestMixin):
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
