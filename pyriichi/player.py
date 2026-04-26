import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from pyriichi.hand import Hand, Meld
from pyriichi.rules import GameAction, GameState
from pyriichi.tiles import Tile


@dataclass
class PublicInfo:
    """
    Public Game Information (Visible Game Information).

    Contains information visible to all players, used for AI decision making.
    """

    turn_number: int
    dora_indicators: List[Tile]
    discards: Dict[int, List[Tile]]  # Discards of each player
    melds: Dict[int, List[Meld]]  # Melds of each player
    riichi_players: List[int]  # List of players who declared Riichi
    scores: List[int]  # Player scores


class BasePlayer(ABC):
    """
    Player Base Class (Abstract Base Class for Players).

    Defines the basic interface for players. All concrete player classes should inherit from this class.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def decide_action(
        self,
        game_state: GameState,
        player_index: int,
        hand: Hand,
        available_actions: List[GameAction],
        public_info: Optional[PublicInfo] = None,
    ) -> Tuple[GameAction, Optional[Tile]]:
        """
        Decide the next action.

        Args:
            game_state (GameState): Current game state.
            player_index (int): Player index (0-3).
            hand (Hand): Player hand.
            available_actions (List[GameAction]): List of available actions.
            public_info (Optional[PublicInfo]): Public game information (Discards, Melds, etc.).

        Returns:
            Tuple[GameAction, Optional[Tile]]: (Selected action, Related tile).
                - If action is DISCARD, Tile is the tile to discard.
                - If action is CHI/PON/KAN, Tile is the related tile (usually target tile).
                - For other actions, Tile is usually None.
        """
        pass


class RandomPlayer(BasePlayer):
    """
    Random Action AI Player.

    Strategy is completely random, only following rules when necessary (e.g., must discard drawn tile after Riichi).
    """

    def decide_action(
        self,
        game_state: GameState,
        player_index: int,
        hand: Hand,
        available_actions: List[GameAction],
        public_info: Optional[PublicInfo] = None,
    ) -> Tuple[GameAction, Optional[Tile]]:
        """
        Decide the next action (Random).

        Args:
            game_state (GameState): Current game state.
            player_index (int): Player index.
            hand (Hand): Player hand.
            available_actions (List[GameAction]): List of available actions.

        Returns:
            Tuple[GameAction, Optional[Tile]]: (Selected action, Related tile).
        """

        if not available_actions:
            return GameAction.PASS, None

        # Simple strategy: Prioritize winning, then Riichi, otherwise random

        # If winning is possible, prioritize winning
        if GameAction.RON in available_actions:
            return GameAction.RON, None
        if GameAction.TSUMO in available_actions:
            return GameAction.TSUMO, None

        # Randomly choose an action, filter out PASS (unless only PASS is available)

        # To avoid infinite loops or getting stuck, prioritize DISCARD
        if GameAction.DISCARD in available_actions:
            # Randomly discard a tile

            if hand.is_riichi:
                # After Riichi, must discard the drawn tile
                tile_to_discard = hand.last_drawn_tile
                if tile_to_discard is None:
                    # Should not happen if we just drew a tile, but fallback to last tile just in case
                    tile_to_discard = hand.tiles[-1]
                return GameAction.DISCARD, tile_to_discard

            tile_to_discard = random.choice(hand.tiles)
            return GameAction.DISCARD, tile_to_discard

        # If in response phase, choose randomly, but give PASS slightly higher weight
        action = random.choice(available_actions)

        if action == GameAction.RICHI:
            valid_discards = hand.tenpai_discards
            if valid_discards:
                return GameAction.RICHI, random.choice(valid_discards)
            else:
                # Should not happen if RICHI is in available_actions
                return GameAction.PASS, None

        # If an action requiring parameters is chosen, temporarily return None

        return action, None


class SimplePlayer(BasePlayer):
    """
    Simple Attack AI (Simple Attack AI).

    Strategy:
    1. Prioritize winning (RON/TSUMO).
    2. Prioritize Riichi (RICHI).
    3. Simple discard strategy: Honors -> Terminals -> Simple tiles.
    """

    def decide_action(
        self,
        game_state: GameState,
        player_index: int,
        hand: Hand,
        available_actions: List[GameAction],
        public_info: Optional[PublicInfo] = None,
    ) -> Tuple[GameAction, Optional[Tile]]:
        """
        Decide the next action (Simple Attack Strategy).

        Args:
            game_state (GameState): Current game state.
            player_index (int): Player index.
            hand (Hand): Player hand.
            available_actions (List[GameAction]): List of available actions.

        Returns:
            Tuple[GameAction, Optional[Tile]]: (Selected action, Related tile).
        """

        if not available_actions:
            return GameAction.PASS, None

        # 1. Prioritize winning
        if GameAction.RON in available_actions:
            return GameAction.RON, None
        if GameAction.TSUMO in available_actions:
            return GameAction.TSUMO, None

        # 2. Prioritize Riichi
        if GameAction.RICHI in available_actions:
            valid_discards = hand.tenpai_discards
            if valid_discards:
                # Choose the best discard from valid Riichi discards
                best_riichi_discard = self._choose_best_discard(hand, valid_discards)
                return GameAction.RICHI, best_riichi_discard

        # 3. Handle Discard
        if GameAction.DISCARD in available_actions:
            # If in Riichi, must discard the drawn tile
            if hand.is_riichi:
                tile_to_discard = hand.last_drawn_tile
                if tile_to_discard is None:
                    tile_to_discard = hand.tiles[-1]
                return GameAction.DISCARD, tile_to_discard

            # Simple discard strategy: Honors -> Terminals -> Simple tiles (Isolated tiles first)
            best_discard = self._choose_best_discard(hand)
            return GameAction.DISCARD, best_discard

        # 4. Handle Melds
        if GameAction.PASS in available_actions:
            return GameAction.PASS, None

        return random.choice(available_actions), None

    def _choose_best_discard(
        self, hand: Hand, candidates: Optional[List[Tile]] = None
    ) -> Tile:
        """
        Choose the best discard.

        Args:
            hand (Hand): Hand.
            candidates (Optional[List[Tile]]): List of candidate tiles. If None, choose from hand.

        Returns:
            Tile: Best discard.
        """
        tiles_to_consider = candidates if candidates is not None else hand.tiles

        best_discard = None
        min_score = 1000

        for tile in tiles_to_consider:
            score = 0

            if tile.is_honor:
                score = 10

            elif tile.is_terminal:
                score = 20

            else:
                score = (
                    30 + (5 - abs(tile.rank - 5))
                )  # 5 is highest score (35), 1/9 is 26 (but already captured by terminal)

            # Add randomness
            score += random.randint(0, 5)

            if score < min_score:
                min_score = score
                best_discard = tile

        return best_discard


class DefensivePlayer(SimplePlayer):
    """
    Defensive AI (Defensive AI).

    Strategy:
    1. Default to SimplePlayer's attack strategy.
    2. When an opponent declares Riichi, enter defense mode:
       - Prioritize discarding Riichi player's Genbutsu (Safe Tiles).
       - If no Genbutsu, try discarding Honors or Suji (Currently only Genbutsu implemented).
       - Betaori (Fold): Do not call melds.
    """

    def decide_action(
        self,
        game_state: GameState,
        player_index: int,
        hand: Hand,
        available_actions: List[GameAction],
        public_info: Optional[PublicInfo] = None,
    ) -> Tuple[GameAction, Optional[Tile]]:
        """
        Decide the next action (With defensive logic).
        """
        if not available_actions:
            return GameAction.PASS, None

        # Check if defense is needed
        is_defense_mode = False
        threatening_players = []

        if public_info:
            for i in public_info.riichi_players:
                if i != player_index:
                    is_defense_mode = True
                    threatening_players.append(i)

        # If defense is not needed, use simple strategy
        if not is_defense_mode:
            return super().decide_action(
                game_state, player_index, hand, available_actions, public_info
            )

        # Defense Mode

        # 1. If winning is possible, still win (Chase Riichi / Push, or lucky)
        if GameAction.RON in available_actions:
            return GameAction.RON, None
        if GameAction.TSUMO in available_actions:
            return GameAction.TSUMO, None

        # 2. Betaori (Fold): No Riichi, No Melds
        if GameAction.DISCARD in available_actions:
            # Find safe tile
            safe_tile = self._find_safe_tile(hand, public_info, threatening_players)
            if safe_tile:
                return GameAction.DISCARD, safe_tile

            # If no completely safe tile, fallback to SimplePlayer's discard logic (at least discard Honors/Terminals)
            # But we want it to be more conservative, here temporarily call parent class
            return super().decide_action(
                game_state, player_index, hand, available_actions, public_info
            )

        # Reject all meld requests (PASS)
        if GameAction.PASS in available_actions:
            return GameAction.PASS, None

        return GameAction.PASS, None

    def _find_safe_tile(
        self,
        hand: Hand,
        public_info: Optional[PublicInfo],
        threatening_players: List[int],
    ) -> Optional[Tile]:
        """Find safe tile (Genbutsu) in hand."""
        if not public_info:
            return None

        # Collect Genbutsu of all threatening players

        # Simplified handling: As long as it is Genbutsu of any Riichi player, consider it "relatively" safe
        # Stricter defense should target Common Safe Tiles of all Riichi players
        # But if cannot cover all, prioritize defending against Shimocha/Toimen/Kamicha? Or random?
        # Here we take intersection (Safe against all), if none then take union (Safe against at least one)

        common_safe_tiles = None

        for player_idx in threatening_players:
            discards = public_info.discards.get(player_idx, [])
            player_safe_tiles = set(discards)

            if common_safe_tiles is None:
                common_safe_tiles = player_safe_tiles
            else:
                common_safe_tiles = common_safe_tiles.intersection(player_safe_tiles)

        # Check if there are common safe tiles in hand
        if common_safe_tiles:
            for tile in hand.tiles:
                if tile in common_safe_tiles:
                    return tile

        # If no common safe tiles, try to find safe tile against a specific Riichi player (Avoid dealing into the most dangerous one?)
        # Temporarily choose a safe tile against someone randomly
        all_safe_tiles = set()
        for player_idx in threatening_players:
            all_safe_tiles.update(public_info.discards.get(player_idx, []))

        for tile in hand.tiles:
            if tile in all_safe_tiles:
                return tile

        return None
