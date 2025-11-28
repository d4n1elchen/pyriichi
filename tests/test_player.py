import pytest

from pyriichi.game_state import GameState
from pyriichi.hand import Hand
from pyriichi.player import DefensivePlayer, PublicInfo, RandomPlayer, SimplePlayer
from pyriichi.rules import GameAction
from pyriichi.tiles import Suit, Tile
from pyriichi.utils import parse_tiles


class TestPlayer:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.game_state = GameState()

    def test_random_player_discard(self):
        player = RandomPlayer("Random")
        hand = Hand(parse_tiles("123m456m789m123p4p"))
        available_actions = [GameAction.DISCARD]

        action, tile = player.decide_action(self.game_state, 0, hand, available_actions)

        assert action == GameAction.DISCARD
        assert tile in hand.tiles

    def test_simple_player_discard_honor(self):
        player = SimplePlayer("Simple")
        # 手牌包含一張字牌（東）
        hand = Hand(parse_tiles("123m456m789m123p1z"))
        available_actions = [GameAction.DISCARD]

        action, tile = player.decide_action(self.game_state, 0, hand, available_actions)

        assert action == GameAction.DISCARD
        assert tile == Tile(Suit.JIHAI, 1)  # 應該打出東

    def test_defensive_player_genbutsu(self):
        player = DefensivePlayer("Defense")
        # 手牌：1m（安全），2m（危險），...
        hand = Hand(parse_tiles("123m456m789m123p4p"))
        available_actions = [GameAction.DISCARD]

        # 玩家 1 已立直並打過 1m
        public_info = PublicInfo(
            turn_number=10,
            dora_indicators=[],
            discards={1: [Tile(Suit.MANZU, 1)]},
            melds={},
            riichi_players=[1],
            scores=[25000] * 4,
        )

        action, tile = player.decide_action(
            self.game_state, 0, hand, available_actions, public_info
        )

        assert action == GameAction.DISCARD
        # 應該打出 1m，因為它是對玩家 1 的現物
        assert tile == Tile(Suit.MANZU, 1)

    def test_defensive_player_no_threat(self):
        player = DefensivePlayer("Defense")
        # 手牌包含 1z（字牌）和 1m
        hand = Hand(parse_tiles("123m456m789m123p1z"))
        available_actions = [GameAction.DISCARD]

        # 無人立直
        public_info = PublicInfo(
            turn_number=10,
            dora_indicators=[],
            discards={},
            melds={},
            riichi_players=[],
            scores=[25000] * 4,
        )

        action, tile = player.decide_action(
            self.game_state, 0, hand, available_actions, public_info
        )

        # 應該像 SimplePlayer 一樣行動（打出字牌）
        assert action == GameAction.DISCARD
        assert tile == Tile(Suit.JIHAI, 1)


if __name__ == "__main__":
    pytest.main([__file__])
