import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pyriichi.rules import RuleEngine, GameAction, GamePhase
from pyriichi.player import RandomPlayer, SimplePlayer

def main():
    print("=== PyRiichi AI Game Demo ===")

    # Initialize Engine
    engine = RuleEngine()
    engine.start_game()
    engine.start_round()
    engine.deal()

    # Initialize Players
    players = [
        SimplePlayer("Player 1 (East)"),
        SimplePlayer("Player 2 (South)"),
        SimplePlayer("Player 3 (West)"),
        SimplePlayer("Player 4 (North)")
    ]

    print("Game Started!")

    turn_count = 0
    max_turns = 1000 # Safety limit

    while engine.get_phase() != GamePhase.ENDED and turn_count < max_turns:
        current_player_idx = engine.get_current_player()
        player = players[current_player_idx]

        # Get available actions
        available_actions = engine.get_available_actions(current_player_idx)

        # AI decides action
        # Note: We need to pass the hand object.
        # In a real game, we might want to pass a copy or a view to prevent cheating,
        # but for now we pass the direct reference.
        hand = engine.get_hand(current_player_idx)
        game_state = engine.game_state

        action, tile = player.decide_action(game_state, current_player_idx, hand, available_actions)

        print(f"Turn {turn_count}: {player.name} performs {action.name} {tile if tile else ''}")

        # Execute action
        result = engine.execute_action(current_player_idx, action, tile)

        # Check result (e.g., if someone won or ryuukyoku)
        if result.winners or result.ryuukyoku:
            if result.winners:
                print(f"WINNER! Players: {result.winners}")
            else:
                print(f"RYUUKYOKU! Type: {result.ryuukyoku.ryuukyoku_type}")

            # End round
            engine.end_round(result.winners)

            # Check if game ended
            if engine.get_phase() == GamePhase.ENDED:
                break

            # Start next round
            print(f"Starting Next Round: {engine.game_state.round_wind.name} {engine.game_state.round_number}")
            engine.start_round()
            engine.deal()

        turn_count += 1

    print(f"Game Ended. Phase: {engine.get_phase()}")
    print("Final Scores:")
    for i, p in enumerate(players):
        print(f"{p.name}: {engine.game_state.scores[i]}")

if __name__ == "__main__":
    main()
