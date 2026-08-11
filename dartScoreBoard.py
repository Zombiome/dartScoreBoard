# Author : Corentin Bondallaz
# Date : 11.08.2026
# Description : Main file of the DartScoreBoard project.

import sys
from gameFrm.logo import show_logo
from gameFrm.launcher import Launcher

if __name__ == "__main__":

    show_logo()

    app = Launcher(sys.argv)



