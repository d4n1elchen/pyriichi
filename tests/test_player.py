import pytest
from pyriichi.player import RandomPlayer, SimplePlayer, DefensivePlayer, PublicInfo
from pyriichi.rules import GameAction
from pyriichi.game_state import GameState
from pyriichi.hand import Hand
from pyriichi.tiles import Tile, Suit
from pyriichi.utils import parse_tiles

class TestPlayer:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.game_state = GameState()

    def test_random_player_discard(self):
        player = RandomPlayer("Random")
        hand = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p4p"))
        available_actions = [GameAction.DISCARD]

        action, tile = player.decide_action(self.game_state, 0, hand, available_actions)

        assert action == GameAction.DISCARD
        assert tile in hand.tiles

    def test_simple_player_discard_honor(self):
        player = SimplePlayer("Simple")
        # Hand with one honor (East)
        hand = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p1z"))
        available_actions = [GameAction.DISCARD]

        action, tile = player.decide_action(self.game_state, 0, hand, available_actions)

        assert action == GameAction.DISCARD
        assert tile == Tile(Suit.JIHAI, 1) # Should discard East

    def test_defensive_player_genbutsu(self):
        player = DefensivePlayer("Defense")
        # Hand: 1m (safe), 2m (unsafe), ...
        hand = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p4p"))
        available_actions = [GameAction.DISCARD]

        # Player 1 is in Riichi and discarded 1m
        public_info = PublicInfo(
            turn_number=10,
            dora_indicators=[],
            discards={1: [Tile(Suit.MANZU, 1)]},
            melds={},
            riichi_players=[1],
            scores=[25000] * 4
        )

        action, tile = player.decide_action(self.game_state, 0, hand, available_actions, public_info)

        assert action == GameAction.DISCARD
        # Should discard 1m because it's Genbutsu against Player 1
        assert tile == Tile(Suit.MANZU, 1)

    def test_defensive_player_no_threat(self):
        player = DefensivePlayer("Defense")
        # Hand with 1z (Honor) and 1m
        hand = Hand(parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p1z"))
        available_actions = [GameAction.DISCARD]

        # No one in Riichi
        public_info = PublicInfo(
            turn_number=10,
            dora_indicators=[],
            discards={},
            melds={},
            riichi_players=[],
            scores=[25000] * 4
        )

        action, tile = player.decide_action(self.game_state, 0, hand, available_actions, public_info)

        # Should behave like SimplePlayer (discard Honor)
        assert action == GameAction.DISCARD
        assert tile == Tile(Suit.JIHAI, 1)

if __name__ == '__main__':
    pytest.main([__file__])
