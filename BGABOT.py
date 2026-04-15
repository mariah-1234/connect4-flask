import os
import time
import random
import math
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException

# -------------------- CONFIG --------------------
ROWS, COLS = 9, 9
PLAYER_PIECE, AI_PIECE, EMPTY = 1, 2, 0
CENTER_COL = COLS // 2

# -------------------- IA LOGIC --------------------
def create_board():
    return [[EMPTY]*COLS for _ in range(ROWS)]

def drop_piece(board,row,col,piece):
    board[row][col]=piece

def is_valid_location(board,col):
    return board[0][col]==EMPTY

def get_next_open_row(board,col):
    for r in reversed(range(ROWS)):
        if board[r][col]==EMPTY:
            return r
    return None

def winning_move(board,piece):
    # horizontal
    for r in range(ROWS):
        for c in range(COLS-3):
            if all(board[r][c+i]==piece for i in range(4)): return True
    # vertical
    for c in range(COLS):
        for r in range(ROWS-3):
            if all(board[r+i][c]==piece for i in range(4)): return True
    # diag /
    for r in range(3,ROWS):
        for c in range(COLS-3):
            if all(board[r-i][c+i]==piece for i in range(4)): return True
    # diag \
    for r in range(ROWS-3):
        for c in range(COLS-3):
            if all(board[r+i][c+i]==piece for i in range(4)): return True
    return False

def evaluate_window(window,piece):
    score = 0
    opp_piece = PLAYER_PIECE if piece==AI_PIECE else AI_PIECE
    if window.count(piece)==4: score+=100000
    elif window.count(piece)==3 and window.count(EMPTY)==1: score+=100
    elif window.count(piece)==2 and window.count(EMPTY)==2: score+=10
    if window.count(opp_piece)==3 and window.count(EMPTY)==1: score-=120
    return score

def score_position(board,piece):
    score=0
    # center priority
    center_array=[board[r][CENTER_COL] for r in range(ROWS)]
    score+=center_array.count(piece)*6
    # horizontal
    for r in range(ROWS):
        row_array=[board[r][c] for c in range(COLS)]
        for c in range(COLS-3):
            score+=evaluate_window(row_array[c:c+4],piece)
    # vertical
    for c in range(COLS):
        col_array=[board[r][c] for r in range(ROWS)]
        for r in range(ROWS-3):
            score+=evaluate_window(col_array[r:r+4],piece)
    # diag \
    for r in range(ROWS-3):
        for c in range(COLS-3):
            score+=evaluate_window([board[r+i][c+i] for i in range(4)],piece)
    # diag /
    for r in range(3,ROWS):
        for c in range(COLS-3):
            score+=evaluate_window([board[r-i][c+i] for i in range(4)],piece)
    return score

def get_valid_locations(board):
    return [c for c in range(COLS) if is_valid_location(board,c)]

def is_terminal_node(board):
    return winning_move(board,PLAYER_PIECE) or winning_move(board,AI_PIECE) or len(get_valid_locations(board))==0

def order_moves(valid_moves):
    return sorted(valid_moves,key=lambda x:abs(x-CENTER_COL))

def minimax(board,depth,alpha,beta,maximizing):
    valid_locations=get_valid_locations(board)
    terminal=is_terminal_node(board)
    if depth==0 or terminal:
        if terminal:
            if winning_move(board,AI_PIECE): return None,1000000
            elif winning_move(board,PLAYER_PIECE): return None,-1000000
            else: return None,0
        else: return None,score_position(board,AI_PIECE)
    if maximizing:
        value=-math.inf
        best_col=random.choice(valid_locations)
        for col in order_moves(valid_locations):
            row=get_next_open_row(board,col)
            b_copy=[r.copy() for r in board]
            drop_piece(b_copy,row,col,AI_PIECE)
            new_score=minimax(b_copy,depth-1,alpha,beta,False)[1]
            if new_score>value:
                value,best_col=new_score,col
            alpha=max(alpha,value)
            if alpha>=beta: break
        return best_col,value
    else:
        value=math.inf
        best_col=random.choice(valid_locations)
        for col in order_moves(valid_locations):
            row=get_next_open_row(board,col)
            b_copy=[r.copy() for r in board]
            drop_piece(b_copy,row,col,PLAYER_PIECE)
            new_score=minimax(b_copy,depth-1,alpha,beta,True)[1]
            if new_score<value:
                value,best_col=new_score,col
            beta=min(beta,value)
            if alpha>=beta: break
        return best_col,value

# -------------------- BGA BOT --------------------
class BGABot:
    def __init__(self,use_ai=True):
        self.use_ai=use_ai
        self.board=create_board()
        self.counter=0
        script_dir=os.path.dirname(os.path.abspath(__file__))
        user_data_path=os.path.join(script_dir,"profile")
        options=uc.ChromeOptions()
        options.add_argument(f"--user-data-dir={user_data_path}")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--start-maximized")
        print("Launching Chrome...")
        self.driver=uc.Chrome(options=options)
        self.wait=WebDriverWait(self.driver,20)

    def login(self):
        print("Opening BGA... log in manually.")
        self.driver.get("https://en.boardgamearena.com/account")
        WebDriverWait(self.driver,600).until(lambda d:"account" not in d.current_url)
        print("--- LOGIN DETECTED ---")
        time.sleep(2)

    def navigate_to_game(self,game_name="connectfour"):
        self.driver.get(f"https://boardgamearena.com/gamepanel?game={game_name}")

    def start_table(self):
        start_xpath="//a[contains(@class,'bga-button')]//div[contains(text(),'Démarrer')]"
        accept_id="ags_start_game_accept"
        board_id="board"
        while True:
            self.clear_popups()
            try:
                board_elements=self.driver.find_elements(By.ID,board_id)
                if board_elements and board_elements[0].is_displayed(): return True
                accept_btns=self.driver.find_elements(By.ID,accept_id)
                if accept_btns and accept_btns[0].is_displayed():
                    self.driver.execute_script("arguments[0].click();",accept_btns[0])
                    time.sleep(2)
                    continue
                start_btns=self.driver.find_elements(By.XPATH,start_xpath)
                if start_btns and start_btns[0].is_displayed():
                    self.driver.execute_script("arguments[0].click();",start_btns[0])
                    time.sleep(2)
                    continue
                body_class=self.driver.find_element(By.TAG_NAME,"body").get_attribute("class")
                if "current_player_is_active" in body_class: return True
                time.sleep(2)
            except WebDriverException:
                time.sleep(2)
            except:
                time.sleep(2)

    def clear_popups(self):
        try:
            popups=self.driver.find_elements(By.CSS_SELECTOR,"div[id^='continue_btn_']")
            for popup in popups:
                if popup.is_displayed():
                    self.driver.execute_script("arguments[0].click();",popup)
                    time.sleep(1)
                    self.clear_popups()
        except:
            pass

    def update_board_from_dom(self):
        squares=self.driver.find_elements(By.CSS_SELECTOR,"#board .square")
        for idx,sq in enumerate(squares):
            row=idx//COLS
            col=idx%COLS
            classes=sq.get_attribute("class")
            if "player1" in classes: self.board[row][col]=PLAYER_PIECE
            elif "player2" in classes: self.board[row][col]=AI_PIECE
            else: self.board[row][col]=EMPTY

    def play_ai_move(self):
        self.update_board_from_dom()
        # Opening: always center first
        first_moves=[4,5,3,6,2,7,1,8,0]
        for col in first_moves:
            if is_valid_location(self.board,col):
                row=get_next_open_row(self.board,col)
                drop_piece(self.board,row,col,AI_PIECE)
                clickable_squares=self.driver.find_elements(By.CSS_SELECTOR,"#board .square.possibleMove")
                if clickable_squares:
                    self.driver.execute_script("arguments[0].click();",clickable_squares[col])
                return "MOVED"
        # Minimax
        col,_=minimax(self.board,6,-math.inf,math.inf,True)
        if col is not None and is_valid_location(self.board,col):
            row=get_next_open_row(self.board,col)
            drop_piece(self.board,row,col,AI_PIECE)
            clickable_squares=self.driver.find_elements(By.CSS_SELECTOR,"#board .square.possibleMove")
            if clickable_squares:
                self.driver.execute_script("arguments[0].click();",clickable_squares[col])
            return "MOVED"
        return "WAITING"

    def play_human_move(self):
        self.update_board_from_dom()
        return "WAITING"

    def select_realtime_mode(self):
        while True:
            try:
                dropdown=self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,".panel-block--buttons__mode-select .bga-dropdown-button")))
                if "TEMPS RÉEL" in dropdown.text.upper(): return True
                self.driver.execute_script("arguments[0].click();",dropdown)
                time.sleep(1.5)
                realtime=self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,".bga-dropdown-option-realtime")))
                self.driver.execute_script("arguments[0].click();",realtime)
                time.sleep(2)
            except: time.sleep(2)

    def close(self):
        print("\nBot terminé. Appuyez sur Entrée pour fermer.")
        input()
        self.driver.quit()

# -------------------- MAIN --------------------
if __name__=="__main__":
    choice=input("Qui joue ? 1=Moi 2=IA : ").strip()
    use_ai=(choice=="2")
    bot=BGABot(use_ai=use_ai)
    try:
        bot.login()
        while True:
            print("\n🚀 Nouvelle session...")
            bot.navigate_to_game("connectfour")
            bot.select_realtime_mode()
            if bot.start_table():
                bot.counter+=1
                print(f"--- Partie numéro {bot.counter} ---")
                game_in_progress=True
                while game_in_progress:
                    if bot.use_ai:
                        status=bot.play_ai_move()
                    else:
                        status=bot.play_human_move()
                    try:
                        title_text=bot.driver.find_element(By.ID,"pagemaintitletext").text
                        if "Fin de la partie" in title_text or "Victoire" in title_text:
                            print("♻️ Partie terminée. Nouvelle partie dans 10s...")
                            time.sleep(10)
                            game_in_progress=False
                    except: pass
                    time.sleep(1)
    finally:
        bot.close()