# benchmark_guess.py
# Only for auto-guessing during benchmarking (does NOT affect actual game)

import random

def auto_best_guess(probabilities, revealed, flagged):
    """
    Input:
        probabilities = { (r,c): mine_probability }
    Output:
        (cell, prob) where prob is the lowest mine probability.

    Note:
      This function is NOT used by the actual game. Only by benchmarking.
    """

    if not probabilities:
        return None, None

    # Hidden and unflagged only
    hidden = [
        cell for cell in probabilities.keys()
        if not revealed[cell[0]][cell[1]] and not flagged[cell[0]][cell[1]]
    ]

    if not hidden:
        return None, None

    # Lowest probability
    min_prob = min(probabilities[cell] for cell in hidden)

    best_cells = [
        cell for cell in hidden
        if probabilities[cell] == min_prob
    ]

    return random.choice(best_cells), min_prob
