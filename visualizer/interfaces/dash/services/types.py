from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass
class Competition:
    id: int
    name: str

@dataclass
class SeasonSummary:
    season_id: int
    season_label: str
    competition_id: int
    competition_name: str
    team_count: int
    matchday_min: Optional[int] = None
    matchday_max: Optional[int] = None
    last_finalized_matchday: Optional[int] = None

@dataclass
class TeamItem:
    team_id: int
    team_name: str
    team_city: Optional[str] = None
    team_stadium: Optional[str] = None

@dataclass
class PlayerItem:
    player_id: int
    player_name: str
    team_id: int
    team_name: str
    season_team_id: int
    jersey_number: Optional[int] = None

@dataclass
class MatchItem:
    match_id: int
    matchday_id: int
    home_team_id: int
    away_team_id: int
    home_score: Optional[int]
    away_score: Optional[int]
    duration: int
    stadium: Optional[str] = None
