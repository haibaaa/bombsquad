# BombSquad

BombSquad is a Python-based Minesweeper solver implementing game logic, terminal user interface (TUI), and probabilistic solving algorithms to tackle Minesweeper puzzles.

## Features

- **TUI Interface**: Built with the Rich library for an interactive terminal-based Minesweeper experience, supporting cursor navigation and real-time board updates.
- **Solver Engine**: Applies constraint satisfaction and probabilistic deduction to reveal safe cells and flag mines, with planned winrate analysis and heatmap visualization.
- **Modular Design**: Separates game logic, interface, and solver components for easy extension and testing.

## Planned Roadmap

- Complete game logic implementation
- Enhance TUI (fix input lag, cursor visibility on revealed zeros)
- Refine solver (logic verification, winrate calculation, heatmap output)
- Generate technical report and presentation[1]

## Quick Start

1. Clone the repository: `git clone https://github.com/haibaaa/bombsquad.git`
2. Install dependencies with uv: `uv sync`
3. Run the game/solver: `uv run main.py`
