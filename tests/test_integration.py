"""Deterministic integration smoke tests."""

from pyriichi import GameAction, GamePhase, Hand, RuleEngine, Suit, Tile, Wind, parse_tiles
from pyriichi.hand import MeldType
from pyriichi.rules import RyuukyokuType
from pyriichi.tiles import TileSet
from tests.helpers import no_response_hand


def _initialized_engine():
    engine = RuleEngine(num_players=4)
    engine.start_game()
    engine.start_round()
    engine.deal()
    return engine


def _pass_interrupts(engine):
    while True:
        pass_players = [
            player
            for player, actions in list(engine.waiting_for_actions.items())
            if GameAction.PASS in actions
        ]
        if not pass_players:
            return
        engine.execute_action(pass_players[0], GameAction.PASS)


class TestCompleteGameFlow:
    def test_deal_and_discard_keeps_round_playing(self):
        engine = RuleEngine(num_players=4)

        engine.start_game()
        engine.start_round()
        assert engine.get_phase() == GamePhase.DEALING

        hands = engine.deal()
        assert len(hands) == 4
        assert len(hands[0]) == 14
        for player in range(1, 4):
            assert len(hands[player]) == 13
        assert engine.get_phase() == GamePhase.PLAYING

        engine._hands[0] = Hand(parse_tiles("123456789m12344p"))
        for player in range(1, 4):
            engine._hands[player] = no_response_hand()

        result = engine.execute_action(0, GameAction.DISCARD, tile=Tile(Suit.PINZU, 4))

        assert result.success
        assert engine.get_hand(0).discards[-1] == Tile(Suit.PINZU, 4)
        assert engine.get_phase() == GamePhase.PLAYING

    def test_discard_call_flow_creates_meld(self):
        engine = _initialized_engine()
        discard_tile = Tile(Suit.PINZU, 3)
        engine._hands[0] = Hand(parse_tiles("123456789m12344p"))
        engine._hands[0].add_tile(discard_tile)
        engine._hands[1] = Hand(parse_tiles("12p123456789m11s"))
        engine._hands[2] = no_response_hand()
        engine._hands[3] = no_response_hand()

        engine.execute_action(0, GameAction.DISCARD, tile=discard_tile)
        sequence = next(
            sequence
            for sequence in engine.get_available_chi_sequences(1)
            if sorted(tile.rank for tile in sequence) == [1, 2]
        )
        result = engine.execute_action(1, GameAction.CHI, sequence=sequence)
        _pass_interrupts(engine)

        assert result.success
        assert engine.get_hand(1).melds[-1].type == MeldType.CHI_MELD
        assert engine.get_current_player() == 1


class TestDrawScenarios:
    def test_declare_kyuushu_kyuuhai_flow(self):
        engine = _initialized_engine()
        engine._hands[0] = Hand(parse_tiles("19m19p19s1234567z1m"))
        engine._current_player = 0
        engine._is_first_turn_after_deal = True
        engine._melds = [[] for _ in range(4)]
        engine._waiting_for_actions[0] = engine._calculate_turn_actions(0)

        actions = engine.get_available_actions(0)
        assert GameAction.DECLARE_KYUUSHU_KYUUHAI in actions

        result = engine.execute_action(0, GameAction.DECLARE_KYUUSHU_KYUUHAI)

        assert result.ryuukyoku is not None
        assert result.ryuukyoku.ryuukyoku is True
        assert result.ryuukyoku.ryuukyoku_type == RyuukyokuType.KYUUSHU_KYUUHAI
        assert result.ryuukyoku.kyuushu_kyuuhai_player == 0
        assert engine.get_phase() == GamePhase.RYUUKYOKU


class TestMultiModuleIntegration:
    def test_tileset_deal_shape_matches_engine_deal_shape(self):
        tile_set = TileSet()
        tile_set.shuffle()

        hands = tile_set.deal()
        assert len(hands) == 4
        assert len(hands[0]) == 14
        for player in range(1, 4):
            assert len(hands[player]) == 13

        engine = _initialized_engine()
        assert len(engine.get_hand(0).tiles) == 14
        for player in range(1, 4):
            assert len(engine.get_hand(player).tiles) == 13

    def test_meld_updates_hand_state(self):
        hand = Hand(parse_tiles("123m456p789s111z"))

        meld = hand.pon(Tile(Suit.HONORS, 1))

        assert len(hand.melds) == 1
        assert meld.type == MeldType.PON_MELD
        assert not hand.is_concealed
        assert len(hand.tiles) == 10


class TestRealWorldScenarios:
    def test_game_state_transitions(self):
        engine = RuleEngine(num_players=4)

        engine.start_game()
        assert engine.get_phase() == GamePhase.INIT

        engine.start_round()
        assert engine.get_phase() == GamePhase.DEALING

        engine.deal()
        assert engine.get_phase() == GamePhase.PLAYING
        assert engine.game_state.dealer == 0
        assert engine.game_state.round_number == 1
        assert engine.game_state.round_wind == Wind.EAST
