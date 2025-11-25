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

# Solver imports
from .solver.naive import naive_next_move
from .solver.grouping import grouping_next_move
from .solver.count import count_next_move
from .solver.csp import csp_next_move
from .solver.guess import guess_next_move
from .solver.csp import extract_groups

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
NUMBER_COLOR_MAP = {
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
    return f"{chr(ord('A') + row)}{col}"


# =============================================================================
# MAIN TUI CLASS
# =============================================================================

class MinesweeperTUI:
    def __init__(self, rows=10, cols=10, mines=15):
        self.game = Minesweeper(rows, cols, mines)
        self.console = Console()
        self.cursor_row = 0
        self.cursor_col = 0
        self.running = True

        self.solver_text = Text(
            "Press H for solver", style=f"bold {COLORS['light_purple']}"
        )

        self.last_key = None
        self.last_key_time = 0
        self.key_repeat_delay = 0.3

    # -------------------------------------------------------------

    def get_cell_display(self, row, col, is_cursor=False) -> Text:
        state = self.game.get_cell_state(row, col)

        if state == CellState.COVERED:
            symbol, bg, fg, bold = " ", COLORS["bg_covered"], None, False
        elif state == CellState.FLAGGED:
            symbol, bg, fg, bold = "⚑", COLORS["bg_flagged"], COLORS["fg_flag"], True
        elif state == CellState.REVEALED_MINE:
            symbol, bg, fg, bold = "☠", COLORS["bg_mine"], COLORS["fg_mine"], True
        elif state == CellState.REVEALED_EMPTY:
            symbol, bg, fg, bold = "·", COLORS["bg_empty"], COLORS["fg_empty"], False
        else:
            value = self.game.get_cell_value(row, col)
            symbol = str(value)
            bg = COLORS["bg_number"]
            fg = COLORS[NUMBER_COLOR_MAP[value]]
            bold = True

        if is_cursor:
            bg = COLORS["bg_cursor_highlight"]
            bold = True

        style = []
        if bold:
            style.append("bold")
        if fg:
            style.append(fg)
        style.append(f"on {bg}")

        text = Text(f" {symbol} ", style=" ".join(style))

        if is_cursor:
            text = (
                Text("█", style=f"bold {COLORS['border_cursor']}")
                + text
                + Text("█", style=f"bold {COLORS['border_cursor']}")
            )

        return text

    # -------------------------------------------------------------

    def render_board(self) -> Table:
        table = Table(show_header=True, box=None, padding=(0, 0))

        table.add_column(" ", justify="center", width=3)
        for c in range(self.game.cols):
            table.add_column(
                Text(f"{c}", style=f"bold {COLORS['text_column_label']}"),
                justify="center", width=5 if c == self.cursor_col else 3
            )

        for r in range(self.game.rows):
            row_label = Text(
                f"{chr(ord('A') + r)}",
                style=f"bold {COLORS['text_row_label']}"
            )

            row_cells = [row_label]

            for c in range(self.game.cols):
                row_cells.append(
                    self.get_cell_display(r, c, r == self.cursor_row and c == self.cursor_col)
                )

            table.add_row(*row_cells)

        return table

    # -------------------------------------------------------------

    def render_status(self) -> Text:
        status = self.game.get_status()

        if status == GameStatus.PLAYING:
            remaining = self.game.mines - sum(sum(r) for r in self.game.flagged)
            return Text(
                f"⚑ {remaining} | {to_coord(self.cursor_row, self.cursor_col)}",
                style=f"bold {COLORS['text_status_playing']}",
            )

        elif status == GameStatus.WON:
            return Text("★ YOU WIN ★", style=f"bold {COLORS['text_status_won']}")

        else:
            return Text("☠ YOU LOSE ☠", style=f"bold {COLORS['text_status_lost']}")

    # -------------------------------------------------------------

    def render_instructions(self):
        t = Text()
        t.append("WASD:Move ", style=f"bold {COLORS['text_move']}")
        t.append("E:Reveal ", style=f"bold {COLORS['text_reveal']}")
        t.append("F:Flag ", style=f"bold {COLORS['text_flag']}")
        t.append("H:Solver ", style=f"bold {COLORS['text_solver']}")
        t.append("C:Auto ", style=f"bold {COLORS['text_solver']}")
        t.append("Q:Quit", style=f"bold {COLORS['text_quit']}")
        return Align.center(t)

    # -------------------------------------------------------------

    def render_ui(self) -> Layout:
        layout = Layout()

        top = Layout()
        top.split_column(
            Layout(name="header", size=1),
            Layout(name="board"),
            Layout(name="instructions", size=1),
        )
        top["header"].update(self.render_status())
        top["board"].update(Align.center(self.render_board()))
        top["instructions"].update(self.render_instructions())

        solver_panel = Panel(
            Group(self.solver_text),
            title="◈ solver ◈",
            border_style=f"bold {COLORS['border_solver']}",
            padding=(1, 1),
        )

        layout.split_column(
            Layout(top, ratio=2),
            Layout(solver_panel, ratio=1),
        )

        return layout

    # =============================================================================
    # SOLVER FUNCTIONS
    # =============================================================================

    def run_solver(self):
        board = self.game.board
        rev = self.game.revealed
        flag = self.game.flagged
        total_mines = self.game.mines

        safe, mines = naive_next_move(board, rev, flag)
        if safe or mines:
            self.show_solver_result("naive", safe, mines)
            return

        safe, mines = grouping_next_move(board, rev, flag)
        if safe or mines:
            self.show_solver_result("grouping", safe, mines)
            return

        safe = count_next_move(board, rev, flag, total_mines)
        if safe:
            self.show_solver_result("count", safe, set())
            return
        
        # -----------------------------
        # 4) CSP Solver
        # -----------------------------
        safe, mines, probs = csp_next_move(board, rev, flag)
        if safe or mines:
            self.show_solver_result("csp", safe, mines)
            return

        # ============================================================
        # 5) Fallback Probability Handling (CSP too big / empty)
        # ============================================================

        # --- Hidden cells list ---
        hidden_cells = [
            (r, c)
            for r in range(self.game.rows)
            for c in range(self.game.cols)
            if not rev[r][c] and not flag[r][c]
        ]

        flagged_count = sum(sum(row) for row in flag)
        remaining_mines = total_mines - flagged_count

        # --- If CSP probability dictionary is empty, assign uniform probability ---
        if not probs:
            if len(hidden_cells) > 0:
                uniform_p = remaining_mines / len(hidden_cells)
                probs = {cell: uniform_p for cell in hidden_cells}

        # ============================================================
        # 6) Compute REST-REGION PROBABILITY
        # ============================================================

       # 6) Identify constrained vs unconstrained cells
        constrained_cells = set()
        for g in extract_groups(board, rev, flag):
            constrained_cells |= g.cells

        unconstrained_cells = set(hidden_cells) - constrained_cells

        # --- Expected mines in CSP frontier ---
        committed_mines = sum(probs.values()) if probs else 0

        remaining_unconstrained_mines = max(
            0,
            remaining_mines - committed_mines
        )

        if len(unconstrained_cells) > 0:
            rest_probability = remaining_unconstrained_mines / len(unconstrained_cells)
        else:
            rest_probability = None

        # ============================================================
        # 7) GUESS LIST (sorted by lowest mine chance)
        # ============================================================

        guess_list = guess_next_move(probs)     # List[(cell, prob)]

        self.solver_text = Text(
            "No safe deterministic moves.\nBest guess squares:\n",
            style=f"bold {COLORS['guess_text']}"
        )

        # Show top 8 guesses
        for cell, p in guess_list[:8]:
            self.solver_text.append(
                f"▸ {to_coord(*cell)} = {p*100:.1f}%\n",
                style=f"{COLORS['cyan']}"
            )

        # --- Show rest-probability ---
        if rest_probability is not None:
            self.solver_text.append(
                f"\nRest-region probability (isolated cells): {rest_probability*100:.2f}%\n",
                style=f"bold {COLORS['neon_yellow']}"
            )

        return


        # self.solver_text = Text("no safe moves", style=f"bold {COLORS['guess_text']}")

    # -------------------------------------------------------------

    def apply_solver_moves(self):
        """Auto mode: apply reveal/flag operations."""
        board = self.game.board
        rev = self.game.revealed
        flag = self.game.flagged
        total_mines = self.game.mines

        safe, mines = naive_next_move(board, rev, flag)
        if safe or mines:
            self._apply_moves("naive", safe, mines)
            return

        safe, mines = grouping_next_move(board, rev, flag)
        if safe or mines:
            self._apply_moves("grouping", safe, mines)
            return

        safe = count_next_move(board, rev, flag, total_mines)
        if safe:
            self._apply_moves("count", safe, set())
            return

        self.solver_text = Text(
            "strategy: no automatic moves", style=f"bold {COLORS['error_text']}"
        )

    # -------------------------------------------------------------

    def _apply_moves(self, strategy: str, safe, mines):
        self.show_solver_result(strategy, safe, mines)

        for r, c in safe:
            self.game.reveal(r, c)

        for r, c in mines:
            self.game.flag(r, c)

    # -------------------------------------------------------------

    def show_solver_result(self, strategy, safe, mines):
        t = Text(f"strategy: {strategy}\n", style=f"bold {COLORS['strategy_text']}")

        if safe:
            t.append("safe: ", style=f"bold {COLORS['safe_text']}")
            t.append(", ".join(to_coord(r, c) for r, c in safe) + "\n",
                     style=f"bold {COLORS['safe_text']}")

        if mines:
            t.append("mines: ", style=f"bold {COLORS['mines_text']}")
            t.append(", ".join(to_coord(r, c) for r, c in mines) + "\n",
                     style=f"bold {COLORS['mines_text']}")

        if not safe and not mines:
            t.append("no safe moves\n", style=f"bold {COLORS['guess_text']}")

        self.solver_text = t

    # =============================================================================
    # INPUT HANDLING
    # =============================================================================

    def handle_input(self, key: str, now: float):
        if key is None:
            return False

        if self.game.is_game_over() and key.lower() not in ("h", "c", "q"):
            return False

        process = False

        if key != self.last_key:
            process = True
            self.last_key = key
            self.last_key_time = now
        elif key.lower() in {"w", "a", "s", "d"}:
            if now - self.last_key_time >= self.key_repeat_delay:
                process = True
                self.last_key_time = now

        if not process:
            return False

        # Movement and game actions
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
        elif key.lower() == "c":
            self.apply_solver_moves()
        elif key.lower() == "q":
            self.running = False

        return True

    # =============================================================================
    # GAME LOOP
    # =============================================================================

    def run(self):
        old_settings = None

        try:
            if sys.platform == "win32":
                import msvcrt

                def get_key():
                    return msvcrt.getch().decode() if msvcrt.kbhit() else None

            else:
                old_settings = termios.tcgetattr(sys.stdin)
                tty.setcbreak(sys.stdin.fileno())

                def get_key():
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

                held = False

                while self.running:
                    now = time.time()
                    key = get_key()

                    if key:
                        held = True
                        if self.handle_input(key, now):
                            live.update(self.render_ui(), refresh=True)
                    else:
                        if held:
                            self.last_key = None
                            held = False
                        time.sleep(0.02)

        finally:
            if sys.platform != "win32" and old_settings is not None:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            self.console.clear()


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    console = Console()
    console.clear()

    console.print(f"[bold {COLORS['hot_pink']}]◈ MINESWEEPER ◈[/]")
    console.print(f"[{COLORS['cyan']}]{'═'*40}[/]")

    try:
        rows = int(input("rows (default 10): ") or "10")
        cols = int(input("cols (default 10): ") or "10")
        mines = int(input("mines (default 15): ") or "15")
    except ValueError:
        console.print(
            f"[bold {COLORS['error_text']}]invalid input. using defaults[/]"
        )
        rows, cols, mines = 10, 10, 15

    if rows < 5 or cols < 5:
        console.print(
            f"[bold {COLORS['error_text']}]board too small! using minimum 5x5[/]"
        )
        rows = max(rows, 5)
        cols = max(cols, 5)

    if mines >= rows * cols:
        console.print(
            f"[bold {COLORS['error_text']}]too many mines! lowering mine count[/]"
        )
        mines = (rows * cols) // 2

    console.print(
        f"[bold {COLORS['cyan']}]▸ STARTING {rows}x{cols} WITH {mines} MINES[/]"
    )

    time.sleep(0.5)

    tui = MinesweeperTUI(rows, cols, mines)
    tui.run()


if __name__ == "__main__":
    main()