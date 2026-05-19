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
    riichi_players: List[int]  # List of players who declared riichi
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

    Strategy is completely random, only following rules when necessary (e.g., must discard drawn tile after riichi).
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

        # Simple strategy: Prioritize winning, then riichi, otherwise random

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
                # After riichi, must discard the drawn tile
                tile_to_discard = hand.last_drawn_tile
                if tile_to_discard is None:
                    # Should not happen if we just drew a tile, but fallback to last tile just in case
                    tile_to_discard = hand.tiles[-1]
                return GameAction.DISCARD, tile_to_discard

            tile_to_discard = random.choice(hand.tiles)
            return GameAction.DISCARD, tile_to_discard

        # If in response phase, choose randomly, but give PASS slightly higher weight
        action = random.choice(available_actions)

        if action == GameAction.DECLARE_RIICHI:
            valid_discards = hand.tenpai_discards
            if valid_discards:
                return GameAction.DECLARE_RIICHI, random.choice(valid_discards)
            else:
                # Should not happen if DECLARE_RIICHI is in available_actions
                return GameAction.PASS, None

        # If an action requiring parameters is chosen, temporarily return None

        return action, None


class SimplePlayer(BasePlayer):
    """
    Simple Attack AI (Simple Attack AI).

    Strategy:
    1. Prioritize winning (RON/TSUMO).
    2. Prioritize riichi (DECLARE_RIICHI).
    3. Simple discard strategy: honors -> terminals -> Simple tiles.
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

        # 2. Prioritize riichi
        if GameAction.DECLARE_RIICHI in available_actions:
            valid_discards = hand.tenpai_discards
            if valid_discards:
                # Choose the best discard from valid riichi discards
                best_riichi_discard = self._choose_best_discard(hand, valid_discards)
                return GameAction.DECLARE_RIICHI, best_riichi_discard

        # 3. handle Discard
        if GameAction.DISCARD in available_actions:
            # If in riichi, must discard the drawn tile
            if hand.is_riichi:
                tile_to_discard = hand.last_drawn_tile
                if tile_to_discard is None:
                    tile_to_discard = hand.tiles[-1]
                return GameAction.DISCARD, tile_to_discard

            # Simple discard strategy: honors -> terminals -> Simple tiles (Isolated tiles first)
            best_discard = self._choose_best_discard(hand)
            return GameAction.DISCARD, best_discard

        # 4. handle Melds
        if GameAction.PASS in available_actions:
            return GameAction.PASS, None

        return random.choice(available_actions), None

    def _choose_best_discard(
        self, hand: Hand, candidates: Optional[List[Tile]] = None
    ) -> Tile:
        """
        Choose the best discard.

        Args:
            hand (Hand): hand.
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
                score = 30 + (
                    5 - abs(tile.rank - 5)
                )  # 5 is highest score (35), 1/9 is 26 (but already captured by terminal)

            # Jitter to break ties between tiles in the same priority bucket
            # (e.g. multiple honors), so the player doesn't always pick the
            # first one encountered.
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
    2. When an opponent declares riichi, enter defense mode:
       - Prioritize discarding riichi player's genbutsu.
       - If no genbutsu, try discarding honors or suji (Currently only genbutsu implemented).
       - betaori (Fold): Do not call melds.
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

        # 1. If winning is possible, still win (Chase riichi / Push, or lucky)
        if GameAction.RON in available_actions:
            return GameAction.RON, None
        if GameAction.TSUMO in available_actions:
            return GameAction.TSUMO, None

        # 2. betaori (Fold): No riichi, No Melds
        if GameAction.DISCARD in available_actions:
            # Find genbutsu
            genbutsu = self._find_genbutsu(hand, public_info, threatening_players)
            if genbutsu:
                return GameAction.DISCARD, genbutsu

            # If no genbutsu is available, fall back to SimplePlayer's discard logic.
            # But we want it to be more conservative, here temporarily call parent class
            return super().decide_action(
                game_state, player_index, hand, available_actions, public_info
            )

        # Reject all meld requests (PASS)
        if GameAction.PASS in available_actions:
            return GameAction.PASS, None

        return GameAction.PASS, None

    def _find_genbutsu(
        self,
        hand: Hand,
        public_info: Optional[PublicInfo],
        threatening_players: List[int],
    ) -> Optional[Tile]:
        """Find genbutsu in hand."""
        if not public_info:
            return None

        # Collect genbutsu of all threatening players

        # Simplified handling: As long as it is genbutsu of any riichi player, consider it "relatively" safe
        # Stricter defense should target common genbutsu of all riichi players
        # But if cannot cover all, prioritize defending against shimocha/toimen/kamicha? Or random?
        # Here we take intersection first; if none, take the union.

        common_genbutsu_tiles = None

        for player_idx in threatening_players:
            discards = public_info.discards.get(player_idx, [])
            player_genbutsu_tiles = set(discards)

            if common_genbutsu_tiles is None:
                common_genbutsu_tiles = player_genbutsu_tiles
            else:
                common_genbutsu_tiles = common_genbutsu_tiles.intersection(
                    player_genbutsu_tiles
                )

        # Check if there are common genbutsu in hand
        if common_genbutsu_tiles:
            for tile in hand.tiles:
                if tile in common_genbutsu_tiles:
                    return tile

        # If no common genbutsu, try to find genbutsu against a specific riichi player (Avoid dealing into the most dangerous one?)
        # Temporarily choose a genbutsu against someone randomly
        all_genbutsu_tiles = set()
        for player_idx in threatening_players:
            all_genbutsu_tiles.update(public_info.discards.get(player_idx, []))

        for tile in hand.tiles:
            if tile in all_genbutsu_tiles:
                return tile

        return None
