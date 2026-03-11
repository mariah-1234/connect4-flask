from config import ROWS, COLS

def check_victory(board):
    """
    Vérifie si un joueur a gagné (4,5,6 pions alignés)
    Retourne : (winner, liste_cases_gagnantes)
    """
    directions = [(0,1),(1,0),(1,1),(1,-1)]
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] == ".":
                continue
            for dr, dc in directions:
                line = [(r,c)]
                for k in range(1,6):
                    nr, nc = r + dr*k, c + dc*k
                    if 0 <= nr < ROWS and 0 <= nc < COLS and board[nr][nc] == board[r][c]:
                        line.append((nr,nc))
                    else:
                        break
                if len(line) >= 4:
                    return board[r][c], line
    return None, []