# Author : Corentin Bondallaz
# Date : 18.08.2026
# Description : Persistent per-player performance statistics. One JSON
#               file per player under data/stats/ (rather than one big
#               shared file), so each player's history can grow freely
#               and files can be read/written independently.
#
#               For every finished countdown game (301, 501, ...) this
#               module records, per player :
#                 - the scoring average of that game (points scored /
#                   turns played), kept in a full game history so
#                   trends can be displayed later ;
#                 - the highest single-turn score, across every game
#                   ever played ;
#                 - the win rate (games_won / games_played) ;
#                 - the number of darts landed in each zone (1-20 and
#                   25), split into single/double/triple, across every
#                   game ever played (each history entry also keeps its
#                   own game's dart hits, so the per-zone counts can be
#                   charted over time, not just as a lifetime total).
#
#               Pure data layer, no UI : `record_game` is called once a
#               CountdownGame has a winner ; `build_graphs` turns a
#               loaded stats dict into ready-to-plot time series (X
#               axis always the game's date) for gameFrm.statsScreen.

import copy
import json
import os
from datetime import datetime

# data/stats/<pseudo>.json at the project root
STATS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "stats",
)

DART_ZONES = [str(n) for n in range(1, 21)] + ["25"]


def _empty_dart_hits():
    return {
        "miss": 0,
        **{zone: {"single": 0, "double": 0, "triple": 0} for zone in DART_ZONES},
    }


def _empty_stats(pseudo):
    return {
        "pseudo": pseudo,
        "games_played": 0,
        "games_won": 0,
        "best_turn_score": 0,
        "dart_hits": _empty_dart_hits(),
        "history": [],
    }


def _stats_file(pseudo):
    return os.path.join(STATS_DIR, f"{pseudo.strip()}.json")


def load_stats(pseudo):
    """
    Load a player's stats, creating a fresh (empty) structure if the
    player has never had a game recorded yet. Missing fields (e.g.
    after this module gains new stats later) are backfilled from the
    empty structure, so older files keep working.
    """
    path = _stats_file(pseudo)
    if not os.path.exists(path):
        return _empty_stats(pseudo)

    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return _empty_stats(pseudo)

    stats = _empty_stats(pseudo)
    stats.update(data)
    stats["dart_hits"] = {**_empty_dart_hits(), **data.get("dart_hits", {})}
    return stats


def save_stats(pseudo, stats):
    os.makedirs(STATS_DIR, exist_ok=True)
    with open(_stats_file(pseudo), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)


def win_rate(stats):
    """Percentage (0-100) of games won, from a dict as returned by load_stats."""
    if not stats["games_played"]:
        return 0.0
    return round(100 * stats["games_won"] / stats["games_played"], 1)


def _merge_dart_hits(totals, game_hits):
    totals["miss"] = totals.get("miss", 0) + game_hits.get("miss", 0)
    for zone in DART_ZONES:
        game_zone = game_hits.get(zone, {})
        zone_totals = totals.setdefault(zone, {"single": 0, "double": 0, "triple": 0})
        for key in ("single", "double", "triple"):
            zone_totals[key] += game_zone.get(key, 0)


def record_game(game, game_type, rule_mode):
    """
    Persist the outcome of a finished CountdownGame for every player
    who took part. Updates each player's aggregated stats (games
    played/won, best turn, dart hits) and appends one entry to their
    game history. `game` must already have a winner.
    """
    if game.winner is None:
        raise ValueError("La partie n'est pas terminée : pas de vainqueur à enregistrer.")

    player_names = [p.name for p in game.players]
    played_at = datetime.now().isoformat(timespec="seconds")

    for player in game.players:
        turns_played = len(player.turns_points)
        points_scored = sum(player.turns_points)
        average = round(points_scored / turns_played, 2) if turns_played else 0.0
        best_turn_this_game = max(player.turns_points) if player.turns_points else 0
        is_winner = player is game.winner

        stats = load_stats(player.name)
        stats["games_played"] += 1
        if is_winner:
            stats["games_won"] += 1
        stats["best_turn_score"] = max(stats["best_turn_score"], best_turn_this_game)
        _merge_dart_hits(stats["dart_hits"], player.dart_hits)

        stats["history"].append({
            "date": played_at,
            "game_type": game_type,
            "rule_mode": rule_mode,
            "opponents": [name for name in player_names if name != player.name],
            "result": "win" if is_winner else "loss",
            "turns_played": turns_played,
            "points_scored": points_scored,
            "average": average,
            "best_turn": best_turn_this_game,
            # Snapshot of this single game's dart hits (as opposed to
            # `stats["dart_hits"]`, which is the running total) : this
            # is what lets build_graphs() plot each zone's count over
            # time instead of only ever showing the lifetime total.
            "dart_hits": copy.deepcopy(player.dart_hits),
        })

        save_stats(player.name, stats)


def _parse_date(iso_str):
    return datetime.fromisoformat(iso_str)


def build_graphs(stats):
    """
    Turn a player's stats dict (as returned by load_stats) into an
    ordered list of chart-ready graphs, in the exact order they should
    be browsed : scoring average, personal best turn (running record),
    win rate, then one graph per dart zone (1 to 20, then bull's eye).
    X axis is always the date/time of the game.

    Each graph is a dict :
        {"key": str, "title": str, "unit": str,
         "series": [{"label": str, "points": [(datetime, value), ...]}]}

    Returns an empty list if the player has no recorded game yet.
    """
    history = stats.get("history", [])
    if not history:
        return []

    dated_history = sorted(
        ({**entry, "_date": _parse_date(entry["date"])} for entry in history),
        key=lambda e: e["_date"],
    )

    graphs = [
        {
            "key": "average",
            "title": "Moyenne de points par partie",
            "unit": "pts / tour",
            "series": [{
                "label": "Moyenne",
                "points": [(e["_date"], e["average"]) for e in dated_history],
            }],
        },
    ]

    # Best turn score : running record across every game played so far.
    running_best = 0
    best_points = []
    for e in dated_history:
        running_best = max(running_best, e.get("best_turn", 0))
        best_points.append((e["_date"], running_best))
    graphs.append({
        "key": "best_turn_record",
        "title": "Meilleur tour (record, toutes parties confondues)",
        "unit": "pts",
        "series": [{"label": "Record", "points": best_points}],
    })

    # Win rate : running percentage across every game played so far.
    played = 0
    won = 0
    rate_points = []
    for e in dated_history:
        played += 1
        if e.get("result") == "win":
            won += 1
        rate_points.append((e["_date"], round(100 * won / played, 1)))
    graphs.append({
        "key": "win_rate",
        "title": "Pourcentage de parties gagnées",
        "unit": "%",
        "series": [{"label": "Victoires", "points": rate_points}],
    })

    # Dart hits per zone, running total across every game, one graph
    # per zone (1..20, then bull's eye), single/double/(triple) split.
    running_totals = {zone: {"single": 0, "double": 0, "triple": 0} for zone in DART_ZONES}
    per_zone_points = {zone: {"single": [], "double": [], "triple": []} for zone in DART_ZONES}
    for e in dated_history:
        game_hits = e.get("dart_hits", {})
        for zone in DART_ZONES:
            zone_hits = game_hits.get(zone, {})
            for mult in ("single", "double", "triple"):
                running_totals[zone][mult] += zone_hits.get(mult, 0)
                per_zone_points[zone][mult].append((e["_date"], running_totals[zone][mult]))

    for zone in DART_ZONES:
        series = [
            {"label": "Simple", "points": per_zone_points[zone]["single"]},
            {"label": "Double", "points": per_zone_points[zone]["double"]},
        ]
        if zone != "25":
            series.append({"label": "Triple", "points": per_zone_points[zone]["triple"]})

        zone_name = "bull's eye" if zone == "25" else zone
        graphs.append({
            "key": f"zone_{zone}",
            "title": f"Fléchettes dans le {zone_name}",
            "unit": "fléchettes (cumulé)",
            "series": series,
        })

    return graphs
