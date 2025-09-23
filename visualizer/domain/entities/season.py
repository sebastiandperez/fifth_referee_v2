from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from ..ids import SeasonId, CompetitionId, TeamId
from ..value_objects import Name
from .matchday import Matchday


__all__ = ["Season", "SeasonTeam", "SeasonSchedule"]


@dataclass(frozen=True)
class Season:
    """
    Aggregate root representing a specific edition (year/range) of a Competition.
    Owns:
      - SeasonTeam membership (roster of teams participating this season)
      - Matchdays (list of jornadas)
    """
    season_id: SeasonId
    competition_id: CompetitionId
    label: Name  # e.g., "2023/24"


@dataclass
class SeasonTeam:
    """
    Association entity owned by Season: declares a Team participates in this Season.
    Invariants enforced by Season (at application/services level):
      - team appears at most once per season
      - optional cap on number of teams
    """
    season_id: SeasonId
    team_id: TeamId
    seed_number: Optional[int] = None  # optional ordering/seed
    status: Optional[str] = None       # e.g., "confirmed", "withdrawn"


@dataclass
class SeasonSchedule:
    """
    Optional helper aggregate to hold Season's structure in memory.
    """
    season: Season
    teams: List[SeasonTeam] = field(default_factory=list)
    matchdays: List[Matchday] = field(default_factory=list)

    def add_team(self, st: SeasonTeam) -> None:
        if st.season_id != self.season.season_id:
            raise ValueError("SeasonTeam.season_id mismatch")
        if any(x.team_id == st.team_id for x in self.teams):
            raise ValueError("Team already registered for this season")
        self.teams.append(st)

    def add_matchday(self, md: Matchday) -> None:
        if md.season_id != self.season.season_id:
            raise ValueError("Matchday.season_id mismatch")
        if any(x.number == md.number for x in self.matchdays):
            raise ValueError("Duplicate matchday number in season")
        self.matchdays.append(md)
