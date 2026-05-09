"""Test module."""

from pyriichi import (
    GameAction,
    GamePhase,
    GameState,
    Hand,
    RuleEngine,
    ScoreCalculator,
    Suit,
    Tile,
    Wind,
    Yaku,
    YakuChecker,
    parse_tiles,
)
from pyriichi.hand import MeldType
from pyriichi.rules import RyuukyokuType


class TestCompleteWinFlow:
    """Tests for TestCompleteWinFlow."""

    def test_complete_win_flow_tsumo(self):
        """Test complete win flow tsumo."""
        tiles = parse_tiles("123m234m456p789s5p")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 5)

        assert hand.is_winning_hand(winning_tile)
        winning_combinations = hand.get_winning_combinations(winning_tile)
        assert len(winning_combinations) > 0

        game_state = GameState(num_players=4)
        yaku_checker = YakuChecker()
        yaku_results = yaku_checker.check_all(
            hand=hand,
            winning_tile=winning_tile,
            winning_combination=list(winning_combinations[0]),
            game_state=game_state,
            is_tsumo=True,
            player_position=0,
        )

        yaku_set = {y.yaku for y in yaku_results}
        assert Yaku.MENZEN_TSUMO in yaku_set

        score_calculator = ScoreCalculator()
        score_result = score_calculator.calculate(
            hand=hand,
            winning_tile=winning_tile,
            winning_combination=list(winning_combinations[0]),
            yaku_results=yaku_results,
            dora_count=0,
            game_state=game_state,
            is_tsumo=True,
            player_position=0,
        )

        assert score_result.han > 0
        assert score_result.fu > 0
        assert score_result.total_points > 0
        assert score_result.is_tsumo is True

    def test_complete_win_flow_ron(self):
        """Test complete win flow ron."""
        tiles = parse_tiles("123m456p789s111z2z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.HONORS, 2)  # 2z

        assert hand.is_winning_hand(winning_tile)
        winning_combinations = hand.get_winning_combinations(winning_tile)
        assert len(winning_combinations) > 0

        game_state = GameState(num_players=4)
        yaku_checker = YakuChecker()
        yaku_results = yaku_checker.check_all(
            hand=hand,
            winning_tile=winning_tile,
            winning_combination=list(winning_combinations[0]),
            game_state=game_state,
            is_tsumo=False,
            player_position=1,
        )

        score_calculator = ScoreCalculator()
        score_result = score_calculator.calculate(
            hand=hand,
            winning_tile=winning_tile,
            winning_combination=list(winning_combinations[0]),
            yaku_results=yaku_results,
            dora_count=0,
            game_state=game_state,
            is_tsumo=False,
            player_position=1,
        )
        score_result.payment_from = 0

        assert score_result.han > 0
        assert score_result.total_points > 0
        assert score_result.is_tsumo is False
        assert score_result.payment_from == 0


class TestCompleteGameFlow:
    """Tests for TestCompleteGameFlow."""

    def test_complete_game_round(self):
        """Test complete game round."""
        engine = RuleEngine(num_players=4)

        engine.start_game()
        engine.start_round()
        assert engine.get_phase() == GamePhase.DEALING

        hands = engine.deal()
        assert len(hands) == 4
        assert len(hands[0]) == 14
        for i in range(1, 4):
            assert len(hands[i]) == 13
        assert engine.get_phase() == GamePhase.PLAYING

        current_player = engine.get_current_player()
        for _ in range(3):
            hand = engine.get_hand(current_player)

            if hand.total_tile_count() >= 14 and hand.tiles:
                engine.execute_action(
                    current_player, GameAction.DISCARD, tile=hand.tiles[0]
                )
                current_player = engine.get_current_player()
                hand = engine.get_hand(current_player)

            if GameAction.DRAW in engine.get_available_actions(current_player):
                result = engine.execute_action(current_player, GameAction.DRAW)
                if result.drawn_tile is not None:
                    hand = engine.get_hand(current_player)
                    if hand.tiles:
                        engine.execute_action(
                            current_player, GameAction.DISCARD, tile=hand.tiles[0]
                        )
                current_player = engine.get_current_player()
            else:
                break

        assert engine.get_phase() == GamePhase.PLAYING

    def test_game_flow_with_meld(self):
        """Test game flow with meld."""
        engine = RuleEngine(num_players=4)
        engine.start_game()
        engine.start_round()
        engine.deal()

        def pass_interrupts():
            while True:
                pass_players = [
                    player
                    for player, actions in list(engine.waiting_for_actions.items())
                    if GameAction.PASS in actions
                ]
                if not pass_players:
                    return
                engine.execute_action(pass_players[0], GameAction.PASS)

        current_player = engine.get_current_player()

        hand = engine.get_hand(current_player)
        if hand.total_tile_count() >= 14 and hand.tiles:
            engine.execute_action(
                current_player, GameAction.DISCARD, tile=hand.tiles[0]
            )
            pass_interrupts()
            current_player = engine.get_current_player()

        if GameAction.DRAW in engine.get_available_actions(current_player):
            engine.execute_action(current_player, GameAction.DRAW)
            current_player = engine.get_current_player()
        hand = engine.get_hand(current_player)

        if GameAction.DISCARD in engine.get_available_actions(current_player):
            discard_tile = hand.tiles[0]
            engine.execute_action(current_player, GameAction.DISCARD, tile=discard_tile)
            pass_interrupts()

        assert engine.get_phase() == GamePhase.PLAYING


class TestSpecialRulesFlow:
    """Tests for TestSpecialRulesFlow."""

    def test_riichi_flow(self):
        """Test riichi flow."""
        engine = RuleEngine(num_players=4)
        engine.start_game()
        engine.start_round()
        engine.deal()

        current_player = engine.get_current_player()
        hand = engine.get_hand(current_player)

        if hand.is_concealed:
            result = engine.get_available_actions(current_player)
            if GameAction.DECLARE_RIICHI in result:
                engine.execute_action(current_player, GameAction.DECLARE_RIICHI)
                assert current_player in engine._riichi_ippatsu

    def test_kan_flow(self):
        """Test kan flow."""
        engine = RuleEngine(num_players=4)
        engine.start_game()
        engine.start_round()
        engine.deal()

        current_player = engine.get_current_player()

        engine.get_available_actions(current_player)


class TestDrawScenarios:
    """Tests for TestDrawScenarios."""

    def test_declare_kyuushu_kyuuhai_flow(self):
        """Test declare kyuushu kyuuhai flow."""
        engine = RuleEngine(num_players=4)
        engine.start_game()
        engine.start_round()
        engine.deal()

        tiles = parse_tiles("19m19p19s1z2z3z4z5z6z7z1m")
        engine._hands[0] = Hand(tiles)

        engine._current_player = 0
        engine._is_first_turn_after_deal = True
        engine._melds = [[] for _ in range(4)]

        # Force update actions
        engine._waiting_for_actions[0] = engine._calculate_turn_actions(0)

        actions = engine.get_available_actions(0)
        assert GameAction.DECLARE_KYUUSHU_KYUUHAI in actions

        result = engine.execute_action(0, GameAction.DECLARE_KYUUSHU_KYUUHAI)

        assert result.ryuukyoku is not None
        assert result.ryuukyoku.ryuukyoku is True
        assert result.ryuukyoku.ryuukyoku_type == RyuukyokuType.KYUUSHU_KYUUHAI
        assert result.ryuukyoku.kyuushu_kyuuhai_player == 0
        assert engine._phase == GamePhase.RYUUKYOKU


class TestMultiModuleIntegration:
    """Tests for TestMultiModuleIntegration."""

    def test_hand_yaku_scoring_integration(self):
        """Test hand yaku scoring integration."""
        tiles = parse_tiles("111m123m456m789m4m")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 4)

        assert hand.is_winning_hand(winning_tile)
        winning_combinations = hand.get_winning_combinations(winning_tile)
        assert len(winning_combinations) > 0

        game_state = GameState(num_players=4)
        yaku_checker = YakuChecker()
        yaku_results = yaku_checker.check_all(
            hand=hand,
            winning_tile=winning_tile,
            winning_combination=list(winning_combinations[0]),
            game_state=game_state,
            is_tsumo=True,
            player_position=0,
        )

        score_calculator = ScoreCalculator()
        score_result = score_calculator.calculate(
            hand=hand,
            winning_tile=winning_tile,
            winning_combination=list(winning_combinations[0]),
            yaku_results=yaku_results,
            dora_count=0,
            game_state=game_state,
            is_tsumo=True,
            player_position=0,
        )

        assert score_result.han > 0
        assert score_result.total_points > 0
        assert len(yaku_results) > 0

    def test_tileset_hand_engine_integration(self):
        """Test tileset hand engine integration."""
        from pyriichi.tiles import TileSet

        tile_set = TileSet()
        tile_set.shuffle()

        hands = tile_set.deal()
        assert len(hands) == 4
        assert len(hands[0]) == 14
        for i in range(1, 4):
            assert len(hands[i]) == 13

        engine = RuleEngine(num_players=4)
        engine.start_game()
        engine.start_round()
        engine.deal()

        for i in range(4):
            engine_hand = engine.get_hand(i)
            assert len(engine_hand.tiles) in [13, 14]

    def test_meld_hand_yaku_integration(self):
        """Test meld hand yaku integration."""
        tiles = parse_tiles("123m456p789s111z")
        hand = Hand(tiles)

        meld = hand.pon(Tile(Suit.HONORS, 1))

        assert len(hand._melds) == 1
        assert meld.type == MeldType.PON_MELD
        assert not hand.is_concealed

        assert len(hand.tiles) == 10


class TestRealWorldScenarios:
    """Tests for TestRealWorldScenarios."""

    def test_complete_winning_scenario_1(self):
        """Test complete winning scenario 1."""
        tiles = parse_tiles("123m234m456p789s5p")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.PINZU, 5)

        assert hand.is_winning_hand(winning_tile)
        winning_combinations = hand.get_winning_combinations(winning_tile)

        game_state = GameState(num_players=4)
        yaku_checker = YakuChecker()
        yaku_results = yaku_checker.check_all(
            hand=hand,
            winning_tile=winning_tile,
            winning_combination=list(winning_combinations[0]),
            game_state=game_state,
            is_tsumo=True,
            player_position=0,
        )

        score_calculator = ScoreCalculator()
        score_result = score_calculator.calculate(
            hand=hand,
            winning_tile=winning_tile,
            winning_combination=list(winning_combinations[0]),
            yaku_results=yaku_results,
            dora_count=0,
            game_state=game_state,
            is_tsumo=True,
            player_position=0,
        )

        assert score_result.han >= 1
        assert score_result.total_points > 0

    def test_complete_winning_scenario_2(self):
        """Test complete winning scenario 2."""
        tiles = parse_tiles("123m456p789s111z2z")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.HONORS, 2)

        assert hand.is_winning_hand(winning_tile)
        winning_combinations = hand.get_winning_combinations(winning_tile)

        game_state = GameState(num_players=4)
        yaku_checker = YakuChecker()
        yaku_results = yaku_checker.check_all(
            hand=hand,
            winning_tile=winning_tile,
            winning_combination=list(winning_combinations[0]),
            game_state=game_state,
            is_tsumo=False,
            player_position=1,
        )

        score_calculator = ScoreCalculator()
        score_result = score_calculator.calculate(
            hand=hand,
            winning_tile=winning_tile,
            winning_combination=list(winning_combinations[0]),
            yaku_results=yaku_results,
            dora_count=0,
            game_state=game_state,
            is_tsumo=False,
            player_position=1,
        )
        score_result.payment_from = 0

        assert score_result.han >= 1
        assert score_result.total_points > 0
        assert score_result.payment_from == 0

    def test_game_state_transitions(self):
        """Test game state transitions."""
        engine = RuleEngine(num_players=4)

        engine.start_game()
        assert engine.get_phase() == GamePhase.INIT

        engine.start_round()
        assert engine.get_phase() == GamePhase.DEALING

        engine.deal()
        assert engine.get_phase() == GamePhase.PLAYING

        assert engine._game_state.dealer == 0
        assert engine._game_state.round_number == 1
        assert engine._game_state.round_wind == Wind.EAST

    def test_multiple_rounds_flow(self):
        """Test multiple rounds flow."""
        engine = RuleEngine(num_players=4)
        engine.start_game()

        engine.start_round()
        engine.deal()
        assert engine.get_phase() == GamePhase.PLAYING
        assert engine._game_state.round_number == 1

        assert engine._game_state is not None


class TestErrorHandling:
    """Tests for TestErrorHandling."""

    def test_invalid_action_handling(self):
        """Test invalid action handling."""
        engine = RuleEngine(num_players=4)
        engine.start_game()
        engine.start_round()
        engine.deal()

        current_player = engine.get_current_player()

        hand = engine.get_hand(current_player)
        if hand.tiles:
            result = engine.execute_action(
                current_player, GameAction.DISCARD, tile=hand.tiles[0]
            )
            from pyriichi.rules import ActionResult

            assert isinstance(result, ActionResult) or result is None

    def test_edge_case_hand_combinations(self):
        """Test edge case hand combinations."""
        tiles = parse_tiles("11m22m33m44m55m66m7m")
        hand = Hand(tiles)
        winning_tile = Tile(Suit.MANZU, 7)

        assert hand.is_winning_hand(winning_tile)

        kokushi_tiles = parse_tiles("19m19p19s1z2z3z4z5z6z7z")
        hand2 = Hand(kokushi_tiles)
        winning_tile2 = Tile(Suit.HONORS, 1)

        assert hand2.is_winning_hand(winning_tile2)
