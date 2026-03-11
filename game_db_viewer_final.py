import tkinter as tk
from tkinter import messagebox
from db import get_connection
from game import Game
from config import ROWS, COLS

CELL = 60
TOP = 60

COLORS = {
    "R": "red",
    "Y": "yellow",
    ".": "white"
}


class GameDBViewer:

    def __init__(self):

        self.root = tk.Tk()
        self.root.title("Puissance 4 - DB Viewer")

        self.canvas = tk.Canvas(
            self.root,
            width=COLS * CELL,
            height=ROWS * CELL + TOP,
            bg="blue"
        )
        self.canvas.pack()

        # ========================
        # BOUTONS
        # ========================

        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        tk.Button(frame, text="Charger Partie DB",
                  command=self.load_game).pack(side="left", padx=5)

        tk.Button(frame, text="Next",
                  command=self.next_move).pack(side="left", padx=5)

        tk.Button(frame, text="Prev",
                  command=self.prev_move).pack(side="left", padx=5)

        tk.Button(frame, text="Quit",
                  command=self.root.destroy).pack(side="left", padx=5)

        # ========================
        # PLATEAU
        # ========================

        self.cells = [[None] * COLS for _ in range(ROWS)]

        for r in range(ROWS):
            for c in range(COLS):

                x1 = c * CELL
                y1 = TOP + r * CELL

                x2 = x1 + CELL
                y2 = y1 + CELL

                self.cells[r][c] = self.canvas.create_oval(
                    x1 + 5,
                    y1 + 5,
                    x2 - 5,
                    y2 - 5,
                    fill="white"
                )

        self.moves = []
        self.step = 0
        self.game = Game()

        self.root.mainloop()

    # ======================================
    # CHARGER UNE PARTIE DEPUIS LA DB
    # ======================================

    def load_game(self):

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT id, moves FROM games ORDER BY id DESC LIMIT 500"
        )

        games = cur.fetchall()

        if not games:
            messagebox.showinfo("Info", "Aucune partie dans la base")
            return

        win = tk.Toplevel(self.root)
        win.title("Choisir une partie")

        scrollbar = tk.Scrollbar(win)
        scrollbar.pack(side="right", fill="y")

        listbox = tk.Listbox(
            win,
            width=60,
            height=25,
            yscrollcommand=scrollbar.set
        )

        for g in games:
            listbox.insert(
                tk.END,
                f"Game {g[0]}  |  Moves : {g[1]}"
            )

        listbox.pack(side="left", fill="both")

        scrollbar.config(command=listbox.yview)

        def select():

            sel = listbox.curselection()

            if not sel:
                return

            index = sel[0]

            moves_string = games[index][1]

            self.moves = [int(x) for x in moves_string]

            self.game = Game()
            self.step = 0

            self.update_board()

            win.destroy()

        tk.Button(win, text="Charger", command=select).pack(pady=10)

        conn.close()

    # ======================================
    # MOVE SUIVANT
    # ======================================

    def next_move(self):

        if self.step >= len(self.moves):
            return

        col = self.moves[self.step]

        self.game.play(col)

        self.step += 1

        self.update_board()

    # ======================================
    # MOVE PRECEDENT
    # ======================================

    def prev_move(self):

        if self.step <= 0:
            return

        self.game.undo()

        self.step -= 1

        self.update_board()

    # ======================================
    # UPDATE AFFICHAGE
    # ======================================

    def update_board(self):

        for r in range(ROWS):
            for c in range(COLS):

                val = self.game.board[r][c]

                self.canvas.itemconfig(
                    self.cells[r][c],
                    fill=COLORS[val]
                )


if __name__ == "__main__":
    GameDBViewer()