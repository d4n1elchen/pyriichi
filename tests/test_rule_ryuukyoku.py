"""Ryuukyoku tests for RuleEngine."""

import pytest

from pyriichi.hand import Hand
from pyriichi.rules import GameAction, GamePhase, RyuukyokuType
from pyriichi.tiles import Suit, Tile
from pyriichi.utils import parse_tiles
from tests.helpers import RuleEngineTestMixin


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

        with pytest.raises(ValueError, match="牌組未初始化"):
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
        while self.engine._tile_set._tiles:
            self.engine._tile_set.draw()
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
        assert self.engine._game_state.dealer == player
        assert self.engine._game_state.round_number == 1
        assert self.engine._game_state.honba == 1

    def test_abortive_draw_can_rotate_dealer(self):
        """Test abortive draw dealer rotation configuration."""
        self._init_game()
        self.engine._game_state.ruleset.abortive_draw_dealer_continues = False
        player = self.engine.get_current_player()

        tiles = parse_tiles("19m19p19s1234567z1m")
        self.engine._hands[player] = Hand(tiles)
        self.engine._is_first_turn_after_deal = True
        self.engine._waiting_for_actions[player] = self.engine._calculate_turn_actions(
            player
        )

        result = self.engine.execute_action(player, GameAction.DECLARE_KYUUSHU_KYUUHAI)

        assert result.ryuukyoku is not None
        assert result.ryuukyoku.ryuukyoku_type == RyuukyokuType.KYUUSHU_KYUUHAI
        assert self.engine._game_state.dealer == 1
        assert self.engine._game_state.round_number == 2
        assert self.engine._game_state.honba == 1

    def test_handle_draw_suucha_riichi(self):
        """Test suucha_riichi (Four riichi) ryuukyoku handling"""
        self._init_game()

        # Set all players riichi
        for i in range(4):
            self.engine._hands[i].set_riichi(True)

        # Check ryuukyoku
        ryuukyoku_type = self.engine.check_ryuukyoku()
        assert ryuukyoku_type == RyuukyokuType.SUUCHA_RIICHI

    def test_handle_ryuukyoku_suufon_renda_settles_round_state(self):
        """Test suufon_renda updates round state."""
        self._init_game()
        self.engine._game_state.set_dealer(0)
        self.engine._game_state._honba = 2
        self.engine._is_first_turn_after_deal = False
        wind_tile = Tile(Suit.HONORS, 1)
        for player in range(4):
            self.engine._discard_history.append((player, wind_tile))

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
