"""Ryuukyoku tests for RuleEngine."""

import pytest

from pyriichi.game_state import Wind
from pyriichi.hand import Hand
from pyriichi.rules import GameAction, GamePhase, RyuukyokuType
from pyriichi.tiles import Suit, Tile
from pyriichi.utils import parse_tiles
from tests.helpers import RuleEngineTestMixin


def _set_same_discard_history(engine, tile):
    for player in range(4):
        engine._discard_history.append((player, tile))


def _exhaust_wall(engine):
    assert engine._tile_set is not None
    while engine._tile_set._tiles:
        engine._tile_set.draw()


def _set_ron_ready_players(engine, players, discard_tile, hand_str):
    engine._last_discarded_tile = discard_tile
    engine._last_discarded_player = 0
    for player in players:
        engine._hands[player] = Hand(parse_tiles(hand_str))


def _prepare_kyuushu_kyuuhai(engine, player):
    engine._hands[player] = Hand(parse_tiles("19m19p19s1234567z1m"))
    engine._is_first_turn_after_deal = True
    engine._waiting_for_actions[player] = engine._calculate_turn_actions(player)


def _score_deltas(initial_scores, current_scores):
    return [score - initial_scores[i] for i, score in enumerate(current_scores)]


def _yaochuu_discards():
    return [
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


def _set_nagashi_mangan_candidate(engine, player, discards=None, called=False):
    engine._hands[player]._discards = (
        list(discards) if discards is not None else _yaochuu_discards()
    )
    engine._has_called_discard[player] = called


def _prepare_fourth_kan_chankan(engine):
    engine._kan_count = 3
    engine._current_player = 0
    kan_tile = Tile(Suit.SOUZU, 4)

    hand = Hand(parse_tiles("444s234567m1234p"))
    hand.pon(kan_tile)
    hand.add_tile(kan_tile)
    engine._hands[0] = hand
    engine._last_discarded_tile = None
    engine._last_discarded_player = None

    engine._hands[1] = Hand(parse_tiles("23s234567m789p44p"))
    engine._waiting_for_actions[0] = engine._calculate_turn_actions(0)


def _prepare_fourth_kan_ron(engine):
    winning_tile = Tile(Suit.PINZU, 1)
    engine._kan_count = 4
    engine._hands[1] = Hand(parse_tiles("234567m789p234s1p"))
    engine._last_discarded_tile = winning_tile
    engine._last_discarded_player = 0
    engine._check_interrupts(winning_tile, 0)
    return winning_tile


def _prepare_fourth_kan_rinshan(engine, player):
    engine._kan_count = 3
    engine._hands[player] = Hand(parse_tiles("1111m234567m1234p"))
    rinshan_tile = Tile(Suit.PINZU, 4)
    assert engine._tile_set is not None
    engine._tile_set._rinshan_tiles[0] = rinshan_tile
    engine._waiting_for_actions[player] = engine._calculate_turn_actions(player)


class TestRyuukyoku(RuleEngineTestMixin):
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

        _set_same_discard_history(self.engine, wind_tile)

        # Check suufon_renda
        ryuukyoku_type = self.engine.check_ryuukyoku()
        assert ryuukyoku_type is not None
        assert ryuukyoku_type == RyuukyokuType.SUUFON_RENDA

    def test_check_draw_sancha_ron(self):
        """Test sancha_ron (Three ron) ryuukyoku check"""
        self._init_game()

        # Set triple_ron to allow ryuukyoku
        self.engine._game_state.ruleset.allow_triple_ron = False

        winning_tile = Tile(Suit.PINZU, 4)
        _set_ron_ready_players(
            self.engine, [1, 2, 3], winning_tile, "123456789m1234p"
        )

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
        _exhaust_wall(self.engine)

        # Check exhaustive_draw ryuukyoku
        ryuukyoku_type = self.engine.check_ryuukyoku()
        assert ryuukyoku_type is not None
        assert ryuukyoku_type == RyuukyokuType.EXHAUSTIVE_DRAW

    def test_execute_action_draw_no_tile_set(self):
        """Test draw when tile set is not initialized."""
        self._init_game()
        hand = self.engine.get_hand(0)
        self.engine.execute_action(0, GameAction.DISCARD, tile=hand.tiles[0])
        current_player = self.engine.get_current_player()

        self.engine._tile_set = None

        hand = self.engine.get_hand(current_player)
        if hand.total_tile_count() >= 14:
            hand.tiles.pop()

        with pytest.raises(ValueError, match="牌山未初始化"):
            self.engine._handle_draw(current_player)

    def test_execute_action_draw_last_tile(self):
        """Test draw last tile."""
        self._init_game()
        current_player = self.engine.get_current_player()

        hand = self.engine.get_hand(current_player)
        hand._tiles.pop()

        assert self.engine._tile_set is not None
        self.engine._tile_set._tiles = [Tile(Suit.MANZU, 1)]

        result = self.engine._handle_draw(current_player)

        assert result.is_last_tile is True

    def test_execute_action_draw_no_tile_drawn(self):
        """Test draw when no tiles left."""
        self._init_game()
        current_player = self.engine.get_current_player()

        assert self.engine._tile_set is not None
        hand = self.engine.get_hand(current_player)
        assert hand.tiles is not None
        self.engine.execute_action(
            current_player, GameAction.DISCARD, tile=hand.tiles[0]
        )
        _exhaust_wall(self.engine)
        current_player = self.engine.get_current_player()

        hand = self.engine.get_hand(current_player)
        while hand.total_tile_count() >= 14:
            hand._tiles.pop()

        result = self.engine._handle_draw(current_player)

        assert result.ryuukyoku is not None
        assert result.ryuukyoku.ryuukyoku is True
        assert result.ryuukyoku.ryuukyoku_type == RyuukyokuType.EXHAUSTIVE_DRAW
        assert self.engine._phase == GamePhase.RYUUKYOKU

    def test_declare_kyuushu_kyuuhai(self):
        """Test kyuushu_kyuuhai handling."""
        self._init_game()
        player = self.engine.get_current_player()

        _prepare_kyuushu_kyuuhai(self.engine, player)

        # Execute action
        result = self.engine.execute_action(player, GameAction.DECLARE_KYUUSHU_KYUUHAI)

        assert result.ryuukyoku is not None
        assert result.ryuukyoku.ryuukyoku is True
        assert result.ryuukyoku.ryuukyoku_type == RyuukyokuType.KYUUSHU_KYUUHAI
        assert result.ryuukyoku.kyuushu_kyuuhai_player == player
        assert self.engine._game_state.dealer == player
        assert self.engine._game_state.round_number == 1
        assert self.engine._game_state.honba == 1

    def test_kyuushu_kyuuhai_requires_first_turn_after_deal(self):
        """Test kyuushu_kyuuhai is unavailable after the first turn."""
        self._init_game()
        player = self.engine.get_current_player()
        _prepare_kyuushu_kyuuhai(self.engine, player)
        self.engine._is_first_turn_after_deal = False

        actions = self.engine._calculate_turn_actions(player)

        assert not self.engine._check_kyuushu_kyuuhai(player)
        assert GameAction.DECLARE_KYUUSHU_KYUUHAI not in actions

    def test_abortive_draw_can_rotate_dealer(self):
        """Test abortive draw dealer rotation configuration."""
        self._init_game()
        self.engine._game_state.ruleset.abortive_draw_dealer_continues = False
        player = self.engine.get_current_player()

        _prepare_kyuushu_kyuuhai(self.engine, player)

        result = self.engine.execute_action(player, GameAction.DECLARE_KYUUSHU_KYUUHAI)

        assert result.ryuukyoku is not None
        assert result.ryuukyoku.ryuukyoku_type == RyuukyokuType.KYUUSHU_KYUUHAI
        assert self.engine._game_state.dealer == 1
        assert self.engine._game_state.round_number == 2
        assert self.engine._game_state.honba == 1

    def test_handle_draw_suucha_riichi(self):
        """Test suucha_riichi (Four riichi) ryuukyoku handling"""
        self._init_game()

        for i in range(4):
            self.engine._hands[i].set_riichi(True)

        ryuukyoku_type = self.engine.check_ryuukyoku()
        assert ryuukyoku_type == RyuukyokuType.SUUCHA_RIICHI

    def test_suucha_riichi_does_not_transfer_points(self):
        """Test suucha_riichi abortive draw has no immediate payment."""
        self._init_game()
        initial_scores = self.engine._game_state.scores.copy()

        for i in range(4):
            self.engine._hands[i].set_riichi(True)

        result = self.engine.handle_ryuukyoku()

        assert result.ryuukyoku is True
        assert result.ryuukyoku_type == RyuukyokuType.SUUCHA_RIICHI
        assert self.engine._game_state.scores == initial_scores

    def test_handle_ryuukyoku_suufon_renda_settles_round_state(self):
        """Test suufon_renda updates round state."""
        self._init_game()
        self.engine._game_state.set_dealer(0)
        self.engine._game_state._honba = 2
        self.engine._is_first_turn_after_deal = False
        wind_tile = Tile(Suit.HONORS, 1)
        _set_same_discard_history(self.engine, wind_tile)

        result = self.engine.handle_ryuukyoku()

        assert result.ryuukyoku is True
        assert result.ryuukyoku_type == RyuukyokuType.SUUFON_RENDA
        assert self.engine._game_state.dealer == 0
        assert self.engine._game_state.round_number == 1
        assert self.engine._game_state.honba == 3

    def test_check_nagashi_mangan(self):
        """Test nagashi_mangan check"""
        self._init_game()
        player = 0

        _set_nagashi_mangan_candidate(self.engine, player)
        assert self.engine._check_nagashi_mangan(player) is True

        self.engine._hands[player]._discards.append(Tile(Suit.MANZU, 5))
        assert self.engine._check_nagashi_mangan(player) is False

        _set_nagashi_mangan_candidate(self.engine, player, called=True)
        assert self.engine._check_nagashi_mangan(player) is False

    def test_handle_ryuukyoku_scores_nagashi_mangan_as_mangan(self):
        """Test handle_ryuukyoku scores nagashi_mangan as mangan."""
        self._init_game()
        player = 1
        self.engine._game_state.set_dealer(0)
        self.engine._tile_set._tiles = []
        _set_nagashi_mangan_candidate(
            self.engine,
            player,
            [
                Tile(Suit.MANZU, 1),
                Tile(Suit.MANZU, 9),
                Tile(Suit.PINZU, 1),
                Tile(Suit.PINZU, 9),
            ],
        )
        initial_scores = self.engine._game_state.scores

        result = self.engine.handle_ryuukyoku()

        score_deltas = _score_deltas(initial_scores, self.engine._game_state.scores)
        assert result.nagashi_mangan_players == [player]
        assert score_deltas == [-4000, 8000, -2000, -2000]

    def test_check_sancha_ron(self):
        """Test sancha_ron (Three ron) check"""
        self._init_game()

        winning_tile = Tile(Suit.PINZU, 4)
        _set_ron_ready_players(
            self.engine, [1, 2, 3], winning_tile, "123456789m1234p"
        )

        # Check sancha_ron
        result = self.engine._check_sancha_ron()
        assert result is True

    def test_end_round_draw(self):
        """Test end round (ryuukyoku)"""
        self._init_game()

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
        _prepare_fourth_kan_chankan(self.engine)

        result = self.engine.execute_action(0, GameAction.KAN)
        assert result.chankan is True
        assert self.engine._kan_count == 3
        assert self.engine.check_ryuukyoku() is None

    def test_fourth_kan_ron_does_not_trigger_suukan_sanra(self):
        """Test ron after fourth kan does not trigger suukan_sanra."""
        self._init_game()
        winning_tile = _prepare_fourth_kan_ron(self.engine)

        win_result = self.engine.check_win(1, winning_tile)
        assert win_result is not None
        assert self.engine.check_ryuukyoku() is None

    def test_fourth_kan_rinshan_win_does_not_trigger_suukan_sanra(self):
        """Test rinshan after fourth kan does not trigger suukan_sanra."""
        self._init_game()

        player = self.engine.get_current_player()
        _prepare_fourth_kan_rinshan(self.engine, player)

        result = self.engine.execute_action(player, GameAction.DECLARE_ANKAN)

        assert result.rinshan_win is not None
        assert result.rinshan_win.win is True
        assert self.engine.check_ryuukyoku() is None

    def test_triple_ron_disabled_ryuukyoku(self):
        """Test triple_ron disabled: Three players ron leads to ryuukyoku"""
        self._init_game()

        # Disable triple_ron (default)
        assert not self.engine._game_state.ruleset.allow_triple_ron

        discard_tile = Tile(Suit.MANZU, 1)
        _set_ron_ready_players(
            self.engine, [1, 2, 3], discard_tile, "23456789m123p44p"
        )

        # Test check_multiple_ron
        winners = self.engine.check_multiple_ron(discard_tile, 0)

        # Detect three players can ron but triple_ron disabled, return empty list (trigger ryuukyoku)
        assert len(winners) == 0  # Empty list means sancha_ron ryuukyoku
