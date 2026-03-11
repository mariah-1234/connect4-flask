import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    cfg = json.load(f)

ROWS = cfg.get("rows", 9)
COLS = cfg.get("cols", 9)
FIRST_PLAYER = cfg.get("first_player", "R")
AI_DEPTH = cfg.get("ai_depth", 3)

