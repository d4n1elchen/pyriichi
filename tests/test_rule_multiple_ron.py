"""Multiple ron decision tests for RuleEngine."""

from pyriichi.rules import GameAction
from pyriichi.tiles import Suit, Tile
from pyriichi.utils import parse_tiles
from tests.helpers import RuleEngineTestMixin


class TestMultipleRon(RuleEngineTestMixin):
    def test_multiple_ron_decision(self):
        """Test multiple ron decisions (One ron, One Pass)"""
        self._init_game()

        # Enable double_ron
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True

        # Set Player 1 tenpai (machi 5p)
        # 123m 456s 789p 11z + 46p (machi 5p for 456p)
        self.engine.get_hand(1)._tiles = parse_tiles("123m456s789p11z46p")
        self.engine.get_hand(1)._melds = []

        # Set Player 2 tenpai (machi 5p)
        # 123m 456s 789p 22z + 46p (machi 5p for 456p)
        self.engine.get_hand(2)._tiles = parse_tiles("123m456s789p22z46p")
        self.engine.get_hand(2)._melds = []

        # Player 0 discards 5p
        discard_tile = Tile(Suit.PINZU, 5)
        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # Check interrupts
        interrupts = self.engine._check_interrupts(discard_tile, discarded_player=0)

        # Ensure Player 1 and Player 2 can both ron
        assert 1 in interrupts
        assert GameAction.RON in interrupts[1]
        assert 2 in interrupts
        assert GameAction.RON in interrupts[2]

        # Set waiting for actions
        self.engine._waiting_for_actions = interrupts
        self.engine._incoming_actions = {}
        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # Player 1 chooses RON
        self.engine.execute_action(1, GameAction.RON)

        # Player 2 chooses PASS
        result = self.engine.execute_action(2, GameAction.PASS)

        # Verify result
        # Only Player 1 should win
        assert result.success
        assert len(result.winners) == 1
        assert result.winners[0] == 1

        # Verify Player 2 furiten (Missed ron)
        assert self.engine._furiten_temp[2]
