"""Quick training script for the AI."""
from src.mines.game import Minesweeper
from src.mines.ai_player.ai_player import PlayerAI
from src.mines.ai_player.learning import AILearning

def train_ai(rows=10, cols=10, mines=15, iterations=100):
    """Train the AI for specified number of games.
    
    Args:
        rows: Board rows
        cols: Board columns
        mines: Number of mines
        iterations: Number of games to play
    """
    print(f"\n🎓 Training AI for {iterations} games on {rows}x{cols} board with {mines} mines...")
    print("="*60)
    
    learning = AILearning()
    initial_games = learning.stats['games_played']
    initial_wins = learning.stats['games_won']
    
    for i in range(iterations):
        # Create new game and AI for each iteration
        game = Minesweeper(rows, cols, mines)
        ai = PlayerAI(game, enable_learning=True)
        
        # Play until game ends
        moves = 0
        while not game.is_game_over() and moves < 1000:  # Add safety limit
            move = ai.move()
            if move:
                was_mine = game.board[move[0]][move[1]] == -1
                game.reveal(move[0], move[1])
                ai.record_move_outcome(not was_mine)
                moves += 1
            else:
                # No valid moves, game stuck
                break
        
        # Record game outcome
        ai.record_game_end()
        
        # Progress update every 10 games or at end
        if (i + 1) % 10 == 0 or (i + 1) == iterations:
            current_wins = learning.stats['games_won'] - initial_wins
            current_rate = current_wins / (i + 1) if (i + 1) > 0 else 0
            print(f"Progress: {i + 1}/{iterations} | Wins: {current_wins} | Rate: {current_rate:.1%}")
    
    print("="*60)
    final_wins = learning.stats['games_won'] - initial_wins
    final_rate = final_wins / iterations if iterations > 0 else 0
    
    print(f"\n✅ Training Complete!")
    print(f"   Games: {iterations} | Wins: {final_wins} | Win Rate: {final_rate:.1%}")
    print(f"\n📊 Overall Stats: {learning.get_stats_display()}")
    print("\n🎯 Current Parameters:")
    for key, value in learning.params.items():
        print(f"   {key}: {value:.3f}")
    print()

if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        try:
            iterations = int(sys.argv[1])
            rows = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            cols = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            mines = int(sys.argv[4]) if len(sys.argv) > 4 else 15
            train_ai(rows, cols, mines, iterations)
        except ValueError:
            print("Usage: python train_ai.py [iterations] [rows] [cols] [mines]")
            print("Example: python train_ai.py 100 10 10 15")
    else:
        # Interactive mode
        print("AI Training Script")
        print("="*60)
        try:
            iterations = int(input("Number of games to train (default 100): ") or "100")
            rows = int(input("Board rows (default 10): ") or "10")
            cols = int(input("Board columns (default 10): ") or "10")
            mines = int(input("Number of mines (default 15): ") or "15")
            train_ai(rows, cols, mines, iterations)
        except ValueError:
            print("Invalid input. Using defaults.")
            train_ai()
