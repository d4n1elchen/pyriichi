"""
PyRiichi - Python Riichi Mahjong Engine

Complete implementation of Riichi Mahjong rule engine.
"""

__version__ = "0.1.0"

# Core Classes
from pyriichi.game_state import GameState, Wind
from pyriichi.hand import Hand, Meld, MeldType
from pyriichi.rules import (
    ActionResult,
    GameAction,
    GamePhase,
    RuleEngine,
    RyuukyokuResult,
    RyuukyokuType,
    WinResult,
)
from pyriichi.rules_config import RulesetConfig
from pyriichi.scoring import ScoreCalculator, ScoreResult
from pyriichi.tiles import Suit, Tile, TileSet

# Convenience Functions
from pyriichi.utils import format_tiles, is_winning_hand, parse_tiles
from pyriichi.yaku import Yaku, YakuChecker, YakuResult

__all__ = [
    # Core Classes
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
    "RyuukyokuResult",
    "RyuukyokuType",
    "YakuChecker",
    "YakuResult",
    "Yaku",
    "ScoreCalculator",
    "ScoreResult",
    "RulesetConfig",
    # Utility Functions
    "parse_tiles",
    "format_tiles",
    "is_winning_hand",
]
