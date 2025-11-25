"""Minesweeper TUI"""

import sys
import time
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.text import Text
from rich.layout import Layout
import termios
import tty
import select

from .game import Minesweeper, CellState, GameStatus

# Solver imports with type stubs
from .solver.naive import naive_next_move as naive_next_move
from .solver.grouping import grouping_next_move as grouping_next_move
from .solver.count import count_next_move as count_next_move
from .solver.csp import csp_next_move as csp_next_move
from .solver.guess import guess_next_move as guess_next_move

COLORS: dict[str, str] = {
    # Core neon palette colors
    "deep_navy": "#463F9E",  # Dark background base
    "darker_navy": "#2a2550",  # Even darker for contrast
    "hot_pink": "#F354A9",  # Vibrant pink/magenta
    "cyan": "#84F5D5",  # Bright cyan/aqua
    "light_purple": "#9B62E5",  # Mid-tone purple
    "dark_magenta": "#9D2EB0",  # Strong accent purple
    "neon_blue": "#5B9EFF",  # Bright blue variation
    "electric_pink": "#FF3EAD",  # Brighter pink
    "aqua_bright": "#00FFF7",  # Pure aqua
    "purple_pink": "#D946EF",  # Purple-pink blend
    "dim_cyan": "#4A7C8C",  # Dimmed cyan for subtle elements
    "neon_yellow": "#F5FF00",  # Neon yellow accent
    # Cell background colors - dark navy base with neon accents
    "bg_covered": "#3A3580",  # Dark navy with cyan tint
    "bg_flagged": "#F354A9",  # Hot pink
    "bg_mine": "#9D2EB0",  # Dark magenta
    "bg_empty": "#2e2860",  # Very dark navy
    "bg_number": "#363070",  # Dark navy base
    # CURSOR HIGHLIGHTING
    "bg_cursor_highlight": "#9B8FE8",  # Much lighter purple/lavender for visibility
    "border_cursor": "#84F5D5",  # Cyan border accent
    # Foreground colors for game elements
    "fg_flag": "#FFFFFF",  # White on hot pink bg
    "fg_mine": "#84F5D5",  # Cyan bomb
    "fg_empty": "#4A7C8C",  # Dim cyan dot
    # Number colors - each gets unique neon color for maximum differentiation
    "fg_number_1": "#84F5D5",  # Cyan
    "fg_number_2": "#9B62E5",  # Light purple
    "fg_number_3": "#F354A9",  # Hot pink
    "fg_number_4": "#00FFF7",  # Aqua bright
    "fg_number_5": "#FF3EAD",  # Electric pink
    "fg_number_6": "#D946EF",  # Purple-pink blend
    "fg_number_7": "#5B9EFF",  # Neon blue
    "fg_number_8": "#9D2EB0",  # Dark magenta
    # UI element colors
    "border_solver": "#9B62E5",  # Light purple
    "text_status_playing": "#84F5D5",  # Cyan
    "text_status_won": "#9B62E5",  # Light purple
    "text_status_lost": "#F354A9",  # Hot pink
    "text_column_label": "#84F5D5",  # Cyan
    "text_row_label": "#84F5D5",  # Cyan
    "text_move": "#84F5D5",  # Cyan
    "text_reveal": "#9B62E5",  # Light purple
    "text_flag": "#F354A9",  # Hot pink
    "text_solver": "#9B62E5",  # Light purple
    "text_quit": "#F354A9",  # Hot pink
    # Solver result colors
    "safe_text": "#84F5D5",  # Cyan
    "mines_text": "#F354A9",  # Hot pink
    "strategy_text": "#9B62E5",  # Light purple
    "guess_text": "#F5FF00",  # Neon yellow
    "error_text": "#F354A9",  # Hot pink
}

# Map number to color key
NUMBER_COLOR_MAP: dict[int, str] = {
    1: "fg_number_1",
    2: "fg_number_2",
    3: "fg_number_3",
    4: "fg_number_4",
    5: "fg_number_5",
    6: "fg_number_6",
    7: "fg_number_7",
    8: "fg_number_8",
}


def to_coord(row: int, col: int) -> str:
    """Convert (row, col) to battleship style: A0, B3, etc."""
    return f"{chr(ord('A') + row)}{col}"


class MinesweeperTUI:
    def __init__(self, rows: int = 10, cols: int = 10, mines: int = 15) -> None:
        self.game: Minesweeper = Minesweeper(rows, cols, mines)
        self.console: Console = Console()
        self.cursor_row: int = 0
        self.cursor_col: int = 0
        self.running: bool = True

        self.solver_text: Text = Text(
            "Press H for solver", style=f"bold {COLORS['light_purple']}"
        )

        # Key repeat tracking
        self.last_key: str | None = None
        self.last_key_time: float = 0.0
        self.key_repeat_delay: float = 0.3
        self.key_repeat_interval: float = 0.05

    def get_cell_display(self, row: int, col: int, is_cursor: bool = False) -> Text:
        """
        Render a cell with neon vaporwave styling.

        CRITICAL FIX: When is_cursor=True, use a much lighter background color
        to ensure cursor is always visible on any cell state.
        """
        state: CellState = self.game.get_cell_state(row, col)

        # Determine symbol and styling based on state
        symbol: str
        bg_color: str
        fg_color: str | None
        bold: bool

        if state == CellState.COVERED:
            symbol = " "
            bg_color = COLORS["bg_covered"]
            fg_color = None
            bold = False

        elif state == CellState.FLAGGED:
            symbol = "⚑"
            bg_color = COLORS["bg_flagged"]
            fg_color = COLORS["fg_flag"]
            bold = True

        elif state == CellState.REVEALED_MINE:
            symbol = "☠︎︎"
            bg_color = COLORS["bg_mine"]
            fg_color = COLORS["fg_mine"]
            bold = True

        elif state == CellState.REVEALED_EMPTY:
            symbol = "·"
            bg_color = COLORS["bg_empty"]
            fg_color = COLORS["fg_empty"]
            bold = False

        else:  # REVEALED_NUMBER
            value: int | None = self.game.get_cell_value(row, col)
            symbol = str(value) if value else " "
            bg_color = COLORS["bg_number"]
            color_key: str = NUMBER_COLOR_MAP.get(value or 0, COLORS["cyan"])
            fg_color = COLORS.get(color_key, COLORS["cyan"])
            bold = True

        # CURSOR
        if is_cursor:
            bg_color = COLORS["bg_cursor_highlight"]
            bold = True  # Ensure cursor cell content is always bold

        # Build style string
        style_parts: list[str] = []
        if bold:
            style_parts.append("bold")
        if fg_color:
            style_parts.append(fg_color)
        style_parts.append(f"on {bg_color}")
        style_str: str = " ".join(style_parts)

        # Create cell text with styled background
        text: Text = Text(f" {symbol} ", style=style_str)

        # Optional: Add cyan border effect for extra cursor visibility
        if is_cursor:
            # Add subtle border styling using box drawing characters
            text = (
                Text("█", style=f"bold {COLORS['border_cursor']}")
                + text
                + Text("█", style=f"bold {COLORS['border_cursor']}")
            )

        return text

    def render_board(self) -> Table:
        """Render the game board as a Rich Table with neon styling."""
        table: Table = Table(
            show_header=True,
            box=None,
            padding=(0, 0),
            collapse_padding=True,
            pad_edge=False,
        )

        # Column labels - neon cyan
        table.add_column(" ", justify="center", width=3, no_wrap=True)
        for c in range(self.game.cols):
            table.add_column(
                Text(f"{c}", style=f"bold {COLORS['text_column_label']}"),
                justify="center",
                width=5 if c == self.cursor_col else 3,  # Wider for cursor column
                no_wrap=True,
            )

        # Rows with labels - neon cyan
        for r in range(self.game.rows):
            row_label: Text = Text(
                f"{chr(ord('A') + r)}", style=f"bold {COLORS['text_row_label']}"
            )
            row_cells: list[Text] = [row_label]

            for c in range(self.game.cols):
                is_cursor_pos: bool = r == self.cursor_row and c == self.cursor_col
                row_cells.append(self.get_cell_display(r, c, is_cursor_pos))

            table.add_row(*row_cells)

        return table

    def render_status(self) -> Text:
        """Render the game status line with vibrant neon colors."""
        status: GameStatus = self.game.get_status()

        if status == GameStatus.PLAYING:
            remaining: int = self.game.mines - sum(
                sum(row) for row in self.game.flagged
            )
            msg: str = f"⚑ {remaining} | {to_coord(self.cursor_row, self.cursor_col)}"
            color: str = COLORS["text_status_playing"]
        elif status == GameStatus.WON:
            msg = "★ YOU WIN ★"
            color = COLORS["text_status_won"]
        else:
            msg = "☠ YOU LOSE ☠"
            color = COLORS["text_status_lost"]

        return Text(msg, style=f"bold {color}", justify="center")

    def render_instructions(self) -> Align:
        """Render the instruction line with rotating neon colors."""
        t: Text = Text()
        _ = t.append("WASD:Move ", style=f"bold {COLORS['text_move']}")
        _ = t.append("E:Reveal ", style=f"bold {COLORS['text_reveal']}")
        _ = t.append("F:Flag ", style=f"bold {COLORS['text_flag']}")
        _ = t.append("H:Solver ", style=f"bold {COLORS['text_solver']}")
        _ = t.append("Q:Quit", style=f"bold {COLORS['text_quit']}")
        return Align.center(t)

    def render_ui(self) -> Layout:
        """Render the full UI layout with neon vaporwave styling."""
        layout: Layout = Layout()

        # Create top section (game)
        top: Layout = Layout()
        top.split_column(
            Layout(name="header", size=1),
            Layout(name="board"),
            Layout(name="instructions", size=1),
        )
        top["header"].update(self.render_status())
        top["board"].update(Align.center(self.render_board()))
        top["instructions"].update(self.render_instructions())

        # Create bottom section (solver) with light purple border
        solver_panel: Panel = Panel(
            Group(self.solver_text),
            title="◈ solver ◈",
            title_align="center",
            border_style=f"bold {COLORS['border_solver']}",
            padding=(1, 1),
            expand=True,
        )

        # Split main layout vertically
        layout.split_column(
            Layout(top, name="game", ratio=2),
            Layout(solver_panel, name="solver", ratio=1),
        )

        return layout

    def run_solver(self) -> None:
        """Run the solver pipeline through all strategies."""
        board = self.game.board
        revealed = self.game.revealed
        flagged = self.game.flagged
        total_mines: int = self.game.mines

        # 1) Naive
        safe, mines = naive_next_move(board, revealed, flagged)
        if safe or mines:
            _ = self.show_solver_result("naive", safe, mines)
            return

        # 2) Grouping
        safe, mines = grouping_next_move(board, revealed, flagged)
        if safe or mines:
            _ = self.show_solver_result("grouping", safe, mines)
            return

        # 3) count method
        safe = count_next_move(board, revealed, flagged, total_mines)
        if safe:
            _ = self.show_solver_result("count", safe, set())
            return

        # 4) CSP
        safe, mines, probs = csp_next_move(board, revealed, flagged)
        if safe or mines:
            _ = self.show_solver_result("csp", safe, mines)
            return

        # 5) Guessing
        guess_list = guess_next_move(probs)
        _ = self.solver_text = Text("strategy: ", style=f"bold {COLORS['guess_text']}")
        _ = self.solver_text.append(
            "probability guess\n", style=f"bold {COLORS['guess_text']}"
        )
        for cell, p in guess_list[:10]:
            _ = self.solver_text.append(
                f"▸ {to_coord(*cell)} = {p*100:.1f}%\n", style=f"bold {COLORS['cyan']}"
            )

    def show_solver_result(
        self, strategy: str, safe: set[tuple[int, int]], mines: set[tuple[int, int]]
    ) -> None:
        """Display solver strategy and results with neon styling."""
        self.solver_text = Text(
            f"strategy: {strategy}\n", style=f"bold {COLORS['strategy_text']}"
        )

        if safe:
            _ = self.solver_text.append("safe: ", style=f"bold {COLORS['safe_text']}")
            safe_coords: list[str] = [to_coord(r, c) for r, c in safe]
            _ = self.solver_text.append(
                ", ".join(safe_coords) + "\n", style=f"bold {COLORS['safe_text']}"
            )

        if mines:
            _ = self.solver_text.append("mines: ", style=f"bold {COLORS['mines_text']}")
            mine_coords: list[str] = [to_coord(r, c) for r, c in mines]
            _ = self.solver_text.append(
                ", ".join(mine_coords) + "\n", style=f"bold {COLORS['mines_text']}"
            )

        if not safe and not mines:
            _ = self.solver_text.append(
                "no safe moves\n", style=f"bold {COLORS['guess_text']}"
            )

    def handle_input(self, key: str, current_time: float) -> bool:
        """Handle keyboard input with key repeat support."""
        if key is None:
            return False

        # Don't process game moves if game is over
        if self.game.is_game_over() and key.lower() not in ("h", "q"):
            return False

        # Check if this is a repeatable key (movement keys)
        repeatable_keys: set[str] = {"w", "s", "a", "d"}
        is_repeatable: bool = key.lower() in repeatable_keys

        # Determine if we should process this key
        should_process: bool = False

        if key != self.last_key:
            should_process = True
            self.last_key = key
            self.last_key_time = current_time
        elif is_repeatable:
            time_since_last: float = current_time - self.last_key_time
            if time_since_last >= self.key_repeat_delay:
                should_process = True
                self.last_key_time = current_time
        else:
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

    def run(self) -> None:
        """Run the main game loop."""
        old_settings: list[int | list[bytes | int]] | None = None

        try:
            # Platform-specific input handling setup
            if sys.platform == "win32":
                import msvcrt

                def get_key() -> str | None:
                    if msvcrt.kbhit():
                        return msvcrt.getch().decode("utf-8", errors="ignore")
                    return None

            else:
                old_settings = termios.tcgetattr(sys.stdin)
                tty.setcbreak(sys.stdin.fileno())

                def get_key() -> str | None:
                    if select.select([sys.stdin], [], [], 0)[0]:
                        return sys.stdin.read(1)
                    return None

            with Live(
                self.render_ui(),
                console=self.console,
                refresh_per_second=10,
                screen=True,
                auto_refresh=False,
            ) as live:
                key_held: bool = False

                while self.running:
                    current_time: float = time.time()
                    key: str | None = get_key()

                    if key:
                        key_held = True
                        if self.handle_input(key, current_time):
                            live.update(self.render_ui(), refresh=True)
                    else:
                        if key_held:
                            self.last_key = None
                            key_held = False
                        time.sleep(0.02)

        except KeyboardInterrupt:
            pass
        finally:
            if sys.platform != "win32" and old_settings is not None:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            self.console.clear()


def main() -> None:
    """Main entry point for the game."""
    console: Console = Console()
    console.clear()

    console.print(
        f"[bold {COLORS['hot_pink']}]◈ MINESWEEPER ◈[/bold {COLORS['hot_pink']}]"
    )
    console.print(f"[{COLORS['cyan']}]" + "═" * 40 + f"[/{COLORS['cyan']}]")

    try:
        rows: int = int(input("rows (default 10): ") or "10")
        cols: int = int(input("cols (default 10): ") or "10")
        mines: int = int(input("mines (default 15): ") or "15")
    except ValueError:
        console.print(
            f"[bold {COLORS['error_text']}]invalid input. using defaults (10x10, 15 mines)[/bold {COLORS['error_text']}]"
        )
        rows, cols, mines = 10, 10, 15

    # Validate inputs
    if rows < 5 or cols < 5:
        console.print(
            f"[bold {COLORS['error_text']}]board too small! using minimum 5x5[/bold {COLORS['error_text']}]"
        )
        rows, cols = max(5, rows), max(5, cols)

    if mines >= rows * cols:
        console.print(
            f"[bold {COLORS['error_text']}]too many mines! using maximum safe value[/bold {COLORS['error_text']}]"
        )
        mines = (rows * cols) // 2

    console.print(
        f"\n[bold {COLORS['cyan']}]▸ STARTING GAME: {rows}x{cols} board with {mines} mines[/bold {COLORS['cyan']}]"
    )
    console.print(f"[{COLORS['light_purple']}]Loading...[/{COLORS['light_purple']}]\n")
    time.sleep(1)

    tui: MinesweeperTUI = MinesweeperTUI(rows, cols, mines)
    tui.run()


if __name__ == "__main__":
    main()
