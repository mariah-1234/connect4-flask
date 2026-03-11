from flask import Flask, render_template, request, jsonify, redirect, url_for
from game import Game
from puissance4 import check_victory
from save_to_db import save_game_from_list
from db import get_statistics, get_connection, insert_game

import random
import os
app = Flask(__name__)

# stockage des parties
games = {}

# ---------------- MENU ----------------
@app.route("/")
def menu():
    return render_template("menu.html")

# ---------------- START GAME ----------------
@app.route("/start_game", methods=["POST"])
def start_game():
    mode = int(request.form.get("mode", 2))
    game_id = len(games) + 1
    games[game_id] = {
        "game": Game(),
        "mode": mode,
        "moves": [],
        "ai_type": "minimax",
        "ai_depth": 4,
        "saved": False
    }
    return redirect(url_for("play", game_id=game_id))

# ---------------- PAGE GAME ----------------
@app.route("/play/<int:game_id>")
def play(game_id):
    game_info = games.get(game_id)
    if not game_info:
        return "Game not found", 404
    return render_template(
        "play.html",
        game_id=game_id,
        mode=game_info["mode"]
    )

# ---------------- PLAY MOVE ----------------
@app.route("/play_move", methods=["POST"])
def play_move():
    data = request.json
    game_id = int(data["game_id"])
    col = data.get("col")

    game_info = games.get(game_id)
    if not game_info:
        return jsonify({"error": "Game not found"}), 404

    game = game_info["game"]
    mode = game_info["mode"]
    ai_type = game_info["ai_type"]
    depth = game_info["ai_depth"]

    # ---------------- HUMAIN ----------------
    if col is not None:
        col = int(col)
        if col in game.valid_moves():
            game.play(col)
            game_info["moves"].append(col)

    # ---------------- IA ----------------
    winner, _ = check_victory(game.board)
    if not winner and (mode == 0 or (mode == 1 and game.current_player == "Y")):
        from minimax import minimax
        if ai_type == "random":
            ai_col = random.choice(game.valid_moves())
        else:
            _, ai_col = minimax(game, depth, True, game.current_player)
        if ai_col is not None:
            game.play(ai_col)
            game_info["moves"].append(ai_col)

    # ---------------- CHECK WIN ----------------
    winner, line = check_victory(game.board)

    # **SAUVEGARDE AUTOMATIQUE SUPPRIMÉE**

    return jsonify({
        "board": game.board,
        "winner": winner,
        "current_player": game.current_player,
        "line": line  # ligne gagnante ajoutée
    })

# ---------------- UNDO ----------------
@app.route("/undo_move", methods=["POST"])
def undo_move():
    game_id = int(request.json["game_id"])
    game_info = games.get(game_id)
    if not game_info:
        return jsonify({"error": "Game not found"}), 404

    game = game_info["game"]
    if game_info["moves"]:
        game_info["moves"].pop()
        game.undo()

    return jsonify({"board": game.board})

# ---------------- RESTART ----------------
@app.route("/restart_game", methods=["POST"])
def restart_game():
    game_id = int(request.json["game_id"])
    game_info = games.get(game_id)
    if not game_info:
        return jsonify({"error": "Game not found"}), 404

    mode = game_info["mode"]
    games[game_id] = {
        "game": Game(),
        "mode": mode,
        "moves": [],
        "ai_type": "minimax",
        "ai_depth": 4,
        "saved": False
    }

    return jsonify({"board": games[game_id]["game"].board})

# ---------------- IA SETTINGS ----------------
@app.route("/set_ai_type", methods=["POST"])
def set_ai_type():
    game_id = int(request.json["game_id"])
    ai_type = request.json["ai_type"]
    if game_id in games:
        games[game_id]["ai_type"] = ai_type
    return jsonify({"status": "ok"})

@app.route("/set_ai_depth", methods=["POST"])
def set_ai_depth():
    game_id = int(request.json["game_id"])
    depth = int(request.json["depth"])
    if game_id in games:
        games[game_id]["ai_depth"] = depth
    return jsonify({"status": "ok"})

# ---------------- SAVE GAME ----------------
@app.route("/save_game", methods=["POST"])
def save_game():
    data = request.json
    game_id = data["game_id"]

    game_info = games.get(game_id)
    if not game_info:
        return jsonify({"error": "Game not found"}), 404

    game = game_info["game"]
    moves = ",".join(map(str, game_info["moves"]))
    winner, _ = check_victory(game.board)
    w = 0
    if winner == "R":
        w = 1
    elif winner == "Y":
        w = 2

    conn = get_connection()
    cur = conn.cursor()

    # Vérifie si cette partie existe déjà
    cur.execute("SELECT id FROM games WHERE moves = %s", (moves,))
    existing = cur.fetchone()

    if existing:
        cur.close()
        conn.close()
        return jsonify({"message": "Cette partie existe déjà !"}), 200

    # Sinon, on insère
    cur.execute(
        "INSERT INTO games (player1, player2, moves, winner) VALUES (%s, %s, %s, %s)",
        ("Player1", "Player2", moves, w)
    )
    conn.commit()
    cur.close()
    conn.close()

    game_info["saved"] = True

    return jsonify({"message": f"Partie sauvegardée : {game_id}"})

# ---------------- STATS ----------------
@app.route("/stats")
def stats():
    stats = get_statistics()
    return render_template("stats.html", stats=stats)

# ---------------- HISTORY ----------------
@app.route("/history")
def history():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, player1, player2, moves, winner
        FROM games
        ORDER BY id DESC
        LIMIT 100
    """)
    games_list = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("history.html", games=games_list)

@app.route("/start_bga_game", methods=["POST"])
def start_bga_game():
    data = request.json
    moves = data.get("moves")
    if not moves:
        return jsonify({"error": "Aucun coup fourni"}), 400

    # Crée une nouvelle partie
    game_id = len(games) + 1
    games[game_id] = {
        "game": Game(),
        "mode": 2,  # Humain vs Humain pour rejouer la partie
        "moves": [],
        "ai_type": "none",
        "saved": False
    }

    game_obj = games[game_id]["game"]
    valid_moves = game_obj.valid_moves()

    for col in moves:
        if col in valid_moves:
            game_obj.play(col)
            games[game_id]["moves"].append(col)
        else:
            print(f"Ignoré coup invalide : {col}")

    return jsonify({"game_id": game_id})
# ---------------- BGA SCRAPER ----------------


# ---------------- AI MOVE ----------------
@app.route("/ai_move", methods=["POST"])
def ai_move():
    data = request.json
    game_id = int(data["game_id"])
    game_info = games.get(game_id)
    if not game_info:
        return jsonify({"error": "Game not found"}), 404

    game = game_info["game"]
    ai_type = game_info["ai_type"]
    depth = game_info["ai_depth"]

    from minimax import minimax
    if ai_type == "random":
        ai_col = random.choice(game.valid_moves())
    else:
        _, ai_col = minimax(game, depth, True, game.current_player)

    if ai_col is not None:
        game.play(ai_col)
        game_info["moves"].append(ai_col)

    winner, line = check_victory(game.board)

    return jsonify({
        "board": game.board,
        "winner": winner,
        "current_player": game.current_player,
        "line": line
    })

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
