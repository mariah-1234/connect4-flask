# save_to_db.py
from db import get_connection
from game import Game
from puissance4 import check_victory

# ===============================
# miroir du plateau
# ===============================
def mirror_board(board_text, rows=9, cols=9):
    """Renvoie le plateau miroir horizontal"""
    mirrored = ""
    for r in range(rows):
        row = board_text[r*cols:(r+1)*cols]
        mirrored += row[::-1]
    return mirrored

# ===============================
# miroir des coups
# ===============================
def mirror_moves(moves_string, cols=9):
    """Renvoie la séquence de coups miroir"""
    return "".join(str(cols-1 - int(c)) for c in moves_string)

# ===============================
# vérifier si situation existe
# ===============================
def situation_exists(board_text):
    """
    Vérifie si la situation existe déjà dans la table 'situations'.
    Renvoie (True/False, True/False) selon existence et symétrie.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id FROM situations WHERE base3_hex = %s",
        (board_text,)
    )
    res = cur.fetchone()
    if res:
        cur.close()
        conn.close()
        return True, False

    mirror = mirror_board(board_text)
    cur.execute(
        "SELECT id FROM situations WHERE base3_hex = %s",
        (mirror,)
    )
    res = cur.fetchone()
    cur.close()
    conn.close()
    if res:
        return True, True

    return False, False

# ===============================
# sauvegarder une partie
# ===============================
def save_game_from_list(player1, player2, mode, moves_list, confidence=None):
    """
    Sauvegarde une partie avec tous les coups et situations.
    'mode' est le niveau de confiance (0-3) du joueur/bot.
    """
    conn = get_connection()
    cur = conn.cursor()

    moves_string = "".join(str(m) for m in moves_list)
    mirror_moves_string = mirror_moves(moves_string)

    # Vérifier si la partie ou sa symétrie existe déjà
    cur.execute(
        "SELECT id FROM games WHERE moves = %s OR moves = %s",
        (moves_string, mirror_moves_string)
    )
    if cur.fetchone():
        print("Partie ou symétrie déjà existante")
        cur.close()
        conn.close()
        return

    # Créer la partie
    cur.execute("""
        INSERT INTO games(player1, player2, moves, status)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (player1, player2, moves_string, 1))  # status=1 = finished
    game_id = cur.fetchone()[0]

    game = Game()
    for i, col in enumerate(moves_list):
        game.play(col)

        # transformer le plateau en string
        board_text = "".join("".join(row) for row in game.board)

        exists, sym = situation_exists(board_text)

        if not exists:
            # Ajouter la situation avec confidence, rows et cols
            cur.execute("""
                INSERT INTO situations(base3_hex, sym_base3_hex, confidence, rows, cols)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                board_text,
                mirror_board(board_text) if sym else None,
                mode,
                len(game.board),        # rows
                len(game.board[0])      # cols
            ))
            situation_id = cur.fetchone()[0]
        else:
            situation_id = None  # Déjà existante

        # Ajouter le coup
        cur.execute("""
            INSERT INTO game_moves(game_id, move_number, column_played, situation_id)
            VALUES (%s, %s, %s, %s)
        """, (game_id, i+1, col, situation_id))

    # Déterminer le gagnant
    winner, _ = check_victory(game.board)
    winner_db = 0
    if winner == "R":
        winner_db = 1
    elif winner == "Y":
        winner_db = 2

    # Mettre à jour le winner dans la table games
    cur.execute("UPDATE games SET winner = %s WHERE id = %s", (winner_db, game_id))

    conn.commit()
    cur.close()
    conn.close()

    print("Partie sauvegardée :", game_id)