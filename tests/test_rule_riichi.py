"""Riichi rule tests for RuleEngine."""

import pytest

from pyriichi.hand import Hand
from pyriichi.rules import GameAction, GamePhase
from pyriichi.tiles import Suit, Tile
from pyriichi.utils import parse_tiles
from tests.helpers import (
    RuleEngineTestMixin,
    no_response_hand,
    set_non_matching_scoring_dora,
)


def _set_ippatsu(engine, players):
    engine._riichi_ippatsu = {player: True for player in players}
    engine._riichi_ippatsu_discard = {player: 0 for player in players}


def _discard_for_call(engine, discarder, discard_tile, discarder_hand, responder_hands):
    engine._hands[discarder] = Hand(parse_tiles(discarder_hand))
    for player, hand_str in responder_hands.items():
        engine._hands[player] = Hand(parse_tiles(hand_str))
    engine._current_player = discarder
    engine.execute_action(discarder, GameAction.DISCARD, tile=discard_tile)


def _pass_waiting_players(engine, except_player=None):
    for player in list(engine.waiting_for_actions.keys()):
        if player == except_player:
            continue
        if GameAction.PASS in engine.get_available_actions(player):
            engine.execute_action(player, GameAction.PASS)


def _chi_sequence_with_ranks(engine, player, ranks):
    return next(
        (
            sequence
            for sequence in engine.get_available_chi_sequences(player)
            if sorted(tile.rank for tile in sequence) == ranks
        ),
        None,
    )


class TestRiichi(RuleEngineTestMixin):
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

    def test_execute_action_riichi(self):
        """Test execute riichi action."""
        self._init_game()
        current_player = self.engine.get_current_player()
        initial_score = self.engine._game_state.scores[current_player]
        tiles = parse_tiles("123456789m1234p")
        hand = Hand(tiles)
        hand.add_tile(Tile(Suit.SOUZU, 9))
        self.engine._hands[current_player] = hand

        self.engine._waiting_for_actions[current_player] = (
            self.engine._calculate_turn_actions(current_player)
        )

        assert self._has_action(current_player, GameAction.DECLARE_RIICHI)

        result = self.engine.execute_action(
            current_player, GameAction.DECLARE_RIICHI, tile=Tile(Suit.SOUZU, 9)
        )
        assert result.riichi is True
        assert self.engine.get_hand(current_player).is_riichi
        assert current_player in self.engine._riichi_ippatsu
        assert self.engine._riichi_ippatsu[current_player]
        assert self.engine._game_state.scores[current_player] == initial_score - 1000
        assert self.engine._game_state.riichi_sticks == 1

    def test_riichi_declaration_discard_ron_reverts_riichi_stick(self):
        """Test ron on a riichi declaration discard reverts the declaration."""
        self._init_game()
        set_non_matching_scoring_dora(self.engine)
        discard_tile = Tile(Suit.SOUZU, 9)
        self.engine._current_player = 0
        self.engine._hands[0] = Hand(parse_tiles("123456789m1234p9s"))
        self.engine._hands[1] = Hand(parse_tiles("123m123p123s78s55p"))
        self.engine._hands[1].set_riichi(True)
        self.engine._hands[2] = no_response_hand()
        self.engine._hands[3] = no_response_hand()

        result = self.engine._handle_riichi(0, tile=discard_tile)

        assert result.riichi is True
        assert self.engine.get_hand(0).is_riichi
        assert self.engine._game_state.riichi_sticks == 1
        assert 0 in self.engine._pending_riichi_discards
        assert GameAction.RON in self.engine.get_available_actions(1)

        _pass_waiting_players(self.engine, except_player=1)
        ron_result = self.engine.execute_action(1, GameAction.RON)

        assert 1 in ron_result.win_results
        assert not self.engine.get_hand(0).is_riichi
        assert 0 not in self.engine._riichi_ippatsu
        assert 0 not in self.engine._pending_riichi_discards
        assert self.engine._game_state.riichi_sticks == 0
        assert ron_result.win_results[1].score_result.riichi_sticks_bonus == 0

    def test_invalid_riichi_applies_chombo(self):
        """Test invalid riichi applies chombo."""
        self._init_game()
        player = self.engine.get_current_player()
        hand = Hand(parse_tiles("124578m1245p78s1z"))
        tile = Tile(Suit.HONORS, 1)
        hand.add_tile(tile)
        self.engine._hands[player] = hand
        initial_scores = self.engine._game_state.scores.copy()

        result = self.engine._handle_riichi(player, tile=tile)

        assert result.chombo is True
        assert result.chombo_player == player
        assert self.engine.get_phase() == GamePhase.RYUUKYOKU
        assert self.engine._game_state.scores[player] == initial_scores[player] - 12000

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

    def test_interrupt_riichi_ippatsu_on_chi(self):
        """Test chi interrupts ippatsu"""
        self._init_game()
        _set_ippatsu(self.engine, [0])

        chi_tile = Tile(Suit.MANZU, 4)
        _discard_for_call(
            self.engine,
            0,
            chi_tile,
            "11223344556677m",
            {1: "23456789m12345p"},
        )
        target_sequence = _chi_sequence_with_ranks(self.engine, 1, [2, 3])

        assert target_sequence is not None
        self.engine.execute_action(1, GameAction.CHI, sequence=target_sequence)
        _pass_waiting_players(self.engine, except_player=1)

        assert self.engine._riichi_ippatsu[0] is False

    def test_interrupt_riichi_ippatsu_on_pon(self):
        """Test pon interrupts ippatsu"""
        self._init_game()
        _set_ippatsu(self.engine, [0])

        pon_tile = Tile(Suit.PINZU, 7)
        _discard_for_call(
            self.engine,
            0,
            pon_tile,
            "7p1112233445566m",
            {2: "77p11223344556p"},
        )

        assert GameAction.PON in self.engine.get_available_actions(2)
        self.engine.execute_action(2, GameAction.PON)
        _pass_waiting_players(self.engine)

        assert self.engine._riichi_ippatsu[0] is False

    def test_interrupt_riichi_ippatsu_on_kan(self):
        """Test open_kan interrupts ippatsu"""
        self._init_game()
        _set_ippatsu(self.engine, [0])

        kan_tile = Tile(Suit.SOUZU, 9)
        _discard_for_call(
            self.engine,
            0,
            kan_tile,
            "9s1122334455667m",
            {1: "999s1122334455s"},
        )

        assert GameAction.KAN in self.engine.get_available_actions(1)
        self.engine.execute_action(1, GameAction.KAN, tile=kan_tile)
        _pass_waiting_players(self.engine, except_player=1)

        assert self.engine._riichi_ippatsu[0] is False

    def test_interrupt_riichi_ippatsu_on_declare_ankan(self):
        """Test declare_ankan interrupts ippatsu"""
        self._init_game()
        _set_ippatsu(self.engine, [0, 1])

        self.engine._hands[3] = Hand(parse_tiles("111123456789m1p"))

        # Force update actions
        self.engine._current_player = 3
        self.engine._waiting_for_actions = {}
        self.engine._waiting_for_actions[3] = self.engine._calculate_turn_actions(3)

        assert GameAction.DECLARE_ANKAN in self.engine.get_available_actions(3)
        result = self.engine.execute_action(3, GameAction.DECLARE_ANKAN)

        assert result.closed_kan is True or result.kan is True
        assert all(flag is False for flag in self.engine._riichi_ippatsu.values())

    def test_ippatsu_interrupt_can_be_disabled(self):
        """Test ippatsu interruption can be disabled by ruleset."""
        self._init_game()
        self.engine._game_state.ruleset.ippatsu_interrupt_on_meld_or_kan = False
        self.engine._riichi_ippatsu = {0: True}

        self.engine._interrupt_ippatsu(GameAction.PON, acting_player=1)

        assert self.engine._riichi_ippatsu[0] is True

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
