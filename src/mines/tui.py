"""Minesweeper TUI using Rich library."""

import sys
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.text import Text
from rich.layout import Layout
from .game import Minesweeper, CellState, GameStatus

# Pastel color palette
COLORS = {
    "pink": "#ffb3ba",
    "peach": "#ffdfba",
    "yellow": "#ffffba",
    "mint": "#baffc9",
    "blue": "#bae1ff",
}

# Color mapping for numbers (1-8)
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


class MinesweeperTUI:
    """Terminal UI for Minesweeper game."""

    def __init__(self, rows: int = 10, cols: int = 10, mines: int = 15) -> None:
        """Initialize the TUI.

        Args:
            rows: Number of rows in the grid
            cols: Number of columns in the grid
            mines: Number of mines to place
        """
        self.game = Minesweeper(rows, cols, mines)
        self.console = Console()
        self.cursor_row = 0
        self.cursor_col = 0
        self.running = True

    def get_cell_display(self, row: int, col: int, is_cursor: bool = False) -> Text:
        """Get the display representation of a cell.

        Args:
            row: Row index
            col: Column index
            is_cursor: Whether this is the cursor position

        Returns:
            Styled Text object for the cell
        """
        state = self.game.get_cell_state(row, col)

        # Base symbol
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
        else:  # REVEALED_NUMBER
            value = self.game.get_cell_value(row, col)
            symbol = str(value) if value else " "
            color = NUMBER_COLORS.get(value, "white")

        # Create text with styling
        text = Text(f" {symbol} ", style=f"bold {color}")

        # Add cursor highlight
        if is_cursor:
            text.stylize(f'reverse on {COLORS["yellow"]}')

        return text

    def render_board(self) -> Panel:
        """Render the game board as a Rich Table.

        Returns:
            Panel containing the game board
        """
        table = Table(
            show_header=False,
            show_edge=True,
            box=None,
            padding=(0, 0),
            collapse_padding=False,
            pad_edge=False,
        )

        # Add columns
        for _ in range(self.game.cols):
            table.add_column(justify="center", width=3)

        # Add rows
        for r in range(self.game.rows):
            row_cells = []
            for c in range(self.game.cols):
                is_cursor = r == self.cursor_row and c == self.cursor_col
                row_cells.append(self.get_cell_display(r, c, is_cursor))
            table.add_row(*row_cells)

        # Wrap in panel with border
        return Panel(
            Align.center(table),
            border_style=COLORS["blue"],
            padding=(1, 2),
        )

    def render_status(self) -> Text:
        """Render the game status message.

        Returns:
            Styled status text
        """
        status = self.game.get_status()

        if status == GameStatus.PLAYING:
            flags_remaining = self.game.mines - sum(
                sum(row) for row in self.game.flagged
            )
            msg = f"⚑ Flags: {flags_remaining} | Position: ({self.cursor_row}, {self.cursor_col})"
            color = COLORS["mint"]
        elif status == GameStatus.WON:
            msg = "🎉 YOU WON! Press Q to quit."
            color = COLORS["mint"]
        else:  # LOST
            msg = "💥 GAME OVER! Press Q to quit."
            color = COLORS["pink"]

        return Text(msg, style=f"bold {color}", justify="center")

    def render_instructions(self) -> Text:
        """Render control instructions.

        Returns:
            Styled instruction text
        """
        instructions = Text()
        instructions.append("Controls: ", style=f'bold {COLORS["blue"]}')
        instructions.append("[W/A/S/D] Move ", style=COLORS["peach"])
        instructions.append("[E] Reveal ", style=COLORS["mint"])
        instructions.append("[F] Flag ", style=COLORS["pink"])
        instructions.append("[Q] Quit", style=COLORS["yellow"])

        return Align.center(instructions)

    def render_ui(self) -> Layout:
        """Render the complete UI layout.

        Returns:
            Complete layout with all UI elements
        """
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="board"),
            Layout(name="instructions", size=3),
        )

        layout["header"].update(Align.center(self.render_status()))
        layout["board"].update(Align.center(self.render_board()))
        layout["instructions"].update(self.render_instructions())

        return layout

    def handle_input(self, key: str) -> None:
        """Handle keyboard input.

        Args:
            key: The pressed key
        """
        # Don't process game moves if game is over
        if self.game.is_game_over() and key.lower() != "q":
            return

        # Movement controls
        if key.lower() == "w":
            self.cursor_row = max(0, self.cursor_row - 1)
        elif key.lower() == "s":
            self.cursor_row = min(self.game.rows - 1, self.cursor_row + 1)
        elif key.lower() == "a":
            self.cursor_col = max(0, self.cursor_col - 1)
        elif key.lower() == "d":
            self.cursor_col = min(self.game.cols - 1, self.cursor_col + 1)

        # Action controls
        elif key.lower() == "e":
            self.game.reveal(self.cursor_row, self.cursor_col)
        elif key.lower() == "f":
            self.game.flag(self.cursor_row, self.cursor_col)

        # Quit
        elif key.lower() == "q":
            self.running = False

    def run(self) -> None:
        """Run the main game loop."""
        try:
            # Platform-specific input handling
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

                old_settings = termios.tcgetattr(sys.stdin)

                def get_key() -> str | None:
                    tty.setcbreak(sys.stdin.fileno())
                    if select.select([sys.stdin], [], [], 0.05)[0]:
                        return sys.stdin.read(1)
                    return None

            with Live(
                self.render_ui(),
                console=self.console,
                refresh_per_second=20,
                screen=True,
            ) as live:
                while self.running:
                    # Get input
                    key = get_key()
                    if key:
                        self.handle_input(key)

                    # Update display
                    live.update(self.render_ui())

        except KeyboardInterrupt:
            pass
        finally:
            if sys.platform != "win32":
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            self.console.clear()


def main() -> None:
    """Entry point for the game."""
    print("Welcome to Minesweeper!")
    print("=" * 40)

    # Get game parameters
    try:
        rows = int(input("Enter number of rows (default 10): ") or "10")
        cols = int(input("Enter number of columns (default 10): ") or "10")
        mines = int(input("Enter number of mines (default 15): ") or "15")
    except ValueError:
        print("Invalid input. Using default values (10x10, 15 mines)")
        rows, cols, mines = 10, 10, 15

    # Validate inputs
    if rows < 5 or cols < 5:
        print("Board too small! Using minimum 5x5")
        rows, cols = max(5, rows), max(5, cols)

    if mines >= rows * cols:
        print("Too many mines! Using maximum safe value")
        mines = (rows * cols) // 2

    print(f"\nStarting game: {rows}x{cols} board with {mines} mines")
    print("Loading...\n")

    # Start game
    tui = MinesweeperTUI(rows, cols, mines)
    tui.run()

    print("\nThanks for playing!")


if __name__ == "__main__":
    main()
