import pickle
import os

SAVE_DIR = "saves"

if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

def save_game(game, name):
    with open(f"{SAVE_DIR}/{name}.p4", "wb") as f:
        pickle.dump(game, f)

def load_game(name):
    with open(f"{SAVE_DIR}/{name}.p4", "rb") as f:
        return pickle.load(f)

def list_saves():
    return [f for f in os.listdir(SAVE_DIR) if f.endswith(".p4")]