"""
PyRiichi - Python Japanese Mahjong Engine

A complete implementation of Japanese Mahjong (Riichi Mahjong) rules engine.
"""

__version__ = "0.1.0"

# Core classes
from pyriichi.tiles import Tile, Suit, TileSet
from pyriichi.hand import Hand, Meld, MeldType
from pyriichi.game_state import GameState, Wind
from pyriichi.rules import RuleEngine, GameAction, GamePhase, ActionResult, WinResult, DrawResult
from pyriichi.yaku import YakuChecker, YakuResult
from pyriichi.scoring import ScoreCalculator, ScoreResult
from pyriichi.rules_config import RulesetConfig

# Convenience functions
from pyriichi.utils import parse_tiles, format_tiles, is_winning_hand

__all__ = [
    # Core classes
    "Tile",
    "Suit",
    "TileSet",
    "Hand",
    "Meld",
    "MeldType",
    "GameState",
    "Wind",
    "RuleEngine",
    "GameAction",
    "GamePhase",
    "ActionResult",
    "WinResult",
    "DrawResult",
    "YakuChecker",
    "YakuResult",
    "ScoreCalculator",
    "ScoreResult",
    "RulesetConfig",
    # Utility functions
    "parse_tiles",
    "format_tiles",
    "is_winning_hand",
]
