import copy
from config import ROWS, COLS, FIRST_PLAYER

ROUGE = "R"
JAUNE = "Y"
VIDE = "."

class Game:
    def __init__(self):
        self.board = [[VIDE]*COLS for _ in range(ROWS)]
        self.current_player = FIRST_PLAYER
        self.moves = []

    def copy(self):
        g = Game()
        g.board = copy.deepcopy(self.board)
        g.current_player = self.current_player
        g.moves = self.moves[:]
        return g

    def valid_moves(self):
        return [c for c in range(COLS) if self.board[0][c] == VIDE]

    def play(self, col):
        if col not in self.valid_moves():
            return False
        for r in reversed(range(ROWS)):
            if self.board[r][col] == VIDE:
                self.board[r][col] = self.current_player
                self.moves.append(col)
                self.current_player = ROUGE if self.current_player == JAUNE else JAUNE
                return True

    def undo(self):
        if not self.moves:
            return
        col = self.moves.pop()
        for r in range(ROWS):
            if self.board[r][col] != VIDE:
                self.board[r][col] = VIDE
                break
        self.current_player = ROUGE if self.current_player == JAUNE else JAUNE