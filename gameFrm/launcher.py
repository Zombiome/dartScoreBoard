# Author : Corentin Bondallaz
# Date : 11.08.2026
# Description : Launcher of the game. Main Tk window that chains the
#               different setup screens (player count, player selection,
#               and later game type, scoring, stats...). Entirely
#               keyboard-driven, no mouse required.

import tkinter as tk

from gameFrm.players import PlayerRegistry
from gameFrm.playerSetup import PlayerCountScreen, PlayerSelectScreen
from gameFrm.gameTypeSetup import GameTypeScreen


class Launcher(tk.Tk):
    def __init__(self, argv):
        super().__init__()

        self.title("DartScoreBoard")
        self.configure(background="black")
        self.attributes("-fullscreen", True)
        self.focus_force()

        # Global safety exit: Escape quits the app, unless a screen
        # (e.g. new player entry) intercepts it first with "break".
        self.bind("<Escape>", lambda event: self.destroy())

        self.registry = PlayerRegistry()
        self.nb_players = 0
        self.selected_players = []
        self.game_type = None
        self._current_frame = None

        self._show_player_count_screen()

        self.mainloop()

    def _set_frame(self, frame_cls, **kwargs):
        if self._current_frame is not None:
            self._current_frame.destroy()
        self._current_frame = frame_cls(self, **kwargs)
        self._current_frame.pack(fill="both", expand=True)

    def _show_player_count_screen(self):
        self._set_frame(PlayerCountScreen, on_confirm=self._start_player_selection)

    def _start_player_selection(self, nb_players):
        self.nb_players = nb_players
        self.selected_players = []
        self._select_next_player()

    def _select_next_player(self):
        index = len(self.selected_players)
        if index >= self.nb_players:
            self._on_players_ready()
            return

        self._set_frame(
            PlayerSelectScreen,
            registry=self.registry,
            player_number=index + 1,
            total_players=self.nb_players,
            already_selected=self.selected_players,
            on_select=self._on_player_selected,
        )

    def _on_player_selected(self, pseudo):
        self.selected_players.append(pseudo)
        self._select_next_player()

    def _on_players_ready(self):
        self._set_frame(GameTypeScreen, on_confirm=self._on_game_type_selected)

    def _on_game_type_selected(self, game_type):
        self.game_type = game_type
        # TODO : next step will be the turn order and score entry
        print("Joueurs sélectionnés :", self.selected_players)
        print("Type de partie :", self.game_type)
