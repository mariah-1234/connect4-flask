from game import Game, ROUGE, JAUNE, VIDE
from puissance4 import check_victory

def minimax(game, depth, maximizing, ai_player):
    """
    Fonction récursive minimax.
    - game : instance de Game
    - depth : profondeur de recherche
    - maximizing : True si c'est le joueur AI
    - ai_player : "R" ou "Y"
    Retourne (score, colonne_choisie)
    """
    winner, _ = check_victory(game.board)
    if winner == ai_player:
        return 1000, None
    if winner is not None:
        return -1000, None
    if depth == 0:
        return 0, None

    best_col = None
    if maximizing:
        best = -9999
        for col in game.valid_moves():
            g = game.copy()
            g.play(col)
            score, _ = minimax(g, depth-1, False, ai_player)
            if score > best:
                best = score
                best_col = col
        return best, best_col
    else:
        best = 9999
        for col in game.valid_moves():
            g = game.copy()
            g.play(col)
            score, _ = minimax(g, depth-1, True, ai_player)
            if score < best:
                best = score
                best_col = col
        return best, best_col