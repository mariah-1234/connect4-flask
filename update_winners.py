# update_winners.py
from db import get_connection
from game import Game
from puissance4 import check_victory

def update_all_winners():
    conn = get_connection()
    cur = conn.cursor()

    # Récupérer toutes les parties
    cur.execute("SELECT id, moves FROM games")
    games = cur.fetchall()
    print(f"{len(games)} parties trouvées")

    for game_id, moves_string in games:
        game = Game()
        for c in moves_string:
            game.play(int(c))

        winner, _ = check_victory(game.board)
        winner_db = 0
        if winner == "R":
            winner_db = 1
        elif winner == "Y":
            winner_db = 2

        # Mettre à jour la colonne winner
        cur.execute("UPDATE games SET winner = %s WHERE id = %s", (winner_db, game_id))
        print(f"Partie {game_id} mise à jour, winner = {winner_db}")

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Toutes les parties ont été mises à jour")

if __name__ == "__main__":
    update_all_winners()