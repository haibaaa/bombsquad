"""Minesweeper game package."""

from .game import Minesweeper, CellState, GameStatus
from .tui import MinesweeperTUI
from .ai_player import PlayerAI

__version__ = "0.1.0"
__all__ = ["Minesweeper", "CellState", "GameStatus", "MinesweeperTUI", "PlayerAI"]