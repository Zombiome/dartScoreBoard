# Author : Corentin Bondallaz
# Date : 11.08.2026
# Description : Screen used to choose the 301 rule variant : Double IN,
#               Master IN, Double OUT or Master OUT. Keyboard-only
#               (arrows + Enter), no mouse.

from gameFrm.keyboardMenu import KeyboardMenu
from gameFrm.game301 import GAME_MODES

DEFAULT_MODE = "Double OUT"


class RuleModeScreen(KeyboardMenu):
    """
    Ask which IN/OUT rule variant will be used for the game.
    """

    def __init__(self, master, on_confirm):
        items = list(GAME_MODES.keys())
        initial_index = items.index(DEFAULT_MODE)

        super().__init__(
            master,
            title="Quelle règle de jeu ?",
            items=items,
            on_confirm=on_confirm,
            initial_index=initial_index,
        )
