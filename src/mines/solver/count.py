# COUNT-BASED SOLVER

from collections import deque

def get_hidden_regions(board, revealed):
    """Return list of connected components of hidden cells."""
    rows = len(board)
    cols = len(board[0])
    rows, cols = len(board), len(board[0])
    visited = set()
    regions = []

    for r in range(rows):
        for c in range(cols):
            if not revealed[r][c] and (r, c) not in visited:
                # BFS for region
                queue = deque([(r, c)])
                region = set([(r, c)])
                visited.add((r, c))

                while queue:
                    x, y = queue.popleft()
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nx, ny = x + dr, y + dc
                            if 0 <= nx < rows and 0 <= ny < cols:
                                if not revealed[nx][ny] and (nx, ny) not in visited:
                                    visited.add((nx, ny))
                                    region.add((nx, ny))
                                    queue.append((nx, ny))

                regions.append(region)

    return regions


def required_mines_in_region(region, board, revealed, flagged):
    """Return how many mines MUST be in this region, based on adjacent numbers."""
    rows = len(board)
    cols = len(board[0])
    required = 0
    for (r, c) in region:
        # Check neighbors
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue

                nr = r + dr
                nc = c + dc

                if 0 <= nr < len(board) and 0 <= nc < len(board[0]):
                    if revealed[nr][nc] and board[nr][nc] > 0:
                        # board number minus flagged neighbors gives unaccounted mines
                        mines_left = board[nr][nc]

                        flagged_count = 0
                        hidden_count = 0

                        for x in (-1, 0, 1):
                            for y in (-1, 0, 1):
                                rr = nr + x
                                cc = nc + y
                                if 0 <= rr < len(board) and 0 <= cc < len(board[0]):
                                    if flagged[rr][cc]:
                                        flagged_count += 1
                                    elif not revealed[rr][cc]:
                                        hidden_count += 1

                        unaccounted = mines_left - flagged_count
                        if unaccounted > 0:
                            # distribute unaccounted mines evenly among region?
                            required += unaccounted

    return max(0, required)


def count_next_move(board, revealed, flagged, total_mines):
    """Find safe moves using global count logic."""
    rows = len(board)
    cols = len(board[0])
    rows, cols = len(board), len(board[0])

    flagged_count = sum(sum(row) for row in flagged)
    remaining_mines = total_mines - flagged_count

    regions = get_hidden_regions(board, revealed)

    region_mine_sum = 0
    for region in regions:
        region_mine_sum += required_mines_in_region(region, board, revealed, flagged)

    safe_moves = set()

    # If all remaining mines are fully inside regions → outside is safe
    if region_mine_sum == remaining_mines:
        all_hidden = {(r, c)
                      for r in range(rows)
                      for c in range(cols)
                      if not revealed[r][c] and not flagged[r][c]}

        combined = set()
        for reg in regions:
            combined |= reg

        safe_moves = all_hidden - combined

    return safe_moves
