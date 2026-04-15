from db import get_connection

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # TABLE GAMES
    cur.execute("""
    CREATE TABLE IF NOT EXISTS games (
        id SERIAL PRIMARY KEY,
        player1 TEXT,
        player2 TEXT,
        moves TEXT,
        winner INTEGER,
        status INTEGER DEFAULT 3,
        created_at TIMESTAMP
    )
    """)

    # TABLE GAME_MOVES
    cur.execute("""
    CREATE TABLE IF NOT EXISTS game_moves (
        id SERIAL PRIMARY KEY,
        game_id INTEGER,
        move_number INTEGER,
        column_played INTEGER,
        situation_id INTEGER
    )
    """)

    # TABLE SITUATIONS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS situations (
        id SERIAL PRIMARY KEY,
        base3_hex TEXT UNIQUE,
        sym_base3_hex TEXT,
        rows INTEGER,
        cols INTEGER,
        result INTEGER,
        confidence INTEGER
    )
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Base de données initialisée")

if __name__ == "__main__":
    init_db()