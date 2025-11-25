"""Learning system for AI to improve over time."""
import json
import os
from pathlib import Path

class AILearning:
    """Manages AI learning parameters and statistics."""
    
    def __init__(self, save_path: str = "ai_learning.json"):
        self.save_path = save_path
        self.stats = {
            "games_played": 0,
            "games_won": 0,
            "games_lost": 0,
            "total_moves": 0,
            "safe_moves": 0,
            "mine_hits": 0,
            "win_rate": 0.0,
        }
        
        # Learnable parameters
        self.params = {
            "danger_threshold": 0.7,  # When to mark as dangerous
            "flag_threshold": 0.95,   # When to auto-flag
            "constraint_weight_factor": 3.0,  # How much to weight constraints
            "risk_tolerance": 0.3,    # Max acceptable risk for a move
        }
        
        self.load()
    
    def load(self):
        """Load learning data from file."""
        if os.path.exists(self.save_path):
            try:
                with open(self.save_path, 'r') as f:
                    data = json.load(f)
                    self.stats.update(data.get('stats', {}))
                    self.params.update(data.get('params', {}))
            except Exception as e:
                print(f"Warning: Could not load AI learning data: {e}")
    
    def save(self):
        """Save learning data to file."""
        try:
            data = {
                'stats': self.stats,
                'params': self.params
            }
            with open(self.save_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save AI learning data: {e}")
    
    def record_move(self, was_safe: bool):
        """Record outcome of a move."""
        self.stats['total_moves'] += 1
        if was_safe:
            self.stats['safe_moves'] += 1
        else:
            self.stats['mine_hits'] += 1
    
    def record_game(self, won: bool, moves_made: int):
        """Record game outcome and adjust parameters."""
        self.stats['games_played'] += 1
        
        if won:
            self.stats['games_won'] += 1
            # Successful game - reinforce current strategy slightly
            self.params['risk_tolerance'] = min(0.5, self.params['risk_tolerance'] * 1.02)
        else:
            self.stats['games_lost'] += 1
            # Failed game - become more conservative
            self.params['risk_tolerance'] = max(0.1, self.params['risk_tolerance'] * 0.95)
            self.params['flag_threshold'] = max(0.85, self.params['flag_threshold'] - 0.01)
        
        # Update win rate
        self.stats['win_rate'] = self.stats['games_won'] / self.stats['games_played']
        
        # Adjust constraint weighting based on performance
        if self.stats['win_rate'] > 0.6:
            # Doing well - trust local constraints more
            self.params['constraint_weight_factor'] = min(5.0, self.params['constraint_weight_factor'] * 1.05)
        elif self.stats['win_rate'] < 0.3:
            # Doing poorly - balance more with global probability
            self.params['constraint_weight_factor'] = max(2.0, self.params['constraint_weight_factor'] * 0.95)
        
        self.save()
    
    def get_stats_display(self) -> str:
        """Get formatted statistics string."""
        if self.stats['games_played'] == 0:
            return "No games played yet"
        
        return (f"Games: {self.stats['games_played']} | "
                f"Wins: {self.stats['games_won']} | "
                f"Win Rate: {self.stats['win_rate']:.1%} | "
                f"Safe Moves: {self.stats['safe_moves']}/{self.stats['total_moves']}")
    
    def reset_stats(self):
        """Reset statistics (keep learned parameters)."""
        self.stats = {
            "games_played": 0,
            "games_won": 0,
            "games_lost": 0,
            "total_moves": 0,
            "safe_moves": 0,
            "mine_hits": 0,
            "win_rate": 0.0,
        }
        self.save()
