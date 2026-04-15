from game import ROUGE, JAUNE, VIDE
from puissance4 import check_victory
from config import ROWS, COLS

CENTER_COL = COLS // 2


# --------------------------------------------------
# UTILITAIRES
# --------------------------------------------------
def opponent_of(player):
    return ROUGE if player == JAUNE else JAUNE


def order_moves(valid_moves):
    """
    Priorité au centre, puis autour du centre.
    """
    return sorted(valid_moves, key=lambda x: abs(x - CENTER_COL))


def is_immediate_win(game, col, player):
    """
    Vérifie si player gagne immédiatement en jouant col.
    """
    g = game.copy()
    g.current_player = player
    g.play(col)
    winner, _ = check_victory(g.board)
    return winner == player


def count_immediate_wins(game, player):
    """
    Compte combien de coups gagnants immédiats player possède.
    Très utile pour détecter les doubles menaces.
    """
    count = 0
    for col in game.valid_moves():
        if is_immediate_win(game, col, player):
            count += 1
    return count


# --------------------------------------------------
# ÉVALUATION D'UNE FENÊTRE DE 4
# --------------------------------------------------
def evaluate_window(window, ai_player):
    opp = opponent_of(ai_player)

    ai_count = window.count(ai_player)
    opp_count = window.count(opp)
    empty = window.count(VIDE)

    score = 0

    # Attaque
    if ai_count == 4:
        score += 1000000
    elif ai_count == 3 and empty == 1:
        score += 12000
    elif ai_count == 2 and empty == 2:
        score += 400
    elif ai_count == 1 and empty == 3:
        score += 8

    # Défense
    if opp_count == 4:
        score -= 1000000
    elif opp_count == 3 and empty == 1:
        score -= 15000
    elif opp_count == 2 and empty == 2:
        score -= 500

    return score


# --------------------------------------------------
# ÉVALUATION DU PLATEAU
# --------------------------------------------------
def evaluate_board(game, ai_player):
    board = game.board
    opp = opponent_of(ai_player)
    score = 0

    # 1) Priorité au centre
    center_array = [board[r][CENTER_COL] for r in range(ROWS)]
    score += center_array.count(ai_player) * 80
    score -= center_array.count(opp) * 80

    # 2) Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            window = [board[r][c+i] for i in range(4)]
            score += evaluate_window(window, ai_player)

    # 3) Vertical
    for c in range(COLS):
        for r in range(ROWS - 3):
            window = [board[r+i][c] for i in range(4)]
            score += evaluate_window(window, ai_player)

    # 4) Diagonale \
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r+i][c+i] for i in range(4)]
            score += evaluate_window(window, ai_player)

    # 5) Diagonale /
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            window = [board[r-i][c+i] for i in range(4)]
            score += evaluate_window(window, ai_player)

    # 6) Coups gagnants immédiats
    ai_wins = count_immediate_wins(game, ai_player)
    opp_wins = count_immediate_wins(game, opp)

    score += ai_wins * 50000
    score -= opp_wins * 60000

    # 7) Double menace = énorme bonus
    if ai_wins >= 2:
        score += 300000
    if opp_wins >= 2:
        score -= 350000

    return score


# --------------------------------------------------
# MINIMAX CHAMPION
# --------------------------------------------------
def minimax(game, depth, alpha, beta, maximizing, ai_player):
    opp = opponent_of(ai_player)

    winner, _ = check_victory(game.board)

    # États terminaux
    if winner == ai_player:
        return 10_000_000 + depth, None
    elif winner == opp:
        return -10_000_000 - depth, None

    valid_moves = order_moves(game.valid_moves())

    if not valid_moves:
        return 0, None  # nul

    if depth == 0:
        return evaluate_board(game, ai_player), None

    # --------------------------------------------------
    # 1) PRIORITÉ ABSOLUE : gagner immédiatement
    # --------------------------------------------------
    for col in valid_moves:
        if is_immediate_win(game, col, game.current_player):
            if game.current_player == ai_player:
                return 9_999_999 + depth, col
            else:
                return -9_999_999 - depth, col

    # --------------------------------------------------
    # 2) PRIORITÉ : bloquer un coup gagnant adverse
    # --------------------------------------------------
    current = game.current_player
    other = opponent_of(current)

    opponent_winning_moves = []
    for col in valid_moves:
        if is_immediate_win(game, col, other):
            opponent_winning_moves.append(col)

    if len(opponent_winning_moves) == 1:
        forced_col = opponent_winning_moves[0]
        if current == ai_player:
            return 8_888_888 + depth, forced_col
        else:
            return -8_888_888 - depth, forced_col

    # --------------------------------------------------
    # 3) MINIMAX ALPHA-BETA
    # --------------------------------------------------
    if maximizing:
        best_score = -10**18
        best_col = valid_moves[0]

        for col in valid_moves:
            g = game.copy()
            g.play(col)

            score, _ = minimax(g, depth - 1, alpha, beta, False, ai_player)

            if score > best_score:
                best_score = score
                best_col = col

            alpha = max(alpha, best_score)
            if beta <= alpha:
                break

        return best_score, best_col

    else:
        best_score = 10**18
        best_col = valid_moves[0]

        for col in valid_moves:
            g = game.copy()
            g.play(col)

            score, _ = minimax(g, depth - 1, alpha, beta, True, ai_player)

            if score < best_score:
                best_score = score
                best_col = col

            beta = min(beta, best_score)
            if beta <= alpha:
                break

        return best_score, best_col