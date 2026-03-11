import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()))

print("Connexion à BGA")

driver.get("https://boardgamearena.com")

input("Connecte-toi puis appuie ENTER")

print("Ouverture Puissance 4")

driver.get("https://boardgamearena.com/gamepanel?game=connectfour")

time.sleep(5)

print("Création table")

try:
    create = driver.find_element(By.CLASS_NAME, "newgame")
    create.click()
except:
    print("Impossible de créer table")

time.sleep(5)

print("Bot en train de jouer...")

while True:
    try:
        cells = driver.find_elements(By.CLASS_NAME, "possibleMove")

        if cells:
            move = random.choice(cells)
            move.click()

        time.sleep(1)

    except:
        print("Fin de partie ou erreur")
        break
    