# Author : Corentin Bondallaz
# Date : 11.08.2026
# Description : Score entry screen for a countdown game (301, 501, ...).
#               Shows every player's current score, highlights whose
#               turn it is, and captures the 3 darts of each turn from
#               the keyboard : digits for the value (0-20, 25 = bull),
#               "D" prefix for a double, "T" prefix for a triple,
#               Enter to validate a throw, Backspace to correct.

import math
import random
import tkinter as tk

from gameFrm.countdownGame import build_throw

INSTRUCTIONS = (
    "Chiffres : valeur (0-20, 25 = bull)   ·   D : double   ·   T : triple\n"
    "Entrée : valider le lancer   ·   Retour arrière : corriger"
)

CELEBRATION_COLORS = [
    "#ff4d4d", "#ffd633", "#4dff88", "#4da6ff", "#c266ff", "#ff9933", "#ffffff",
]
CONFETTI_COUNT = 110
FIREWORK_BURSTS = 5


class CountdownScreen(tk.Frame):
    def __init__(self, master, game, on_game_over, on_restart, mode_label=None, game_label="301"):
        super().__init__(master, background="black")
        self.game = game
        self.on_game_over = on_game_over
        self.on_restart = on_restart

        self._prefix = ""  # "" | "D" | "T"
        self._digits = ""
        self._message = ""

        self._celebration_active = False
        self._confetti = []
        self._confetti_job = None

        title = game_label if mode_label is None else f"{game_label} — {mode_label}"
        tk.Label(
            self, text=title, font=("Helvetica", 26), fg="white", background="black"
        ).pack(pady=(30, 10))

        self.scores_frame = tk.Frame(self, background="black")
        self.scores_frame.pack(pady=10)
        self.score_rows = {}

        self.turn_var = tk.StringVar()
        self.turn_label = tk.Label(
            self, textvariable=self.turn_var, font=("Helvetica", 18),
            fg="#8fd3ff", background="black",
        )
        self.turn_label.pack(pady=(20, 5))

        self.turn_throws_var = tk.StringVar()
        tk.Label(
            self, textvariable=self.turn_throws_var, font=("Helvetica", 16),
            fg="white", background="black",
        ).pack(pady=5)

        self.input_var = tk.StringVar()
        tk.Label(
            self, textvariable=self.input_var, font=("Helvetica", 24),
            fg="yellow", background="black",
        ).pack(pady=10)

        self.message_var = tk.StringVar()
        tk.Label(
            self, textvariable=self.message_var, font=("Helvetica", 16),
            fg="#ff6666", background="black",
        ).pack(pady=5)

        self.instructions_var = tk.StringVar(value=INSTRUCTIONS)
        tk.Label(
            self, textvariable=self.instructions_var, font=("Helvetica", 13),
            fg="grey", background="black", justify="center",
        ).pack(pady=(20, 0))

        # Fullscreen overlay for the victory animation : covers the
        # whole screen (confetti fly in front of everything), and
        # redraws the winner text itself so nothing is hidden behind it.
        self.celebration_canvas = tk.Canvas(self, background="black", highlightthickness=0)

        self._build_score_rows()
        self._refresh()

        self.bind("<Key>", self._on_key)
        self.bind("<Destroy>", self._on_destroy)
        self.focus_set()

    def _build_score_rows(self):
        for player in self.game.players:
            row = tk.Frame(self.scores_frame, background="black")
            row.pack(fill="x", pady=4)

            name_label = tk.Label(
                row, text=player.name, font=("Helvetica", 20), width=16,
                anchor="w", background="black", fg="white",
            )
            name_label.pack(side="left", padx=10)

            score_label = tk.Label(
                row, text=str(player.score), font=("Helvetica", 20), width=6,
                anchor="e", background="black", fg="white",
            )
            score_label.pack(side="left", padx=10)

            self.score_rows[player.name] = (row, name_label, score_label)

    def _refresh(self):
        current = self.game.current_player
        game_over = self.game.winner is not None

        for player in self.game.players:
            row, name_label, score_label = self.score_rows[player.name]
            is_current = (player is current) and not game_over

            bg = "#3366cc" if is_current else "black"
            marker = "▶ " if is_current else "   "

            row.config(background=bg)
            name_label.config(background=bg, text=f"{marker}{player.name}")
            score_label.config(background=bg, text=str(player.score))

        if game_over:
            self.turn_label.config(font=("Helvetica", 32, "bold"), fg="#ffd633")
            self.turn_var.set(f"🏆 {self.game.winner.name} remporte la partie !")
            self.turn_throws_var.set("")
            self.input_var.set("")
            self.instructions_var.set("R : rejouer une partie   ·   Échap : quitter le programme")
        else:
            throws_done = len(self.game.current_turn_throws)

            hint = ""
            if self.game.in_rule != "straight" and not current.opened:
                needed = "un double" if self.game.in_rule == "double" else "un double ou un triple"
                hint = f"  (il faut {needed} pour ouvrir le compteur)"

            self.turn_var.set(f"Au tour de {current.name} — lancer {throws_done + 1}/3{hint}")

            if self.game.current_turn_throws:
                parts = [f"{t.label} ({t.points})" for t in self.game.current_turn_throws]
                self.turn_throws_var.set("Ce tour : " + "   ".join(parts))
            else:
                self.turn_throws_var.set("Ce tour : —")

            self.input_var.set(f"Saisie : {self._prefix}{self._digits}")

        self.message_var.set(self._message)

    def _on_key(self, event):
        if self.game.winner is not None:
            return self._on_key_game_over(event)

        keysym = event.keysym.lower()

        if keysym == "d" and not self._digits:
            self._prefix = "D"
            self._message = ""
        elif keysym == "t" and not self._digits:
            self._prefix = "T"
            self._message = ""
        elif event.char.isdigit() and len(self._digits) < 2:
            self._digits += event.char
            self._message = ""
        elif keysym == "backspace":
            if self._digits:
                self._digits = self._digits[:-1]
            elif self._prefix:
                self._prefix = ""
            else:
                self._undo_last_throw()
        elif keysym in ("return", "kp_enter"):
            self._submit_throw()

        self._refresh()
        return "break"

    def _on_key_game_over(self, event):
        keysym = event.keysym.lower()

        if keysym == "r":
            self._stop_celebration()
            self.on_restart()
            return "break"

        if keysym == "escape":
            # Don't swallow it : let it bubble up to the Launcher's
            # global quit binding.
            return None

        return "break"

    def _undo_last_throw(self):
        if self.game.undo_last_throw():
            self._message = "Dernier lancer annulé."
        else:
            self._message = "Rien à annuler pour ce tour."

    def _submit_throw(self):
        if not self._digits:
            self._message = "Entre une valeur avant de valider."
            return

        try:
            value = int(self._digits)
            throw = build_throw(self._prefix, value)
        except ValueError as exc:
            self._message = str(exc)
            self._prefix = ""
            self._digits = ""
            return

        self._prefix = ""
        self._digits = ""

        result = self.game.record_throw(throw.multiplier, throw.value)

        if result["status"] == "bust":
            self._message = f"BUST ! Score de {result['player_name']} remis à {result['score_after']}."
        elif result["status"] == "win":
            self._message = f"{result['player_name']} termine la partie !"
        elif not result["counted"]:
            self._message = "Ne compte pas encore : il faut d'abord ouvrir le compteur."
        else:
            self._message = ""

        self._refresh()

        if result["status"] == "win":
            self._start_celebration()
            self.on_game_over(result["player_name"])

    # --- victory celebration : confetti + firework bursts on a Canvas ---

    def _start_celebration(self):
        self._celebration_active = True

        # Cover the entire frame (not just the leftover space below the
        # other labels) so confetti/fireworks fly in front of everything.
        self.celebration_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        # Canvas shadows both .lift() and .tkraise() with its own
        # per-item "tag_raise" (which needs a tagOrId argument), so
        # calling either on a Canvas instance crashes. Go through the
        # raw Tk "raise" command instead, which always raises the
        # whole widget in the sibling stacking order.
        self.tk.call("raise", str(self.celebration_canvas))
        self.celebration_canvas.delete("all")
        self._confetti = []
        self.update_idletasks()

        width = self.celebration_canvas.winfo_width() or self.winfo_width() or 800
        height = self.celebration_canvas.winfo_height() or self.winfo_height() or 600

        # Redraw the winner announcement and final scores directly on
        # the canvas first, so the confetti/fireworks created afterwards
        # naturally stack on top of them (front layer), while the text
        # itself stays fully visible underneath.
        self._draw_victory_text(width, height)

        for _ in range(CONFETTI_COUNT):
            self._spawn_confetti(width)

        for i in range(FIREWORK_BURSTS):
            delay = 150 + i * 450 + random.randint(0, 250)
            self.after(delay, lambda w=width, h=height: self._spawn_firework(w, h))

        self._animate_confetti()

    def _draw_victory_text(self, width, height):
        cx = width / 2

        self.celebration_canvas.create_text(
            cx, height * 0.15,
            text=f"🏆 {self.game.winner.name} remporte la partie !",
            font=("Helvetica", 34, "bold"), fill="#ffd633",
            justify="center",
        )

        scores_lines = [
            f"{'👑 ' if player is self.game.winner else '    '}{player.name} : {player.score}"
            for player in self.game.players
        ]
        self.celebration_canvas.create_text(
            cx, height * 0.15 + 70,
            text="\n".join(scores_lines),
            font=("Helvetica", 20), fill="white",
            justify="center",
        )

        self.celebration_canvas.create_text(
            cx, height * 0.93,
            text="R : rejouer une partie   ·   Échap : quitter le programme",
            font=("Helvetica", 14), fill="grey",
            justify="center",
        )

    def _stop_celebration(self):
        self._celebration_active = False
        if self._confetti_job is not None:
            self.after_cancel(self._confetti_job)
            self._confetti_job = None
        if self.celebration_canvas.winfo_exists():
            self.celebration_canvas.delete("all")
            self.celebration_canvas.place_forget()

    def _spawn_confetti(self, width):
        x = random.randint(0, max(width, 1))
        y = random.randint(-200, 0)
        size = random.randint(4, 9)
        color = random.choice(CELEBRATION_COLORS)
        item = self.celebration_canvas.create_rectangle(
            x, y, x + size, y + size, fill=color, outline=""
        )
        self._confetti.append({
            "id": item,
            "x": float(x),
            "y": float(y),
            "vx": random.uniform(-1.2, 1.2),
            "vy": random.uniform(2.0, 5.0),
            "size": size,
        })

    def _animate_confetti(self):
        if not self._celebration_active or not self.celebration_canvas.winfo_exists():
            return

        width = self.celebration_canvas.winfo_width() or 800
        height = self.celebration_canvas.winfo_height() or 250

        for particle in self._confetti:
            particle["x"] += particle["vx"]
            particle["y"] += particle["vy"]
            if particle["y"] > height:
                particle["y"] = random.uniform(-40, 0)
                particle["x"] = random.uniform(0, max(width, 1))
            self.celebration_canvas.coords(
                particle["id"],
                particle["x"], particle["y"],
                particle["x"] + particle["size"], particle["y"] + particle["size"],
            )

        self._confetti_job = self.after(40, self._animate_confetti)

    def _spawn_firework(self, width, height):
        if not self._celebration_active or not self.celebration_canvas.winfo_exists():
            return

        cx = random.randint(int(width * 0.15), max(int(width * 0.85), 1))
        cy = random.randint(int(height * 0.1), max(int(height * 0.85), 1))
        color = random.choice(CELEBRATION_COLORS)
        angles = list(range(0, 360, 15))
        rays = [
            self.celebration_canvas.create_line(cx, cy, cx, cy, fill=color, width=4)
            for _ in angles
        ]
        self._animate_firework(cx, cy, angles, rays, radius=0)

    def _animate_firework(self, cx, cy, angles, rays, radius):
        if not self._celebration_active or not self.celebration_canvas.winfo_exists():
            return

        if radius > 130:
            for ray in rays:
                self.celebration_canvas.delete(ray)
            return

        fade_width = max(1, 4 - radius // 40)
        for ray, angle_deg in zip(rays, angles):
            angle = math.radians(angle_deg)
            x2 = cx + radius * math.cos(angle)
            y2 = cy + radius * math.sin(angle)
            self.celebration_canvas.coords(ray, cx, cy, x2, y2)
            self.celebration_canvas.itemconfig(ray, width=fade_width)

        self.after(25, lambda: self._animate_firework(cx, cy, angles, rays, radius + 7))

    def _on_destroy(self, event):
        if event.widget is self:
            self._celebration_active = False
