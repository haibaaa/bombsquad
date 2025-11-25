"""Minesweeper TUI with Solver Panel (Game on Top + Solver Below)."""

import sys
import os
import time
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.text import Text
from rich.layout import Layout

from .game import Minesweeper, CellState, GameStatus

# Solver imports
from .solver.naive import naive_next_move
from .solver.grouping import grouping_next_move
from .solver.count import count_next_move
from .solver.csp import csp_next_move
from .solver.guess import guess_next_move

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

        # Key repeat tracking
        self.last_key = None
        self.last_key_time = 0
        self.key_repeat_delay = 0.3  # Initial delay before repeat starts
        self.key_repeat_interval = 0.05  # Interval between repeats

    # ------------------------------------------------------
    # Cell rendering
    # ------------------------------------------------------
    def get_cell_display(self, row: int, col: int, is_cursor: bool = False) -> Text:
        """Get the display representation of a cell."""
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
            symbol = "·"
            color = "white"
        else:
            value = self.game.get_cell_value(row, col)
            symbol = str(value) if value else "·"
            color = NUMBER_COLORS.get(value, "white")

        text = Text(f" {symbol} ", style=f"bold {color}")

        if is_cursor:
            text.stylize(f"reverse on {COLORS['yellow']}")

        return text

    def render_board(self) -> Panel:
        """Render the game board as a Rich Table.

        Returns:
            Table containing the game board
        """
        table = Table(
            show_header=True,
            box=None,
            padding=(0, 0),
            collapse_padding=True,
            pad_edge=False,
        )

        # Column labels
        table.add_column(" ", justify="center", width=2, no_wrap=True)
        for c in range(self.game.cols):
            table.add_column(
                Text(f"{c}", style=f"bold {COLORS['yellow']}"),
                justify="center",
                width=3,
                no_wrap=True,
            )

        # Rows with labels
        for r in range(self.game.rows):
            row_label = Text(f"{chr(ord('A') + r)}", style=f"bold {COLORS['yellow']}")
            row_cells = [row_label]

            for c in range(self.game.cols):
                is_cursor = r == self.cursor_row and c == self.cursor_col
                row_cells.append(self.get_cell_display(r, c, is_cursor))

            table.add_row(*row_cells)

        return Panel(
            table,
            border_style=COLORS["blue"],
            padding=(0, 1),
            expand=False,
        )

    # ------------------------------------------------------
    # Status
    # ------------------------------------------------------
    def render_status(self) -> Text:
        status = self.game.get_status()

        if status == GameStatus.PLAYING:
            remaining = self.game.mines - sum(sum(row) for row in self.game.flagged)
            msg = f"⚑ {remaining} | {to_coord(self.cursor_row, self.cursor_col)}"
            color = COLORS["mint"]
        elif status == GameStatus.WON:
            msg = "YOU WON! Press Q to quit."
            color = COLORS["mint"]
        else:  # LOST
            msg = "GAME OVER! Press Q to quit."
            color = COLORS["pink"]

        return Text(msg, style=f"bold {color}", justify="center")

    # ------------------------------------------------------
    # Instructions
    # ------------------------------------------------------
    def render_instructions(self) -> Text:
        t = Text()
        t.append("WASD:Move ", style=COLORS["peach"])
        t.append("E:Reveal ", style=COLORS["mint"])
        t.append("F:Flag ", style=COLORS["pink"])
        t.append("H:Solver ", style=COLORS["blue"])
        t.append("Q:Quit", style=COLORS["yellow"])
        return Align.center(t)

    # ------------------------------------------------------
    # UI layout
    # ------------------------------------------------------
    def render_ui(self):
        layout = Layout()

        # Create top section (game)
        top = Layout()
        top.split_column(
            Layout(name="header", size=1),
            Layout(name="board"),
            Layout(name="instructions", size=1),
        )
        top["header"].update(self.render_status())
        top["board"].update(Align.center(self.render_board()))
        top["instructions"].update(self.render_instructions())

        # Create bottom section (solver)
        solver_panel = Panel(
            Group(self.solver_text),
            title="solver",
            border_style=COLORS["pink"],
            padding=(1, 1),
            expand=True,
        )
        main_table.add_column(justify="center")

        # Split main layout vertically
        layout.split_column(
            Layout(top, name="game", ratio=2),
            Layout(solver_panel, name="solver", ratio=1),
        )

        return main_table

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
        self.solver_text = Text(f"strategy:\n", style="yellow")
        for cell, p in guess_list[:10]:
            self.solver_text.append(f"• {to_coord(*cell)} = {p*100:.1f}%\n")
        return

    # ------------------------------------------------------
    # Display solver results
    # ------------------------------------------------------
    def show_solver_result(self, strategy, safe, mines):
        self.solver_text = Text(f"strategy: {strategy}\n", style="cyan")

        if safe:
            self.solver_text.append("✔ Safe: ", style="green")
            safe_coords = [to_coord(r, c) for r, c in safe]
            self.solver_text.append(", ".join(safe_coords) + "\n", style="green")

        if mines:
            self.solver_text.append("💣 Mines: ", style="red")
            mine_coords = [to_coord(r, c) for r, c in mines]
            self.solver_text.append(", ".join(mine_coords) + "\n", style="red")

        if not safe and not mines:
            self.solver_text.append("⚠ No certain moves.\n", style="yellow")

        self.solver_text.append("Press H again after action.", style="dim")

    # ------------------------------------------------------
    # Input handling with key repeat
    # ------------------------------------------------------
    def handle_input(self, key, current_time):
        if key is None:
            return False

        # Don't process game moves if game is over
        if self.game.is_game_over() and key.lower() not in ("h", "q"):
            return False

        # Check if this is a repeatable key (movement keys)
        repeatable_keys = {"w", "s", "a", "d"}
        is_repeatable = key.lower() in repeatable_keys

        # Determine if we should process this key
        should_process = False

        if key != self.last_key:
            # New key pressed
            should_process = True
            self.last_key = key
            self.last_key_time = current_time
        elif is_repeatable:
            # Same repeatable key held down
            time_since_last = current_time - self.last_key_time

            # Check if enough time has passed for initial delay
            if self.last_key_time == current_time - time_since_last:  # First repeat
                if time_since_last >= self.key_repeat_delay:
                    should_process = True
                    self.last_key_time = current_time
            else:  # Subsequent repeats
                if time_since_last >= self.key_repeat_interval:
                    should_process = True
                    self.last_key_time = current_time
        else:
            # Non-repeatable key held down - only process once
            should_process = False

        if not should_process:
            return False

        # Process the key
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

    def run(self) -> None:
        """Run the main game loop."""
        old_settings = None

        try:
            # Platform-specific input handling setup
            if sys.platform == "win32":
                import msvcrt

                def get_key() -> str | None:
                    if msvcrt.kbhit():
                        return msvcrt.getch().decode("utf-8", errors="ignore")
                    return None

            else:
                import tty
                import termios
                import fcntl

                # Set terminal to raw mode ONCE before the loop
                old_settings = termios.tcgetattr(sys.stdin)
                tty.setcbreak(sys.stdin.fileno())

                def get_key() -> str | None:
                    # Use select to check if input is available (non-blocking)
                    if select.select([sys.stdin], [], [], 0)[0]:
                        return sys.stdin.read(1)
                    return None

            with Live(
                Align.center(self.render_ui()),
                console=self.console,
                refresh_per_second=10,  # Moderate refresh rate
                screen=True,  # Use screen mode to prevent stacking
                auto_refresh=False,  # Manual refresh control
            ) as live:
                last_seen_key = None
                key_held = False

                while self.running:
                    current_time = time.time()

                    # Get input (non-blocking)
                    key = get_key()

                    if key:
                        # Key is being pressed
                        last_seen_key = key
                        key_held = True

                        # Handle input and check if UI needs update
                        if self.handle_input(key, current_time):
                            live.update(self.render_ui(), refresh=True)
                    else:
                        # No key detected - key was released
                        if key_held:
                            # Key was just released, reset state
                            self.last_key = None
                            key_held = False

                        # Sleep briefly when no input
                        time.sleep(0.02)

        except KeyboardInterrupt:
            pass
        finally:
            # Restore terminal settings on Unix-like systems
            if sys.platform != "win32" and old_settings is not None:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            self.console.clear()


def main():
    console = Console()
    console.clear()

    console.print("[bold cyan]Welcome to Minesweeper with Solver![/bold cyan]")
    console.print("=" * 40)

    try:
        rows = int(input("Rows (default 10): ") or "10")
        cols = int(input("Cols (default 10): ") or "10")
        mines = int(input("Mines (default 15): ") or "15")
    except ValueError:
        console.print(
            "[yellow]Invalid input. Using defaults (10x10, 15 mines)[/yellow]"
        )
        rows, cols, mines = 10, 10, 15

    # Validate inputs
    if rows < 5 or cols < 5:
        console.print("[yellow]Board too small! Using minimum 5x5[/yellow]")
        rows, cols = max(5, rows), max(5, cols)

    if mines >= rows * cols:
        console.print("[yellow]Too many mines! Using maximum safe value[/yellow]")
        mines = (rows * cols) // 2

    console.print(
        f"\n[green]Starting game: {rows}x{cols} board with {mines} mines[/green]"
    )
    console.print("Loading...\n")
    time.sleep(1)

    tui = MinesweeperTUI(rows, cols, mines)
    tui.run()

    console.print("\n[cyan]Thanks for playing![/cyan]")


if __name__ == "__main__":
    main()
