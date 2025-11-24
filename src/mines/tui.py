"""Minesweeper TUI with Solver Panel (Left Game + Right Solver)."""

import sys
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.text import Text
from rich.layout import Layout

from .game import Minesweeper, CellState, GameStatus

# Solver imports
from naive import naive_next_move
from grouping import grouping_next_move
from count import count_next_move
from csp import csp_next_move
from guess import guess_next_move

# Pastel colors
COLORS = {
    "pink": "#ffb3ba",
    "peach": "#ffdfba",
    "yellow": "#ffffba",
    "mint": "#baffc9",
    "blue": "#bae1ff",
}

NUMBER_COLORS = {
    1: COLORS["blue"],
    2: COLORS["mint"],
    3: COLORS["peach"],
    4: COLORS["pink"],
    5: COLORS["yellow"],
    6: COLORS["blue"],
    7: COLORS["mint"],
    8: COLORS["peach"],
}


def to_coord(row, col):
    """Convert (row, col) to battleship style: A0, B3, etc."""
    return f"{chr(ord('A') + row)}{col}"


class MinesweeperTUI:
    def __init__(self, rows: int = 10, cols: int = 10, mines: int = 15) -> None:
        self.game = Minesweeper(rows, cols, mines)
        self.console = Console()
        self.cursor_row = 0
        self.cursor_col = 0
        self.running = True

        self.solver_text = Text("Press H for solver", style="white")

    # ------------------------------------------------------
    # Cell rendering
    # ------------------------------------------------------
    def get_cell_display(self, row: int, col: int, is_cursor: bool = False) -> Text:
        state = self.game.get_cell_state(row, col)

        if state == CellState.COVERED:
            symbol = "■"
            color = COLORS["mint"]
        elif state == CellState.FLAGGED:
            symbol = "⚑"
            color = COLORS["pink"]
        elif state == CellState.REVEALED_MINE:
            symbol = "💣"
            color = COLORS["peach"]
        elif state == CellState.REVEALED_EMPTY:
            symbol = " "
            color = "white"
        else:
            value = self.game.get_cell_value(row, col)
            symbol = str(value) if value else " "
            color = NUMBER_COLORS.get(value, "white")

        text = Text(f" {symbol} ", style=f"bold {color}")

        if is_cursor:
            text.stylize(f"reverse on {COLORS['yellow']}")

        return text

    # ------------------------------------------------------
    # Board rendering with labels
    # ------------------------------------------------------
    def render_board(self) -> Panel:
        table = Table(show_header=True, box=None, padding=(0, 0))

        # Column labels
        table.add_column(" ", justify="center", width=3)
        for c in range(self.game.cols):
            table.add_column(
                Text(f" {c} ", style=f"bold {COLORS['yellow']}"),
                justify="center",
                width=3,
            )

        # Rows with labels
        for r in range(self.game.rows):
            row_label = Text(f"{chr(ord('A') + r)}", style=f"bold {COLORS['yellow']}")
            row_cells = [row_label]

            for c in range(self.game.cols):
                is_cursor = (r == self.cursor_row and c == self.cursor_col)
                row_cells.append(self.get_cell_display(r, c, is_cursor))

            table.add_row(*row_cells)

        return Panel(Align.center(table), border_style=COLORS["blue"], padding=(1, 2))

    # ------------------------------------------------------
    # Status
    # ------------------------------------------------------
    def render_status(self) -> Text:
        status = self.game.get_status()

        if status == GameStatus.PLAYING:
            remaining = self.game.mines - sum(sum(row) for row in self.game.flagged)
            msg = f"⚑ Flags left: {remaining} | Cursor: {to_coord(self.cursor_row, self.cursor_col)}"
            color = COLORS["mint"]
        elif status == GameStatus.WON:
            msg = "🎉 YOU WON!"
            color = COLORS["mint"]
        else:
            msg = "💥 GAME OVER"
            color = COLORS["pink"]

        return Text(msg, style=f"bold {color}")

    # ------------------------------------------------------
    # Instructions
    # ------------------------------------------------------
    def render_instructions(self) -> Text:
        t = Text()
        t.append("[WASD] Move  ", style=COLORS["peach"])
        t.append("[E] Reveal  ", style=COLORS["mint"])
        t.append("[F] Flag  ", style=COLORS["pink"])
        t.append("[H] Solver  ", style=COLORS["blue"])
        t.append("[Q] Quit", style=COLORS["yellow"])
        return Align.center(t)

    # ------------------------------------------------------
    # UI layout
    # ------------------------------------------------------
    def render_ui(self):
        layout = Layout()
        layout.split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=1),
        )

        # LEFT side
        left = Layout()
        left.split_column(
            Layout(name="header", size=3),
            Layout(name="board"),
            Layout(name="instructions", size=3),
        )
        left["header"].update(Align.center(self.render_status()))
        left["board"].update(self.render_board())
        left["instructions"].update(self.render_instructions())
        layout["left"].update(left)

        # RIGHT side (solver)
        solver_panel = Panel(
            Group(self.solver_text),
            title="🧠 Solver",
            border_style=COLORS["pink"],
            padding=(1, 2),
        )
        layout["right"].update(solver_panel)

        return layout

    # ------------------------------------------------------
    # Full solver pipeline in one H press
    # ------------------------------------------------------
    def run_solver(self):
        board = self.game.board
        revealed = self.game.revealed
        flagged = self.game.flagged
        total_mines = self.game.mines

        # 1) Naive
        safe, mines = naive_next_move(board, revealed, flagged)
        if safe or mines:
            self.show_solver_result("Naive", safe, mines)
            return

        # 2) Grouping
        safe, mines = grouping_next_move(board, revealed, flagged)
        if safe or mines:
            self.show_solver_result("Grouping", safe, mines)
            return

        # 3) Count method
        safe = count_next_move(board, revealed, flagged, total_mines)
        if safe:
            self.show_solver_result("Count", safe, set())
            return

        # 4) CSP
        safe, mines, probs = csp_next_move(board, revealed, flagged)
        if safe or mines:
            self.show_solver_result("CSP", safe, mines)
            return

        # 5) Guessing
        guess_list = guess_next_move(probs)
        self.solver_text = Text(f"🤔 Guessing Strategy:\n", style="yellow")
        for (cell, p) in guess_list[:10]:
            self.solver_text.append(f"• {to_coord(*cell)} = {p*100:.1f}%\n")
        return

    # ------------------------------------------------------
    # Display solver results
    # ------------------------------------------------------
    def show_solver_result(self, strategy, safe, mines):
        self.solver_text = Text(f"🔎 Strategy Used: {strategy}\n\n", style="cyan")

        if safe:
            self.solver_text.append("✔ Safe Moves:\n", style="green")
            for (r, c) in safe:
                self.solver_text.append(f"  • {to_coord(r,c)}\n")

        if mines:
            self.solver_text.append("\n💣 Mines:\n", style="red")
            for (r, c) in mines:
                self.solver_text.append(f"  • {to_coord(r,c)}\n")

        if not safe and not mines:
            self.solver_text.append("\n⚠ No certain moves.\n", style="yellow")

        self.solver_text.append("\nPress H again after taking action.\n", style="cyan")

    # ------------------------------------------------------
    # Input handling (non blocking)
    # ------------------------------------------------------
    def handle_input(self, key):
        if key is None:
            return

        if key.lower() == "w":
            self.cursor_row = max(0, self.cursor_row - 1)
        elif key.lower() == "s":
            self.cursor_row = min(self.game.rows - 1, self.cursor_row + 1)
        elif key.lower() == "a":
            self.cursor_col = max(0, self.cursor_col - 1)
        elif key.lower() == "d":
            self.cursor_col = min(self.game.cols - 1, self.cursor_col + 1)
        elif key.lower() == "e":
            self.game.reveal(self.cursor_row, self.cursor_col)
        elif key.lower() == "f":
            self.game.flag(self.cursor_row, self.cursor_col)
        elif key.lower() == "h":
            self.run_solver()
        elif key.lower() == "q":
            self.running = False

    # ------------------------------------------------------
    # Main game loop
    # ------------------------------------------------------
    def run(self):
        try:
            if sys.platform != "win32":
                import tty, termios, select
                old = termios.tcgetattr(sys.stdin)

                def get_key():
                    tty.setcbreak(sys.stdin.fileno())
                    if select.select([sys.stdin], [], [], 0.05)[0]:
                        return sys.stdin.read(1)
                    return None
            else:
                import msvcrt

                def get_key():
                    if msvcrt.kbhit():
                        return msvcrt.getch().decode("utf-8")
                    return None

            with Live(self.render_ui(), refresh_per_second=20, screen=True) as live:
                while self.running:
                    key = get_key()
                    self.handle_input(key)
                    live.update(self.render_ui())

        finally:
            if sys.platform != "win32":
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old)
            self.console.clear()


def main():
    print("Welcome to Minesweeper!")
    print("=" * 40)

    try:
        rows = int(input("Rows (default 10): ") or "10")
        cols = int(input("Cols (default 10): ") or "10")
        mines = int(input("Mines (default 15): ") or "15")
    except:
        rows, cols, mines = 10, 10, 15

    tui = MinesweeperTUI(rows, cols, mines)
    tui.run()


if __name__ == "__main__":
    main()
