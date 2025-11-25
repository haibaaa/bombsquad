# CSP-BASED SOLVER

from itertools import product

def extract_constraints(board, revealed, flagged):
    """Return CSP constraints: list of (cells, required_mines)."""
    rows, cols = len(board), len(board[0])
    constraints = []

    for r in range(rows):
        for c in range(cols):
            if revealed[r][c] and board[r][c] > 0:
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

                need = board[r][c] - flagged_count
                if need >= 0 and len(hidden) > 0:
                    constraints.append((tuple(hidden), need))

    return constraints


def solve_csp(constraints, hidden_cells):
    """Return probability map for each hidden cell."""
    hidden_cells = list(hidden_cells)
    n = len(hidden_cells)

    assignments = []  # each assignment is a list of 0/1

    def valid(assign):
        # Convert list of booleans into mapping
        mapping = {hidden_cells[i]: assign[i] for i in range(len(assign))}
        # Check every constraint
        for (cells, need) in constraints:
            s = sum(mapping[cell] for cell in cells if cell in mapping)
            if s != need:
                return False
        return True

    # Try all assignments (2^n) — small areas only
    for bits in product([0,1], repeat=n):
        bits = list(bits)
        if valid(bits):
            assignments.append(bits)

    if not assignments:
        return {}  # no info

    # compute probability for each cell
    probabilities = {}
    for i, cell in enumerate(hidden_cells):
        mine_count = sum(assign[i] for assign in assignments)
        prob = mine_count / len(assignments)
        probabilities[cell] = prob

    return probabilities


def csp_next_move(board, revealed, flagged):
    """Return deterministic safe/mine moves + probabilities."""
    rows = len(board)
    cols = len(board[0])
    rows, cols = len(board), len(board[0])

    constraints = extract_constraints(board, revealed, flagged)
    hidden_cells = {
        (r, c)
        for r in range(rows)
        for c in range(cols)
        if not revealed[r][c] and not flagged[r][c]
    }

    probabilities = solve_csp(constraints, hidden_cells)

    safe_moves = {cell for cell, p in probabilities.items() if p == 0}
    mine_moves = {cell for cell, p in probabilities.items() if p == 1}

    return safe_moves, mine_moves, probabilities
