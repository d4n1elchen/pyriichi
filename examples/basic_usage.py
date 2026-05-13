import os
import sys

# Allow running this example directly from a source checkout.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pyriichi.player import RandomPlayer
from pyriichi.rules import GamePhase, RuleEngine
from pyriichi.utils import format_tiles


def format_actions(actions):
    return ", ".join(action.value for action in actions)


def main():
    print("=== PyRiichi Basic Usage Example ===\n")

    engine = RuleEngine(num_players=4)
    players = [RandomPlayer(f"Player {i}") for i in range(4)]

    engine.start_game()
    engine.start_round()
    engine.deal()

    print("Game started. Initial hands:")
    for player_index in range(4):
        hand = engine.get_hand(player_index)
        print(f"Player {player_index}: {format_tiles(hand.tiles)}")
    print("-" * 40)

    last_result = None
    max_steps = 100

    for step in range(max_steps):
        if engine.get_phase() != GamePhase.PLAYING:
            break

        waiting_map = engine.waiting_for_actions
        if not waiting_map:
            print("No available action is pending.")
            break

        player_index = next(iter(waiting_map))
        actions = engine.get_available_actions(player_index)
        player = players[player_index]
        hand = engine.get_hand(player_index)

        print(f"\nStep {step + 1}: Player {player_index}")
        print(f"Actions: {format_actions(actions)}")

        action, tile = player.decide_action(
            engine.game_state,
            player_index,
            hand,
            actions,
        )

        print(f"Selected: {action.value}" + (f" {tile}" if tile else ""))
        last_result = engine.execute_action(player_index, action, tile)

        if not last_result.success:
            print("Action failed.")
            break

        if last_result.drawn_tile:
            print(
                f"Player {engine.get_current_player()} drew "
                f"{last_result.drawn_tile}"
            )

        if last_result.discarded:
            print(f"Player {player_index} discarded {tile}")

        if last_result.waiting_for:
            waiting = {
                pid: [action.value for action in actions]
                for pid, actions in last_result.waiting_for.items()
            }
            print(f"Waiting for: {waiting}")

        if last_result.winners:
            print(f"Winners: {last_result.winners}")
            break

        if last_result.ryuukyoku:
            print(f"Ryuukyoku: {last_result.ryuukyoku.ryuukyoku_type.value}")
            break

    print("\n=== Game End ===")
    print(f"Final phase: {engine.get_phase().value}")
    print(f"Scores: {engine.game_state.scores}")

    if last_result and last_result.win_results:
        for player_index, win_result in last_result.win_results.items():
            print(
                f"Player {player_index}: {win_result.han} han, "
                f"{win_result.fu} fu, {win_result.points} points"
            )


if __name__ == "__main__":
    main()
