import random
from puissance4 import check_victory
from minimax import minimax
from game import Game

def choose_move(board, confidence):

    cols = len(board[0])
    possible_moves = [c for c in range(cols) if board[0][c] == "."]

    if not possible_moves:
        return None

    # -------------------------
    # confidence 0 : exprès perdre
    # -------------------------
    if confidence == 0:
        return random.choice(possible_moves)

    # -------------------------
    # confidence 1 : aléatoire
    # -------------------------
    elif confidence == 1:
        return random.choice(possible_moves)

    # -------------------------
    # confidence 2 : semi stratégique
    # -------------------------
    elif confidence == 2:

        # essayer de gagner
        for col in possible_moves:
            temp = [row[:] for row in board]

            for r in reversed(range(len(board))):
                if temp[r][col] == ".":
                    temp[r][col] = "R"
                    break

            winner, _ = check_victory(temp)
            if winner == "R":
                return col

        # bloquer l'adversaire
        for col in possible_moves:
            temp = [row[:] for row in board]

            for r in reversed(range(len(board))):
                if temp[r][col] == ".":
                    temp[r][col] = "Y"
                    break

            winner, _ = check_victory(temp)
            if winner == "Y":
                return col

        return random.choice(possible_moves)

    # -------------------------
    # confidence 3 : IA forte (MINIMAX)
    # -------------------------
    elif confidence == 3:

        g = Game()
        g.board = [row[:] for row in board]

        score, col = minimax(g, 3, True, "R")

        if col is None:
            return random.choice(possible_moves)

        return col

    return random.choice(possible_moves)