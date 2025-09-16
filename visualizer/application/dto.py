from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from domain.models import (
    Competition, Season, Match ,Matchday, Team, Player,
    StandingRow as DomainStandingRow,
    TeamFormRow as DomainTeamFormRow,
    TeamSplit as DomainTeamSplit,
    ScorerRow as DomainScorerRow,
    AssisterRow as DomainAssisterRow,
    KeeperKPI as DomainKeeperKPI,
    TeamResult,
)

# --------- DTOs "planos" para UI / capa superior ---------

@dataclass(frozen=True)
class CompetitionDTO:
    competition_id: int
    competition_name: str
    default_matchdays: Optional[int] = None
    is_international: Optional[bool] = None
    continent: Optional[str] = None

@dataclass(frozen=True)
class SeasonDTO:
    season_id: int
    competition_id: int
    season_label: str
    is_completed: Optional[bool] = None

@dataclass(frozen=True)
class MatchdayDTO:
    matchday_id: int
    season_id: int
    matchday_number: int

@dataclass(frozen=True)
class TeamDTO:
    team_id: int
    team_name: str

@dataclass(frozen=True)
class PlayerDTO:
    player_id: int
    player_name: str

@dataclass(frozen=True)
class StandingRowDTO:
    team_id: int
    team_name: str
    MP: int
    Pts: int
    GF: int
    GA: int
    GD: int

@dataclass(frozen=True)
class TeamFormRowDTO:
    match_id: int
    matchday_number: int
    home_team_id: int
    away_team_id: int
    local_score: Optional[int]
    away_score: Optional[int]
    result: Optional[TeamResult]  # "W" / "D" / "L" desde la perspectiva del equipo consultado

@dataclass(frozen=True)
class TeamSplitDTO:
    home_ppg: float
    away_ppg: float
    home_gf: int
    home_ga: int
    away_gf: int
    away_ga: int
    home_gd: int
    away_gd: int

@dataclass(frozen=True)
class ScorerDTO:
    player_id: int
    player_name: str
    goals: int

@dataclass(frozen=True)
class AssisterDTO:
    player_id: int
    player_name: str
    assists: int

@dataclass(frozen=True)
class KeeperKPIDTO:
    player_id: int
    player_name: str
    goalkeeper_saves: Optional[int]
    goals_prevented: Optional[float]
    goals_conceded: Optional[int]


# --------- Helpers de mapeo desde el dominio ---------

def to_competition_dto(x: Competition) -> CompetitionDTO:
    return CompetitionDTO(
        competition_id=int(x.competition_id),
        competition_name=x.competition_name,
        default_matchdays=x.default_matchdays,
        is_international=x.is_international,
        continent=x.continent,
    )

def to_season_dto(x: Season) -> SeasonDTO:
    return SeasonDTO(
        season_id=int(x.season_id),
        competition_id=int(x.competition_id),
        season_label=x.season_label,
        is_completed=x.is_completed,
    )

def to_matchday_dto(x: Matchday) -> MatchdayDTO:
    return MatchdayDTO(
        matchday_id=int(x.matchday_id),
        season_id=int(x.season_id),
        matchday_number=x.matchday_number,
    )

def to_team_dto(x: Team) -> TeamDTO:
    return TeamDTO(team_id=int(x.team_id), team_name=x.team_name)

def to_player_dto(x: Player) -> PlayerDTO:
    return PlayerDTO(player_id=int(x.player_id), player_name=x.player_name)

def to_standing_row_dto(x: DomainStandingRow) -> StandingRowDTO:
    return StandingRowDTO(
        team_id=int(x.team_id),
        team_name=x.team_name,
        MP=x.MP, Pts=x.Pts, GF=x.GF, GA=x.GA, GD=x.GD,
    )

def to_team_form_row_dto(x: DomainTeamFormRow) -> TeamFormRowDTO:
    return TeamFormRowDTO(
        match_id=int(x.match_id),
        matchday_number=x.matchday_number,
        home_team_id=int(x.home_team_id),
        away_team_id=int(x.away_team_id),
        local_score=x.local_score,
        away_score=x.away_score,
        result=x.result,
    )

def to_team_split_dto(x: DomainTeamSplit) -> TeamSplitDTO:
    return TeamSplitDTO(
        home_ppg=x.home_ppg, away_ppg=x.away_ppg,
        home_gf=x.home_gf, home_ga=x.home_ga,
        away_gf=x.away_gf, away_ga=x.away_ga,
        home_gd=x.home_gd, away_gd=x.away_gd,
    )

def to_scorer_dto(x: DomainScorerRow) -> ScorerDTO:
    return ScorerDTO(player_id=int(x.player_id), player_name=x.player_name, goals=x.goals)

def to_assister_dto(x: DomainAssisterRow) -> AssisterDTO:
    return AssisterDTO(player_id=int(x.player_id), player_name=x.player_name, assists=x.assists)

def to_keeper_kpi_dto(x: DomainKeeperKPI) -> KeeperKPIDTO:
    return KeeperKPIDTO(
        player_id=int(x.player_id),
        player_name=x.player_name,
        goalkeeper_saves=x.goalkeeper_saves,
        goals_prevented=x.goals_prevented,
        goals_conceded=x.goals_conceded,
    )


@dataclass(frozen=True)
class MatchDTO:
    match_id: int
    matchday_id: int
    home_team_id: int
    away_team_id: int
    local_score: Optional[int]
    away_score: Optional[int]
    stadium: Optional[str] = None

def to_match_dto(x: Match) -> MatchDTO:
    return MatchDTO(
        match_id=int(x.match_id),
        matchday_id=int(x.matchday_id),
        home_team_id=int(x.local_team_id),
        away_team_id=int(x.away_team_id),
        local_score=x.score.home,
        away_score=x.score.away,
        stadium=x.stadium,
    )
