# Author : Corentin Bondallaz
# Date : 11.08.2026
# Description : Screens used to set up the players for a game :
#               1) how many players are present
#               2) for each slot, pick an existing player or create one
#               Entirely keyboard-driven (arrows + Enter), no mouse.

import tkinter as tk

from gameFrm.keyboardMenu import KeyboardMenu, DEFAULT_INSTRUCTIONS

MIN_PLAYERS = 1
MAX_PLAYERS = 8
DEFAULT_PLAYER_COUNT = 2

NEW_PLAYER_LABEL = "+ Nouveau joueur"


class PlayerCountScreen(KeyboardMenu):
    """
    Ask how many players will take part in the game. Also the app's
    entry point for the statistics dashboard : pressing S opens the
    player-selection screen for browsing recorded performance graphs,
    without disturbing the normal Up/Down/Enter flow of this menu.
    """

    def __init__(self, master, on_confirm, on_stats=None):
        items = [str(n) for n in range(MIN_PLAYERS, MAX_PLAYERS + 1)]
        initial_index = items.index(str(DEFAULT_PLAYER_COUNT))

        instructions = DEFAULT_INSTRUCTIONS
        if on_stats is not None:
            instructions += "   ·   S : statistiques"

        super().__init__(
            master,
            title="Combien de joueurs sont présents ?",
            items=items,
            on_confirm=lambda value: on_confirm(int(value)),
            initial_index=initial_index,
            instructions=instructions,
        )

        self.on_stats = on_stats
        if self.on_stats is not None:
            self.listbox.bind("<Key>", self._on_extra_key)

    def _on_extra_key(self, event):
        if event.keysym.lower() == "s":
            self.on_stats()
            return "break"
        return None


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
        self.already_selected = already_selected
        self._renaming_pseudo = None  # None => creating ; else renaming this pseudo

        self.items = self._available_items()

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
        self.listbox.bind("<Key>", self._on_list_key)

        tk.Label(
            self.list_frame,
            text="↑ / ↓ pour naviguer   ·   Entrée pour valider   ·   R pour renommer",
            font=("Helvetica", 14),
            fg="grey",
            background="black",
        ).pack(pady=(30, 0))

        # --- entry mode : type a pseudo, either for a new player or
        # to rename the one currently highlighted in the list ---
        self.entry_title_var = tk.StringVar()
        tk.Label(
            self.entry_frame,
            textvariable=self.entry_title_var,
            font=("Helvetica", 20),
            fg="white",
            background="black",
            wraplength=800,
            justify="center",
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
        self.entry.bind("<Return>", self._on_entry_confirm)
        self.entry.bind("<KP_Enter>", self._on_entry_confirm)
        self.entry.bind("<Escape>", self._on_entry_cancel)

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

    def _available_items(self):
        available = [
            p for p in self.registry.list_players() if p not in self.already_selected
        ]
        return available + [NEW_PLAYER_LABEL]

    def _show_list_mode(self, select_value=None):
        self.entry_frame.pack_forget()
        self.list_frame.pack(fill="both", expand=True)
        self.listbox.focus_set()

        if select_value is not None:
            self.items = self._available_items()
            self.listbox.delete(0, tk.END)
            for item in self.items:
                self.listbox.insert(tk.END, item)

            index = self.items.index(select_value) if select_value in self.items else 0
            self.listbox.selection_set(index)
            self.listbox.activate(index)
            self.listbox.see(index)

    def _show_entry_mode(self):
        self.list_frame.pack_forget()
        self.error_var.set("")

        if self._renaming_pseudo is not None:
            self.entry_title_var.set(f"Renommer « {self._renaming_pseudo} » — nouveau pseudo :")
            self.new_name_var.set(self._renaming_pseudo)
        else:
            self.entry_title_var.set("Nouveau joueur — entre le pseudo :")
            self.new_name_var.set("")

        self.entry_frame.pack(fill="both", expand=True)
        self.entry.focus_set()
        self.entry.icursor(tk.END)
        self.entry.selection_range(0, tk.END)

    def _on_list_confirm(self, event=None):
        selection = self.listbox.curselection()
        if not selection:
            return "break"
        value = self.listbox.get(selection[0])
        if value == NEW_PLAYER_LABEL:
            self._renaming_pseudo = None
            self._show_entry_mode()
        else:
            self.on_select(value)
        return "break"

    def _on_list_key(self, event):
        if event.keysym.lower() == "r":
            selection = self.listbox.curselection()
            if selection:
                value = self.listbox.get(selection[0])
                if value != NEW_PLAYER_LABEL:
                    self._renaming_pseudo = value
                    self._show_entry_mode()
            return "break"
        return None

    def _on_entry_confirm(self, event=None):
        pseudo = self.new_name_var.get().strip()

        try:
            if self._renaming_pseudo is not None:
                pseudo = self.registry.rename_player(self._renaming_pseudo, pseudo)
            else:
                self.registry.add_player(pseudo)
        except ValueError as exc:
            self.error_var.set(str(exc))
            return "break"

        if self._renaming_pseudo is not None:
            self._renaming_pseudo = None
            self._show_list_mode(select_value=pseudo)
        else:
            self.on_select(pseudo)
        return "break"

    def _on_entry_cancel(self, event=None):
        self._renaming_pseudo = None
        self._show_list_mode()
        return "break"
