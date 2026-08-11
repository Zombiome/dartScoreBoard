# Author : Corentin Bondallaz
# Date : 11.08.2026
# Description : Main file of the DartScoreBoard project.

import sys
from gameFrm.logo import show_logo
from gameFrm.launcher import Launcher

if __name__ == "__main__":

    # Loop so that asking to "rejouer" from the victory screen restarts
    # the whole app from scratch, logo included.
    while True:
        show_logo()

        app = Launcher(sys.argv)

        if not app.restart_requested:
            break
