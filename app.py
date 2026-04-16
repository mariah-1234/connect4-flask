from flask import Flask, render_template, request, jsonify, redirect, url_for
from game import Game
from puissance4 import check_victory
from save_to_db import save_game_from_list
from db import get_statistics, get_connection
from minimax import minimax
from config import ROWS, COLS
import random
import os
import json
from werkzeug.utils import secure_filename
from init_db import init_db

app = Flask(__name__)

# stockage des parties en mémoire
games = {}

# =========================================================
# OUTILS ANALYSE
# =========================================================
COLOR_NAME = {
    "R": "Rouge",
    "Y": "Jaune"
}


def predict_label(score):
    if score is None:
        return "Incertain"

    if score >= 900000:
        return "Victoire certaine"
    elif score >= 500000:
        return "Victoire probable"
    elif score <= -900000:
        return "Défaite certaine"
    elif score <= -500000:
        return "Défaite probable"
    elif -100 <= score <= 100:
        return "Nul probable"
    else:
        return "Incertain"


def board_key(board):
    return tuple(tuple(row) for row in board)


def ordered_moves(valid_moves):
    center = COLS // 2
    return sorted(valid_moves, key=lambda c: abs(c - center))


def forced_outcome_search(game, depth, root_player, cache=None):
    if cache is None:
        cache = {}

    key = (board_key(game.board), game.current_player, depth, root_player)
    if key in cache:
        return cache[key]

    winner, _ = check_victory(game.board)
    if winner:
        if winner == root_player:
            result = (1, 0)
        else:
            result = (-1, 0)
        cache[key] = result
        return result

    valid = game.valid_moves()
    if not valid:
        result = (0, 0)
        cache[key] = result
        return result

    if depth == 0:
        result = (None, None)
        cache[key] = result
        return result

    current = game.current_player
    valid = ordered_moves(valid)

    if current == root_player:
        best_win = None
        best_draw = None
        best_loss = None
        unknown_found = False

        for col in valid:
            g = game.copy()
            g.play(col)
            outcome, plies = forced_outcome_search(g, depth - 1, root_player, cache)

            if outcome == 1:
                candidate = (1, plies + 1)
                if best_win is None or candidate[1] < best_win[1]:
                    best_win = candidate

            elif outcome == 0:
                candidate = (0, plies + 1)
                if best_draw is None or candidate[1] < best_draw[1]:
                    best_draw = candidate

            elif outcome == -1:
                candidate = (-1, plies + 1)
                if best_loss is None or candidate[1] > best_loss[1]:
                    best_loss = candidate

            else:
                unknown_found = True

            if best_win is not None and best_win[1] == 1:
                cache[key] = best_win
                return best_win

        if best_win is not None:
            cache[key] = best_win
            return best_win

        if best_draw is not None:
            cache[key] = best_draw
            return best_draw

        if unknown_found:
            result = (None, None)
            cache[key] = result
            return result

        if best_loss is not None:
            cache[key] = best_loss
            return best_loss

    else:
        best_loss_for_root = None
        best_draw = None
        best_win_for_root = None
        unknown_found = False

        for col in valid:
            g = game.copy()
            g.play(col)
            outcome, plies = forced_outcome_search(g, depth - 1, root_player, cache)

            if outcome == -1:
                candidate = (-1, plies + 1)
                if best_loss_for_root is None or candidate[1] < best_loss_for_root[1]:
                    best_loss_for_root = candidate

            elif outcome == 0:
                candidate = (0, plies + 1)
                if best_draw is None or candidate[1] < best_draw[1]:
                    best_draw = candidate

            elif outcome == 1:
                candidate = (1, plies + 1)
                if best_win_for_root is None or candidate[1] > best_win_for_root[1]:
                    best_win_for_root = candidate

            else:
                unknown_found = True

            if best_loss_for_root is not None and best_loss_for_root[1] == 1:
                cache[key] = best_loss_for_root
                return best_loss_for_root

        if best_loss_for_root is not None:
            cache[key] = best_loss_for_root
            return best_loss_for_root

        if best_draw is not None:
            cache[key] = best_draw
            return best_draw

        if unknown_found:
            result = (None, None)
            cache[key] = result
            return result

        if best_win_for_root is not None:
            cache[key] = best_win_for_root
            return best_win_for_root

    result = (None, None)
    cache[key] = result
    return result


def forced_prediction_text(outcome, plies, root_player):
    if outcome is None or plies is None:
        return "Incertain à cette profondeur"

    if outcome == 0:
        return "Nul forcé"

    if outcome == 1:
        winner = root_player
        winner_moves = (plies + 1) // 2
    else:
        winner = "Y" if root_player == "R" else "R"
        winner_moves = plies // 2

    if winner_moves <= 1:
        return f"{COLOR_NAME[winner]} gagne en 1 coup"

    return f"{COLOR_NAME[winner]} gagne en {winner_moves} coups"


def best_forced_move(game, depth, root_player, cache=None):
    if cache is None:
        cache = {}

    valid = ordered_moves(game.valid_moves())
    if not valid:
        return None, None, None

    best_col = None
    best_outcome = None
    best_plies = None

    for col in valid:
        g = game.copy()
        g.play(col)

        outcome, plies = forced_outcome_search(g, depth - 1, root_player, cache)

        if outcome is None:
            continue

        total_plies = plies + 1

        if best_col is None:
            best_col = col
            best_outcome = outcome
            best_plies = total_plies
            continue

        # priorité :
        # 1) victoire la plus rapide
        # 2) nul
        # 3) défaite la plus tardive
        if outcome == 1:
            if best_outcome != 1 or total_plies < best_plies:
                best_col = col
                best_outcome = outcome
                best_plies = total_plies

        elif outcome == 0:
            if best_outcome not in [1, 0] or (best_outcome == 0 and total_plies < best_plies):
                best_col = col
                best_outcome = outcome
                best_plies = total_plies

        elif outcome == -1:
            if best_outcome not in [1, 0, -1] or (best_outcome == -1 and total_plies > best_plies):
                best_col = col
                best_outcome = outcome
                best_plies = total_plies

    return best_col, best_outcome, best_plies


def analyze_game_position(game, depth):
    current = game.current_player

    winner, _ = check_victory(game.board)
    if winner:
        return {
            "prediction": f"Victoire : {COLOR_NAME[winner]}",
            "best_move": None,
            "global_score": None,
            "column_scores": {},
            "forced_prediction": f"{COLOR_NAME[winner]} a déjà gagné"
        }

    valid = game.valid_moves()
    if not valid:
        return {
            "prediction": "Nul probable",
            "best_move": None,
            "global_score": 0,
            "column_scores": {},
            "forced_prediction": "Nul forcé"
        }

    empty_cells = sum(row.count(".") for row in game.board)

    if empty_cells <= 14:
        forced_depth = empty_cells
    else:
        forced_depth = depth

    # cache partagé pour éviter de recalculer les mêmes positions
    cache = {}

    outcome, plies = forced_outcome_search(game, forced_depth, current, cache)
    forced_prediction = forced_prediction_text(outcome, plies, current)

    best_move, _, _ = best_forced_move(game, forced_depth, current, cache)

    if outcome == 1:
        prediction = "Victoire certaine"
        global_score = 1000000
    elif outcome == -1:
        prediction = "Défaite certaine"
        global_score = -1000000
    elif outcome == 0:
        prediction = "Nul probable"
        global_score = 0
    else:
        prediction = "Incertain"
        global_score = None

    return {
        "prediction": prediction,
        "best_move": best_move,
        "global_score": global_score,
        "column_scores": {},
        "forced_prediction": forced_prediction
    }


# =========================================================
# MENU
# =========================================================
@app.route("/")
def menu():
    return render_template("menu.html")


# =========================================================
# START GAME
# =========================================================
@app.route("/start_game", methods=["POST"])
def start_game():
    mode = int(request.form.get("mode", 2))
    game_id = len(games) + 1

    depth = 3 if mode == 0 else 4

    games[game_id] = {
        "game": Game(),
        "mode": mode,
        "moves": [],
        "ai_type": "minimax",
        "ai_depth": depth,
        "saved": False
    }

    return redirect(url_for("play", game_id=game_id))


# =========================================================
# PAGE JEU NORMAL
# =========================================================
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


# =========================================================
# ANALYSE POSITION MODE NORMAL
# =========================================================
@app.route("/analyze_position", methods=["POST"])
def analyze_position():
    data = request.json
    game_id = int(data["game_id"])

    game_info = games.get(game_id)
    if not game_info:
        return jsonify({"error": "Game not found"}), 404

    game = game_info["game"]
    depth = game_info["ai_depth"]

    winner, line = check_victory(game.board)
    analysis = analyze_game_position(game, depth)

    return jsonify({
        "board": game.board,
        "winner": winner,
        "line": line,
        "current_player": game.current_player,
        "prediction": analysis["prediction"],
        "forced_prediction": analysis["forced_prediction"],
        "best_move": analysis["best_move"],
        "column_scores": analysis["column_scores"]
    })


# =========================================================
# COUP NORMAL
# =========================================================
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

    winner, line = check_victory(game.board)
    if winner:
        return jsonify({
            "board": game.board,
            "winner": winner,
            "current_player": game.current_player,
            "line": line
        })

    if col is not None:
        col = int(col)
        if col in game.valid_moves():
            game.play(col)
            game_info["moves"].append(col)

    winner, line = check_victory(game.board)

    if not winner and mode == 1 and game.current_player == "Y":
        valid = game.valid_moves()
        if valid:
            if ai_type == "random":
                ai_col = random.choice(valid)
            else:
                _, ai_col = minimax(game, depth, -9999999, 9999999, True, game.current_player)

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


# =========================================================
# IA MOVE
# =========================================================
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

    winner, line = check_victory(game.board)
    if winner:
        return jsonify({
            "board": game.board,
            "winner": winner,
            "current_player": game.current_player,
            "line": line
        })

    valid = game.valid_moves()
    if not valid:
        return jsonify({
            "board": game.board,
            "winner": None,
            "current_player": game.current_player,
            "line": []
        })

    if ai_type == "random":
        ai_col = random.choice(valid)
    else:
        _, ai_col = minimax(game, depth, -9999999, 9999999, True, game.current_player)

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


# =========================================================
# UNDO
# =========================================================
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


# =========================================================
# RESTART
# =========================================================
@app.route("/restart_game", methods=["POST"])
def restart_game():
    game_id = int(request.json["game_id"])
    game_info = games.get(game_id)
    if not game_info:
        return jsonify({"error": "Game not found"}), 404

    mode = game_info["mode"]
    depth = 3 if mode == 0 else 4

    games[game_id] = {
        "game": Game(),
        "mode": mode,
        "moves": [],
        "ai_type": "minimax",
        "ai_depth": depth,
        "saved": False
    }

    return jsonify({"board": games[game_id]["game"].board})


# =========================================================
# IA SETTINGS
# =========================================================
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


# =========================================================
# SAVE GAME
# =========================================================
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

    cur.execute("SELECT id FROM games WHERE moves = %s", (moves,))
    existing = cur.fetchone()
    if existing:
        cur.close()
        conn.close()
        return jsonify({"message": "Cette partie existe déjà !"}), 200

    cur.execute(
        "INSERT INTO games (player1, player2, moves, winner) VALUES (%s, %s, %s, %s)",
        ("Player 1", "Player 2", moves, w)
    )
    conn.commit()
    cur.close()
    conn.close()

    game_info["saved"] = True
    return jsonify({"message": f"Partie sauvegardée : {game_id}"})


# =========================================================
# STATS
# =========================================================
@app.route("/stats")
def stats():
    stats = get_statistics()
    return render_template("stats.html", stats=stats)


# =========================================================
# HISTORY
# =========================================================
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


# =========================================================
# REPLAY GAME FROM DB
# =========================================================
@app.route("/replay_game/<int:db_game_id>")
def replay_game(db_game_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT moves FROM games WHERE id = %s", (db_game_id,))
    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return "Partie introuvable", 404

    moves_string = row[0]

    if moves_string:
        moves_string = str(moves_string).strip()

        if "," in moves_string:
            try:
                moves = [int(x) for x in moves_string.split(",") if x.strip() != ""]
            except Exception:
                moves = []
        else:
            try:
                moves = [int(ch) for ch in moves_string if ch.isdigit()]
            except Exception:
                moves = []
    else:
        moves = []

    game_id = len(games) + 1
    games[game_id] = {
        "game": Game(),
        "mode": "replay",
        "moves": moves,
        "replay_index": 0,
        "saved": False
    }

    return redirect(url_for("replay_view", game_id=game_id))


# =========================================================
# PAGE REPLAY
# =========================================================
@app.route("/replay/<int:game_id>")
def replay_view(game_id):
    game_info = games.get(game_id)
    if not game_info:
        return "Game not found", 404

    return render_template("replay.html", game_id=game_id)


# =========================================================
# REPLAY STEP
# =========================================================
@app.route("/replay_step", methods=["POST"])
def replay_step():
    data = request.json
    game_id = int(data["game_id"])
    direction = data.get("direction")

    game_info = games.get(game_id)
    if not game_info:
        return jsonify({"error": "Game not found"}), 404

    moves = game_info.get("moves", [])
    index = game_info.get("replay_index", 0)

    if direction == "next":
        index = min(index + 1, len(moves))
    elif direction == "prev":
        index = max(index - 1, 0)

    game_info["replay_index"] = index

    g = Game()
    for i in range(index):
        if moves[i] in g.valid_moves():
            g.play(moves[i])

    winner, line = check_victory(g.board)

    return jsonify({
        "board": g.board,
        "winner": winner,
        "line": line,
        "index": index,
        "total": len(moves)
    })


# =========================================================
# START BGA GAME
# =========================================================
@app.route("/start_bga_game", methods=["POST"])
def start_bga_game():
    data = request.json
    moves = data.get("moves")

    if not moves:
        return jsonify({"error": "Aucun coup fourni"}), 400

    game_id = len(games) + 1
    games[game_id] = {
        "game": Game(),
        "mode": 2,
        "moves": [],
        "ai_type": "none",
        "ai_depth": 4,
        "saved": False
    }

    game_obj = games[game_id]["game"]
    for col in moves:
        if col in game_obj.valid_moves():
            game_obj.play(col)
            games[game_id]["moves"].append(col)

    return jsonify({"game_id": game_id})


# =========================================================
# OUTILS PAINT
# =========================================================
def copy_board(board):
    return [row[:] for row in board]


def rebuild_game_from_board(board):
    """
    Reconstruit un objet Game cohérent à partir du plateau.
    ATTENTION : l'ordre des coups reconstruit ici n'est PAS l'ordre réel chronologique.
    Ne pas utiliser g.moves pour sauvegarder une vraie partie importée ou peinte.
    """
    g = Game()
    g.board = [["." for _ in range(COLS)] for _ in range(ROWS)]
    g.current_player = "R"

    if hasattr(g, "moves"):
        g.moves = []

    for c in range(COLS):
        col_values = []
        for r in range(ROWS):
            if board[r][c] != ".":
                col_values.append(board[r][c])

        for val in reversed(col_values):
            g.current_player = val
            g.play(c)

    return g


def detect_player_from_board(board):
    r = sum(row.count("R") for row in board)
    y = sum(row.count("Y") for row in board)
    return "R" if r <= y else "Y"


def normalize_board(raw_board):
    if not isinstance(raw_board, list) or len(raw_board) != ROWS:
        raise ValueError(f"Le plateau doit contenir {ROWS} lignes")

    board = []
    for row in raw_board:
        if isinstance(row, str):
            row = list(row.strip())

        if not isinstance(row, list) or len(row) != COLS:
            raise ValueError(f"Chaque ligne doit contenir {COLS} colonnes")

        clean_row = []
        for cell in row:
            if cell not in ["R", "Y", "."]:
                raise ValueError("Les cases doivent être uniquement R, Y ou .")
            clean_row.append(cell)
        board.append(clean_row)

    return board


def board_from_moves_string(moves_string):
    g = Game()
    moves = []

    for ch in moves_string:
        if ch.isdigit():
            col = int(ch)
            if 0 <= col < COLS and col in g.valid_moves():
                g.play(col)
                moves.append(col)

    return g.board, moves, g.current_player


def parse_txt_content(content, filename=""):
    text = content.strip()

    if not text:
        base = os.path.splitext(filename)[0]
        if base.isdigit():
            return board_from_moves_string(base)
        raise ValueError("Fichier vide et nom de fichier invalide")

    compact = text.replace(",", "").replace(" ", "").replace("\n", "")
    if compact.isdigit():
        return board_from_moves_string(compact)

    lines = [line.strip().replace(" ", "") for line in text.splitlines() if line.strip()]
    if len(lines) == ROWS and all(len(line) == COLS for line in lines):
        board = []
        for line in lines:
            row = list(line)
            for cell in row:
                if cell not in ["R", "Y", "."]:
                    raise ValueError("Plateau TXT invalide : seulement R, Y ou .")
            board.append(row)

        real_game = rebuild_game_from_board(board)
        current = detect_player_from_board(real_game.board)
        moves = []
        return real_game.board, moves, current

    base = os.path.splitext(filename)[0]
    if base.isdigit():
        return board_from_moves_string(base)

    raise ValueError("Format TXT non reconnu")


def parse_json_content(content):
    data = json.loads(content)

    if isinstance(data, dict) and "board" in data:
        board = normalize_board(data["board"])
        real_game = rebuild_game_from_board(board)
        current = detect_player_from_board(real_game.board)
        moves = []
        return real_game.board, moves, current

    if isinstance(data, dict) and "moves" in data:
        moves_data = data["moves"]

        if isinstance(moves_data, list):
            moves_string = "".join(str(x) for x in moves_data)
        else:
            moves_string = str(moves_data)

        return board_from_moves_string(moves_string)

    raise ValueError("Format JSON non reconnu")


# =========================================================
# PAINT PAGE
# =========================================================
@app.route("/paint")
def paint_page():
    game_id = len(games) + 1
    paint_board = [["." for _ in range(COLS)] for _ in range(ROWS)]

    games[game_id] = {
    "game": Game(),
    "mode": "paint",
    "moves": [],
    "moves_known": False,
    "moves_history": [],
    "ai_type": "minimax",
    "ai_depth": 5,
    "saved": False,
    "paint_board": copy_board(paint_board),
    "paint_history": [],
    "game_over": False
}

    return render_template(
        "paint.html",
        game_id=game_id,
        board=paint_board
    )


# =========================================================
# PAINT IMPORT FILE
# =========================================================
@app.route("/paint_import_file", methods=["POST"])
def paint_import_file():
    game_id = request.form.get("game_id")
    if not game_id:
        return jsonify({"error": "game_id manquant"}), 400

    game_id = int(game_id)
    game_info = games.get(game_id)
    if not game_info:
        return jsonify({"error": "Game not found"}), 404

    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier envoyé"}), 400

    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"error": "Fichier invalide"}), 400

    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()

    try:
        content = file.read().decode("utf-8")

        if ext == ".json":
            board, moves, current_player = parse_json_content(content)
        elif ext == ".txt":
            board, moves, current_player = parse_txt_content(content, filename)
        else:
            return jsonify({"error": "Format accepté : .txt ou .json"}), 400

        winner, line = check_victory(board)

        game_info["paint_board"] = copy_board(board)
        game_info["paint_history"] = []
        game_info["moves_history"] = []

        game_info["game"] = rebuild_game_from_board(board)
        game_info["game"].current_player = current_player

        # IMPORTANT : on garde exactement la vraie séquence si elle existe
        game_info["moves"] = moves[:] if moves else []
        game_info["moves_known"] = bool(moves)

        game_info["saved"] = False
        game_info["game_over"] = bool(winner)

        return jsonify({
            "board": game_info["paint_board"],
            "winner": winner,
            "line": line,
            "current_player": current_player
        })

    except Exception as e:
        return jsonify({"error": f"Import impossible : {str(e)}"}), 400

# =========================================================
# PAINT CLICK
# =========================================================
@app.route("/paint_click", methods=["POST"])
def paint_click():
    data = request.json
    game_id = int(data["game_id"])
    row = int(data["row"])
    col = int(data["col"])
    value = data["value"]

    game_info = games.get(game_id)
    if not game_info:
        return jsonify({"error": "Game not found"}), 404

    if game_info.get("game_over"):
        return jsonify({
            "board": game_info["paint_board"],
            "winner": None,
            "line": []
        })

    if value not in ["R", "Y", "."]:
        return jsonify({"error": "Invalid value"}), 400

    # on sauvegarde l'état précédent pour undo
    game_info.setdefault("paint_history", []).append(copy_board(game_info["paint_board"]))
    game_info.setdefault("moves_history", []).append({
        "moves": game_info["moves"][:],
        "moves_known": game_info["moves_known"]
    })

    # modification manuelle => séquence réelle perdue
    game_info["paint_board"][row][col] = value
    game_info["moves"] = []
    game_info["moves_known"] = False

    winner, line = check_victory(game_info["paint_board"])
    game_info["game_over"] = bool(winner)

    return jsonify({
        "board": game_info["paint_board"],
        "winner": winner,
        "line": line
    })
# =========================================================
# PAINT ANALYZE
# =========================================================
@app.route("/paint_analyze", methods=["POST"])
def paint_analyze():
    data = request.json
    game_id = int(data["game_id"])

    game_info = games.get(game_id)
    if not game_info:
        return jsonify({"error": "Game not found"}), 404

    paint_board = game_info["paint_board"]

    real_game = rebuild_game_from_board(paint_board)
    current = detect_player_from_board(real_game.board)
    real_game.current_player = current

    winner, line = check_victory(real_game.board)
    analysis = analyze_game_position(real_game, game_info["ai_depth"])

    return jsonify({
        "board": real_game.board,
        "winner": winner,
        "line": line,
        "current_player": real_game.current_player,
        "prediction": analysis["prediction"],
        "forced_prediction": analysis["forced_prediction"],
        "best_move": analysis["best_move"],
        "column_scores": analysis["column_scores"],
        "depth": game_info["ai_depth"]
    })


# =========================================================
# PAINT IA MOVE
# =========================================================
@app.route("/paint_ai_move", methods=["POST"])
def paint_ai_move():
    data = request.json
    game_id = int(data["game_id"])
    do_analysis = bool(data.get("analyze", True))

    game_info = games.get(game_id)
    if not game_info:
        return jsonify({"error": "Game not found"}), 404

    if game_info.get("game_over"):
        winner, line = check_victory(game_info["paint_board"])

        if do_analysis:
            analysis = analyze_game_position(game_info["game"], game_info["ai_depth"])
            return jsonify({
                "board": game_info["paint_board"],
                "winner": winner,
                "line": line,
                "prediction": analysis["prediction"],
                "forced_prediction": analysis["forced_prediction"],
                "best_move": analysis["best_move"],
                "column_scores": analysis["column_scores"]
            })
        else:
            return jsonify({
                "board": game_info["paint_board"],
                "winner": winner,
                "line": line,
                "prediction": None,
                "forced_prediction": None,
                "best_move": None,
                "column_scores": {}
            })

    paint_board = game_info["paint_board"]

    real_game = rebuild_game_from_board(paint_board)
    current = detect_player_from_board(real_game.board)
    real_game.current_player = current

    winner, line = check_victory(real_game.board)
    if winner:
        game_info["paint_board"] = copy_board(real_game.board)
        game_info["game"] = real_game
        game_info["game_over"] = True

        if do_analysis:
            analysis = analyze_game_position(real_game, game_info["ai_depth"])
            return jsonify({
                "board": game_info["paint_board"],
                "winner": winner,
                "line": line,
                "prediction": analysis["prediction"],
                "forced_prediction": analysis["forced_prediction"],
                "best_move": analysis["best_move"],
                "column_scores": analysis["column_scores"]
            })
        else:
            return jsonify({
                "board": game_info["paint_board"],
                "winner": winner,
                "line": line,
                "prediction": None,
                "forced_prediction": None,
                "best_move": None,
                "column_scores": {}
            })

    depth = game_info["ai_depth"]
    valid = real_game.valid_moves()

    if not valid:
        if do_analysis:
            analysis = analyze_game_position(real_game, depth)
            return jsonify({
                "board": real_game.board,
                "winner": None,
                "line": [],
                "prediction": analysis["prediction"],
                "forced_prediction": analysis["forced_prediction"],
                "best_move": analysis["best_move"],
                "column_scores": analysis["column_scores"]
            })
        else:
            return jsonify({
                "board": real_game.board,
                "winner": None,
                "line": [],
                "prediction": None,
                "forced_prediction": None,
                "best_move": None,
                "column_scores": {}
            })

    # sauvegarde état précédent pour undo
    game_info.setdefault("paint_history", []).append(copy_board(game_info["paint_board"]))
    game_info.setdefault("moves_history", []).append({
        "moves": game_info["moves"][:],
        "moves_known": game_info["moves_known"]
    })

    if do_analysis:
        analysis = analyze_game_position(real_game, depth)
        ai_col = analysis["best_move"]
    else:
        if game_info["ai_type"] == "random":
            ai_col = random.choice(valid)
        else:
            _, ai_col = minimax(real_game, depth, -9999999, 9999999, True, current)

    if ai_col is not None:
        real_game.play(ai_col)

    winner, line = check_victory(real_game.board)

    game_info["paint_board"] = copy_board(real_game.board)
    game_info["game"] = real_game

    # IMPORTANT :
    # si la séquence importée est connue, on ajoute exactement le nouveau coup
    if ai_col is not None and game_info.get("moves_known", False):
        game_info["moves"].append(ai_col)

    # si la séquence n'est pas connue, on ne tente pas de la reconstruire
    if not game_info.get("moves_known", False):
        game_info["moves"] = []

    game_info["game_over"] = bool(winner)

    if do_analysis:
        new_analysis = analyze_game_position(real_game, depth)
        return jsonify({
            "board": game_info["paint_board"],
            "winner": winner,
            "line": line,
            "current_player": real_game.current_player,
            "prediction": new_analysis["prediction"],
            "forced_prediction": new_analysis["forced_prediction"],
            "best_move": new_analysis["best_move"],
            "column_scores": new_analysis["column_scores"]
        })
    else:
        return jsonify({
            "board": game_info["paint_board"],
            "winner": winner,
            "line": line,
            "current_player": real_game.current_player,
            "prediction": None,
            "forced_prediction": None,
            "best_move": None,
            "column_scores": {}
        })

# =========================================================
# PAINT UNDO
# =========================================================
@app.route("/paint_undo", methods=["POST"])
def paint_undo():
    data = request.json
    game_id = int(data["game_id"])

    game_info = games.get(game_id)
    if not game_info:
        return jsonify({"error": "Game not found"}), 404

    history = game_info.get("paint_history", [])
    moves_history = game_info.get("moves_history", [])

    if not history:
        current = detect_player_from_board(game_info["paint_board"])
        return jsonify({
            "board": game_info["paint_board"],
            "winner": None,
            "line": [],
            "current_player": current
        })

    previous_board = history.pop()
    previous_moves_state = moves_history.pop() if moves_history else {
        "moves": [],
        "moves_known": False
    }

    game_info["paint_board"] = copy_board(previous_board)
    game_info["moves"] = previous_moves_state["moves"][:]
    game_info["moves_known"] = previous_moves_state["moves_known"]

    real_game = rebuild_game_from_board(previous_board)
    current = detect_player_from_board(real_game.board)
    real_game.current_player = current

    game_info["game"] = real_game

    winner, line = check_victory(real_game.board)
    game_info["game_over"] = bool(winner)

    return jsonify({
        "board": game_info["paint_board"],
        "winner": winner,
        "line": line,
        "current_player": real_game.current_player
    })
# =========================================================
# PAINT RESTART
# =========================================================
@app.route("/paint_restart", methods=["POST"])
def paint_restart():
    data = request.json
    game_id = int(data["game_id"])

    game_info = games.get(game_id)
    if not game_info:
        return jsonify({"error": "Game not found"}), 404

    empty_board = [["." for _ in range(COLS)] for _ in range(ROWS)]

    game_info["game"] = Game()
    game_info["moves"] = []
    game_info["moves_known"] = False
    game_info["moves_history"] = []
    game_info["saved"] = False
    game_info["paint_board"] = copy_board(empty_board)
    game_info["paint_history"] = []
    game_info["game_over"] = False

    return jsonify({"board": game_info["paint_board"]})
# =========================================================
# PAINT SAVE
# =========================================================
@app.route("/paint_save", methods=["POST"])
def paint_save():
    data = request.json
    game_id = int(data["game_id"])

    game_info = games.get(game_id)
    if not game_info:
        return jsonify({"error": "Game not found"}), 404

    if not game_info.get("moves_known", False):
        return jsonify({
            "error": "Impossible de sauvegarder cette position en séquence de coups : le plateau a été modifié manuellement et l'ordre exact des coups n'est pas connu."
        }), 400

    moves_list = game_info.get("moves", [])

    if not moves_list:
        return jsonify({"message": "Aucun coup à sauvegarder"}), 200

    moves_string = ",".join(map(str, moves_list))

    winner, _ = check_victory(game_info["paint_board"])
    w = 0
    if winner == "R":
        w = 1
    elif winner == "Y":
        w = 2

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM games WHERE moves = %s", (moves_string,))
    existing = cur.fetchone()
    if existing:
        cur.close()
        conn.close()
        return jsonify({"message": "Cette partie existe déjà !"}), 200

    cur.execute(
        "INSERT INTO games (player1, player2, moves, winner) VALUES (%s, %s, %s, %s)",
        ("Player 1", "Player 2", moves_string, w)
    )
    conn.commit()
    cur.close()
    conn.close()

    game_info["saved"] = True
    return jsonify({"message": f"Partie Paint sauvegardée avec succès : {moves_string}"})


# =========================================================
# PAINT IA TYPE
# =========================================================
@app.route("/paint_set_ai_type", methods=["POST"])
def paint_set_ai_type():
    data = request.json
    game_id = int(data["game_id"])
    ai_type = data["ai_type"]

    if game_id in games:
        games[game_id]["ai_type"] = ai_type

    return jsonify({"status": "ok"})


# =========================================================
# PAINT IA DEPTH
# =========================================================
@app.route("/paint_set_ai_depth", methods=["POST"])
def paint_set_ai_depth():
    data = request.json
    game_id = int(data["game_id"])
    depth = int(data["depth"])

    if game_id in games:
        games[game_id]["ai_depth"] = depth

    return jsonify({"status": "ok"})


# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)