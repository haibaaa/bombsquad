# okay, so I need to use the given functions in state wala code.
# so i need to have 3 example 2d arrays


board = [[0, 0, 0, 0, 1, 1, 1, 1, -1, 1],
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
    
    # we are gonna collect moves
    safe_moves = set()
    mine_moves = set()

    for r in range(rows):
        for c in range(cols):

            if revealed[r][c] and board[r][c] > 0:
                # means, we need to check neighbors/check the number of mines.
                closed_cells = []
                flagged_cells = 0

                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue

                        nr = r + dr
                        nc = c + dc

                        if 0 <= nr < rows and 0 <= nc < cols:

                            if flagged[nr][nc]:
                                flagged_cells += 1

                            elif not revealed[nr][nc]:
                                closed_cells.append((nr, nc))

                number = board[r][c]
            
                # ATP I have the location of closed cells and flagged cells around the current cell.

                # Rule 1: closed cells == remaining mines → all are mines
                if len(closed_cells) > 0 and len(closed_cells) == number - flagged_cells:
                    for cell in closed_cells:
                        mine_moves.add(cell)

                # Rule 2: flagged cells == number → all closed cells are safe
                if flagged_cells == number:
                    for cell in closed_cells:
                        safe_moves.add(cell)

    return safe_moves, mine_moves