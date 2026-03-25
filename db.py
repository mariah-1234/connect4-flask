import psycopg2
import os
from psycopg2.extras import execute_values
from datetime import datetime

# ==========================
# Connexion PostgreSQL
# ==========================
def get_connection():
    # Si DATABASE_URL est défini (Render ou autre prod)
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        return psycopg2.connect(db_url)
    else:
        # Connexion locale pour tests
        return psycopg2.connect(
            dbname="connect4",
            user="postgres",
            password="MARIA",
            host="localhost",
            port=5432
        )

# ==========================
# Encode / Decode Base3
# ==========================
def encode_base3(board):
    """Encode un plateau (2D list 9x9) en string base3"""
    flat = ''.join(str(cell) for row in board for cell in row)
    return flat

def decode_base3(base3_str):
    """Decode base3 string en plateau 2D 9x9"""
    board = [[0]*9 for _ in range(9)]
    base3_str = base3_str.zfill(81)
    for r in range(9):
        for c in range(9):
            board[r][c] = int(base3_str[r*9 + c])
    return board

def sym_board(board):
    """Renvoie le plateau symétrique (horizontal miroir)"""
    return [row[::-1] for row in board]

# ==========================
# INSERTION SITUATION
# ==========================
def insert_situation(base3_hex, sym_base3_hex=None, rows=8, cols=9, result=3, confidence=1):
    if sym_base3_hex is None:
        sym_base3_hex = base3_hex[::-1]  # simple symétrie
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO situations (base3_hex, sym_base3_hex, rows, cols, result, confidence)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (base3_hex) DO UPDATE
        SET confidence = GREATEST(situations.confidence, EXCLUDED.confidence),
            result = EXCLUDED.result
        RETURNING id
    """, (base3_hex, sym_base3_hex, rows, cols, result, confidence))
    situation_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return situation_id

# ==========================
# INSERTION GAME
# ==========================
def insert_game(player1, player2, moves, winner=3, status=3):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO games (player1, player2, moves, winner, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (player1, player2, moves, winner, status, datetime.now()))
    game_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return game_id

# ==========================
# INSERTION GAME MOVES
# ==========================
def insert_game_move(game_id, move_number, column_played, situation_id=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO game_moves (game_id, move_number, column_played, situation_id)
        VALUES (%s, %s, %s, %s)
    """, (game_id, move_number, column_played, situation_id))
    conn.commit()
    cur.close()
    conn.close()

def insert_game_moves_bulk(game_id, moves_list):
    """Insère plusieurs coups [(move_number, col, situation_id)]"""
    if not moves_list:
        return
    conn = get_connection()
    cur = conn.cursor()
    execute_values(cur,
        """
        INSERT INTO game_moves (game_id, move_number, column_played, situation_id)
        VALUES %s
        """,
        [(game_id, m[0], m[1], m[2]) for m in moves_list]
    )
    conn.commit()
    cur.close()
    conn.close()

# ==========================
# RECUPERATION SITUATION
# ==========================
def get_situation_by_base3(base3_hex):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, base3_hex, sym_base3_hex, rows, cols, confidence, result
        FROM situations
        WHERE base3_hex = %s
    """, (base3_hex,))
    res = cur.fetchone()
    cur.close()
    conn.close()
    return res

# ==========================
# STATISTIQUES
# ==========================
def get_statistics():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM games")
    total_games = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM games WHERE winner = 1")
    rouge_wins = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM games WHERE winner = 2")
    jaune_wins = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM games WHERE winner = 0")
    draws = cur.fetchone()[0]
    cur.close()
    conn.close()
    return {"total": total_games, "rouge": rouge_wins, "jaune": jaune_wins, "draws": draws}

# ==========================
# DERNIERE SITUATION D’UNE PARTIE
# ==========================
def last_situation(game_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT situation_id FROM game_moves
        WHERE game_id = %s
        ORDER BY move_number DESC
        LIMIT 1
    """, (game_id,))
    res = cur.fetchone()
    cur.close()
    conn.close()
    return res[0] if res else None

# ==========================
# Récupérer toutes les parties
# ==========================
def fetch_games(limit=500):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, player1, player2, moves, winner FROM games ORDER BY id DESC LIMIT %s",
        (limit,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    games = []
    for r in rows:
        games.append({
            "id": r[0],
            "player1": r[1],
            "player2": r[2],
            "moves": r[3],
            "winner": r[4]
        })
    return games