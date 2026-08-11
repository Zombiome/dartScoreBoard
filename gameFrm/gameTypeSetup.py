# Author : Corentin Bondallaz
# Date : 11.08.2026
# Description : Screen used to choose the type of game : 301, 501 or Criquet.
#               Keyboard-only (arrows + Enter), no mouse.

from gameFrm.keyboardMenu import KeyboardMenu

GAME_TYPES = ["301", "501", "Criquet"]
DEFAULT_GAME_TYPE = "501"


class GameTypeScreen(KeyboardMenu):
    """
    Ask which type of game will be played.
    """

    def __init__(self, master, on_confirm):
        initial_index = GAME_TYPES.index(DEFAULT_GAME_TYPE)

        super().__init__(
            master,
            title="Quel type de partie ?",
            items=GAME_TYPES,
            on_confirm=on_confirm,
            initial_index=initial_index,
        )
