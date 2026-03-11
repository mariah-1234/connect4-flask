import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
from game import Game
from minimax import minimax
from puissance4 import check_victory
from save_load import save_game, load_game, list_saves
from save_to_db import save_game_from_list
from config import ROWS, COLS, AI_DEPTH

# -----------------------
# Taille des cellules adaptée pour 9x9
# -----------------------
CELL = 50        # réduit un peu pour que tout rentre
TOP_MARGIN = 60
BOTTOM_MARGIN = 60

COLORS = {
    "R": "red",
    "Y": "yellow",
    ".": "white"
}

class Connect4GUI:
    def __init__(self, mode):
        self.mode = mode
        self.game_saved = False
        self.moves_history = []

        self.root = tk.Tk()
        self.root.title("Puissance 4")

        self.game = Game()
        self.ai_player = "Y"
        self.ai_enabled = (mode in [0,1])
        self.human_enabled = (mode in [1,2])
        self.ai_type = "minimax"
        self.depth = AI_DEPTH

        # -----------------------
        # Canvas adapté pour 9x9
        # -----------------------
        w = COLS * CELL
        h = TOP_MARGIN + ROWS * CELL + BOTTOM_MARGIN
        self.canvas = tk.Canvas(self.root, width=w, height=h, bg="blue")
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_click)

        # -----------------------
        # Texte joueur
        # -----------------------
        self.turn_text = self.canvas.create_text(
            w//2, TOP_MARGIN//2,
            text=f"Au tour du joueur {self.game.current_player}",
            fill="white",
            font=("Arial", 12, "bold")
        )

        self.create_buttons()
        self.draw_static()
        self.update_board()

        if self.mode == 0:
            self.root.after(500, self.ai_turn)

        self.root.mainloop()

    # -----------------------
    # Dessin plateau et poids / colonnes
    # -----------------------
    def draw_static(self):
        self.cells = [[None]*COLS for _ in range(ROWS)]

        # Numéros de colonnes
        for c in range(COLS):
            self.canvas.create_text(
                c*CELL + CELL//2,
                TOP_MARGIN - 20,
                text=str(c),
                fill="white",
                font=("Arial", 12, "bold")
            )

        for r in range(ROWS):
            for c in range(COLS):
                x1 = c*CELL
                y1 = TOP_MARGIN + r*CELL
                x2 = x1 + CELL
                y2 = y1 + CELL
                self.cells[r][c] = self.canvas.create_oval(
                    x1+5, y1+5, x2-5, y2-5,
                    fill="white",
                    outline="black"
                )

        # Poids Minimax / IA
        self.weights = []
        for c in range(COLS):
            t = self.canvas.create_text(
                c*CELL + CELL//2,
                TOP_MARGIN + ROWS*CELL + 20,
                text="",
                fill="white",
                font=("Arial", 11, "bold")
            )
            self.weights.append(t)

    # -----------------------
    # Boutons
    # -----------------------
    def create_buttons(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=5)
        tk.Button(frame, text="Undo", command=self.undo).pack(side="left")
        tk.Button(frame, text="Restart", command=self.restart).pack(side="left")
        tk.Button(frame, text="Save", command=self.save).pack(side="left")
        tk.Button(frame, text="Load", command=self.load_txt_or_db).pack(side="left")
        tk.Button(frame, text="IA Random", command=self.set_random).pack(side="left")
        tk.Button(frame, text="IA Minimax", command=self.set_minimax).pack(side="left")
        tk.Button(frame, text="Profondeur", command=self.set_depth).pack(side="left")
        tk.Button(frame, text="Quit", command=self.root.destroy).pack(side="left")

    # -----------------------
    # Update plateau et texte joueur
    # -----------------------
    def update_board(self):
        for r in range(ROWS):
            for c in range(COLS):
                self.canvas.itemconfig(self.cells[r][c], fill=COLORS[self.game.board[r][c]])

        self.canvas.itemconfig(self.turn_text, text=f"Au tour du joueur {self.game.current_player}")
        self.update_weights()
        self.highlight_winner()
        self.check_end()

    # -----------------------
    # Poids Minimax
    # -----------------------
    def update_weights(self):
        if not self.ai_enabled or self.game.current_player != self.ai_player:
            return
        for c in range(COLS):
            if c not in self.game.valid_moves():
                self.canvas.itemconfig(self.weights[c], text="X")
                continue
            g = self.game.copy()
            g.play(c)
            score,_ = minimax(g, self.depth, False, self.ai_player)
            self.canvas.itemconfig(self.weights[c], text=str(score))

    # -----------------------
    # Surbrillance gagnant
    # -----------------------
    def highlight_winner(self):
        winner, line = check_victory(self.game.board)
        if winner:
            for r, c in line:
                self.canvas.itemconfig(self.cells[r][c], fill="green")

    # -----------------------
    # Click humain
    # -----------------------
    def on_click(self, event):
        if (self.mode == 0) or (self.mode==1 and self.game.current_player==self.ai_player):
            return
        col = event.x // CELL
        if col not in self.game.valid_moves():
            return
        self.game.play(col)
        self.moves_history.append(col)
        self.update_board()
        if self.mode in [0,1]:
            self.root.after(100, self.ai_turn)

    # -----------------------
    # Tour IA
    # -----------------------
    def ai_turn(self):
        if self.mode == 2 or not self.game.valid_moves():
            return
        current = self.game.current_player
        if self.ai_type=="random":
            import random
            col = random.choice(self.game.valid_moves())
        else:
            _, col = minimax(self.game, self.depth, True, current)
        if col is not None:
            self.game.play(col)
            self.moves_history.append(col)
            self.update_board()
        if self.mode==0:
            self.root.after(300, self.ai_turn)

    # -----------------------
    # Fin partie
    # -----------------------
    def check_end(self):
        winner, line = check_victory(self.game.board)
        if winner and not self.game_saved:
            messagebox.showinfo("Fin de partie", f"Victoire du joueur {winner}")
            save_game_from_list(
                player1="Humain",
                player2="IA" if self.mode==1 else "Humain",
                mode=self.mode,
                moves_list=self.moves_history
            )
            self.game_saved = True
            self.ai_enabled = False
            self.human_enabled = False

    # -----------------------
    # Undo / Restart / Save
    # -----------------------
    def undo(self):
        if self.moves_history:
            self.moves_history.pop()
        self.game.undo()
        self.update_board()

    def restart(self):
        self.game = Game()
        self.moves_history = []
        self.game_saved = False
        self.ai_enabled = (self.mode in [0,1])
        self.human_enabled = (self.mode in [1,2])
        self.update_board()

    def save(self):
        name = simpledialog.askstring("Sauvegarde", "Nom de la partie :")
        if name:
            save_game(self.game, name)

    # -----------------------
    # Load (BDD ou TXT)
    # -----------------------
    def load_txt_or_db(self):
        file_path = filedialog.askopenfilename(title="Charger fichier TXT", filetypes=[("Text files","*.txt")])
        if file_path:
            import os
            name = os.path.basename(file_path)
            moves_string = name.replace(".txt","")
            if not moves_string.isdigit():
                messagebox.showerror("Erreur", "Nom fichier doit contenir seulement des chiffres")
                return
            self.game = Game()
            self.moves_history = [int(c) for c in moves_string]
            self.game_saved = False
            self.moves_history_play_all()
            self.update_board()
            return

        saves = list_saves()
        if not saves:
            messagebox.showerror("Erreur", "Aucune sauvegarde")
            return
        name = simpledialog.askstring("Chargement", "Sauvegardes disponibles:\n" + "\n".join(saves))
        if name:
            self.game = load_game(name.replace(".p4",""))
            self.moves_history = self.game.history.copy()
            self.game_saved = False
            self.moves_history_play_all()
            self.update_board()

    def moves_history_play_all(self):
        self.game = Game()
        for col in self.moves_history:
            self.game.play(col)
        self.step = len(self.moves_history)

    # -----------------------
    # IA SETTINGS
    # -----------------------
    def set_random(self): self.ai_type="random"
    def set_minimax(self): self.ai_type="minimax"
    def set_depth(self):
        d = simpledialog.askinteger("Profondeur","Nouvelle profondeur :", minvalue=1, maxvalue=8)
        if d: self.depth=d

# -----------------------
# Lancement
# -----------------------
def launch_game(mode):
    Connect4GUI(mode)