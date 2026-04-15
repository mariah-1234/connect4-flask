import tkinter as tk
from tkinter import messagebox, simpledialog
from game import Game
from minimax import minimax
from puissance4 import check_victory
from save_to_db import save_game_from_list
from config import ROWS, COLS, AI_DEPTH

CELL = 50
TOP_MARGIN = 60

COLORS = {
    "R": "red",
    "Y": "yellow",
    ".": "white"
}


class PaintGUI:

    def __init__(self):

        self.root = tk.Tk()
        self.root.title("🎨 Paint IA PRO")

        self.game = Game()
        self.depth = AI_DEPTH

        self.game_over = False
        self.auto_play = False

        self.paint_mode = "R"

        w = COLS * CELL
        h = TOP_MARGIN + ROWS * CELL

        self.canvas = tk.Canvas(self.root, width=w, height=h, bg="blue")
        self.canvas.pack()

        self.canvas.bind("<Button-1>", self.on_click)

        self.info = self.canvas.create_text(
            w // 2, 20,
            text="🎨 Dessine → puis clique IA",
            fill="white",
            font=("Arial", 12, "bold")
        )

        self.cells = []
        self.draw_board()

        frame = tk.Frame(self.root)
        frame.pack()

        tk.Button(frame, text="🔴 Rouge", command=lambda: self.set_mode("R")).pack(side="left")
        tk.Button(frame, text="🟡 Jaune", command=lambda: self.set_mode("Y")).pack(side="left")
        tk.Button(frame, text="⬜ Effacer", command=lambda: self.set_mode(".")).pack(side="left")

        tk.Button(frame, text="🤖 IA joue", command=self.ai_one_move).pack(side="left")
        tk.Button(frame, text="🔁 IA vs IA", command=self.ai_auto).pack(side="left")
        tk.Button(frame, text="⏹ Stop", command=self.stop_ai).pack(side="left")

        tk.Button(frame, text="💾 Save", command=self.save).pack(side="left")
        tk.Button(frame, text="🔄 Reset", command=self.reset).pack(side="left")
        tk.Button(frame, text="❌ Quit", command=self.root.destroy).pack(side="left")

        self.root.mainloop()

    def draw_board(self):

        self.cells = [[None] * COLS for _ in range(ROWS)]

        for r in range(ROWS):
            for c in range(COLS):

                x1 = c * CELL
                y1 = TOP_MARGIN + r * CELL
                x2 = x1 + CELL
                y2 = y1 + CELL

                self.cells[r][c] = self.canvas.create_oval(
                    x1 + 5, y1 + 5,
                    x2 - 5, y2 - 5,
                    fill="white",
                    outline="black"
                )

        self.update()

    def update(self):

        for r in range(ROWS):
            for c in range(COLS):
                self.canvas.itemconfig(
                    self.cells[r][c],
                    fill=COLORS[self.game.board[r][c]]
                )

    def set_mode(self, mode):
        self.paint_mode = mode

    def on_click(self, event):

        if self.game_over:
            return

        col = event.x // CELL
        row = (event.y - TOP_MARGIN) // CELL

        if 0 <= row < ROWS and 0 <= col < COLS:
            self.game.board[row][col] = self.paint_mode
            self.update()

    def rebuild_game_from_board(self):

        new_game = Game()

        for c in range(COLS):
            col_values = []

            for r in range(ROWS):
                if self.game.board[r][c] != ".":
                    col_values.append(self.game.board[r][c])

            for val in reversed(col_values):
                new_game.current_player = val
                new_game.play(c)

        return new_game

    def ai_one_move(self):

        if self.game_over:
            return

        real_game = self.rebuild_game_from_board()

        r = sum(row.count("R") for row in real_game.board)
        y = sum(row.count("Y") for row in real_game.board)
        current = "R" if r <= y else "Y"

        real_game.current_player = current

        winner, line = check_victory(real_game.board)
        if winner:
            self.end_game(winner, line)
            return

        _, col = minimax(
            real_game,
            self.depth,
            -999999,
            999999,
            True,
            current
        )

        if col is not None:
            real_game.play(col)

        self.game = real_game

        self.update()
        self.check_end()

    def ai_auto(self):
        self.auto_play = True
        self.run_auto()

    def run_auto(self):

        if not self.auto_play or self.game_over:
            return

        self.ai_one_move()
        self.root.after(400, self.run_auto)

    def stop_ai(self):
        self.auto_play = False

    def check_end(self):

        winner, line = check_victory(self.game.board)

        if winner:
            self.end_game(winner, line)

        elif not self.game.valid_moves():
            self.game_over = True
            self.canvas.itemconfig(self.info, text="🤝 Match nul")

    def end_game(self, winner, line):

        self.game_over = True
        self.auto_play = False

        for r, c in line:
            self.canvas.itemconfig(self.cells[r][c], fill="green")

        self.canvas.itemconfig(self.info, text=f"🏆 Gagnant : {winner}")

        messagebox.showinfo("Fin", f"Gagnant : {winner}")

    def save(self):

        name = simpledialog.askstring("Save", "Nom ?")

        if name:
            real_game = self.rebuild_game_from_board()

            save_game_from_list(
                "Paint",
                "IA",
                3,
                real_game.moves
            )

            messagebox.showinfo("OK", "Sauvegardé DB")

    def reset(self):

        self.game = Game()
        self.game_over = False
        self.auto_play = False
        self.update()

        self.canvas.itemconfig(self.info, text="🎨 Nouveau plateau")


def launch_paint():
    PaintGUI()