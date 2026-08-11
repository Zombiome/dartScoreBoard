# Author : Corentin Bondallaz
# Date : 11.08.2026
# Description : Persistent registry of registered players (pseudos).

import json
import os

# data/players.json at the project root
PLAYERS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "players.json",
)


class PlayerRegistry:
    """
    Manages the list of registered player pseudos, persisted as JSON.
    """

    def __init__(self, file_path=PLAYERS_FILE):
        self.file_path = file_path
        self._players = self._load()

    def _load(self):
        if not os.path.exists(self.file_path):
            return []
        with open(self.file_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    def _save(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self._players, f, indent=2, ensure_ascii=False)

    def list_players(self):
        """Return the registered pseudos, sorted alphabetically."""
        return sorted(self._players)

    def exists(self, pseudo):
        """Check if a pseudo is already registered (case-insensitive)."""
        return pseudo.strip().lower() in (p.lower() for p in self._players)

    def add_player(self, pseudo):
        """
        Register a new player. Raises ValueError if the pseudo is
        empty or already taken.
        """
        pseudo = pseudo.strip()
        if not pseudo:
            raise ValueError("Le pseudo ne peut pas être vide.")
        if self.exists(pseudo):
            raise ValueError(f"Le joueur '{pseudo}' existe déjà.")

        self._players.append(pseudo)
        self._save()
        return pseudo
