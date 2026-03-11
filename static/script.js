let game_id = window.game_id;
let board = [];
let winningLine = [];  // coordonnées des pions gagnants

function drawBoard(){
    const canvas = document.getElementById("board");
    const ctx = canvas.getContext("2d");
    const CELL = 50;
    const ROWS = board.length;
    const COLS = board[0].length;

    ctx.clearRect(0,0,canvas.width,canvas.height);

    for(let r=0;r<ROWS;r++){
        for(let c=0;c<COLS;c++){
            let x = c*CELL;
            let y = r*CELL + 60;

            ctx.beginPath();
            ctx.arc(x+CELL/2, y+CELL/2, 20, 0, Math.PI*2);

            // si ce pion fait partie de la ligne gagnante => vert
            if(winningLine.some(pos => pos[0]===r && pos[1]===c)){
                ctx.fillStyle = "green";
            } else if(board[r][c]=="R") ctx.fillStyle="red";
            else if(board[r][c]=="Y") ctx.fillStyle="yellow";
            else ctx.fillStyle="white";

            ctx.fill();
            ctx.stroke();
        }
    }
}

async function playMove(col){
    const res = await fetch("/play_move",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({game_id, col})
    });
    const data = await res.json();
    board = data.board;
    winningLine = data.winning_line || [];
    drawBoard();

    if(data.winner){
        alert("Winner : " + data.winner);
    }
}

async function undo(){
    const res = await fetch("/undo_move",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({game_id})
    });
    const data = await res.json();
    board = data.board;
    winningLine = [];
    drawBoard();
}

async function restart(){
    const res = await fetch("/restart_game",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({game_id})
    });
    const data = await res.json();
    board = data.board;
    winningLine = [];
    drawBoard();
}

async function saveGame(){
    const res = await fetch("/save_game",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({game_id})
    });
    const data = await res.json();
    alert(data.message);
}  
async function loadBGA() {
    const match_id = document.getElementById('bga_url').value;
    if (!match_id) return alert("Entrez le numéro de table BGA");

    // 1️⃣ Scraper BGA
    const resp = await fetch("/scrape_bga", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({match_id})
    });
    const data = await resp.json();
    if (data.error) return alert("Erreur : " + data.error);

    // 2️⃣ Créer la partie et rejouer tous les coups
    const resp2 = await fetch("/start_bga_game", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({moves: data.moves})
    });
    const gameData = await resp2.json();
    if (gameData.error) return alert("Erreur : " + gameData.error);

    // 3️⃣ Mettre à jour le plateau
    game_id = gameData.game_id;
    const boardResp = await fetch("/play/" + game_id);
    board = []; // initialisé vide
    winningLine = [];
    drawBoard();

    alert("Partie BGA chargée ! ID = " + game_id);
}