import tkinter as tk
from gui import Connect4GUI
from stats_viewer import StatsViewer
from  game_db_viewer_final import  GameDBViewer
class Menu:
    def __init__(self):
        # Fenêtre principale
        self.root = tk.Tk()
        self.root.title("Puissance 4")
        self.root.geometry("400x450")
        self.root.configure(bg="#2c3e50")  # fond bleu foncé

        # Titre
        tk.Label(
            self.root,
            text="🎯 Puissance 4 🎯",
            font=("Arial", 20, "bold"),
            fg="white",
            bg="#2c3e50"
        ).pack(pady=20)

        # Sous-titre
        tk.Label(
            self.root,
            text="Choisissez le mode de jeu :",
            font=("Arial", 14),
            fg="white",
            bg="#2c3e50"
        ).pack(pady=10)

        # Frame pour les boutons
        button_frame = tk.Frame(self.root, bg="#2c3e50")
        button_frame.pack(pady=20)

        # Style des boutons
        btn_config = {
            "width": 20,
            "height": 2,
            "fg": "white",
            "font": ("Arial", 12, "bold"),
            "bd": 0,
            "activeforeground": "white"
        }

        # Boutons de jeu
        tk.Button(button_frame, text="0 : IA vs IA", bg="#3498db", activebackground="#2980b9",
                  command=lambda: self.lancer(0), **btn_config).pack(pady=8)
        tk.Button(button_frame, text="1 : Humain vs IA", bg="#2ecc71", activebackground="#27ae60",
                  command=lambda: self.lancer(1), **btn_config).pack(pady=8)
        tk.Button(button_frame, text="2 : Humain vs Humain", bg="#f1c40f", activebackground="#f39c12",
                  command=lambda: self.lancer(2), **btn_config).pack(pady=8)
        tk.Button(button_frame, text="Statistiques", bg="#9b59b6", activebackground="#8e44ad",
                  command=StatsViewer, **btn_config).pack(pady=8)
        tk.Button(button_frame, text="Quitter", bg="#e74c3c", activebackground="#c0392b",
                  command=self.root.destroy, **btn_config).pack(pady=8)
        tk.Button(button_frame, text="Explorer la base", 
                  command= GameDBViewer, **btn_config).pack(pady=8)
        
        self.root.mainloop()

    def lancer(self, mode):
        # Détruire le menu et lancer le jeu
        self.root.destroy()
        Connect4GUI(mode)