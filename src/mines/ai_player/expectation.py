from ..game import Minesweeper, GameStatus, CellState, CellVisuals

class Expectation:
    board: Minesweeper

    
    def __init__(self, board: Minesweeper, learning=None):
        self.board = board
        self.learning = learning
    
    def evaluate(self) -> list[list[float]]:
        board_state = self.board.get_board_state_2()
        game_state = board_state['cells']

        revealed_cells: list[tuple[int, int]] = []
        covered_cells_count = 0

        # rows x cols (initialized to all zeroes)
        bomb_probability_map: list[list[float]] = [
            [
                0 for _ in range(board_state['cols'])
            ] for _ in range(board_state['rows'])
        ]

        flag_count = 0

        for r in range(board_state['rows']):
            for c in range(board_state['cols']):
                cell_state = game_state[r][c]['state']
                
                if cell_state == CellState.FLAGGED:
                    bomb_probability_map[r][c] = -1
                    flag_count += 1
                    continue
                    
                if cell_state in [CellState.COVERED, CellState.REVEALED_EMPTY, CellState.REVEALED_MINE]:
                    if cell_state in [CellState.REVEALED_EMPTY, CellState.REVEALED_MINE]:
                        bomb_probability_map[r][c] = -1

                    if cell_state is CellState.COVERED:
                        covered_cells_count += 1
                    continue
                
                revealed_cells.append((r, c))
                bomb_probability_map[r][c] = -1

        if covered_cells_count == 0:
            return bomb_probability_map

        remaining_mines = max(0, board_state['mines'] - flag_count)
        uniform_probability = remaining_mines / covered_cells_count
        
        for r in range(board_state['rows']):
            for c in range(board_state['cols']):
                if bomb_probability_map[r][c] == 0:
                    bomb_probability_map[r][c] = uniform_probability

        # determinstic
        changes_made = True
        iterations = 0
        max_iterations = 10
        
        while changes_made and iterations < max_iterations:
            changes_made = False
            iterations += 1
            
            for rev_coords in revealed_cells:
                r, c = rev_coords
                total_bombs = game_state[r][c]['value']
                
                if not total_bombs:
                    continue
                
                surrounding = self.board.get_neighbors(r, c)
                covered_neighbors = []
                flagged_count = 0
                
                for sr, sc in surrounding:
                    cell_state = game_state[sr][sc]['state']
                    if cell_state == CellState.COVERED:
                        covered_neighbors.append((sr, sc))
                    elif cell_state == CellState.FLAGGED:
                        flagged_count += 1
                
                remaining_bombs = total_bombs - flagged_count
                
                # remaining_bombs == 0 => neighbors are safe (p=0)
                if remaining_bombs == 0:
                    for sr, sc in covered_neighbors:
                        if bomb_probability_map[sr][sc] > 0:
                            bomb_probability_map[sr][sc] = 0.0
                            changes_made = True
                
                # remaining_bombs == len(covered_neighbors) => all are mines (p=1)
                elif len(covered_neighbors) > 0 and remaining_bombs == len(covered_neighbors):
                    for sr, sc in covered_neighbors:
                        if bomb_probability_map[sr][sc] < 1.0:
                            bomb_probability_map[sr][sc] = 1.0
                            changes_made = True

        # probabilistic
        constraint_count = [[0 for _ in range(board_state['cols'])] for _ in range(board_state['rows'])]
        probability_sum = [[0.0 for _ in range(board_state['cols'])] for _ in range(board_state['rows'])]

        for rev_coords in revealed_cells:
            r, c = rev_coords
            surrounding = self.board.get_neighbors(r, c)

            covered_neighbors = []
            total_bombs = game_state[r][c]['value']

            if not total_bombs:
                continue

            flagged_count = 0
            for sr, sc in surrounding:
                cell_state = game_state[sr][sc]['state']
                if cell_state == CellState.COVERED:
                    # skip deterministically computed cells
                    if bomb_probability_map[sr][sc] in [0.0, 1.0]:
                        if bomb_probability_map[sr][sc] == 1.0:
                            flagged_count += 1 
                    else:
                        covered_neighbors.append((sr, sc))
                elif cell_state == CellState.FLAGGED:
                    flagged_count += 1

            remaining_bombs = total_bombs - flagged_count
            
            if len(covered_neighbors) == 0 or remaining_bombs <= 0:
                continue

            local_prob = remaining_bombs / len(covered_neighbors)

            for sr, sc in covered_neighbors:
                constraint_count[sr][sc] += 1
                probability_sum[sr][sc] += local_prob

        
        weight_factor = 2.0 # learned factor, from ai_learning.json (initally: 3)
        if self.learning:
            weight_factor = self.learning.params['constraint_weight_factor']
        
        for r in range(board_state['rows']):
            for c in range(board_state['cols']):
                if constraint_count[r][c] > 0 and bomb_probability_map[r][c] not in [0.0, 1.0, -1]:
                    constraint_prob = probability_sum[r][c] / constraint_count[r][c]
                    weight = min(constraint_count[r][c] / weight_factor, 1.0)
                    
                    bomb_probability_map[r][c] = (
                        weight * constraint_prob + (1 - weight) * uniform_probability
                    )
        
        return bomb_probability_map
