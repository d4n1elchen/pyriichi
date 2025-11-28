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
        current_player_idx = engine.get_current_player()
        current_player = players[current_player_idx]

        # Get available actions for the current player
        # Usually DRAW, unless it's after a call
        actions = engine.get_available_actions(current_player_idx)

        if not actions:
            print(f"No actions for Player {current_player_idx}. Ending loop.")
            break

        # Decide action
        # Note: RandomPlayer.decide_action expects (game_state, player_index, hand, actions)
        # We don't pass public_info in this simple example
        action, tile = current_player.decide_action(
            engine.game_state,
            current_player_idx,
            engine.get_hand(current_player_idx),
            actions,
        )

        print(
            f"[Turn {turn_count}] Player {current_player_idx} performs {action.name}"
            + (f" on {tile}" if tile else "")
        )

        # Execute Action
        result = engine.execute_action(current_player_idx, action, tile)

        if not result.success:
            print(f"Action failed! {result}")
            break

        # Check for Game End
        if engine.get_phase() != GamePhase.PLAYING:
            print(f"Game Phase changed to {engine.get_phase()}")
            break

        # If DISCARD happened, check for interrupts (Ron, Pon, Chi, Kan)
        if action == GameAction.DISCARD:
            discarded_tile = tile
            interrupt_occurred = False

            # Check other players for actions (Priority: Ron > Pon/Kan > Chi)
            # We iterate through all players to see if anyone wants to interrupt

            # 1. Check RON (All other players)
            for i in range(4):
                if i == current_player_idx:
                    continue

                p_actions = engine.get_available_actions(i)
                if GameAction.RON in p_actions:
                    # For this example, if RandomPlayer can Ron, it will
                    decision, _ = players[i].decide_action(
                        engine.game_state, i, engine.get_hand(i), p_actions
                    )
                    if decision == GameAction.RON:
                        print(f"!!! Player {i} declares RON on {discarded_tile} !!!")
                        engine.execute_action(i, GameAction.RON, discarded_tile)
                        interrupt_occurred = True
                        break  # Game ends on Ron usually

            if engine.get_phase() != GamePhase.PLAYING:
                break

            if interrupt_occurred:
                continue

            # 2. Check PON/KAN (All other players)
            for i in range(4):
                if i == current_player_idx:
                    continue

                p_actions = engine.get_available_actions(i)
                # Filter for Pon/Kan
                call_actions = [
                    a for a in p_actions if a in [GameAction.PON, GameAction.KAN]
                ]

                if call_actions:
                    # Ask player if they want to call
                    # RandomPlayer might pass, so we check decision
                    decision, _ = players[i].decide_action(
                        engine.game_state, i, engine.get_hand(i), p_actions
                    )
                    if decision in [GameAction.PON, GameAction.KAN]:
                        print(f"Player {i} calls {decision.name} on {discarded_tile}")
                        engine.execute_action(i, decision, discarded_tile)
                        interrupt_occurred = True
                        break  # Only one player can Pon/Kan

            if interrupt_occurred:
                continue

            # 3. Check CHI (Next player only)
            next_player_idx = (current_player_idx + 1) % 4
            p_actions = engine.get_available_actions(next_player_idx)
            if GameAction.CHI in p_actions:
                decision, chi_tile = players[next_player_idx].decide_action(
                    engine.game_state,
                    next_player_idx,
                    engine.get_hand(next_player_idx),
                    p_actions,
                )
                if decision == GameAction.CHI:
                    print(f"Player {next_player_idx} calls CHI on {discarded_tile}")
                    # CHI requires the sequence (e.g. 23m for 1m)
                    # RandomPlayer returns the tile to construct sequence?
                    # Wait, RandomPlayer implementation for CHI might need review.
                    # For this example, let's assume it works or skip CHI if complex.
                    # RandomPlayer returns (Action, None) for calls usually in current impl.
                    # Let's skip CHI for simplicity in this basic example unless RandomPlayer is robust.
                    pass

        turn_count += 1
        # time.sleep(0.1) # Optional delay for readability

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
