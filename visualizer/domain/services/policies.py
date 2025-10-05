from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Tuple

@dataclass(frozen=True)
class PointsPolicy:
    points_for_win: int = 3
    points_for_draw: int = 1
    points_for_loss: int = 0

    def points(self, gf: int, ga: int) -> int:
        if gf > ga:
            return self.points_for_win
        if gf == ga:
            return self.points_for_draw
        return self.points_for_loss


@dataclass(frozen=True)
class TieBreakPolicy:
    """
    Defines sorting order for standings.
    Default: Points → Goal Difference → Goals For (desc).
    """
    key: Callable[[Tuple[int, int, int, int]], Tuple] = lambda row: (-row[0], -row[1], -row[2])
    # row tuple convention: (Pts, GD, GF, TeamId or a stable tiebreaker)

    def compare_key(self, pts: int, gd: int, gf: int, team_id: int) -> Tuple:
        return self.key((pts, gd, gf, team_id))
