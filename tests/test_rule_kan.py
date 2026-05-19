"""Kan rule tests for RuleEngine."""

import pytest

from pyriichi.hand import Hand, Meld, MeldType
from pyriichi.rules import GameAction, GamePhase, RuleEngine, RyuukyokuType
from pyriichi.tiles import Suit, Tile, TileSet
from pyriichi.utils import parse_tiles
from tests.helpers import RuleEngineTestMixin, no_response_hand


def _set_hand(engine, player, hand_str):
    hand = Hand(parse_tiles(hand_str))
    engine._hands[player] = hand
    return hand


def _set_no_response_hands(engine, players):
    for player in players:
        engine._hands[player] = no_response_hand()


def _discard_tile(engine, player, tile):
    engine._current_player = player
    engine.get_hand(player).add_tile(tile)
    engine.execute_action(player, GameAction.DISCARD, tile=tile)


def _set_rinshan_tile(engine, tile):
    assert engine._tile_set is not None
    engine._tile_set._rinshan_tiles[0] = tile


def _set_waiting_turn_actions(engine, player):
    engine._waiting_for_actions[player] = engine._calculate_turn_actions(player)


def _prepare_exhausted_kan_wall(engine, rinshan_tile):
    assert engine._tile_set is not None
    engine._tile_set._wall = [Tile(Suit.PINZU, 2)]
    engine._tile_set._dead_wall = [rinshan_tile] * 14
    engine._tile_set._rinshan_tiles = [rinshan_tile] * 4
    engine._tile_set._tiles = []


def _closed_kan_selection_engine(hand_str):
    tiles = parse_tiles(hand_str)
    engine = RuleEngine(num_players=1)
    engine._hands = [Hand(tiles)]
    engine._tile_set = TileSet()
    for tile in tiles:
        if tile in engine._tile_set._tiles:
            engine._tile_set._tiles.remove(tile)
    engine._tile_set.shuffle()
    engine._phase = GamePhase.PLAYING
    engine._current_player = 0
    engine._riichi_ippatsu = {}
    _set_waiting_turn_actions(engine, 0)
    return engine


class TestKanBehavior(RuleEngineTestMixin):
    def test_open_kan_logic(self):
        """Test open_kan logic: Automatically infer tile and remove from discards."""
        self.engine.start_game()
        self.engine.start_round()
        self.engine.deal()

        p1 = 1
        hand1 = _set_hand(self.engine, p1, "111m123456789p1p")
        _set_no_response_hands(self.engine, [2, 3])

        p0 = 0
        hand0 = self.engine.get_hand(p0)
        discard_tile = Tile(Suit.MANZU, 1)
        _discard_tile(self.engine, p0, discard_tile)

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

        _set_no_response_hands(self.engine, [0, 2, 3])
        p1_hand = _set_hand(self.engine, 1, "444z123456789m1p")
        tile_4z = Tile(Suit.HONORS, 4)
        _discard_tile(self.engine, 0, tile_4z)

        actions = self.engine.get_available_actions(1)
        assert GameAction.KAN in actions

        result = self.engine.execute_action(1, GameAction.KAN, tile_4z)

        assert result.success
        assert result.kan is True
        assert self.engine.get_current_player() == 1

        p1_actions = self.engine.get_available_actions(1)
        assert GameAction.DISCARD in p1_actions

        tile_to_discard = p1_hand.tiles[0]
        result_discard = self.engine.execute_action(
            1, GameAction.DISCARD, tile_to_discard
        )
        assert result_discard.success

        assert self.engine.get_current_player() == 2
        assert self.engine.check_furiten_temp(0) is False

    def test_draw_with_kan(self):
        """Test Draw with kan (hand size limit should increase)"""
        self._init_game()

        hand = self.engine.get_hand(0)
        hand._tiles = parse_tiles("1m2m3m4m5m6m7m8m9m1p")
        kan_tiles = parse_tiles("2p2p2p2p")
        meld = Meld(MeldType.CLOSED_KAN, kan_tiles)
        hand._melds = [meld]

        self.engine._current_player = 0

        self.engine._handle_draw(0)

        assert hand.total_tile_count() == 15
        assert len(hand.melds) == 1

    def test_execute_action_kan_tile_none(self):
        """Test kan with tile as None."""
        self._init_game()
        current_player = self.engine.get_current_player()

        with pytest.raises(ValueError):
            self.engine.execute_action(current_player, GameAction.KAN, tile=None)

    def test_execute_action_add_kan_no_tile(self):
        """Test added kan without specifying tile."""
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
        assert not self._has_action(current_player, GameAction.DECLARE_ANKAN)
        result = self.engine.execute_action(current_player, GameAction.KAN, tile=None)

        assert result.kan is True
        assert hand.melds[0].type == MeldType.OPEN_KAN

    def test_execute_action_kan_rinshan_win(self):
        """Test rinshan after open_kan."""
        self._init_game()

        kan_tile = Tile(Suit.MANZU, 1)
        ten_tile = Tile(Suit.PINZU, 4)
        _set_hand(self.engine, 1, "111234567m1234p")
        self.engine._current_player = 0
        self.engine._last_discarded_tile = kan_tile
        self.engine._last_discarded_player = 0
        self.engine.get_hand(0)._discards.append(kan_tile)
        _set_rinshan_tile(self.engine, ten_tile)
        self.engine._waiting_for_actions = self.engine._check_interrupts(kan_tile, 0)

        assert self._has_action(1, GameAction.KAN)
        result = self.engine.execute_action(1, GameAction.KAN, tile=kan_tile)

        assert result.rinshan_tile is not None
        assert result.rinshan_win is not None

    def test_execute_action_declare_ankan_rinshan_win(self):
        """Test rinshan after declare_ankan."""
        self._init_game()

        ten_tile = Tile(Suit.PINZU, 4)
        _set_hand(self.engine, 0, "1111234567m1234p")
        self.engine._current_player = 0
        _set_rinshan_tile(self.engine, ten_tile)
        _set_waiting_turn_actions(self.engine, 0)

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

        _set_hand(self.engine, 1, "23456m12344789p")
        _set_waiting_turn_actions(self.engine, 0)

        assert self._has_action(0, GameAction.KAN)
        assert not self._has_action(0, GameAction.DECLARE_ANKAN)
        result = self.engine.execute_action(0, GameAction.KAN, tile=kan_tile)

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

        discarded_player = self.engine.get_current_player()
        player = (discarded_player + 1) % self.engine.get_num_players()
        num_players = self.engine.get_num_players()
        kan_tile = Tile(Suit.MANZU, 6)
        _set_hand(self.engine, player, "1112345666788m")
        # Pin non-acting hands so they can't compete for the call and defer
        # KAN resolution (the discarding dealer's hand is left as-dealt).
        _set_no_response_hands(
            self.engine,
            [(player + offset) % num_players for offset in (1, 2)],
        )
        self.engine._last_discarded_tile = kan_tile
        self.engine._last_discarded_player = discarded_player
        self.engine.get_hand(discarded_player)._discards.append(kan_tile)
        self.engine._kan_count = 3
        _prepare_exhausted_kan_wall(self.engine, Tile(Suit.PINZU, 1))
        self.engine._waiting_for_actions = self.engine._check_interrupts(
            kan_tile, discarded_player
        )

        result = self.engine.execute_action(player, GameAction.KAN, tile=kan_tile)

        assert result.kan is True
        assert self.engine._kan_count == 4
        assert self.engine.check_ryuukyoku() == RyuukyokuType.SUUKAN_SANRA

    def test_execute_action_declare_ankan_wall_exhausted(self):
        """Test closed_kan triggers suukan_sanra."""
        self._init_game()

        player = self.engine.get_current_player()
        _set_hand(self.engine, player, "2222334455678m")
        self.engine._kan_count = 3
        _prepare_exhausted_kan_wall(self.engine, Tile(Suit.HONORS, 1))
        _set_waiting_turn_actions(self.engine, player)

        result = self.engine.execute_action(player, GameAction.DECLARE_ANKAN)

        assert result.closed_kan is True
        assert self.engine._kan_count == 4
        assert self.engine.check_ryuukyoku() == RyuukyokuType.SUUKAN_SANRA


class TestClosedKanSelection:
    def test_closed_kan_selection(self):
        engine = _closed_kan_selection_engine("1111m2222m567p89s")

        tile_to_kan = Tile(Suit.MANZU, 2)
        result = engine.execute_action(0, GameAction.DECLARE_ANKAN, tile=tile_to_kan)

        assert result.success

        melds = engine._hands[0].melds
        assert len(melds) == 1
        assert melds[0].type == MeldType.CLOSED_KAN
        assert melds[0].tiles[0] == tile_to_kan

        remaining_tiles = engine._hands[0].tiles
        count_1m = sum(
            1 for t in remaining_tiles if t.suit == Suit.MANZU and t.rank == 1
        )
        assert count_1m == 4

        tile_to_kan_1 = Tile(Suit.MANZU, 1)
        result = engine.execute_action(0, GameAction.DECLARE_ANKAN, tile=tile_to_kan_1)
        assert result.success

        melds = engine._hands[0].melds
        assert len(melds) == 2
        assert melds[1].tiles[0] == tile_to_kan_1
