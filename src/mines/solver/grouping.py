# # Strategy 2: Grouping-based solver
# # This uses subset relationships between constraint groups to deduce safe/mine cells

# class Group:
#     def __init__(self, cells: set, mines: int):
#         self.cells = set(cells)     # set of (r, c)
#         self.mines = mines          # integer number of mines

# def build_groups(board, revealed, flagged):
#     """Build constraint groups from revealed numbered cells"""
#     groups = []
#     rows = len(board)
#     cols = len(board[0])

#     for r in range(rows):
#         for c in range(cols):
#             if revealed[r][c] and board[r][c] > 0:
#                 # Check neighbors of this numbered cell
#                 hidden = []
#                 flagged_count = 0

#                 for dr in (-1, 0, 1):
#                     for dc in (-1, 0, 1):
#                         if dr == 0 and dc == 0:
#                             continue
                        
#                         nr = r + dr
#                         nc = c + dc

#                         if 0 <= nr < rows and 0 <= nc < cols:
#                             if flagged[nr][nc]:
#                                 flagged_count += 1
#                             elif not revealed[nr][nc]:
#                                 hidden.append((nr, nc))

#                 # Calculate how many mines are yet to be found
#                 yet_to_flag = board[r][c] - flagged_count
                
#                 if yet_to_flag > 0 and len(hidden) > 0:
#                     groups.append(Group(cells=hidden, mines=yet_to_flag))

#     return groups


# def grouping_next_move(board, revealed, flagged):
#     """Find safe/mine moves using group subset logic"""
#     rows = len(board)
#     cols = len(board[0])
#     groups = build_groups(board, revealed, flagged)

#     safe_moves = set()
#     mine_moves = set()

#     changed = True
#     while changed:
#         changed = False

#         # Compare each pair of groups
#         for i in range(len(groups)):
#             for j in range(len(groups)):
#                 if i == j:
#                     continue

#                 g1: Group = groups[i]
#                 g2: Group = groups[j]

#                 # Check if g2 is a subset of g1
#                 if g2.cells.issubset(g1.cells):
#                     # Subtract to get remaining cells and mines
#                     remaining_cells = g1.cells - g2.cells
#                     remaining_mines = g1.mines - g2.mines

#                     # Skip invalid subtractions
#                     if remaining_mines < 0:
#                         continue

#                     # Case 1: No mines left → all remaining cells are safe
#                     if remaining_mines == 0:
#                         for (rr, cc) in remaining_cells:
#                             safe_moves.add((rr, cc))
#                         changed = True

#                     # Case 2: All remaining cells are mines
#                     elif len(remaining_cells) == remaining_mines:
#                         for (rr, cc) in remaining_cells:
#                             mine_moves.add((rr, cc))
#                         changed = True

#                     # Case 3: Create new group for further analysis
#                     elif remaining_mines > 0 and len(remaining_cells) > 0:
#                         new_group = Group(cells=remaining_cells, mines=remaining_mines)
#                         # Only add if not already present
#                         if all(new_group.cells != g.cells or new_group.mines != g.mines
#                                for g in groups):
#                             groups.append(new_group)
#                             changed = True

#     return safe_moves, mine_moves

# updated method 
# Strategy 2: Grouping-based solver (final, safe, optimized)

class Group:
    def __init__(self, cells, mines):
        self.cells = set(cells)
        self.mines = mines

    def copy(self):
        return Group(set(self.cells), self.mines)

    def signature(self):
        return (frozenset(self.cells), self.mines)

    def __repr__(self):
        return f"Group({self.cells}, mines={self.mines})"


def build_groups(board, revealed, flagged):
    groups = []
    rows, cols = len(board), len(board[0])

    for r in range(rows):
        for c in range(cols):
            if not revealed[r][c]:
                continue
            number = board[r][c]
            if number <= 0:
                continue

            hidden = []
            flagged_count = 0

            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        if flagged[nr][nc]:
                            flagged_count += 1
                        elif not revealed[nr][nc]:
                            hidden.append((nr, nc))

            mines_left = number - flagged_count

            if hidden:
                groups.append(Group(hidden, mines_left))

    return groups


def prune_groups(groups):
    """Remove empty or duplicate groups."""
    seen = set()
    pruned = []

    for g in groups:
        if len(g.cells) == 0:
            continue
        sig = g.signature()
        if sig not in seen:
            seen.add(sig)
            pruned.append(g)

    return pruned


def reduce_groups(groups, safe_moves, mine_moves):
    """Apply found safes/mines to all groups."""
    result = []

    for g in groups:
        new_cells = set()
        new_mines = g.mines

        for cell in g.cells:
            if cell in safe_moves:
                continue
            if cell in mine_moves:
                new_mines -= 1
            else:
                new_cells.add(cell)

        if new_mines < 0:
            continue
        if len(new_cells) == 0:
            continue

        result.append(Group(new_cells, new_mines))

    return prune_groups(result)


def grouping_next_move(board, revealed, flagged):
    groups = build_groups(board, revealed, flagged)

    safe_moves = set()
    mine_moves = set()

    changed = True
    iteration_limit = 30   # prevents infinite loops

    while changed and iteration_limit > 0:
        iteration_limit -= 1
        changed = False

        groups = reduce_groups(groups, safe_moves, mine_moves)

        n = len(groups)
        for i in range(n):
            for j in range(i + 1, n):
                A = groups[i]
                B = groups[j]

                # try A ⊂ B
                if A.cells.issubset(B.cells):
                    rem = B.cells - A.cells
                    diff = B.mines - A.mines

                    if diff == 0:
                        safe_moves |= rem
                        changed = True
                    elif diff == len(rem):
                        mine_moves |= rem
                        changed = True
                    elif 0 < diff < len(rem):
                        groups.append(Group(rem, diff))
                        changed = True

                # try B ⊂ A
                if B.cells.issubset(A.cells):
                    rem = A.cells - B.cells
                    diff = A.mines - B.mines

                    if diff == 0:
                        safe_moves |= rem
                        changed = True
                    elif diff == len(rem):
                        mine_moves |= rem
                        changed = True
                    elif 0 < diff < len(rem):
                        groups.append(Group(rem, diff))
                        changed = True

        groups = prune_groups(groups)

    return safe_moves, mine_moves
