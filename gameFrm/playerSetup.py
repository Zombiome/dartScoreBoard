# Author : Corentin Bondallaz
# Date : 11.08.2026
# Description : Screens used to set up the players for a game :
#               1) how many players are present
#               2) for each slot, pick an existing player or create one
#               Entirely keyboard-driven (arrows + Enter), no mouse.

import tkinter as tk

from gameFrm.keyboardMenu import KeyboardMenu

MIN_PLAYERS = 1
MAX_PLAYERS = 8
DEFAULT_PLAYER_COUNT = 2

NEW_PLAYER_LABEL = "+ Nouveau joueur"


class PlayerCountScreen(KeyboardMenu):
    """
    Ask how many players will take part in the game.
    """

    def __init__(self, master, on_confirm):
        items = [str(n) for n in range(MIN_PLAYERS, MAX_PLAYERS + 1)]
        initial_index = items.index(str(DEFAULT_PLAYER_COUNT))

        super().__init__(
            master,
            title="Combien de joueurs sont présents ?",
            items=items,
            on_confirm=lambda value: on_confirm(int(value)),
            initial_index=initial_index,
        )


class PlayerSelectScreen(tk.Frame):
    """
    Let the user fill one player slot: either pick an already
    registered player from a keyboard-navigable list, or type the
    pseudo of a brand new one.
    """

    def __init__(self, master, registry, player_number, total_players,
                 already_selected, on_select):
        super().__init__(master, background="black")
        self.registry = registry
        self.on_select = on_select

        available = [
            p for p in registry.list_players() if p not in already_selected
        ]
        self.items = available + [NEW_PLAYER_LABEL]

        tk.Label(
            self,
            text=f"Joueur {player_number}/{total_players}",
            font=("Helvetica", 28),
            fg="white",
            background="black",
        ).pack(pady=(50, 10))

        if already_selected:
            participants_text = "Participants : " + "   ".join(
                f"{i + 1}. {p}" for i, p in enumerate(already_selected)
            )
        else:
            participants_text = "Participants : (aucun pour l'instant)"

        tk.Label(
            self,
            text=participants_text,
            font=("Helvetica", 16),
            fg="#8fd3ff",
            background="black",
            wraplength=900,
            justify="center",
        ).pack(pady=(0, 20))

        self.list_frame = tk.Frame(self, background="black")
        self.entry_frame = tk.Frame(self, background="black")

        # --- list mode : existing players + "new player" entry ---
        self.listbox = tk.Listbox(
            self.list_frame,
            font=("Helvetica", 22),
            height=min(len(self.items), 10),
            width=30,
            justify="center",
            activestyle="none",
            bg="black",
            fg="white",
            selectbackground="#3366cc",
            selectforeground="white",
            highlightthickness=0,
            bd=0,
            exportselection=False,
        )
        for item in self.items:
            self.listbox.insert(tk.END, item)
        self.listbox.pack(pady=10)
        if self.items:
            self.listbox.selection_set(0)
            self.listbox.activate(0)

        self.listbox.bind("<Return>", self._on_list_confirm)
        self.listbox.bind("<KP_Enter>", self._on_list_confirm)

        tk.Label(
            self.list_frame,
            text="↑ / ↓ pour naviguer   ·   Entrée pour valider",
            font=("Helvetica", 14),
            fg="grey",
            background="black",
        ).pack(pady=(30, 0))

        # --- entry mode : type the pseudo of a new player ---
        tk.Label(
            self.entry_frame,
            text="Nouveau joueur — entre le pseudo :",
            font=("Helvetica", 20),
            fg="white",
            background="black",
        ).pack(pady=(30, 10))

        self.new_name_var = tk.StringVar()
        self.entry = tk.Entry(
            self.entry_frame,
            textvariable=self.new_name_var,
            font=("Helvetica", 22),
            justify="center",
            bg="black",
            fg="white",
            insertbackground="white",
            highlightthickness=1,
            highlightbackground="grey",
            highlightcolor="#3366cc",
        )
        self.entry.pack(pady=10, ipadx=10, ipady=5)
        self.entry.bind("<Return>", self._on_create_confirm)
        self.entry.bind("<KP_Enter>", self._on_create_confirm)
        self.entry.bind("<Escape>", self._on_create_cancel)

        self.error_var = tk.StringVar()
        tk.Label(
            self.entry_frame,
            textvariable=self.error_var,
            font=("Helvetica", 14),
            fg="#ff6666",
            background="black",
        ).pack(pady=(10, 0))

        tk.Label(
            self.entry_frame,
            text="Entrée pour valider   ·   Échap pour revenir à la liste",
            font=("Helvetica", 14),
            fg="grey",
            background="black",
        ).pack(pady=(30, 0))

        self._show_list_mode()

    def _show_list_mode(self):
        self.entry_frame.pack_forget()
        self.list_frame.pack(fill="both", expand=True)
        self.listbox.focus_set()

    def _show_entry_mode(self):
        self.list_frame.pack_forget()
        self.error_var.set("")
        self.new_name_var.set("")
        self.entry_frame.pack(fill="both", expand=True)
        self.entry.focus_set()

    def _on_list_confirm(self, event=None):
        selection = self.listbox.curselection()
        if not selection:
            return "break"
        value = self.listbox.get(selection[0])
        if value == NEW_PLAYER_LABEL:
            self._show_entry_mode()
        else:
            self.on_select(value)
        return "break"

    def _on_create_confirm(self, event=None):
        pseudo = self.new_name_var.get().strip()
        try:
            self.registry.add_player(pseudo)
        except ValueError as exc:
            self.error_var.set(str(exc))
            return "break"
        self.on_select(pseudo)
        return "break"

    def _on_create_cancel(self, event=None):
        self._show_list_mode()
        return "break"
