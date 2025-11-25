"""Minesweeper TUI with Professional Cell Styling and Refined Borders."""

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
from rich import box

from .game import Minesweeper, CellState, GameStatus

# Solver imports
from .solver.naive import naive_next_move
from .solver.grouping import grouping_next_move
from .solver.count import count_next_move
from .solver.csp import csp_next_move
from .solver.guess import guess_next_move

# Pastel colors
COLORS = {
    "lavender": "#dabfde",
    "red": "#ff6961",
    "pink": "#ffb3ba",
    "peach": "#ffdfba",
    "yellow": "#ffffba",
    "mint": "#baffc9",
    "blue": "#bae1ff",
    "cyan": "#b7fffa",
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
    # Cell rendering with professional backgrounds
    # ------------------------------------------------------
    def get_cell_display(self, row: int, col: int, is_cursor: bool = False) -> Text:
        """
        Render a cell with professional background styling.

        Background colors represent cell state:
        - COVERED: Mint (unopened tile aesthetic)
        - FLAGGED: Pink (flagged indicator)
        - REVEALED_MINE: Red (danger/warning)
        - REVEALED_EMPTY: Light neutral (#f5f5f5)
        - REVEALED_NUMBER: Off-white (#fafafa)

        Foreground colors:
        - Numbers: COLOR-CODED per NUMBER_COLORS
        - Flags: Dark red on pink
        - Mines: Yellow on red
        - Empty: Subtle gray dot

        Cursor highlighting uses reverse + yellow for visibility over any background.
        """
        state = self.game.get_cell_state(row, col)

        # Determine symbol and styling based on state
        if state == CellState.COVERED:
            symbol = " "
            bg_color = COLORS["mint"]
            fg_color = None
            bold = False

        elif state == CellState.FLAGGED:
            symbol = "⚑"
            bg_color = COLORS["pink"]
            fg_color = COLORS["red"]
            bold = True

        elif state == CellState.REVEALED_MINE:
            symbol = "☠︎︎"
            bg_color = COLORS["red"]
            fg_color = COLORS["yellow"]
            bold = True

        elif state == CellState.REVEALED_EMPTY:
            symbol = "·"
            bg_color = "#f5f5f5"
            fg_color = "#999999"
            bold = False

        else:  # REVEALED_NUMBER
            value = self.game.get_cell_value(row, col)
            symbol = str(value) if value else " "
            bg_color = "#fafafa"
            fg_color = NUMBER_COLORS.get(value, "white")
            bold = True

        # Build style string
        style_parts = []
        if bold:
            style_parts.append("bold")
        if fg_color:
            style_parts.append(fg_color)
        style_parts.append(f"on {bg_color}")
        style_str = " ".join(style_parts)

        # Create cell text with background
        text = Text(f" {symbol} ", style=style_str)

        # Apply cursor highlighting
        # reverse inverts the cell colors, then yellow background creates bright frame
        if is_cursor:
            text.stylize(f"reverse bold on {COLORS['yellow']}")

        return text

    # ------------------------------------------------------
    # Board rendering with thin cell separators
    # ------------------------------------------------------
    def render_board(self) -> Table:  # Change return type from Panel to Table
        table = Table(
            show_header=True,
            box=None,
            padding=(0, 0),
            collapse_padding=True,
            pad_edge=False,
        )

        # Column labels
        table.add_column(" ", justify="center", width=3, no_wrap=True)
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

        return table  # Just return table, no Panel wrapper

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
            msg = "you win"
            color = COLORS["mint"]
        else:
            msg = "you lose"
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
        """
        Render the full UI layout with game (top) and solver (bottom).

        Changes from original:
        - render_board() now returns bare Table (no Panel wrapper)
        - Game section displays table without surrounding border
        - Solver panel retains lavender border for visual hierarchy
        - Overall effect: cleaner board focus, solver clearly separated
        """
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

        # Create bottom section (solver) - KEEP panel border
        solver_panel = Panel(
            Group(self.solver_text),
            title="solver",
            border_style=COLORS["lavender"],
            padding=(1, 1),
            expand=True,
        )

        # Split main layout vertically
        layout.split_column(
            Layout(top, name="game", ratio=2),
            Layout(solver_panel, name="solver", ratio=1),
        )

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
            _ = self.solver_text.append("safe: ", style="green")
            safe_coords = [to_coord(r, c) for r, c in safe]
            _ = self.solver_text.append(", ".join(safe_coords) + "\n", style="green")

        if mines:
            _ = self.solver_text.append("mines: ", style="red")
            mine_coords = [to_coord(r, c) for r, c in mines]
            _ = self.solver_text.append(", ".join(mine_coords) + "\n", style="red")

        if not safe and not mines:
            _ = self.solver_text.append("no safe moves\n", style="yellow")

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

        return True

    # ------------------------------------------------------
    # Main game loop with optimizations
    # ------------------------------------------------------
    def run(self):
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
                import select

                # Set terminal to raw mode ONCE before the loop
                old_settings = termios.tcgetattr(sys.stdin)
                tty.setcbreak(sys.stdin.fileno())

                def get_key() -> str | None:
                    # Use select to check if input is available (non-blocking)
                    if select.select([sys.stdin], [], [], 0)[0]:
                        return sys.stdin.read(1)
                    return None

            with Live(
                self.render_ui(),
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

    console.print("[bold cyan]Minesweeper[/bold cyan]")
    console.print("=" * 40)

    try:
        rows = int(input("rows (default 10): ") or "10")
        cols = int(input("cols (default 10): ") or "10")
        mines = int(input("mines (default 15): ") or "15")
    except ValueError:
        console.print(
            "[yellow]invalid input. using defaults (10x10, 15 mines)[/yellow]"
        )
        rows, cols, mines = 10, 10, 15

    # Validate inputs
    if rows < 5 or cols < 5:
        console.print("[yellow]board too small! using minimum 5x5[/yellow]")
        rows, cols = max(5, rows), max(5, cols)

    if mines >= rows * cols:
        console.print("[yellow]too many mines! using maximum safe value[/yellow]")
        mines = (rows * cols) // 2

    console.print(
        f"\n[green]starting game: {rows}x{cols} board with {mines} mines[/green]"
    )
    console.print("Loading...\n")
    time.sleep(1)

    tui = MinesweeperTUI(rows, cols, mines)
    tui.run()


if __name__ == "__main__":
    main()
