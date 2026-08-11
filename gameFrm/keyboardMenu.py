# Author : Corentin Bondallaz
# Date : 11.08.2026
# Description : Reusable full-screen menu navigable only with the keyboard
#               (Up / Down to move, Enter to confirm). Used by every
#               selection screen so the whole app works without a mouse.

import tkinter as tk

DEFAULT_INSTRUCTIONS = "↑ / ↓ pour naviguer   ·   Entrée pour valider"


class KeyboardMenu(tk.Frame):
    """
    A titled, keyboard-only list of choices.

    Up/Down arrow key navigation is Tk's built-in Listbox behaviour
    (no custom binding needed) ; only Enter is bound explicitly to
    confirm the highlighted item.
    """

    def __init__(self, master, title, items, on_confirm, initial_index=0,
                 instructions=DEFAULT_INSTRUCTIONS):
        super().__init__(master, background="black")
        self.items = items
        self.on_confirm = on_confirm

        tk.Label(
            self,
            text=title,
            font=("Helvetica", 28),
            fg="white",
            background="black",
        ).pack(pady=(60, 30))

        self.listbox = tk.Listbox(
            self,
            font=("Helvetica", 22),
            height=min(len(items), 10) if items else 1,
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
        for item in items:
            self.listbox.insert(tk.END, item)
        self.listbox.pack(pady=10)

        if items:
            start = max(0, min(initial_index, len(items) - 1))
            self.listbox.selection_set(start)
            self.listbox.activate(start)
            self.listbox.see(start)

        self.listbox.bind("<Return>", self._confirm)
        self.listbox.bind("<KP_Enter>", self._confirm)

        tk.Label(
            self,
            text=instructions,
            font=("Helvetica", 14),
            fg="grey",
            background="black",
        ).pack(pady=(30, 0))

        self.listbox.focus_set()

    def _confirm(self, event=None):
        selection = self.listbox.curselection()
        if not selection:
            return "break"
        index = selection[0]
        self.on_confirm(self.items[index])
        return "break"
