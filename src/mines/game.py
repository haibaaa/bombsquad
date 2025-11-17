"""Minesweeper game logic module."""

import random
from enum import Enum


class CellState(Enum):
    COVERED = 0
    REVEALED_EMPTY = 1
    REVEALED_NUMBER = 2
    REVEALED_MINE = 3
    FLAGGED = 4


class GameStatus(Enum):
    PLAYING = 0
    WON = 1
    LOST = 2


class Minesweeper:
    """Core Minesweeper game logic."""

    def __init__(self, rows: int = 10, cols: int = 10, mines: int = 15):
        self.rows: int = rows
        self.cols: int = cols
        self.mines: int = mines
        self.board: list[list[int]] = [[0 for _ in range(cols)] for _ in range(rows)]
        self.revealed: list[list[bool]] = [
            [False for _ in range(cols)] for _ in range(rows)
        ]
        self.flagged: list[list[bool]] = [
            [False for _ in range(cols)] for _ in range(rows)
        ]
        self.status: GameStatus = GameStatus.PLAYING
        self.first_click: bool = True

    def place_mines(self, safe_row: int, safe_col: int) -> None:
        """Place mines randomly, avoiding safe cell."""
        mines_placed = 0
        while mines_placed < self.mines:
            r = random.randint(0, self.rows - 1)
            c = random.randint(0, self.cols - 1)
            if (r == safe_row and c == safe_col) or self.board[r][c] == -1:
                continue
            self.board[r][c] = -1
            mines_placed += 1
        self._calculate_numbers()

    def _calculate_numbers(self) -> None:
        """Calculate adjacent mine counts."""
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] != -1:
                    self.board[r][c] = self._count_adjacent_mines(r, c)

    def _count_adjacent_mines(self, row: int, col: int) -> int:
        """Count mines adjacent to a cell."""
        count = 0
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    if self.board[nr][nc] == -1:
                        count += 1
        return count

    def get_neighbors(self, row: int, col: int) -> list[tuple[int, int]]:
        """Get all valid neighboring cells."""
        neighbors = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    neighbors.append((nr, nc))
        return neighbors

    def reveal(self, row: int, col: int) -> bool:
        """Reveal cell. Returns True if safe, False if mine."""
        if self.first_click:
            self.place_mines(row, col)
            self.first_click = False

        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return True
        if self.revealed[row][col] or self.flagged[row][col]:
            return True

        self.revealed[row][col] = True

        if self.board[row][col] == -1:
            self.status = GameStatus.LOST
            return False

        if self.board[row][col] == 0:
            for nr, nc in self.get_neighbors(row, col):
                if not self.revealed[nr][nc] and not self.flagged[nr][nc]:
                    _ = self.reveal(nr, nc)

        if self._check_win():
            self.status = GameStatus.WON

        return True

    def flag(self, row: int, col: int) -> None:
        """Toggle flag on unrevealed cell."""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            if not self.revealed[row][col]:
                self.flagged[row][col] = not self.flagged[row][col]

    def _check_win(self) -> bool:
        """Check if won."""
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] != -1 and not self.revealed[r][c]:
                    return False
        return True

    def get_cell_state(self, row: int, col: int) -> CellState:
        """Get cell state."""
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            raise ValueError(f"Invalid coordinates: ({row}, {col})")

        if self.flagged[row][col]:
            return CellState.FLAGGED
        if not self.revealed[row][col]:
            return CellState.COVERED
        if self.board[row][col] == -1:
            return CellState.REVEALED_MINE
        elif self.board[row][col] == 0:
            return CellState.REVEALED_EMPTY
        else:
            return CellState.REVEALED_NUMBER

    def get_cell_value(self, row: int, col: int) -> int | None:
        """Get cell value (0-8) or None."""
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return None
        if not self.revealed[row][col]:
            return None
        value = self.board[row][col]
        return value if value != -1 else None

    def get_board_state(self) -> dict[str, object]:
        """Get complete board state."""
        cells = []
        for r in range(self.rows):
            row_cells = []
            for c in range(self.cols):
                state = self.get_cell_state(r, c)
                value = self.get_cell_value(r, c)
                row_cells.append({"state": state, "value": value})
            cells.append(row_cells)

        return {
            "rows": self.rows,
            "cols": self.cols,
            "mines": self.mines,
            "status": self.status,
            "cells": cells,
        }

    def is_game_over(self) -> bool:
        """Check if game ended."""
        return self.status in (GameStatus.WON, GameStatus.LOST)

    def get_status(self) -> GameStatus:
        """Get game status."""
        return self.status
