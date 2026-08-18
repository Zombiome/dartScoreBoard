# Author : Corentin Bondallaz
# Date : 11.08.2026
# Description : Rule engine for countdown darts games (301, 501, ...)
#               (pure logic, no UI, easily unit-testable). `starting_score`
#               is a parameter, so the same engine serves every variant.

STARTING_SCORE_301 = 301
STARTING_SCORE_501 = 501

# Maps a game type label (as chosen in GameTypeScreen) to its starting
# score, for every countdown-style game this engine covers.
STARTING_SCORES = {
    "301": STARTING_SCORE_301,
    "501": STARTING_SCORE_501,
}

IN_RULES = ("straight", "double", "master")
OUT_RULES = ("straight", "double", "master")

# The game offers a single "rule mode" choice to the player : each
# label constrains either the opening or the finish, the other side
# staying "straight" (no constraint). "Jeu simple" has no constraint
# on either side (no Double/Master IN or OUT) and is listed first.
GAME_MODES = {
    "Jeu simple": {"in_rule": "straight", "out_rule": "straight"},
    "Double IN": {"in_rule": "double", "out_rule": "straight"},
    "Master IN": {"in_rule": "master", "out_rule": "straight"},
    "Double OUT": {"in_rule": "straight", "out_rule": "double"},
    "Master OUT": {"in_rule": "straight", "out_rule": "master"},
}

MULTIPLIER_CODES = {"": 1, "D": 2, "T": 3}


class Throw:
    """One dart : a multiplier (1/2/3) applied to a value (0-20 or 25)."""

    def __init__(self, multiplier, value):
        self.multiplier = multiplier
        self.value = value

    @property
    def points(self):
        return self.multiplier * self.value

    @property
    def label(self):
        if self.value == 0:
            return "-"
        prefix = {1: "", 2: "D", 3: "T"}[self.multiplier]
        return f"{prefix}{self.value}"


def build_throw(multiplier_code, value):
    """
    Build and validate a Throw from a multiplier code ('' / 'D' / 'T')
    and a numeric value. Raises ValueError for an impossible dart.
    """
    multiplier = MULTIPLIER_CODES.get(multiplier_code)
    if multiplier is None:
        raise ValueError("Multiplicateur invalide (attendu vide, D ou T).")

    if not (0 <= value <= 20 or value == 25):
        raise ValueError("La valeur doit être entre 0 et 20, ou 25 pour le bull.")

    if value == 0 and multiplier != 1:
        raise ValueError("Un raté (0) ne peut pas être doublé ou triplé.")

    if value == 25 and multiplier == 3:
        raise ValueError("Il n'y a pas de triple bull.")

    return Throw(multiplier, value)


class PlayerState:
    def __init__(self, name, starting_score):
        self.name = name
        self.score = starting_score
        self.opened = False
        self.winner = False

        # Raw stats accumulated for this single game only ; read by
        # gameFrm.stats once the game is over to update the player's
        # persistent performance file.
        self.turns_points = []  # raw point total of each completed turn
        self.dart_hits = {}     # "miss" -> n ; "1".."20"/"25" -> {"single","double","triple"}

    def record_dart(self, throw):
        """Track one physical dart landing, regardless of bust/counted status."""
        if throw.value == 0:
            self.dart_hits["miss"] = self.dart_hits.get("miss", 0) + 1
            return
        mult_key = {1: "single", 2: "double", 3: "triple"}[throw.multiplier]
        zone = self.dart_hits.setdefault(
            str(throw.value), {"single": 0, "double": 0, "triple": 0}
        )
        zone[mult_key] += 1

    def undo_dart(self, throw):
        """Reverse the effect of `record_dart` for the dart being undone."""
        if throw.value == 0:
            if self.dart_hits.get("miss"):
                self.dart_hits["miss"] -= 1
            return
        mult_key = {1: "single", 2: "double", 3: "triple"}[throw.multiplier]
        zone = self.dart_hits.get(str(throw.value))
        if zone and zone.get(mult_key):
            zone[mult_key] -= 1


class CountdownGame:
    """
    Turn-based rule engine : players throw 3 darts per turn, the score
    counts down from `starting_score` to exactly 0 following the
    chosen IN / OUT rule. Handles bust detection with the official
    "revert to start-of-turn score" behaviour. Used for 301, 501, and
    any other countdown variant sharing the same rules.
    """

    def __init__(self, player_names, in_rule="straight", out_rule="straight",
                 starting_score=STARTING_SCORE_301):
        if in_rule not in IN_RULES:
            raise ValueError(f"Règle IN invalide : {in_rule}")
        if out_rule not in OUT_RULES:
            raise ValueError(f"Règle OUT invalide : {out_rule}")
        if not player_names:
            raise ValueError("Il faut au moins un joueur.")

        self.in_rule = in_rule
        self.out_rule = out_rule
        self.starting_score = starting_score
        self.players = [PlayerState(name, starting_score) for name in player_names]
        self.current_index = 0
        self.current_turn_throws = []
        self.winner = None

        self._turn_start_score = starting_score
        self._turn_start_opened = False

    @property
    def current_player(self):
        return self.players[self.current_index]

    def _satisfies(self, rule, throw):
        if rule == "straight":
            return True
        if rule == "double":
            return throw.multiplier == 2
        if rule == "master":
            return throw.multiplier in (2, 3)
        return False

    def record_throw(self, multiplier, value):
        """
        Record one dart for the current player and resolve it :
        updates the score, detects busts (reverting the score to the
        start of the turn) and wins. Returns a result dict.
        """
        if self.winner is not None:
            raise RuntimeError("La partie est déjà terminée.")

        throw = Throw(multiplier, value)
        player = self.current_player

        if not self.current_turn_throws:
            self._turn_start_score = player.score
            self._turn_start_opened = player.opened

        counted = True
        if not player.opened:
            if self._satisfies(self.in_rule, throw):
                player.opened = True
            else:
                counted = False

        self.current_turn_throws.append(throw)
        player.record_dart(throw)

        if counted:
            candidate = player.score - throw.points
            bust = (
                candidate < 0
                or (candidate == 0 and not self._satisfies(self.out_rule, throw))
                or (candidate == 1 and self.out_rule != "straight")
            )
        else:
            candidate = player.score
            bust = False

        if bust:
            player.score = self._turn_start_score
            player.opened = self._turn_start_opened
            self._commit_turn_points(player)
            self._end_turn()
            return {
                "status": "bust",
                "player_name": player.name,
                "throw": throw,
                "counted": counted,
                "turn_over": True,
                "score_after": player.score,
            }

        player.score = candidate

        if candidate == 0:
            player.winner = True
            self.winner = player
            self._commit_turn_points(player)
            return {
                "status": "win",
                "player_name": player.name,
                "throw": throw,
                "counted": counted,
                "turn_over": True,
                "score_after": player.score,
            }

        turn_over = len(self.current_turn_throws) >= 3
        if turn_over:
            self._commit_turn_points(player)
            self._end_turn()

        return {
            "status": "ok",
            "player_name": player.name,
            "throw": throw,
            "counted": counted,
            "turn_over": turn_over,
            "score_after": candidate,
        }

    def undo_last_throw(self):
        """
        Undo the last dart of the turn currently in progress (only
        works before the turn ends). Returns True if something was
        undone.
        """
        if not self.current_turn_throws:
            return False

        removed = self.current_turn_throws.pop()
        player = self.current_player
        player.undo_dart(removed)
        player.score = self._turn_start_score
        player.opened = self._turn_start_opened

        for t in self.current_turn_throws:
            if not player.opened:
                if self._satisfies(self.in_rule, t):
                    player.opened = True
                else:
                    continue
            player.score -= t.points

        return True

    def _commit_turn_points(self, player):
        """
        Record the raw point total of the turn that is about to end
        (sum of every dart thrown this visit, bust or not) : this is
        what gameFrm.stats uses to compute the per-game scoring
        average and the best single-turn score.
        """
        raw_points = sum(t.points for t in self.current_turn_throws)
        player.turns_points.append(raw_points)

    def _end_turn(self):
        self.current_turn_throws = []
        self.current_index = (self.current_index + 1) % len(self.players)
