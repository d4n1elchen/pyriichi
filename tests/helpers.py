"""Shared test helpers."""

from pyriichi.hand import Hand
from pyriichi.rules import GameAction, RuleEngine
from pyriichi.tiles import Suit, Tile
from pyriichi.utils import parse_tiles


def initialized_engine(num_players: int = 4) -> RuleEngine:
    engine = RuleEngine(num_players=num_players)
    engine.start_game()
    engine.start_round()
    engine.deal()
    return engine


def no_response_hand() -> Hand:
    return Hand(parse_tiles("23456789p23456s"))


def set_non_matching_scoring_dora(engine: RuleEngine) -> None:
    assert engine._tile_set is not None
    engine._tile_set._dora_indicators = [Tile(Suit.HONORS, 1)]
    engine._tile_set._ura_dora_indicators = [Tile(Suit.HONORS, 2)]


class RuleEngineTestMixin:
    engine: RuleEngine

    def setup_method(self):
        self.engine = RuleEngine(num_players=4)

    def _has_action(self, player: int, action: GameAction) -> bool:
        return action in self.engine.get_available_actions(player)

    def _init_game(self):
        self.engine = initialized_engine()
