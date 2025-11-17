"""Minesweeper game logic module."""

import random
from enum import Enum


class CellState(Enum):
    """Represents the visual state of a cell on the board."""

    COVERED = 0
    REVEALED_EMPTY = 1
    REVEALED_NUMBER = 2
    REVEALED_MINE = 3
    FLAGGED = 4


class GameStatus(Enum):
    """Represents the overall status of the game."""

    PLAYING = 0
    WON = 1
    LOST = 2


class Minesweeper:
    """Core Minesweeper game logic.

    Manages board state, mine placement, cell revelation, and win/loss conditions.
    Automatically reveals connected empty cells (cascade effect) when a cell with
    zero adjacent mines is revealed.
    """

    def __init__(self, rows: int = 10, cols: int = 10, mines: int = 15) -> None:
        """Initialize the game board.

        Args:
            rows: Number of rows in the grid
            cols: Number of columns in the grid
            mines: Number of mines to place on the board
        """
        self.rows: int = rows
        self.cols: int = cols
        self.mines: int = mines
        # Store mine positions (-1) and adjacent mine counts (0-8) for each cell
        self.board: list[list[int]] = [[0 for _ in range(cols)] for _ in range(rows)]
        # Track which cells have been revealed to the player
        self.revealed: list[list[bool]] = [
            [False for _ in range(cols)] for _ in range(rows)
        ]
        # Track which cells have been flagged as suspected mines
        self.flagged: list[list[bool]] = [
            [False for _ in range(cols)] for _ in range(rows)
        ]
        self.status: GameStatus = GameStatus.PLAYING
        # Flag to defer mine placement until first click (to ensure first click is safe)
        self.first_click: bool = True

    def place_mines(self, safe_row: int, safe_col: int) -> None:
        """Place mines randomly on the board, avoiding the safe cell.

        Args:
            safe_row: Row index of the first clicked cell (must be mine-free)
            safe_col: Column index of the first clicked cell (must be mine-free)
        """
        mines_placed: int = 0
        while mines_placed < self.mines:
            # Generate random coordinates
            r: int = random.randint(0, self.rows - 1)
            c: int = random.randint(0, self.cols - 1)
            # Skip if cell is the safe cell or already has a mine
            if (r == safe_row and c == safe_col) or self.board[r][c] == -1:
                continue
            # Mark cell as a mine (-1 indicates mine)
            self.board[r][c] = -1
            mines_placed += 1
        # Calculate adjacent mine counts for all non-mine cells
        self._calculate_numbers()

    def _calculate_numbers(self) -> None:
        """Calculate and store the count of adjacent mines for each non-mine cell."""
        for r in range(self.rows):
            for c in range(self.cols):
                # Only calculate for non-mine cells
                if self.board[r][c] != -1:
                    self.board[r][c] = self._count_adjacent_mines(r, c)

    def _count_adjacent_mines(self, row: int, col: int) -> int:
        """Count the number of mines adjacent to a specific cell.

        Args:
            row: Row index of the cell
            col: Column index of the cell

        Returns:
            Number of adjacent mines (0-8)
        """
        count: int = 0
        # Check all 8 adjacent cells (including diagonals)
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                # Skip the center cell
                if dr == 0 and dc == 0:
                    continue
                nr: int = row + dr
                nc: int = col + dc
                # Verify coordinates are within board bounds
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    # Count if adjacent cell contains a mine
                    if self.board[nr][nc] == -1:
                        count += 1
        return count

    def get_neighbors(self, row: int, col: int) -> list[tuple[int, int]]:
        """Get all valid neighboring cells (8 adjacent cells).

        Args:
            row: Row index of the cell
            col: Column index of the cell

        Returns:
            List of (row, col) tuples for all valid neighbors
        """
        neighbors: list[tuple[int, int]] = []
        # Check all 8 adjacent cells (including diagonals)
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                # Skip the center cell
                if dr == 0 and dc == 0:
                    continue
                nr: int = row + dr
                nc: int = col + dc
                # Add only cells within board bounds
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    neighbors.append((nr, nc))
        return neighbors

    def reveal(self, row: int, col: int) -> bool:
        """Reveal a cell and handle cascade effect for empty cells.

        On the first click, mines are placed to guarantee the first cell is safe.
        If a revealed cell has no adjacent mines, all unrevealed neighbors are
        recursively revealed (cascade effect).

        Args:
            row: Row index of the cell to reveal
            col: Column index of the cell to reveal

        Returns:
            True if the cell is safe (non-mine), False if it's a mine
        """
        # Defer mine placement to first click to ensure it's safe
        if self.first_click:
            self.place_mines(row, col)
            self.first_click = False

        # Validate coordinates
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return True
        # Skip if cell is already revealed or flagged
        if self.revealed[row][col] or self.flagged[row][col]:
            return True

        # Mark cell as revealed
        self.revealed[row][col] = True

        # Check if cell contains a mine (game lost)
        if self.board[row][col] == -1:
            self.status = GameStatus.LOST
            return False

        # Cascade effect: recursively reveal all neighbors if cell has no adjacent mines
        if self.board[row][col] == 0:
            for nr, nc in self.get_neighbors(row, col):
                # Reveal unrevealed and unflagged neighbors
                if not self.revealed[nr][nc] and not self.flagged[nr][nc]:
                    _ = self.reveal(nr, nc)

        # Check win condition after reveal
        if self._check_win():
            self.status = GameStatus.WON

        return True

    def flag(self, row: int, col: int) -> None:
        """Toggle a flag on an unrevealed cell to mark it as a suspected mine.

        Args:
            row: Row index of the cell to flag
            col: Column index of the cell to flag
        """
        # Validate coordinates
        if 0 <= row < self.rows and 0 <= col < self.cols:
            # Only allow flagging unrevealed cells
            if not self.revealed[row][col]:
                self.flagged[row][col] = not self.flagged[row][col]

    def _check_win(self) -> bool:
        """Check if the player has won the game.

        Win condition: all non-mine cells have been revealed.

        Returns:
            True if the player has won, False otherwise
        """
        # Iterate through all cells
        for r in range(self.rows):
            for c in range(self.cols):
                # If any non-mine cell is unrevealed, game is still ongoing
                if self.board[r][c] != -1 and not self.revealed[r][c]:
                    return False
        # All non-mine cells are revealed
        return True

    def get_cell_state(self, row: int, col: int) -> CellState:
        """Get the current visual state of a cell.

        Args:
            row: Row index of the cell
            col: Column index of the cell

        Returns:
            CellState enum representing the cell's appearance to the player

        Raises:
            ValueError: If coordinates are outside board bounds
        """
        # Validate coordinates
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            raise ValueError(f"Invalid coordinates: ({row}, {col})")

        # Check state in order of priority for display
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
        """Get the numeric value of a revealed cell.

        Args:
            row: Row index of the cell
            col: Column index of the cell

        Returns:
            The count of adjacent mines (0-8) for revealed non-mine cells,
            or None for unrevealed cells or mines
        """
        # Validate coordinates
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return None
        # Only return value for revealed cells
        if not self.revealed[row][col]:
            return None
        value: int = self.board[row][col]
        # Return None for mines (stored as -1), otherwise return the count
        return value if value != -1 else None

    def get_board_state(self) -> dict[str, object]:
        """Get the complete current state of the board.

        Returns:
            Dictionary containing board dimensions, mine count, game status,
            and a 2D array of cell states and values for rendering
        """
        cells: list[list[dict[str, object]]] = []
        # Build 2D array of cell information
        for r in range(self.rows):
            row_cells: list[dict[str, object]] = []
            for c in range(self.cols):
                # Get both visual state and numeric value for each cell
                state: CellState = self.get_cell_state(r, c)
                value: int | None = self.get_cell_value(r, c)
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
        """Check if the game has ended (won or lost).

        Returns:
            True if game is won or lost, False if still playing
        """
        return self.status in (GameStatus.WON, GameStatus.LOST)

    def get_status(self) -> GameStatus:
        """Get the current game status.

        Returns:
            Current GameStatus (PLAYING, WON, or LOST)
        """
        return self.status
