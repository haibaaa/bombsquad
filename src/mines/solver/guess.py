def guess_next_move(probabilities):
    """Return list of cells sorted by mine probability (ascending)."""
    return sorted(probabilities.items(), key=lambda x: x[1])
