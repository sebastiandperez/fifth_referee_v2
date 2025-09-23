from __future__ import annotations
from dataclasses import dataclass

from ..ids import MatchdayId, SeasonId


__all__ = ["Matchday"]


@dataclass(frozen=True)
class Matchday:
    """A numbered round/jornada within a season."""
    matchday_id: MatchdayId
    season_id: SeasonId
    number: int
