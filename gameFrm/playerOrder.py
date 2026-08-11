# Author : Corentin Bondallaz
# Date : 11.08.2026
# Description : Screen showing the selected players in playing order,
#               with the option to shuffle that order randomly before
#               moving on. Keyboard-only (R to shuffle, Enter to confirm).

import random
import tkinter as tk


class PlayerOrderScreen(tk.Frame):
    """
    Display the players in their current playing order. Pressing "R"
    shuffles the order randomly ; Enter confirms and continues.
    """

    def __init__(self, master, players, on_confirm):
        super().__init__(master, background="black")
        self.players = list(players)
        self.on_confirm = on_confirm

        tk.Label(
            self,
            text="Ordre de passage",
            font=("Helvetica", 28),
            fg="white",
            background="black",
        ).pack(pady=(60, 20))

        self.order_var = tk.StringVar()
        tk.Label(
            self,
            textvariable=self.order_var,
            font=("Helvetica", 20),
            fg="#8fd3ff",
            background="black",
            wraplength=900,
            justify="center",
        ).pack(pady=20)
        self._refresh_order_label()

        tk.Label(
            self,
            text="R : mélanger l'ordre aléatoirement   ·   Entrée : valider et continuer",
            font=("Helvetica", 14),
            fg="grey",
            background="black",
        ).pack(pady=(30, 0))

        self.bind("<Key>", self._on_key)
        self.focus_set()

    def _refresh_order_label(self):
        text = "\n".join(f"{i + 1}. {p}" for i, p in enumerate(self.players))
        self.order_var.set(text)

    def _on_key(self, event):
        keysym = event.keysym.lower()
        if keysym == "r":
            self._shuffle()
        elif keysym in ("return", "kp_enter"):
            self._confirm()
        return "break"

    def _shuffle(self):
        random.shuffle(self.players)
        self._refresh_order_label()

    def _confirm(self):
        self.on_confirm(self.players)
