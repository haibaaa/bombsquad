"""Minesweeper TUI application using Textual."""

from textual.app import App, ComposeResult
from textual.widgets import Static, Label
from textual.containers import Center, Vertical
from textual.reactive import reactive
from textual import events
from rich.text import Text
from rich.style import Style

from src.mines.game import Minesweeper, CellState, GameStatus


class GameBoard(Static):
    """Reactive game board widget."""

    cursor_row = reactive(0)
    cursor_col = reactive(0)
    game_state = reactive({})

    def __init__(self, game: Minesweeper):
        super().__init__()
        self.game = game
        self.update_game_state()

    def update_game_state(self):
        """Update the reactive game state."""
        self.game_state = self.game.get_board_state()

    def watch_cursor_row(self, old_value: int, new_value: int) -> None:
        """React to cursor row changes."""
        self.refresh()

    def watch_cursor_col(self, old_value: int, new_value: int) -> None:
        """React to cursor column changes."""
        self.refresh()

    def watch_game_state(self, old_value: dict, new_value: dict) -> None:
        """React to game state changes."""
        self.refresh()

    def render(self) -> Text:
        """Render the game board."""
        text = Text()
        cells = self.game_state.get("cells", [])

        for r, row in enumerate(cells):
            for c, cell in enumerate(row):
                is_cursor = r == self.cursor_row and c == self.cursor_col
                cell_text = self._render_cell(cell, is_cursor)
                text.append(cell_text)
                text.append(" ")
            text.append("\n")

        return text

    def _render_cell(self, cell: dict, is_cursor: bool) -> Text:
        """Render a single cell."""
        state = cell["state"]
        value = cell["value"]

        # Pastel color palette
        PASTEL_BLUE = "#AEC6CF"
        PASTEL_GREEN = "#B2E0B2"
        PASTEL_YELLOW = "#FFFACD"
        PASTEL_ORANGE = "#FFD9B3"
        PASTEL_RED = "#FFB3BA"
        PASTEL_PURPLE = "#E0BBE4"
        PASTEL_PINK = "#FFC0CB"
        PASTEL_GRAY = "#D3D3D3"
        PASTEL_DARK = "#B0B0B0"

        # Number colors (progressively darker pastels)
        number_colors = {
            1: PASTEL_BLUE,
            2: PASTEL_GREEN,
            3: PASTEL_YELLOW,
            4: PASTEL_ORANGE,
            5: PASTEL_RED,
            6: PASTEL_PURPLE,
            7: PASTEL_PINK,
            8: PASTEL_DARK,
        }

        if state == CellState.COVERED:
            char = "▪"
            color = PASTEL_GRAY
        elif state == CellState.FLAGGED:
            char = "F"
            color = PASTEL_YELLOW
        elif state == CellState.REVEALED_MINE:
            char = "M"
            color = PASTEL_RED
        elif state == CellState.REVEALED_EMPTY:
            char = " "
            color = "white"
        elif state == CellState.REVEALED_NUMBER:
            char = str(value)
            color = number_colors.get(value, "white")
        else:
            char = "?"
            color = "white"

        # Add cursor highlight
        if is_cursor:
            style = Style(color=color, bold=True, reverse=True)
        else:
            style = Style(color=color)

        return Text(char, style=style)


class StatusBar(Static):
    """Status bar showing game information."""

    status_text = reactive("")

    def watch_status_text(self, old_value: str, new_value: str) -> None:
        """React to status text changes."""
        self.update(new_value)


class MinesweeperApp(App):
    """Minesweeper TUI application."""

    CSS = """
    Screen {
        align: center middle;
        background: #1a1a2e;
    }
    
    #game_container {
        width: auto;
        height: auto;
        padding: 2;
    }
    
    GameBoard {
        width: auto;
        height: auto;
        background: #16213e;
        padding: 1;
        border: solid #AEC6CF;
    }
    
    StatusBar {
        width: 100%;
        height: 3;
        background: #0f3460;
        color: #AEC6CF;
        text-align: center;
        padding: 1;
    }
    
    #message_overlay {
        width: 50;
        height: 10;
        background: #16213e;
        border: thick #FFB3BA;
        color: #FFD9B3;
        text-align: center;
        padding: 2;
    }
    """

    BINDINGS = [
        ("w", "move_up", "Move Up"),
        ("s", "move_down", "Move Down"),
        ("a", "move_left", "Move Left"),
        ("d", "move_right", "Move Right"),
        ("e", "reveal", "Reveal"),
        ("c", "flag", "Flag"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, rows: int = 10, cols: int = 10, mines: int = 15):
        super().__init__()
        self.game = Minesweeper(rows, cols, mines)
        self.game_board = None
        self.status_bar = None
        self.message_overlay = None

    def compose(self) -> ComposeResult:
        """Compose the UI."""
        with Vertical(id="game_container"):
            self.game_board = GameBoard(self.game)
            yield Center(self.game_board)
            self.status_bar = StatusBar(id="status_bar")
            yield self.status_bar

        self._update_status()

    def _update_status(self) -> None:
        """Update the status bar."""
        if self.status_bar:
            flags_used = sum(
                sum(1 for flagged in row if flagged) for row in self.game.flagged
            )
            status = self.game.get_status()

            if status == GameStatus.PLAYING:
                self.status_bar.status_text = (
                    f"Mines: {self.game.mines} | Flags: {flags_used} | "
                    f"Controls: WASD=Move E=Reveal C=Flag Q=Quit"
                )
            elif status == GameStatus.WON:
                self.status_bar.status_text = "🎉 YOU WIN! Press Q to quit."
            elif status == GameStatus.LOST:
                self.status_bar.status_text = "💣 GAME OVER! Press Q to quit."

    def _show_message(self, message: str) -> None:
        """Show a message overlay."""
        if self.message_overlay:
            self.message_overlay.remove()

        self.message_overlay = Static(message, id="message_overlay")
        self.mount(Center(self.message_overlay))

    def action_move_up(self) -> None:
        """Move cursor up."""
        if self.game.is_game_over():
            return
        self.game_board.cursor_row = max(0, self.game_board.cursor_row - 1)

    def action_move_down(self) -> None:
        """Move cursor down."""
        if self.game.is_game_over():
            return
        self.game_board.cursor_row = min(
            self.game.rows - 1, self.game_board.cursor_row + 1
        )

    def action_move_left(self) -> None:
        """Move cursor left."""
        if self.game.is_game_over():
            return
        self.game_board.cursor_col = max(0, self.game_board.cursor_col - 1)

    def action_move_right(self) -> None:
        """Move cursor right."""
        if self.game.is_game_over():
            return
        self.game_board.cursor_col = min(
            self.game.cols - 1, self.game_board.cursor_col + 1
        )

    def action_reveal(self) -> None:
        """Reveal the current cell."""
        if self.game.is_game_over():
            return

        row, col = self.game_board.cursor_row, self.game_board.cursor_col
        result = self.game.reveal(row, col)

        self.game_board.update_game_state()
        self._update_status()

        if self.game.get_status() == GameStatus.LOST:
            self._show_message("💣 GAME OVER!\nYou hit a mine!\n\nPress Q to quit")
        elif self.game.get_status() == GameStatus.WON:
            self._show_message("🎉 CONGRATULATIONS!\nYou won!\n\nPress Q to quit")

    def action_flag(self) -> None:
        """Toggle flag on the current cell."""
        if self.game.is_game_over():
            return

        row, col = self.game_board.cursor_row, self.game_board.cursor_col
        self.game.flag(row, col)

        self.game_board.update_game_state()
        self._update_status()


def main():
    """Run the application."""
    app = MinesweeperApp(rows=10, cols=10, mines=15)
    app.run()


if __name__ == "__main__":
    main()
