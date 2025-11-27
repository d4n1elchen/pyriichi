import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pyriichi.rules import RuleEngine, GameAction, GamePhase
from pyriichi.player import RandomPlayer, SimplePlayer, DefensivePlayer, PublicInfo

def main():
    print("=== PyRiichi AI Game Demo ===")

    # Initialize Engine
    engine = RuleEngine()
    engine.start_game()
    engine.start_round()
    engine.deal()

    # Initialize Players
    # Use DefensivePlayer for all players to test defense logic
    players = [
        DefensivePlayer("Player 1 (East)"),
        DefensivePlayer("Player 2 (South)"),
        DefensivePlayer("Player 3 (West)"),
        DefensivePlayer("Player 4 (North)")
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
        hand = engine.get_hand(current_player_idx)
        game_state = engine.game_state

        # Construct PublicInfo
        riichi_players = [i for i in range(4) if engine.get_hand(i).is_riichi]

        public_info = PublicInfo(
            turn_number=engine._turn_count,
            dora_indicators=engine._tile_set.get_dora_indicators() if engine._tile_set else [],
            discards={i: engine.get_hand(i)._discards for i in range(4)},
            melds={i: engine.get_hand(i).melds for i in range(4)},
            riichi_players=riichi_players,
            scores=engine.game_state.scores
        )

        action, tile = player.decide_action(game_state, current_player_idx, hand, available_actions, public_info)

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
