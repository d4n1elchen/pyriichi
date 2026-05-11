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


def set_ron_context(
    engine: RuleEngine,
    winner: int,
    discarder: int,
    hand_str: str,
    winning_tile: Tile,
) -> Hand:
    hand = Hand(parse_tiles(hand_str))
    engine._hands[winner] = hand
    engine._last_discarded_tile = winning_tile
    engine._last_discarded_player = discarder
    engine._current_player = winner
    engine._last_drawn_tile = None
    engine._is_first_turn_after_deal = False
    return hand


def set_tsumo_context(
    engine: RuleEngine,
    player: int,
    hand_str: str,
    winning_tile: Tile,
) -> Hand:
    hand = Hand(parse_tiles(hand_str))
    engine._hands[player] = hand
    engine._current_player = player
    engine._last_drawn_tile = (player, winning_tile)
    engine._last_discarded_tile = None
    engine._is_first_turn_after_deal = False
    return hand


def set_chankan_context(
    engine: RuleEngine,
    winner: int,
    kan_player: int,
    hand_str: str,
    kan_tile: Tile,
) -> Hand:
    hand = set_ron_context(engine, winner, kan_player, hand_str, kan_tile)
    engine._pending_kan_tile = (kan_player, kan_tile)
    return hand


class RuleEngineTestMixin:
    engine: RuleEngine

    def setup_method(self):
        self.engine = RuleEngine(num_players=4)

    def _has_action(self, player: int, action: GameAction) -> bool:
        return action in self.engine.get_available_actions(player)

    def _init_game(self):
        self.engine = initialized_engine()
