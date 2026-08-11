# Author : Corentin Bondallaz
# Date : 11.08.2026
# Description : Splash screen displaying the application logo.

import os
import tkinter as tk

# Path to the logo image (assets/logo.png at the project root)
LOGO_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets",
    "logo.png",
)


class LogoScreen(tk.Tk):
    """
    Fullscreen splash screen showing the application logo.
    Closes automatically after `duration_ms`, or immediately on
    any key press. Keyboard-only, no mouse involved.
    """

    def __init__(self, duration_ms=3000):
        super().__init__()

        self.title("DartScoreBoard")
        self.configure(background="black")
        self.attributes("-fullscreen", True)

        # tkinter's PhotoImage reads PNG natively (Tk >= 8.6), no
        # extra dependency (Pillow) needed on the Raspberry Pi.
        self.logo_image = tk.PhotoImage(file=LOGO_PATH)

        label = tk.Label(self, image=self.logo_image, background="black")
        label.pack(expand=True)

        self.bind("<Key>", self._close)
        self.focus_force()

        self.after(duration_ms, self._close)

    def _close(self, event=None):
        self.destroy()


def show_logo(duration_ms=3000):
    """
    Display the branding splash screen and block until it closes
    (either after `duration_ms` or on user input).
    """
    screen = LogoScreen(duration_ms)
    screen.mainloop()


if __name__ == "__main__":
    show_logo()
