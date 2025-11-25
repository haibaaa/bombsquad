from naive import naive_next_move
from grouping import grouping_next_move
from count import count_next_move
from csp import csp_next_move
from guess import guess_next_move

def solver_next_move(board, revealed, flagged, total_mines, strategy="auto"):

    if strategy == "naive":
        return naive_next_move(board, revealed, flagged)

    if strategy == "grouping":
        return grouping_next_move(board, revealed, flagged)

    if strategy == "count":
        safe = count_next_move(board, revealed, flagged, total_mines)
        return safe, set()

    if strategy == "csp":
        return csp_next_move(board, revealed, flagged)

    if strategy == "guess":
        _, _, probabilities = csp_next_move(board, revealed, flagged)
        return guess_next_move(probabilities)

    # AUTO = run strongest → weakest
    safe, mines, probs = csp_next_move(board, revealed, flagged)
    if safe or mines:
        return safe, mines

    # try grouping
    safe, mines = grouping_next_move(board, revealed, flagged)
    if safe or mines:
        return safe, mines

    # naive
    safe, mines = naive_next_move(board, revealed, flagged)
    if safe or mines:
        return safe, mines

    # if nothing — guess
    return guess_next_move(probs)
