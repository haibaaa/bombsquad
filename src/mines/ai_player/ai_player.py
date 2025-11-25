from ..game import Minesweeper, CellState, GameStatus
from .expectation import Expectation
from .learning import AILearning

class PlayerAI:
    board: Minesweeper
    expectation: Expectation
    learning: AILearning | None

    # board_status : nxn -> reveal_coord : (n, n)
    def __init__(self, board: Minesweeper, enable_learning: bool = True, learning_instance: AILearning | None = None):
        self.board = board
        self.enable_learning = enable_learning
        # Use provided learning instance or create new one
        self.learning = learning_instance if learning_instance else (AILearning() if enable_learning else None)
        self.expectation = Expectation(self.board, self.learning)
        self.moves_made = 0
        self.last_move_state = None

    def move(self) -> tuple[int, int] | None:
        """Make a move and record it for learning."""
        move = self.get_best_move()
        if move:
            self.last_move_state = self.board.get_cell_state(move[0], move[1])
            self.moves_made += 1
        return move
    
    def record_move_outcome(self, was_safe: bool):
        """Record whether the last move was safe."""
        if self.learning:
            self.learning.record_move(was_safe)
    
    def record_game_end(self):
        """Record game outcome for learning."""
        if self.learning:
            won = self.board.get_status() == GameStatus.WON
            self.learning.record_game(won, self.moves_made)
    
    def get_best_move(self) -> tuple[int, int] | None:
        heatmap = self.get_heatmap()
        board_state = self.board.get_board_state_2()
        game_state = board_state['cells']
        
        # Get learned thresholds
        flag_threshold = 0.95
        if self.learning:
            flag_threshold = self.learning.params['flag_threshold']
        
        best_cell = None
        lowest_prob = float('inf')
        
        # First, check for cells with 0 probability (guaranteed safe)
        for r in range(board_state['rows']):
            for c in range(board_state['cols']):
                if game_state[r][c]['state'] == CellState.COVERED:
                    prob = heatmap[r][c]
                    if prob == 0:
                        return (r, c)
                    if prob < lowest_prob:
                        lowest_prob = prob
                        best_cell = (r, c)
        
        # Flag cells with high probability using learned threshold
        for r in range(board_state['rows']):
            for c in range(board_state['cols']):
                if game_state[r][c]['state'] == CellState.COVERED:
                    if heatmap[r][c] >= flag_threshold:
                        self.board.flag(r, c)
        
        return best_cell
    
    def get_dangerous_cells(self, threshold: float | None = None) -> list[tuple[int, int]]:
        heatmap = self.get_heatmap()
        board_state = self.board.get_board_state_2()
        game_state = board_state['cells']
        
        # Use learned threshold if available
        if threshold is None:
            threshold = self.learning.params['danger_threshold'] if self.learning else 0.7
        
        dangerous = []
        for r in range(board_state['rows']):
            for c in range(board_state['cols']):
                if game_state[r][c]['state'] == CellState.COVERED:
                    if heatmap[r][c] >= threshold:
                        dangerous.append((r, c))
        
        return dangerous

    def get_heatmap(self):
        return self.expectation.evaluate()