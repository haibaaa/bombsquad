# okay, so I need to use the given functions in state wala code.
# so i need to have 3 example 2d arrays



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




board1 = [[0, 0, 0, 0, 1, 1, 1, 1, -1, 1],
[0, 0, 1, 1, 2, -1, 2, 1, 1, 2],
[0, 0, 1, -1, 3, 2, 2, 0, 0, 1],
[1, 1, 2, 2, -1, 1, 1, 0, 0, 1],
[2, -1, 3, 2, 1, 1, 0, 0, 1, 1],
[3, -1, 3, 1, 0, 0, 0, 1, 2, -1],
[3, -1, 3, 1, 0, 0, 0, 1, -1, 2],
[2, 2, 2, 1, 1, 1, 1, 1, 1, 1],
[1, -1, 1, 0, 0, 1, -1, 1, 0, 0],
[1, 1, 1, 0, 0, 1, 1, 1, 0, 0]]

revealed = [[True,  True,  True,  True,  True,  True,  True,  True, False, True],
[True,  True,  True,  True,  True, False, True,  True, True,  True],
[True,  True,  True, False, True,  True,  True,  True, True,  True],
[True,  True,  True, True, False, True,  True,  True, True,  True],
[True, False, True, True, True, True,  True, True, True,  True],
[True, False, True, True, True, True, True, True, True, False],
[True, False, True, True, True, True, True, True, False, True],
[True, True, True, True, True, True, True, True, True,  True],
[True, False, True, True, True, True, False, True, True, True],
[True, True, True, True, True, True, True, True, True, True]]

flagged = [[False, False, False, False, False, False, False, False, False, False],
[False, False, False, False, False, False, False, False, False, False],
[False, False, False, False, False, False, False, False, False, False],
[False, False, False, False, False, False, False, False, False, False],
[False, False, False, False, False, False, False, False, False, False],
[False, False, False, False, False, False, False, False, False, False],
[False, False, False, False, False, False, False, False, False, False],
[False, False, False, False, False, False, False, False, False, False],
[False, False, False, False, False, False, False, False, False, False],
[False, False, False, False, False, False, False, False, False, False]
]

# Alright, now I have 3 example 2d arrays: board1, revealed, and flagged. I need to calculat the next move based on my naive strategy.

# Naive strategy says that:
#  1. IF THERE ARE AS MANY CLOSED CELLS AS THERE ARE NUMBER OF MINES, THEN ALL THOSE CLOSED CELLS ARE MINES.
#  2. IF A NUMBERED CELL HAS AS MANY FLAGGED CELLS AROUND IT AS THE NUMBER IT DISPLAYS, THEN ALL OTHER CLOSED CELLS AROUND IT ARE SAFE

# so for each revealed cell, I need to check its neighbors and apply the above 2 rules.

def naive_next_move(board, revealed, flagged):
    
    for r in range(rows):
        for c in range(cols):
            if revealed[r][c] and board[r][c] >0:
                # means, we need to check neighbors/check the number of mines.
                # so, 
                closed_cells = 0
                flagged_cells = 0

                for dr in (-1,0,1):
                    for dc in (-1,0,1):
                        if dr == 0 and dc == 0:
                        continue

                        nr: int = row + dr
                        nc: int = col + dc

                        if 0 <= nr < rows and 0 <= nc < cols:

                            if not revealed[nr][nc]:
                                closed_cells += 1
                            if flagged[nr][nc]:
                                flagged_cells += 1
                
                # ATP I have the number of closed cells and flagged cells around the current cell.
                if closed_cells == board[r][c] - flagged_cells:
                    # means all closed cells are mines. we need to make a move.
                    # so we change the arrays accordingly.
                    # now wherever I see closed cell, I'll flag it.
                    for dr in (-1,0,1):
                        for dc in (-1,0,1):
                            if dr == 0 and dc == 0:
                                continue

                            nr: int = row + dr
                            nc: int = col + dc

                            if 0 <= nr < rows and 0 <= nc < cols:
                                if not revealed[nr][nc]:
                                    flagged[nr][nc] = True

                elif flagged_cells == board[r][c]:
                    # means all other closed cells are safe.
                    for dr in (-1,0,1):
                        for dc in (-1,0,1):
                            if dr == 0 and dc == 0:
                                continue

                            nr: int = row + dr
                            nc: int = col + dc

                            if 0 <= nr < rows and 0 <= nc < cols:
                                if not revealed[nr][nc]:
                                    revealed[nr][nc] = True

    