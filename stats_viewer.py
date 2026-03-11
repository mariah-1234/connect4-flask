import tkinter as tk
from db import get_statistics


class StatsViewer:

    def __init__(self):

        stats = get_statistics()

        window = tk.Toplevel()
        window.title("Statistiques")
        window.geometry("300x200")

        tk.Label(window, text="STATISTIQUES DU JEU", font=("Arial", 14, "bold")).pack(pady=10)

        tk.Label(window, text=f"Total des parties : {stats['total']}").pack(pady=5)

        tk.Label(window, text=f"Victoires Rouge : {stats['rouge']}").pack(pady=5)

        tk.Label(window, text=f"Victoires Jaune : {stats['jaune']}").pack(pady=5)

        tk.Label(window, text=f"Egalités : {stats['draws']}").pack(pady=5)