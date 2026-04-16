let game_id = window.game_id || null;
let board = [];
let winningLine = [];
let gameFinished = false;
let autoPaint = false;
let paintValue = "R";
let paintThinking = false;
let lastMoveCell = null;

// ================= DRAW BOARD =================
function drawBoard() {
    const canvas = document.getElementById("board");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    const CELL = 50;
    const TOP_MARGIN = 60;

    const ROWS = board.length;
    const COLS = board.length ? board[0].length : 0;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = "blue";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    if (!ROWS || !COLS) return;

    for (let c = 0; c < COLS; c++) {
        ctx.fillStyle = "white";
        ctx.font = "16px Arial";
        ctx.fillText(c, c * CELL + CELL / 2 - 4, TOP_MARGIN - 30);
    }

    for (let r = 0; r < ROWS; r++) {
        for (let c = 0; c < COLS; c++) {
            const x = c * CELL;
            const y = TOP_MARGIN + r * CELL;

            ctx.beginPath();
            ctx.arc(x + CELL / 2, y + CELL / 2, CELL / 2 - 5, 0, Math.PI * 2);

            if (winningLine.some(pos => pos[0] === r && pos[1] === c)) {
                ctx.fillStyle = "green";
            } else if (board[r][c] === "R") {
                ctx.fillStyle = "red";
            } else if (board[r][c] === "Y") {
                ctx.fillStyle = "yellow";
            } else {
                ctx.fillStyle = "white";
            }

            ctx.fill();
            ctx.stroke();

            if (lastMoveCell && lastMoveCell.row === r && lastMoveCell.col === c) {
                ctx.strokeStyle = "black";
                ctx.lineWidth = 4;
                ctx.strokeRect(x + 4, y + 4, CELL - 8, CELL - 8);
                ctx.lineWidth = 1;
                ctx.strokeStyle = "black";
            }
        }
    }
}

// ================= SCORES COLONNES =================
function drawColumnScores(scores, bestMove) {
    const canvas = document.getElementById("board");
    if (!canvas || !board.length) return;

    const ctx = canvas.getContext("2d");
    const CELL = 50;
    const TOP_MARGIN = 60;
    const ROWS = board.length;
    const COLS = board[0].length;

    ctx.clearRect(0, TOP_MARGIN + ROWS * CELL, canvas.width, 40);

    for (let c = 0; c < COLS; c++) {
        let text = "X";

        if (scores && scores[c] !== null && scores[c] !== undefined) {
            text = String(scores[c]);
        }

        ctx.fillStyle = (c === bestMove) ? "lime" : "white";
        ctx.font = "12px Arial";
        ctx.fillText(text, c * CELL + 5, TOP_MARGIN + ROWS * CELL + 20);
    }
}

function clearColumnScores() {
    const canvas = document.getElementById("board");
    if (!canvas || !board.length) return;

    const ctx = canvas.getContext("2d");
    const CELL = 50;
    const TOP_MARGIN = 60;
    const ROWS = board.length;

    ctx.clearRect(0, TOP_MARGIN + ROWS * CELL, canvas.width, 40);
}

// ================= ANALYSE TEXTE PAINT =================
function updatePaintAnalysis(prediction, bestMove, depth = null) {
    const predictionEl = document.getElementById("prediction");
    const bestMoveEl = document.getElementById("bestmove");

    if (predictionEl) {
        if (depth !== null && depth !== undefined) {
            predictionEl.innerText = "Prédiction (profondeur " + depth + ") : " + (prediction || "-");
        } else {
            predictionEl.innerText = "Prédiction : " + (prediction || "-");
        }
    }

    if (bestMoveEl) {
        if (bestMove !== null && bestMove !== undefined) {
            bestMoveEl.innerText = "Meilleur coup conseillé : colonne " + bestMove;
        } else {
            bestMoveEl.innerText = "Meilleur coup conseillé : -";
        }
    }
}

function resetPaintAnalysis() {
    const predictionEl = document.getElementById("prediction");
    const bestMoveEl = document.getElementById("bestmove");

    if (predictionEl) predictionEl.innerText = "Prédiction : -";
    if (bestMoveEl) bestMoveEl.innerText = "Meilleur coup conseillé : -";
}

function updateForcedPrediction(text) {
    const el = document.getElementById("forcedprediction");
    if (el) {
        el.innerText = "Analyse complète : " + (text || "-");
    }
}

function resetForcedPrediction() {
    const el = document.getElementById("forcedprediction");
    if (el) {
        el.innerText = "Analyse complète : -";
    }
}

// ================= OUTIL DERNIER COUP =================
function findLastMoveCell(oldBoard, newBoard) {
    if (!oldBoard || !newBoard) return null;

    for (let r = 0; r < newBoard.length; r++) {
        for (let c = 0; c < newBoard[r].length; c++) {
            if (oldBoard[r][c] !== newBoard[r][c]) {
                return { row: r, col: c };
            }
        }
    }
    return null;
}

// ================= NORMAL MODE =================
async function analyzeNormalPosition() {
    return;
}

async function playMove(col) {
    const oldBoard = board.map(row => [...row]);

    const res = await fetch("/play_move", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ game_id, col })
    });

    const data = await res.json();

    if (data.error) {
        alert(data.error);
        return;
    }

    board = data.board;
    winningLine = data.line || [];

    const diff = findLastMoveCell(oldBoard, board);
    if (diff) lastMoveCell = diff;

    drawBoard();
    clearColumnScores();

    const status = document.getElementById("status");

    if (data.winner) {
        gameFinished = true;
        if (status) status.innerText = "Victoire : " + data.winner;
        return;
    }

    if (status) {
        status.innerText = "Tour du joueur : " + data.current_player;
    }
}

async function undo() {
    const res = await fetch("/undo_move", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ game_id })
    });

    const data = await res.json();

    if (data.error) {
        alert(data.error);
        return;
    }

    board = data.board;
    winningLine = [];
    lastMoveCell = null;
    gameFinished = false;
    drawBoard();
    clearColumnScores();

    const status = document.getElementById("status");
    if (status) status.innerText = "Tour du joueur : R";
}

async function restart() {
    const res = await fetch("/restart_game", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ game_id })
    });

    const data = await res.json();

    if (data.error) {
        alert(data.error);
        return;
    }

    board = data.board;
    winningLine = [];
    lastMoveCell = null;
    gameFinished = false;
    drawBoard();
    clearColumnScores();

    const status = document.getElementById("status");
    if (status) status.innerText = "Tour du joueur : R";
}

async function saveGame() {
    const res = await fetch("/save_game", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ game_id })
    });

    const data = await res.json();
    alert(data.message || data.error);
}

async function setAI(type) {
    await fetch("/set_ai_type", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ game_id, ai_type: type })
    });

    alert("IA réglée sur " + type);
}

async function setDepth() {
    const d = prompt("Nouvelle profondeur (1-8) :", 4);
    if (!d) return;

    await fetch("/set_ai_depth", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ game_id, depth: parseInt(d) })
    });

    alert("Profondeur réglée sur " + d);
}

async function aiTurn() {
    if (gameFinished) return;

    const oldBoard = board.map(row => [...row]);

    const res = await fetch("/ai_move", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ game_id })
    });

    const data = await res.json();

    if (data.error) {
        alert(data.error);
        return;
    }

    board = data.board;
    winningLine = data.line || [];

    const diff = findLastMoveCell(oldBoard, board);
    if (diff) lastMoveCell = diff;

    drawBoard();
    clearColumnScores();

    const status = document.getElementById("status");

    if (data.winner) {
        gameFinished = true;
        if (status) status.innerText = "Victoire : " + data.winner;
        return;
    }

    if (status) status.innerText = "Tour du joueur : " + data.current_player;

    if (window.mode === 0) {
        setTimeout(aiTurn, 500);
    }
}

async function playNormalAIOneMove() {
    if (gameFinished) return;

    const status = document.getElementById("status");
    if (status) status.innerText = "🤖 IA réfléchit...";

    const oldBoard = board.map(row => [...row]);

    const res = await fetch("/ai_move", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ game_id })
    });

    const data = await res.json();

    if (data.error) {
        alert(data.error);
        return;
    }

    board = data.board;
    winningLine = data.line || [];

    const diff = findLastMoveCell(oldBoard, board);
    if (diff) lastMoveCell = diff;

    drawBoard();
    clearColumnScores();

    if (data.winner) {
        gameFinished = true;
        if (status) status.innerText = "Victoire : " + data.winner;
        return;
    }

    if (status) {
        status.innerText = "🤖 IA a joué. Tour du joueur : " + data.current_player;
    }
}

function goMenu() {
    window.location.href = "/";
}

// ================= PAINT MODE =================
function updatePaintButtons() {
    const ids = ["paint-red", "paint-yellow", "paint-empty"];
    ids.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.remove("paint-selected");
    });

    if (paintValue === "R") {
        const el = document.getElementById("paint-red");
        if (el) el.classList.add("paint-selected");
    }

    if (paintValue === "Y") {
        const el = document.getElementById("paint-yellow");
        if (el) el.classList.add("paint-selected");
    }

    if (paintValue === ".") {
        const el = document.getElementById("paint-empty");
        if (el) el.classList.add("paint-selected");
    }
}

function setPaintValue(value) {
    paintValue = value;
    updatePaintButtons();

    const status = document.getElementById("status");
    if (!status) return;

    if (value === "R") status.innerText = "Mode sélectionné : Rouge";
    else if (value === "Y") status.innerText = "Mode sélectionné : Jaune";
    else status.innerText = "Mode sélectionné : Effacer";
}

function triggerPaintImport() {
    const input = document.getElementById("paint-file-input");
    if (input) input.click();
}

async function importPaintFile(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("game_id", game_id);

    try {
        const res = await fetch("/paint_import_file", {
            method: "POST",
            body: formData
        });

        const data = await res.json();

        if (data.error) {
            alert(data.error);
            return;
        }

        board = data.board;
        winningLine = data.line || [];
        lastMoveCell = null;
        gameFinished = !!data.winner;
        autoPaint = false;
        paintThinking = false;

        drawBoard();
        resetPaintAnalysis();
        resetForcedPrediction();
        clearColumnScores();

        const status = document.getElementById("status");
        if (status) {
            if (data.winner) {
                status.innerText = "Position importée - Victoire : " + data.winner;
            } else {
                status.innerText = "Position importée - Tour du joueur : " + data.current_player;
            }
        }
    } catch (err) {
        console.error(err);
        alert("Erreur lors de l'import du fichier");
    } finally {
        event.target.value = "";
    }
}

async function paintClick(row, col) {
    const res = await fetch("/paint_click", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            game_id,
            row,
            col,
            value: paintValue
        })
    });

    const data = await res.json();

    if (data.error) {
        alert(data.error);
        return;
    }

    board = data.board;
    lastMoveCell = { row, col };
    winningLine = data.line || [];
    drawBoard();
    clearColumnScores();

    const status = document.getElementById("status");
    if (data.winner) {
        gameFinished = true;
        if (status) status.innerText = "Victoire : " + data.winner;
    } else {
        if (status) status.innerText = "Plateau modifié";
    }

    resetPaintAnalysis();
    resetForcedPrediction();
}

async function paintSuggest() {
    const status = document.getElementById("status");
    if (status) status.innerText = "🔍 Analyse en cours...";

    const res = await fetch("/paint_analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ game_id })
    });

    const data = await res.json();

    if (data.error) {
        alert(data.error);
        return;
    }

    board = data.board;
    winningLine = data.line || [];
    drawBoard();

    if (data.column_scores && Object.keys(data.column_scores).length > 0) {
        drawColumnScores(data.column_scores, data.best_move);
      } else {
          clearColumnScores();
    }   

    updatePaintAnalysis(data.prediction, data.best_move, data.depth);
    updateForcedPrediction(data.forced_prediction);

    if (status) {
        if (data.winner) {
            gameFinished = true;
            status.innerText = "Victoire : " + data.winner;
        } else {
            status.innerText =
                "Analyse terminée - Tour : " + data.current_player +
                (data.best_move !== null && data.best_move !== undefined
                    ? " - meilleur coup : colonne " + data.best_move
                    : "");
        }
    }
}

async function paintAIMove(showAnalysis = true) {
    if (gameFinished || paintThinking) return;

    const status = document.getElementById("status");

    if (status) {
        status.innerText = showAnalysis ? "🤖 IA réfléchit..." : "IA vs IA en cours...";
    }

    paintThinking = true;
    const oldBoard = board.map(row => [...row]);

    try {
        const res = await fetch("/paint_ai_move", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                game_id,
                analyze: showAnalysis
            })
        });

        const data = await res.json();

        if (data.error) {
            alert(data.error);
            return;
        }

        board = data.board;
        winningLine = data.line || [];

        const diff = findLastMoveCell(oldBoard, board);
        if (diff) lastMoveCell = diff;

        drawBoard();

        if (showAnalysis) {
            drawColumnScores(data.column_scores, data.best_move);
            updatePaintAnalysis(data.prediction, data.best_move);
            updateForcedPrediction(data.forced_prediction);
        } else {
            clearColumnScores();
            resetPaintAnalysis();
            resetForcedPrediction();
        }

        if (data.winner) {
            gameFinished = true;
            autoPaint = false;
            if (status) status.innerText = "Victoire : " + data.winner;
            return;
        }

        if (status) {
            status.innerText = showAnalysis
                ? "🤖 IA a joué un seul coup"
                : "IA vs IA en cours...";
        }
    } catch (err) {
        console.error(err);
        alert("Erreur lors du coup IA");
    } finally {
        paintThinking = false;
    }
}

async function paintAIAuto() {
    if (gameFinished || paintThinking) return;

    autoPaint = true;
    clearColumnScores();
    resetPaintAnalysis();
    resetForcedPrediction();

    const status = document.getElementById("status");
    if (status) status.innerText = "IA vs IA en cours...";

    runPaintAuto();
}

async function runPaintAuto() {
    if (!autoPaint || gameFinished) return;

    await paintAIMove(false);

    if (!gameFinished && autoPaint) {
        setTimeout(runPaintAuto, 200);
    }
}

function stopAutoPaint() {
    autoPaint = false;
    const status = document.getElementById("status");
    if (status) status.innerText = "IA vs IA arrêté";
}

async function restartPaint() {
    const res = await fetch("/paint_restart", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ game_id })
    });

    const data = await res.json();

    if (data.error) {
        alert(data.error);
        return;
    }

    board = data.board;
    winningLine = [];
    lastMoveCell = null;
    gameFinished = false;
    autoPaint = false;
    paintThinking = false;
    drawBoard();
    clearColumnScores();
    resetPaintAnalysis();
    resetForcedPrediction();

    const status = document.getElementById("status");
    if (status) {
        status.innerText = "Choisissez Rouge, Jaune ou Effacer puis dessinez le plateau";
    }
}

async function savePaintGame() {
    const res = await fetch("/paint_save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ game_id })
    });

    const data = await res.json();
    alert(data.message || data.error);
}

async function setPaintAI(type) {
    await fetch("/paint_set_ai_type", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ game_id, ai_type: type })
    });

    alert("IA réglée sur " + type);
}

async function setPaintDepth() {
    const d = prompt("Nouvelle profondeur (1-8) :", 6);
    if (!d) return;

    await fetch("/paint_set_ai_depth", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ game_id, depth: parseInt(d) })
    });

    alert("Profondeur réglée sur " + d);
}

async function undoPaint() {
    const res = await fetch("/paint_undo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ game_id })
    });

    const data = await res.json();

    if (data.error) {
        alert(data.error);
        return;
    }

    board = data.board;
    winningLine = data.line || [];
    lastMoveCell = null;
    gameFinished = !!data.winner;
    autoPaint = false;
    paintThinking = false;

    drawBoard();
    clearColumnScores();
    resetPaintAnalysis();
    resetForcedPrediction();

    const status = document.getElementById("status");
    if (status) {
        if (data.winner) {
            status.innerText = "Victoire : " + data.winner;
        } else {
            status.innerText = "Tour du joueur : " + data.current_player;
        }
    }
}

// ================= PAGE INIT =================
window.addEventListener("load", () => {
    const canvas = document.getElementById("board");
    if (!canvas) return;

    // ---------- MODE PAINT ----------
    if (window.page_mode === "paint") {
        board = window.paint_initial_board || Array.from({ length: 9 }, () => Array(9).fill("."));
        winningLine = [];
        lastMoveCell = null;
        drawBoard();
        clearColumnScores();
        updatePaintButtons();
        resetPaintAnalysis();
        resetForcedPrediction();

        canvas.addEventListener("click", async (e) => {
            if (gameFinished || paintThinking) return;

            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const col = Math.floor(x / 50);
            const row = Math.floor((y - 60) / 50);

            if (row < 0 || row >= 9 || col < 0 || col >= 9) return;

            await paintClick(row, col);
        });

        return;
    }

    // ---------- MODE NORMAL ----------
    if (window.page_mode === "play") {
        board = Array.from({ length: 9 }, () => Array(9).fill("."));
        winningLine = [];
        lastMoveCell = null;
        drawBoard();
        clearColumnScores();

        canvas.addEventListener("click", async (e) => {
            if (gameFinished) return;

            const col = Math.floor(e.offsetX / 50);
            await playMove(col);
        });

        const status = document.getElementById("status");
        if (status) status.innerText = "Tour du joueur : R";

        if (window.mode === 0) {
            setTimeout(aiTurn, 600);
        }
    }
});