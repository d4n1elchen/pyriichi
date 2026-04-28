"""Test module."""

import pytest
from pyriichi.game_state import GameState, Wind


class TestGameState:
    """Tests for TestGameState."""

    def setup_method(self):
        """Set up test fixtures."""
        self.game_state = GameState(num_players=4)

    def test_initial_state(self):
        """Test initial state."""
        assert self.game_state.round_wind == Wind.EAST
        assert self.game_state.round_number == 1
        assert self.game_state.dealer == 0
        assert self.game_state.honba == 0
        assert self.game_state.riichi_sticks == 0
        assert len(self.game_state.scores) == 4
        assert all(score == 25000 for score in self.game_state.scores)

    def test_set_round(self):
        """Test set round."""
        self.game_state.set_round(Wind.SOUTH, 2)
        assert self.game_state.round_wind == Wind.SOUTH
        assert self.game_state.round_number == 2

    def test_set_dealer(self):
        """Test set dealer."""
        self.game_state.set_dealer(2)
        assert self.game_state.dealer == 2

        with pytest.raises(ValueError):
            self.game_state.set_dealer(4)

    def test_add_honba(self):
        """Test add honba."""
        self.game_state.add_honba()
        assert self.game_state.honba == 1

        self.game_state.add_honba(2)
        assert self.game_state.honba == 3

    def test_reset_honba(self):
        """Test reset honba."""
        self.game_state.add_honba(3)
        self.game_state.reset_honba()
        assert self.game_state.honba == 0

    def test_add_riichi_stick(self):
        """Test add Riichi Stick."""
        self.game_state.add_riichi_stick()
        assert self.game_state.riichi_sticks == 1

        self.game_state.add_riichi_stick()
        assert self.game_state.riichi_sticks == 2

    def test_clear_riichi_sticks(self):
        """Test clear Riichi Stick."""
        self.game_state.add_riichi_stick()
        self.game_state.add_riichi_stick()
        self.game_state.add_riichi_stick()
        self.game_state.clear_riichi_sticks()
        assert self.game_state.riichi_sticks == 0

    def test_update_score(self):
        """Test update score."""
        self.game_state.update_score(0, 1000)
        assert self.game_state.scores[0] == 26000

        self.game_state.update_score(0, -500)
        assert self.game_state.scores[0] == 25500

        with pytest.raises(ValueError):
            self.game_state.update_score(4, 1000)

    def test_transfer_points(self):
        """Test transfer points."""
        self.game_state.transfer_points(0, 1, 1000)
        assert self.game_state.scores[0] == 24000
        assert self.game_state.scores[1] == 26000

    def test_next_round(self):
        """Test next round."""
        self.game_state.ruleset.west_round_extension = False

        assert self.game_state.round_wind == Wind.EAST
        assert self.game_state.round_number == 1

        has_next = self.game_state.next_round()
        assert has_next is True
        assert self.game_state.round_wind == Wind.EAST
        assert self.game_state.round_number == 2

        self.game_state.next_round()
        self.game_state.next_round()
        assert self.game_state.round_number == 4

        has_next = self.game_state.next_round()
        assert has_next is True
        assert self.game_state.round_wind == Wind.SOUTH
        assert self.game_state.round_number == 1

        self.game_state.next_round()
        self.game_state.next_round()
        self.game_state.next_round()
        assert self.game_state.round_number == 4

        has_next = self.game_state.next_round()
        assert has_next is False

    def test_next_dealer(self):
        """Test next dealer."""
        assert self.game_state.dealer == 0

        self.game_state.next_dealer(dealer_won=False)
        assert self.game_state.dealer == 1
        assert self.game_state.honba == 0

        self.game_state.next_dealer(dealer_won=True)
        assert self.game_state.dealer == 1
        assert self.game_state.honba == 1

        self.game_state.next_dealer(dealer_won=False)
        assert self.game_state.dealer == 2
        assert self.game_state.honba == 0

        self.game_state.set_dealer(3)
        self.game_state.next_dealer(dealer_won=False)
        assert self.game_state.dealer == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
