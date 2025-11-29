import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pyriichi.player import RandomPlayer
from pyriichi.rules import GameAction, GamePhase, RuleEngine
from pyriichi.utils import format_tiles


def main():
    print("=== PyRiichi Basic Usage Example (Normal Game Flow) ===\n")

    # 1. Initialize Engine and Players
    engine = RuleEngine(num_players=4)
    players = [RandomPlayer(f"Player {i}") for i in range(4)]

    # 2. Start Game and Round
    engine.start_game()
    engine.start_round()
    engine.deal()

    print("Game Started. Dealing tiles...")
    for i in range(4):
        hand = engine.get_hand(i)
        print(f"Player {i} Hand: {format_tiles(hand.tiles)}")
    print("-" * 40)

    # 3. Game Loop
    turn_count = 0
    max_turns = 100  # Limit turns to prevent infinite loops in this example

    while engine.get_phase() == GamePhase.PLAYING and turn_count < max_turns:
        # Check for waiting actions (Unified Turn & Interrupts)
        waiting_map = engine.waiting_for_actions
        if waiting_map:
            # Iterate over a copy of keys because execute_action modifies the map
            waiting_pids = list(waiting_map.keys())
            for pid in waiting_pids:
                if engine.get_phase() != GamePhase.PLAYING:
                    break

                player = players[pid]
                available_actions = engine.get_available_actions(pid)

                # Determine if it's an interrupt or normal turn for logging
                is_turn = (
                    pid == engine.get_current_player()
                    and GameAction.DISCARD in available_actions
                )
                if is_turn:
                    print(f"\n--- Turn {turn_count} (Player {pid}) ---")
                else:
                    print(f"\n--- Interrupt Opportunity (Player {pid}) ---")

                print(f"Player {pid} waiting actions: {available_actions}")

                # Decide action
                action, tile = player.decide_action(
                    engine.game_state,
                    pid,
                    engine.get_hand(pid),
                    available_actions,
                )

                print(
                    f"Player {pid} responds with {action.name}"
                    + (f" on {tile}" if tile else "")
                )

                try:
                    result = engine.execute_action(pid, action, tile)
                    if not result.success:
                        print(f"Action failed! {result}")
                        break

                    # If resolution happened and phase changed or win, break inner loop
                    if not engine.waiting_for_actions:
                        break
                except Exception as e:
                    print(f"Error executing action for player {pid}: {e}")
                    break

            # Increment turn count if it was a turn action (heuristic)
            # Actually turn count is managed by engine, we just track loop iterations
            turn_count += 1
            continue
        else:
            # Should not happen in unified flow unless transition
            print("No waiting actions. Checking engine state...")
            if engine.get_phase() != GamePhase.PLAYING:
                break
            # If still playing but no actions, maybe just continue?
            continue

    # 4. Game End Results
    print("\n=== Game End ===")
    print(f"Final Phase: {engine.get_phase()}")
    if engine.get_phase() == GamePhase.WINNING:
        print("Winners:", engine._winning_players)  # Or access from last result
        print("Scores:", engine.game_state.scores)
    elif engine.get_phase() == GamePhase.RYUUKYOKU:
        print("Draw (Ryuukyoku)")
        print("Scores:", engine.game_state.scores)
    else:
        print("Game ended (limit reached or other reason)")


if __name__ == "__main__":
    main()
