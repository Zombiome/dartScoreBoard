# Author : Corentin Bondallaz
# Date : 18.08.2026
# Description : Statistics dashboard. First pick which registered
#               player to look at, then browse every performance graph
#               recorded for that player (scoring average, personal
#               best turn, win rate, dart hits per zone) : Up/Down
#               switches which graph is selected, Left/Right pans the
#               selected graph's own time window. X axis is always the
#               game's date/time. Graphs are drawn on plain tk.Canvas
#               widgets (no charting library needed), 2-3 visible at
#               once, the rest scrolls in. Keyboard-only, no mouse.

import math
import tkinter as tk

from gameFrm.keyboardMenu import KeyboardMenu
from gameFrm.stats import load_stats, build_graphs

# Only 2 graphs on screen at once (instead of 3) : gives each one
# enough vertical room for a legible, bigger date axis.
VISIBLE_GRAPHS = 2
WINDOW_SIZE = 8  # games shown at once along a graph's X axis

BACKGROUND = "black"
AXIS_COLOR = "#666666"
GRID_COLOR = "#2a2a2a"
TEXT_COLOR = "white"
MUTED_COLOR = "grey"
SELECTED_TITLE_COLOR = "#ffd633"
UNSELECTED_TITLE_COLOR = "#8fd3ff"
SELECTED_BORDER_COLOR = "#3366cc"

SERIES_COLORS = ["#4da6ff", "#ff9933", "#4dff88", "#ff6666"]

PADDING_LEFT = 95  # room for the Y graduations AND the first point's rotated date label
PADDING_RIGHT = 20
PADDING_TOP = 36  # room for the peak-value label above the highest point
PADDING_BOTTOM = 66  # extra room for the bigger, rotated date labels

GRID_LABEL_FONT = ("Helvetica", 11)
AXIS_DATE_FONT = ("Helvetica", 12)
LEGEND_FONT = ("Helvetica", 10)
UNIT_FONT = ("Helvetica", 10, "italic")
PEAK_LABEL_FONT = ("Helvetica", 12, "bold")
PEAK_COLOR = "#ffd633"

# Panel spacing : more breathing room between graphs.
PANEL_PADY = 18


def _nice_step(span, target_ticks=5):
    """
    Round a raw step (span / target_ticks) up to the nearest "nice"
    number (1, 2, 5 or 10 times a power of ten), so gridlines always
    land on clean values (every 2, every 5, every 10, ...) instead of
    arbitrary fractions that shift as the visible data changes.
    """
    if span <= 0:
        return 1
    raw_step = span / target_ticks
    magnitude = 10 ** math.floor(math.log10(raw_step))
    residual = raw_step / magnitude
    if residual <= 1:
        nice = 1
    elif residual <= 2:
        nice = 2
    elif residual <= 5:
        nice = 5
    else:
        nice = 10
    return nice * magnitude


def _format_grid_value(value):
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:g}"


class StatsPlayerSelectScreen(KeyboardMenu):
    """
    Ask which registered player's statistics to browse. Reached from
    the player-count screen (press S). Escape goes back instead of
    quitting the app.
    """

    def __init__(self, master, registry, on_select, on_back):
        self.on_back = on_back
        items = registry.list_players()

        super().__init__(
            master,
            title="Statistiques de quel joueur ?",
            items=items,
            on_confirm=on_select,
            instructions=(
                "↑ / ↓ pour naviguer   ·   Entrée pour valider   ·   Échap pour revenir"
                if items else
                "Aucun joueur enregistré pour l'instant.   ·   Échap pour revenir"
            ),
        )
        self.listbox.bind("<Escape>", self._on_escape)

    def _on_escape(self, event=None):
        self.on_back()
        return "break"


class StatsDashboardScreen(tk.Frame):
    """
    Full-screen, scrollable browser of every graph recorded for one
    player. Builds every graph up front (gameFrm.stats.build_graphs)
    and only ever renders VISIBLE_GRAPHS of them at a time.
    """

    def __init__(self, master, pseudo, on_back):
        super().__init__(master, background=BACKGROUND)
        self.pseudo = pseudo
        self.on_back = on_back

        self.graphs = build_graphs(load_stats(pseudo))
        self.selected_index = 0
        self.first_visible = 0
        # One time-window offset per graph, so hopping between graphs
        # and coming back keeps whatever window was left showing.
        self.offsets = [0] * len(self.graphs)

        tk.Label(
            self, text=f"Statistiques — {pseudo}",
            font=("Helvetica", 26), fg="white", background=BACKGROUND,
        ).pack(pady=(20, 6))

        if not self.graphs:
            tk.Label(
                self,
                text="Aucune partie enregistrée pour ce joueur pour l'instant.",
                font=("Helvetica", 18), fg=MUTED_COLOR, background=BACKGROUND,
            ).pack(pady=40)
            self.panels = []
        else:
            self.panels_frame = tk.Frame(self, background=BACKGROUND)
            self.panels_frame.pack(fill="both", expand=True, padx=30, pady=6)
            self.panels = [self._build_panel(self.panels_frame) for _ in range(VISIBLE_GRAPHS)]
            self._render_visible()


        tk.Label(
            self,
            text=(
                "↑ / ↓ : changer de graphique   ·   ← / → : parcourir l'historique"
                "   ·   Échap : retour"
            ),
            font=("Helvetica", 14), fg=MUTED_COLOR, background=BACKGROUND,
        ).pack(pady=(6, 16))

        self.bind("<Key>", self._on_key)
        self.bind("<Escape>", self._on_escape)
        self.focus_set()

    # --- widget construction ---

    def _build_panel(self, parent):
        frame = tk.Frame(
            parent, background=BACKGROUND, highlightthickness=2,
            highlightbackground=BACKGROUND,
        )
        frame.pack(fill="both", expand=True, pady=PANEL_PADY)

        title_var = tk.StringVar()
        title_label = tk.Label(
            frame, textvariable=title_var, font=("Helvetica", 16, "bold"),
            fg=UNSELECTED_TITLE_COLOR, background=BACKGROUND,
        )
        title_label.pack(anchor="w", padx=6)

        canvas = tk.Canvas(frame, background=BACKGROUND, highlightthickness=0)
        canvas.pack(fill="both", expand=True, padx=6, pady=(2, 4))
        canvas.bind("<Configure>", lambda event: self._render_visible())

        return {"frame": frame, "title_var": title_var, "title_label": title_label, "canvas": canvas}

    # --- navigation ---

    def _on_key(self, event):
        keysym = event.keysym.lower()
        if keysym == "up":
            self._move_selection(-1)
        elif keysym == "down":
            self._move_selection(1)
        elif keysym == "left":
            self._pan_selected(1)   # older games
        elif keysym == "right":
            self._pan_selected(-1)  # newer games
        else:
            return None
        return "break"

    def _on_escape(self, event=None):
        self.on_back()
        return "break"

    def _move_selection(self, delta):
        if not self.graphs:
            return
        self.selected_index = max(0, min(len(self.graphs) - 1, self.selected_index + delta))

        if self.selected_index < self.first_visible:
            self.first_visible = self.selected_index
        elif self.selected_index >= self.first_visible + VISIBLE_GRAPHS:
            self.first_visible = self.selected_index - VISIBLE_GRAPHS + 1

        self._render_visible()

    def _pan_selected(self, delta):
        if not self.graphs:
            return
        graph = self.graphs[self.selected_index]
        total = len(graph["series"][0]["points"]) if graph["series"] else 0
        max_offset = max(0, total - WINDOW_SIZE)

        current = self.offsets[self.selected_index]
        self.offsets[self.selected_index] = max(0, min(max_offset, current + delta))
        self._render_visible()

    # --- rendering ---

    def _render_visible(self):
        if not self.graphs:
            return
        for slot, panel in enumerate(self.panels):
            index = self.first_visible + slot
            if index >= len(self.graphs):
                panel["frame"].pack_forget()
                continue
            panel["frame"].pack(fill="both", expand=True, pady=PANEL_PADY)
            self._render_graph(panel, index)

    def _render_graph(self, panel, index):
        graph = self.graphs[index]
        is_selected = index == self.selected_index

        panel["title_var"].set(graph["title"])
        panel["title_label"].config(
            fg=SELECTED_TITLE_COLOR if is_selected else UNSELECTED_TITLE_COLOR
        )
        panel["frame"].config(
            highlightbackground=SELECTED_BORDER_COLOR if is_selected else BACKGROUND
        )

        canvas = panel["canvas"]
        canvas.delete("all")

        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width < 10 or height < 10:
            return

        offset = self.offsets[index]
        series_list = graph["series"]
        total_points = len(series_list[0]["points"]) if series_list else 0

        if total_points == 0:
            canvas.create_text(
                width / 2, height / 2, text="Pas encore de données",
                fill=MUTED_COLOR, font=("Helvetica", 12),
            )
            return

        start = max(0, total_points - WINDOW_SIZE - offset)
        end = min(total_points, start + WINDOW_SIZE)
        windows = [s["points"][start:end] for s in series_list]

        self._draw_graph(canvas, width, height, windows, series_list, graph["unit"])

        # Small paging hint when there's more history off-screen
        # (placed below the unit label, top-right, so they never overlap).
        if start > 0 or end < total_points:
            hint = f"{start + 1}-{end} / {total_points} parties"
            canvas.create_text(
                width - PADDING_RIGHT, 16, text=hint, anchor="ne",
                fill=MUTED_COLOR, font=("Helvetica", 9),
            )

    def _draw_graph(self, canvas, width, height, windows, series_list, unit):
        plot_x0 = PADDING_LEFT
        plot_x1 = width - PADDING_RIGHT
        plot_y0 = PADDING_TOP
        plot_y1 = height - PADDING_BOTTOM

        if plot_x1 <= plot_x0 or plot_y1 <= plot_y0:
            return

        all_values = [v for win in windows for _, v in win]
        raw_min = min(all_values)
        raw_max = max(all_values)
        if raw_min == raw_max:
            raw_min -= 1
            raw_max += 1

        # Snap the plotted range to "nice" gridline steps (2 / 5 / 10 /
        # ... depending on the scale of the values) instead of dividing
        # the raw min/max into arbitrary fractions.
        step = _nice_step(raw_max - raw_min)
        v_min = math.floor(raw_min / step) * step
        v_max = math.ceil(raw_max / step) * step
        if v_min == v_max:
            v_max = v_min + step

        dates = [d for d, _ in windows[0]]
        n = len(dates)

        def x_of(i):
            if n <= 1:
                return (plot_x0 + plot_x1) / 2
            return plot_x0 + (plot_x1 - plot_x0) * i / (n - 1)

        def y_of(value):
            return plot_y1 - (plot_y1 - plot_y0) * (value - v_min) / (v_max - v_min)

        # Horizontal gridlines, one every `step` units (a "nice" round
        # number : every 2, every 5, every 10, ... depending on scale).
        num_steps = round((v_max - v_min) / step)
        for s in range(num_steps + 1):
            value = v_min + s * step
            y = y_of(value)
            canvas.create_line(plot_x0, y, plot_x1, y, fill=GRID_COLOR)
            canvas.create_text(
                plot_x0 - 10, y, text=_format_grid_value(value), anchor="e",
                fill=MUTED_COLOR, font=GRID_LABEL_FONT,
            )

        canvas.create_line(plot_x0, plot_y0, plot_x0, plot_y1, fill=AXIS_COLOR)
        canvas.create_line(plot_x0, plot_y1, plot_x1, plot_y1, fill=AXIS_COLOR)

        # X graduations : the game's date/time, in a bigger font, thinned
        # out so labels never overlap regardless of how many points are
        # on screen (rotated so they stay compact but still legible).
        max_labels = max(2, int((plot_x1 - plot_x0) / 95))
        label_stride = max(1, -(-n // max_labels))  # ceil division
        for i, date in enumerate(dates):
            if i % label_stride != 0 and i != n - 1:
                continue
            x = x_of(i)
            canvas.create_line(x, plot_y1, x, plot_y1 + 5, fill=AXIS_COLOR)
            canvas.create_text(
                x, plot_y1 + 9, text=date.strftime("%d/%m %Hh%M"), anchor="e",
                fill=MUTED_COLOR, font=AXIS_DATE_FONT, angle=35,
            )

        # One line + point markers per series ; track the single
        # highest point across every series so it can be highlighted
        # and labelled afterwards (the graph's "peak", visible at a
        # glance).
        peak = None  # (x, y, value)
        for series_index, (series, points) in enumerate(zip(series_list, windows)):
            color = SERIES_COLORS[series_index % len(SERIES_COLORS)]
            coords = []
            for i, (_, value) in enumerate(points):
                x, y = x_of(i), y_of(value)
                coords.extend([x, y])
                canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill=color, outline="")
                if peak is None or value > peak[2]:
                    peak = (x, y, value)
            if len(coords) >= 4:
                canvas.create_line(*coords, fill=color, width=2)

        # Legend, only needed when a graph has more than one series
        # (the per-zone graphs : simple / double / triple).
        if len(series_list) > 1:
            lx = plot_x0
            ly = plot_y0 - 12
            for series_index, series in enumerate(series_list):
                color = SERIES_COLORS[series_index % len(SERIES_COLORS)]
                canvas.create_oval(lx, ly - 4, lx + 8, ly + 4, fill=color, outline="")
                canvas.create_text(
                    lx + 13, ly, text=series["label"], anchor="w",
                    fill=TEXT_COLOR, font=LEGEND_FONT,
                )
                lx += 13 + len(series["label"]) * 7 + 20

        if unit:
            canvas.create_text(
                plot_x1, 4, text=unit, anchor="ne",
                fill=MUTED_COLOR, font=UNIT_FONT,
            )

        # Highlight the peak (highest-value) point and print its value
        # right above it, drawn last so it sits on top of everything
        # else : the maximum jumps out at a glance.
        if peak is not None:
            px, py, pvalue = peak
            canvas.create_oval(
                px - 5, py - 5, px + 5, py + 5, outline=PEAK_COLOR, width=2,
            )
            label_y = max(4, py - 14)
            canvas.create_text(
                px, label_y, text=_format_grid_value(pvalue), anchor="s",
                fill=PEAK_COLOR, font=PEAK_LABEL_FONT,
            )
