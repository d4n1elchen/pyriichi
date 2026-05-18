"""Action availability tests for RuleEngine."""

from pyriichi.hand import Hand, Meld, MeldType
from pyriichi.rules import GameAction, GamePhase
from pyriichi.tiles import Suit, Tile
from pyriichi.utils import parse_tiles
from tests.helpers import RuleEngineTestMixin


class TestActionAvailability(RuleEngineTestMixin):
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
        discarded_player = self.engine.get_current_player()
        caller = (discarded_player + 1) % self.engine.get_num_players()
        # 111m 234m 567m 12p 3p 4p
        self.engine._hands[caller] = Hand(parse_tiles("111m234m567m1234p"))
        self.engine._last_discarded_tile = Tile(Suit.MANZU, 1)
        self.engine._last_discarded_player = discarded_player

        # Force update actions
        self.engine._waiting_for_actions = self.engine._check_interrupts(
            self.engine._last_discarded_tile, discarded_player
        )

        assert self._has_action(caller, GameAction.KAN)
        # Modify last discard to make kan unavailable
        self.engine._last_discarded_tile = Tile(Suit.MANZU, 9)

        # Force update actions again
        self.engine._waiting_for_actions = self.engine._check_interrupts(
            self.engine._last_discarded_tile, discarded_player
        )

        assert not self._has_action(caller, GameAction.KAN)

    def test_get_available_actions_declare_ankan(self):
        """Test if declare_ankan is available"""
        self._init_game()
        # 111m 123m 456m 7m 123p
        self.engine._hands[0] = Hand(parse_tiles("1111m234m567m123p"))

        # Force update actions
        self.engine._waiting_for_actions[0] = self.engine._calculate_turn_actions(0)

        assert self._has_action(0, GameAction.DECLARE_ANKAN)

    def test_drawn_open_winning_hand_can_tsumo(self):
        """Test tsumo is available after drawing a winning tile for an open hand."""
        self._init_game()
        player = 0
        winning_tile = Tile(Suit.HONORS, 6)
        hand = Hand(parse_tiles("123m555z6z"))
        hand._melds.append(
            Meld(
                MeldType.PON_MELD,
                [Tile(Suit.HONORS, 7)] * 3,
                called_tile=Tile(Suit.HONORS, 7),
                called_from=1,
            )
        )
        hand._melds.append(
            Meld(
                MeldType.CHI_MELD,
                [Tile(Suit.MANZU, 7), Tile(Suit.MANZU, 8), Tile(Suit.MANZU, 9)],
                called_tile=Tile(Suit.MANZU, 7),
                called_from=3,
            )
        )
        self.engine._hands[player] = hand
        self.engine._current_player = player
        assert self.engine.tileset is not None
        self.engine.tileset._tiles = [winning_tile]

        result = self.engine._handle_draw(player)

        assert self.engine._last_drawn_tile == (player, winning_tile)
        assert GameAction.TSUMO in result.waiting_for[player]
        assert GameAction.TSUMO in self.engine.get_available_actions(player)

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
