from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class SeasonInfo:
    season_id: int
    competition_id: int
    season_label: str


@dataclass(frozen=True)
class MatchdayInfo:
    matchday_id: int
    season_id: int
    matchday_number: int


@dataclass(frozen=True)
class SeasonTeamInfo:
    season_team_id: int
    season_id: int
    team_id: int


@dataclass(frozen=True)
class TeamPlayerInfo:
    season_team_id: int
    player_id: int
    jersey_number: Optional[int]


@dataclass(frozen=True)
class DimensionsContext:
    competition_id: int
    season: SeasonInfo
    matchday: MatchdayInfo
    season_teams: Dict[int, SeasonTeamInfo]
    team_players: Dict[int, TeamPlayerInfo]
