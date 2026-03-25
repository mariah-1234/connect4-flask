from game import ROUGE, JAUNE, VIDE
from puissance4 import check_victory
from config import ROWS, COLS

CENTER_COL = COLS // 2


def evaluate_window(window, ai_player):
    opponent = ROUGE if ai_player == JAUNE else JAUNE
    score = 0

    ai_count = window.count(ai_player)
    opp_count = window.count(opponent)
    empty = window.count(VIDE)

    if ai_count == 4:
        score += 100000

    elif ai_count == 3 and empty == 1:
        score += 100

    elif ai_count == 2 and empty == 2:
        score += 10

    if opp_count == 3 and empty == 1:
        score -= 120

    return score


def evaluate_board(board, ai_player):

    score = 0

    # priorité au centre
    center = [board[r][CENTER_COL] for r in range(ROWS)]
    score += center.count(ai_player) * 6

    # horizontal
    for r in range(ROWS):
        row = board[r]
        for c in range(COLS - 3):
            window = row[c:c+4]
            score += evaluate_window(window, ai_player)

    # vertical
    for c in range(COLS):
        col = [board[r][c] for r in range(ROWS)]
        for r in range(ROWS - 3):
            window = col[r:r+4]
            score += evaluate_window(window, ai_player)

    # diagonale \
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r+i][c+i] for i in range(4)]
            score += evaluate_window(window, ai_player)

    # diagonale /
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            window = [board[r-i][c+i] for i in range(4)]
            score += evaluate_window(window, ai_player)

    return score


def order_moves(valid_moves):
    """
    priorité au centre (stratégie Puissance 4)
    """
    return sorted(valid_moves, key=lambda x: abs(x - CENTER_COL))


def minimax(game, depth, alpha, beta, maximizing, ai_player):

    winner, _ = check_victory(game.board)

    if winner == ai_player:
        return 1000000, None

    elif winner is not None:
        return -1000000, None

    if depth == 0:
        return evaluate_board(game.board, ai_player), None

    valid_moves = order_moves(game.valid_moves())

    if maximizing:

        best_score = -99999999
        best_col = valid_moves[0]

        for col in valid_moves:

            g = game.copy()
            g.play(col)

            score, _ = minimax(g, depth-1, alpha, beta, False, ai_player)

            if score > best_score:
                best_score = score
                best_col = col

            alpha = max(alpha, best_score)

            if beta <= alpha:
                break

        return best_score, best_col

    else:

        best_score = 99999999
        best_col = valid_moves[0]

        for col in valid_moves:

            g = game.copy()
            g.play(col)

            score, _ = minimax(g, depth-1, alpha, beta, True, ai_player)

            if score < best_score:
                best_score = score
                best_col = col

            beta = min(beta, best_score)

            if beta <= alpha:
                break

        return best_score, best_col