# src/mines/benchmark.py
import sys
import os

# Make sure package root is importable when running from src/mines/
_this_dir = os.path.dirname(__file__)  # .../src/mines
_pkg_root = os.path.abspath(os.path.join(_this_dir, ".."))  # .../src
if _pkg_root not in sys.path:
    sys.path.insert(0, _pkg_root)

# Try importing the pipeline in package form first, fallback to local
try:
    from mines.solver.guessing_benchmark import run_single_solve
except Exception:
    from solver.guessing_benchmark import run_single_solve


def benchmark(name, rows, cols, mines, games=100):
    wins = 0
    for i in range(1, games + 1):
        result = run_single_solve(rows, cols, mines)
        wins += 1 if result else 0
        print(f"{name} game {i}/{games} → {'WIN' if result else 'LOSE'}")

    print("\n========== RESULTS ==========")
    print(f"Difficulty: {name}")
    print(f"Wins: {wins}/{games}")
    print(f"Success Rate: {wins/games * 100:.2f}%")
    print("==============================\n")


if __name__ == "__main__":
    # Example runs — adjust game count as you like
    benchmark("BEGINNER", 9, 9, 10, games=1000)
    benchmark("INTERMEDIATE", 16, 16, 40, games=1000)
    benchmark("EXPERT", 16, 30, 99, games=1000)
