"""Game end condition tests for RuleEngine."""

from pyriichi.game_state import Wind
from pyriichi.rules import GamePhase, RuleEngine


class TestGameEndConditions:
    def setup_method(self):
        self.engine = RuleEngine()
        self.engine.start_game()
        # Reset scores to default
        self.engine.game_state._scores = [25000] * 4

    def test_west_round_extension(self):
        """Test west_round_extension: South 4 ends with no one reaching 30000, enter west round"""
        # Set to South 4
        self.engine.game_state.set_round(Wind.SOUTH, 4)
        self.engine.game_state.set_dealer(3)  # Player 3 is dealer

        # Set scores all below 30000
        self.engine.game_state._scores = [25000, 25000, 25000, 25000]

        # Ensure west_round_extension enabled
        self.engine.game_state.ruleset.west_round_extension = True
        self.engine.game_state.ruleset.return_score = 30000

        # Simulate non-dealer win (dealer loses), trigger next_round
        # Directly call next_round to test GameState logic
        has_next = self.engine.game_state.next_round()

        assert has_next is True
        assert self.engine.game_state.round_wind == Wind.WEST
        assert self.engine.game_state.round_number == 1

    def test_west_round_sudden_death(self):
        """Test west_round_extension end check: Someone reaches 30000 in west round, game ends"""
        # Set to West 1
        self.engine.game_state.set_round(Wind.WEST, 1)

        # Set someone over 30000
        self.engine.game_state._scores = [31000, 20000, 20000, 29000]

        self.engine.game_state.ruleset.return_score = 30000

        # Call next_round
        has_next = self.engine.game_state.next_round()

        assert has_next is False

    def test_no_west_round_if_score_reached(self):
        """Test No west round if score reached: South 4 ends with someone reaching 30000, game ends"""
        self.engine.game_state.set_round(Wind.SOUTH, 4)
        self.engine.game_state._scores = [31000, 20000, 20000, 29000]

        has_next = self.engine.game_state.next_round()

        assert has_next is False

    def test_agari_yame(self):
        """Test agari_yame: south 4 dealer wins and is top, game ends"""
        self.engine.game_state.set_round(Wind.SOUTH, 4)
        self.engine.game_state.set_dealer(0)  # Assume Player 0 is dealer

        # Set Player 0 as Top and over 30000 (Usually agari_yame just requires Top? Need to confirm rules)
        # Standard rule: Just need to be Top to end.
        self.engine.game_state._scores = [35000, 20000, 20000, 25000]

        self.engine.game_state.ruleset.agari_yame = True

        # Simulate dealer win
        winners = [0]
        self.engine.end_round(winners)

        assert self.engine._phase == GamePhase.ENDED

    def test_agari_yame_continuation(self):
        """Test agari_yame continuation: south 4 dealer wins but not top, game continues (renchan)"""
        self.engine.game_state.set_round(Wind.SOUTH, 4)
        self.engine.game_state.set_dealer(0)

        # Set Player 0 not Top
        self.engine.game_state._scores = [30000, 35000, 20000, 15000]

        self.engine.game_state.ruleset.agari_yame = True

        # Simulate dealer win
        winners = [0]
        self.engine.end_round(winners)

        assert self.engine._phase != GamePhase.ENDED
        # Should renchan
        assert self.engine.game_state.round_wind == Wind.SOUTH
        assert self.engine.game_state.round_number == 4
        assert self.engine.game_state.honba == 1
