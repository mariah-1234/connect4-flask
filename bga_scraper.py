import time
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from save_to_db import save_game_from_list

INPUT_FILE = "bga_match_links.txt"

def load_links():
    with open(INPUT_FILE, "r") as f:
        return [line.strip() for line in f if line.strip()]

def get_driver():
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options, version_main=146)
    return driver

def scrape_match(driver, url):
    print("\n🚀 SCRAPING :", url)
    driver.get(url)
    wait = WebDriverWait(driver, 20)

    try:
        # attendre que les logs de jeu soient présents
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "gamelogreview")))
        time.sleep(1)
        logs = driver.find_elements(By.CLASS_NAME, "gamelogreview")
    except:
        print("❌ logs introuvables")
        return

    moves = []
    for log in logs:
        txt = log.text.lower()
        m = re.search(r"(?:column|colonne)\s*(\d+)", txt)
        if m:
            moves.append(int(m.group(1)) - 1)

    if not moves:
        print("⚠️ aucun coup trouvé")
        return

    print("🎮 coups trouvés :", moves)

    # sauvegarde dans DB
    try:
        save_game_from_list(
            player1="BGA_Player1",
            player2="BGA_Player2",
            mode=1,
            moves_list=moves,
            confidence=1
        )
        print("✅ partie sauvegardée dans la DB")
    except Exception as e:
        print("❌ erreur DB :", e)

def main():
    links = load_links()
    if not links:
        print("❌ aucun lien à scraper")
        return

    driver = get_driver()

    print("🔑 Chrome ouvert. Connecte-toi à BGA manuellement, puis appuie sur ENTER...")
    driver.get("https://boardgamearena.com/account")
    input("👉 Appuie sur ENTER quand tu es connecté...")

    for url in links:
        scrape_match(driver, url)
        time.sleep(2)

    print("\n✅ scraping terminé")
    driver.quit()

if __name__ == "__main__":
    main()