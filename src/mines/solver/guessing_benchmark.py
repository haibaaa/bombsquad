# src/mines/solver/guessing_benchmark.py
import sys
import os

# Ensure local package path is available when running as a script
_this_dir = os.path.dirname(__file__)  # .../src/mines/solver
_pkg_root = os.path.abspath(os.path.join(_this_dir, ".."))  # .../src/mines
if _pkg_root not in sys.path:
    sys.path.insert(0, _pkg_root)

# Try package imports first; fallback to local imports if needed
try:
    from mines.game import Minesweeper, GameStatus
    from mines.solver.naive import naive_next_move
    from mines.solver.grouping import grouping_next_move
    from mines.solver.count import count_next_move
    from mines.solver.csp import csp_next_move
    from benchmark_guess import auto_best_guess
except Exception:
    # Running inside src/mines folder (or similar) — import relative modules
    from game import Minesweeper, GameStatus
    from solver.naive import naive_next_move
    from solver.grouping import grouping_next_move
    from solver.count import count_next_move
    from solver.csp import csp_next_move
    from solver.benchmark_guess import auto_best_guess


def run_single_solve(rows, cols, mines):
    """Run one full game automatically until win/lose and return True/False."""
    game = Minesweeper(rows, cols, mines)

    while True:
        board = game.board
        revealed = game.revealed
        flagged = game.flagged

        # Strategy 1 — Naive
        safe, mines_found = naive_next_move(board, revealed, flagged)
        if safe or mines_found:
            for r, c in safe:
                game.reveal(r, c)
            for r, c in mines_found:
                game.flag(r, c)
            if game.is_game_over():
                break
            continue

        # Strategy 2 — Grouping
        safe, mines_found = grouping_next_move(board, revealed, flagged)
        if safe or mines_found:
            for r, c in safe:
                game.reveal(r, c)
            for r, c in mines_found:
                game.flag(r, c)
            if game.is_game_over():
                break
            continue

        # Strategy 3 — Count
        safe = count_next_move(board, revealed, flagged, game.mines)
        if safe:
            for r, c in safe:
                game.reveal(r, c)
            if game.is_game_over():
                break
            continue

        # Strategy 4 — CSP
        safe, mines_found, probs = csp_next_move(board, revealed, flagged)
        if safe or mines_found:
            for r, c in safe:
                game.reveal(r, c)
            for r, c in mines_found:
                game.flag(r, c)
            if game.is_game_over():
                break
            continue

        # Strategy 5 — Automatic Guess (benchmark-only)
        guess_cell, prob = auto_best_guess(probs, revealed, flagged)

        if guess_cell is None:
            # fallback: uniform random guess
            import random
            hidden = [
                (r, c)
                for r in range(game.rows)
                for c in range(game.cols)
                if not revealed[r][c] and not flagged[r][c]
            ]
            if not hidden:
                break
            guess_cell = random.choice(hidden)

        r, c = guess_cell
        game.reveal(r, c)

        if game.is_game_over():
            break

    return game.get_status() == GameStatus.WON
