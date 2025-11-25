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
from .ai_player.ai_player import PlayerAI

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

    def __init__(self, rows: int = 10, cols: int = 10, mines: int = 15, ai_mode: bool = False) -> None:
        """Initialize the TUI.

        Args:
            rows: Number of rows in the grid
            cols: Number of columns in the grid
            mines: Number of mines to place
            ai_mode: Whether to enable AI mode
        """
        self.game = Minesweeper(rows, cols, mines)
        self.console = Console()
        self.cursor_row = 0
        self.cursor_col = 0
        self.running = True
        self.playerAI = PlayerAI(self.game, enable_learning=ai_mode)
        self.show_heatmap_on_exit = False
        self.ai_mode = ai_mode
        self.last_move_was_mine = False
        self.should_restart = False

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
            color = "#808080"  # light gray
        else:  # REVEALED_NUMBER
            value = self.game.get_cell_value(row, col)
            value = value if value else 0

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
            title="[bold]Game Board[/bold]",
        )

    def render_heatmap(self) -> Panel:
        """Render the AI heatmap as a Rich Table.

        Returns:
            Panel containing the heatmap
        """
        heatmap = self.playerAI.get_heatmap()
        best_move = self.playerAI.get_best_move()
        dangerous_cells = self.playerAI.get_dangerous_cells(threshold=0.7)
        
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
            table.add_column(justify="center", width=5)

        # Add rows
        for r in range(self.game.rows):
            row_cells = []
            for c in range(self.game.cols):
                is_cursor = r == self.cursor_row and c == self.cursor_col
                is_best_move = best_move and (r, c) == best_move
                is_dangerous = (r, c) in dangerous_cells
                
                prob = heatmap[r][c]
                if prob == -1:
                    cell_text = Text(" -- ", style=f"bold {COLORS['mint']}")
                else:
                    # Color code based on special status
                    if is_best_move:
                        cell_text = Text(f"{prob:.1f}", style="bold green")
                    elif is_dangerous:
                        cell_text = Text(f"{prob:.1f}", style="bold red")
                    else:
                        cell_text = Text(f"{prob:.1f}", style="bold white")
                
                # Add cursor highlight
                if is_cursor:
                    cell_text.stylize(f'reverse on {COLORS["yellow"]}')
                
                row_cells.append(cell_text)
            table.add_row(*row_cells)

        # Wrap in panel with border
        return Panel(
            Align.center(table),
            border_style=COLORS["peach"],
            padding=(1, 2),
            title="[bold]AI Heatmap (Green=Safe, Red=Danger)[/bold]",
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
            mode_text = "AI Mode" if self.ai_mode else "Manual Mode"
            msg = f"⚑ Flags: {flags_remaining} | Position: ({self.cursor_row}, {self.cursor_col}) | {mode_text}"
            
            # Add AI stats if learning is enabled
            if self.ai_mode and self.playerAI.learning:
                stats = self.playerAI.learning.get_stats_display()
                msg = f"{msg}\n{stats}"
            
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
        
        if self.ai_mode:
            instructions.append("[SPACE] AI Move ", style=COLORS["mint"])
            instructions.append("[W/A/S/D] Move ", style=COLORS["peach"])
        else:
            instructions.append("[W/A/S/D] Move ", style=COLORS["peach"])
            instructions.append("[E] Reveal ", style=COLORS["mint"])
            instructions.append("[F] Flag ", style=COLORS["pink"])
        
        instructions.append("[R] Restart ", style=COLORS["blue"])
        instructions.append("[Q] Quit", style=COLORS["yellow"])

        return Align.center(instructions) # type: ignore

    def render_ui(self) -> Layout:
        """Render the complete UI layout.

        Returns:
            Complete layout with all UI elements
        """
        layout = Layout()
        # Increase header size if showing AI stats
        header_size = 5 if (self.ai_mode and self.playerAI.learning) else 3
        layout.split_column(
            Layout(name="header", size=header_size),
            Layout(name="main"),
            Layout(name="instructions", size=3),
        )

        # Split main area into two columns for board and heatmap
        layout["main"].split_row(
            Layout(name="board"),
            Layout(name="heatmap"),
        )

        layout["header"].update(Align.center(self.render_status()))
        layout["main"]["board"].update(Align.center(self.render_board()))
        layout["main"]["heatmap"].update(Align.center(self.render_heatmap()))
        layout["instructions"].update(self.render_instructions())

        return layout

    def restart_game(self) -> None:
        """Restart the game with same settings."""
        # Record game end if in AI mode before restarting
        if self.ai_mode and self.playerAI.learning and self.game.is_game_over():
            self.playerAI.record_game_end()
        
        # Set restart flag and exit to restart in main loop
        self.should_restart = True
        self.running = False

    def handle_input(self, key: str) -> None:
        """Handle keyboard input.

        Args:
            key: The pressed key
        """
        # Restart game
        if key.lower() == "r":
            self.restart_game()
            return
        
        # Don't process game moves if game is over
        if self.game.is_game_over() and key.lower() not in ["q", "r"]:
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
        elif key == " " and self.ai_mode:
            # AI makes a move
            move = self.playerAI.move()
            if move:
                self.cursor_row, self.cursor_col = move
                # Check if it was a mine before revealing
                was_mine = self.game.board[move[0]][move[1]] == -1
                self.game.reveal(move[0], move[1])
                
                # Record outcome for learning
                if self.playerAI.learning:
                    self.playerAI.record_move_outcome(not was_mine)
                
                self.show_heatmap_on_exit = True
                
                # Check if game ended
                if self.game.is_game_over():
                    if self.playerAI.learning:
                        self.playerAI.record_game_end()
                    
        elif key.lower() == "e" and not self.ai_mode:
            self.game.reveal(self.cursor_row, self.cursor_col)
            self.show_heatmap_on_exit = True
        elif key.lower() == "f" and not self.ai_mode:
            self.game.flag(self.cursor_row, self.cursor_col)

        # Quit
        elif key.lower() == "q":
            # Record game end if quitting in AI mode
            if self.ai_mode and self.playerAI.learning and self.game.is_game_over():
                self.playerAI.record_game_end()
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
            
            # Print heatmap after UI is cleared
            if self.show_heatmap_on_exit:
                map = self.playerAI.get_heatmap()
                for r in range(self.game.rows):
                    row_display = ""
                    for c in range(self.game.cols):
                        prob = map[r][c]
                        if prob == -1:
                            cell_str = " XX "
                        else:
                            cell_str = f" {prob:.2f} "
                        row_display += cell_str
                    self.console.print(row_display)


def main() -> None:
    """Entry point for the game."""
    print("Welcome to Minesweeper!")
    print("=" * 40)

    # Get game parameters
    try:
        rows = int(input("Enter number of rows (default 10): ") or "10")
        cols = int(input("Enter number of columns (default 10): ") or "10")
        mines = int(input("Enter number of mines (default 10): ") or "10")
    except ValueError:
        print("Invalid input. Using default values (10x10, 10 mines)")
        rows, cols, mines = 10, 10, 10

    # Validate inputs
    if rows < 5 or cols < 5:
        print("Board too small! Using minimum 5x5")
        rows, cols = max(5, rows), max(5, cols)

    if mines >= rows * cols:
        print("Too many mines! Using maximum safe value")
        mines = (rows * cols) // 2

    # Choose game mode
    print("\nGame Mode:")
    print("1. Manual Play (you play)")
    print("2. AI Mode (AI plays, you press spacebar for next move)")
    print("3. Training Mode (AI plays multiple games automatically)")
    print("4. Auto-Train Until 80% Win Rate")
    mode_choice = input("Choose mode (1, 2, 3, or 4, default 1): ").strip() or "1"
    
    if mode_choice == "3":
        # Training mode
        try:
            iterations = int(input("How many games to train? (default 100): ") or "100")
        except ValueError:
            iterations = 100
        
        print(f"\n🎓 Training AI for {iterations} games on {rows}x{cols} board with {mines} mines...")
        print("This may take a moment...\n")
        
        from .ai_player.learning import AILearning
        learning = AILearning()
        
        initial_games = learning.stats['games_played']
        initial_wins = learning.stats['games_won']
        
        for i in range(iterations):
            # Create new game and AI for each iteration
            game = Minesweeper(rows, cols, mines)
            ai = PlayerAI(game, enable_learning=True)
            
            # Play until game ends
            while not game.is_game_over():
                move = ai.move()
                if move:
                    was_mine = game.board[move[0]][move[1]] == -1
                    game.reveal(move[0], move[1])
                    ai.record_move_outcome(not was_mine)
                else:
                    # No valid moves, game stuck
                    break
            
            # Record game outcome
            ai.record_game_end()
            
            # Progress update every 50 games or at end
            if (i + 1) % 50 == 0 or (i + 1) == iterations:
                current_wins = learning.stats['games_won'] - initial_wins
                current_rate = current_wins / (i + 1) if (i + 1) > 0 else 0
                print(f"Progress: {i + 1}/{iterations} games | Wins: {current_wins} | Win Rate: {current_rate:.1%}")
        
        final_wins = learning.stats['games_won'] - initial_wins
        final_rate = final_wins / iterations if iterations > 0 else 0
        
        print(f"\n✅ Training Complete!")
        print(f"Games Played: {iterations}")
        print(f"Wins: {final_wins}")
        print(f"Win Rate: {final_rate:.1%}")
        print(f"\nOverall Statistics:")
        print(learning.get_stats_display())
        
        # Ask if user wants to train more
        restart = input("\nTrain again? (y/n, default y): ").strip().lower()
        if restart == "y" or restart == "":
            print("\n" + "="*60 + "\n")
            main()  # Restart from beginning
        else:
            print("\nThanks for training!")
    
    elif mode_choice == "4":
        # Auto-train until 80% win rate
        print(f"\n🎯 Auto-Training AI until 80% win rate is achieved...")
        print(f"Board: {rows}x{cols} with {mines} mines")
        print("="*60)
        
        from .ai_player.learning import AILearning
        learning = AILearning()
        
        target_win_rate = 0.80
        batch_size = 50  # Train in batches of 50 games
        total_trained = 0
        
        print(f"Starting Win Rate: {learning.stats['win_rate']:.1%}")
        print(f"Target Win Rate: {target_win_rate:.1%}\n")
        
        while learning.stats['win_rate'] < target_win_rate:
            batch_start_games = learning.stats['games_played']
            batch_start_wins = learning.stats['games_won']
            
            # Train one batch
            for i in range(batch_size):
                game = Minesweeper(rows, cols, mines)
                ai = PlayerAI(game, enable_learning=True)
                
                # Play until game ends
                moves = 0
                while not game.is_game_over() and moves < 1000:
                    move = ai.move()
                    if move:
                        was_mine = game.board[move[0]][move[1]] == -1
                        game.reveal(move[0], move[1])
                        ai.record_move_outcome(not was_mine)
                        moves += 1
                    else:
                        break
                
                ai.record_game_end()
            
            # Report batch results
            total_trained += batch_size
            batch_wins = learning.stats['games_won'] - batch_start_wins
            batch_rate = batch_wins / batch_size
            overall_rate = learning.stats['win_rate']
        
        if learning.stats['win_rate'] >= target_win_rate:
            print(f"\n🎉 Target Achieved! Win Rate: {learning.stats['win_rate']:.1%}")
        
        print(f"\n✅ Auto-Training Complete!")
        print(f"Total Games Trained: {total_trained}")
        print(f"Final Win Rate: {learning.stats['win_rate']:.1%}")
        print(f"\nFull Statistics:")
        print(learning.get_stats_display())
        print("\nThanks for training!")
    
    else:
        # Regular play modes
        ai_mode = mode_choice == "2"
        mode_name = "AI Mode" if ai_mode else "Manual Mode"
        print(f"\nStarting game: {rows}x{cols} board with {mines} mines - {mode_name}")
        print("Loading...\n")

        # Start game (with restart loop)
        while True:
            tui = MinesweeperTUI(rows, cols, mines, ai_mode=ai_mode)
            tui.run()
            
            # Check if user wants to restart
            if not tui.should_restart:
                break
        
        print("\nThanks for playing!")


if __name__ == "__main__":
    main()
