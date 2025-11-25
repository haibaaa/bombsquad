"""Display AI learning statistics."""
from src.mines.ai_player.learning import AILearning

def main():
    learning = AILearning()
    
    print("\n" + "="*50)
    print("    MINESWEEPER AI LEARNING STATISTICS")
    print("="*50 + "\n")
    
    print("📊 Performance:")
    print(f"   Games Played: {learning.stats['games_played']}")
    print(f"   Wins: {learning.stats['games_won']}")
    print(f"   Losses: {learning.stats['games_lost']}")
    print(f"   Win Rate: {learning.stats['win_rate']:.1%}")
    print(f"   Total Moves: {learning.stats['total_moves']}")
    print(f"   Safe Moves: {learning.stats['safe_moves']}")
    print(f"   Mine Hits: {learning.stats['mine_hits']}")
    if learning.stats['total_moves'] > 0:
        safe_rate = learning.stats['safe_moves'] / learning.stats['total_moves']
        print(f"   Safe Move Rate: {safe_rate:.1%}")
    
    print("\n🎯 Learned Parameters:")
    print(f"   Danger Threshold: {learning.params['danger_threshold']:.3f}")
    print(f"   Flag Threshold: {learning.params['flag_threshold']:.3f}")
    print(f"   Constraint Weight: {learning.params['constraint_weight_factor']:.3f}")
    print(f"   Risk Tolerance: {learning.params['risk_tolerance']:.3f}")
    
    print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()
