# Strategy 2: Grouping-based solver
# This uses subset relationships between constraint groups to deduce safe/mine cells

class Group:
    def __init__(self, cells: set, mines: int):
        self.cells = set(cells)     # set of (r, c)
        self.mines = mines          # integer number of mines

def build_groups(board, revealed, flagged):
    """Build constraint groups from revealed numbered cells"""
    groups = []

    for r in range(rows):
        for c in range(cols):
            if revealed[r][c] and board[r][c] > 0:
                # Check neighbors of this numbered cell
                hidden = []
                flagged_count = 0

                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        
                        nr = r + dr
                        nc = c + dc

                        if 0 <= nr < rows and 0 <= nc < cols:
                            if flagged[nr][nc]:
                                flagged_count += 1
                            elif not revealed[nr][nc]:
                                hidden.append((nr, nc))

                # Calculate how many mines are yet to be found
                yet_to_flag = board[r][c] - flagged_count
                
                if yet_to_flag > 0 and len(hidden) > 0:
                    groups.append(Group(cells=hidden, mines=yet_to_flag))

    return groups


def grouping_next_move(board, revealed, flagged):
    """Find safe/mine moves using group subset logic"""
    groups = build_groups(board, revealed, flagged)

    safe_moves = set()
    mine_moves = set()

    changed = True
    while changed:
        changed = False

        # Compare each pair of groups
        for i in range(len(groups)):
            for j in range(len(groups)):
                if i == j:
                    continue

                g1: Group = groups[i]
                g2: Group = groups[j]

                # Check if g2 is a subset of g1
                if g2.cells.issubset(g1.cells):
                    # Subtract to get remaining cells and mines
                    remaining_cells = g1.cells - g2.cells
                    remaining_mines = g1.mines - g2.mines

                    # Skip invalid subtractions
                    if remaining_mines < 0:
                        continue

                    # Case 1: No mines left → all remaining cells are safe
                    if remaining_mines == 0:
                        for (rr, cc) in remaining_cells:
                            safe_moves.add((rr, cc))
                        changed = True

                    # Case 2: All remaining cells are mines
                    elif len(remaining_cells) == remaining_mines:
                        for (rr, cc) in remaining_cells:
                            mine_moves.add((rr, cc))
                        changed = True

                    # Case 3: Create new group for further analysis
                    elif remaining_mines > 0 and len(remaining_cells) > 0:
                        new_group = Group(cells=remaining_cells, mines=remaining_mines)
                        # Only add if not already present
                        if all(new_group.cells != g.cells or new_group.mines != g.mines
                               for g in groups):
                            groups.append(new_group)
                            changed = True

    return safe_moves, mine_moves