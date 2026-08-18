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
#                   game ever played.
#
#               Pure data layer, no UI : `record_game` is called once a
#               CountdownGame has a winner, display screens can be
#               built later on top of `load_stats` / `win_rate`.

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
        })

        save_stats(player.name, stats)
