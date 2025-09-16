from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import NewType, Optional, Tuple
from datetime import datetime

# ---------- Tipos fuertes para IDs (mejor legibilidad y chequeos estáticos) ----------
TeamId = NewType("TeamId", int)
PlayerId = NewType("PlayerId", int)
CompetitionId = NewType("CompetitionId", int)
SeasonId = NewType("SeasonId", int)
MatchdayId = NewType("MatchdayId", int)
MatchId = NewType("MatchId", int)
BasicStatsId = NewType("BasicStatsId", int)
EventId = NewType("EventId", int)

# ---------- Enums del dominio ----------
class EventType(str, Enum):
    GOAL = "goal"
    OWN_GOAL = "own_goal"
    YELLOW = "yellow_card"
    RED = "red_card"
    SUBSTITUTION = "substitution"
    SHOT = "shot"
    FOUL = "foul"
    OFFSIDE = "offside"
    # Extensible según tus reference enums

class Position(str, Enum):
    GK = "GK"
    DF = "DF"
    MF = "MF"
    FW = "FW"
    # Extensible (RB, LB, AM, DM, etc.) si lo manejas en reference.position_enum

class Status(str, Enum):
    STARTER = "starter"
    BENCH = "bench"
    UNUSED_SUB = "unused_sub"
    # Extensible si tu reference.status_enum tiene otros estados

class TeamResult(str, Enum):
    WIN = "W"
    DRAW = "D"
    LOSS = "L"

# ---------- Value Objects ----------
@dataclass(frozen=True)
class Score:
    """Marcador final de un partido. Usa None si aún no hay datos."""
    home: Optional[int] = None
    away: Optional[int] = None

    def __post_init__(self) -> None:
        if self.home is not None and self.home < 0:
            raise ValueError("home score must be >= 0")
        if self.away is not None and self.away < 0:
            raise ValueError("away score must be >= 0")

    @property
    def is_final(self) -> bool:
        return self.home is not None and self.away is not None

    def result_for(self, team_is_home: bool) -> Optional[TeamResult]:
        """Resultado desde la perspectiva del equipo (siempre que haya marcador)."""
        if not self.is_final:
            return None
        my_goals = self.home if team_is_home else self.away
        op_goals = self.away if team_is_home else self.home
        if my_goals > op_goals:
            return TeamResult.WIN
        if my_goals < op_goals:
            return TeamResult.LOSS
        return TeamResult.DRAW

    def points_for(self, team_is_home: bool) -> int:
        """Puntos para el equipo según el marcador; 0 si no hay marcador."""
        res = self.result_for(team_is_home)
        if res is None:
            return 0
        if res is TeamResult.WIN:
            return 3
        if res is TeamResult.DRAW:
            return 1
        return 0

# ---------- Entidades del dominio (inmutables, igualdad por ID) ----------
@dataclass(frozen=True)
class Team:
    team_id: TeamId = field(metadata={"compare": True})
    team_name: str = field(metadata={"compare": False})
    team_city: Optional[str] = field(default=None, metadata={"compare": False})
    team_stadium: Optional[str] = field(default=None, metadata={"compare": False})

    def __repr__(self) -> str:  # repr corto y estable
        return f"Team(id={int(self.team_id)}, name={self.team_name!r})"

@dataclass(frozen=True)
class Competition:
    competition_id: CompetitionId = field(metadata={"compare": True})
    competition_name: str = field(metadata={"compare": False})
    default_matchdays: Optional[int] = field(default=None, metadata={"compare": False})
    is_international: Optional[bool] = field(default=None, metadata={"compare": False})
    continent: Optional[str] = field(default=None, metadata={"compare": False})

    def __repr__(self) -> str:
        return f"Competition(id={int(self.competition_id)}, name={self.competition_name!r})"

@dataclass(frozen=True)
class Season:
    season_id: SeasonId = field(metadata={"compare": True})
    season_label: str = field(metadata={"compare": False})
    competition_id: CompetitionId = field(metadata={"compare": False})
    is_completed: Optional[bool] = field(default=None, metadata={"compare": False})

    def __repr__(self) -> str:
        return f"Season(id={int(self.season_id)}, label={self.season_label!r})"

@dataclass(frozen=True)
class Matchday:
    matchday_id: MatchdayId = field(metadata={"compare": True})
    season_id: SeasonId = field(metadata={"compare": False})
    matchday_number: int = field(metadata={"compare": False})

    def __post_init__(self) -> None:
        if self.matchday_number <= 0:
            raise ValueError("matchday_number must be positive")

    def __repr__(self) -> str:
        return f"Matchday(id={int(self.matchday_id)}, num={self.matchday_number})"

@dataclass(frozen=True)
class Match:
    match_id: MatchId = field(metadata={"compare": True})
    matchday_id: MatchdayId = field(metadata={"compare": False})
    local_team_id: TeamId = field(metadata={"compare": False})
    away_team_id: TeamId = field(metadata={"compare": False})
    score: Score = field(default_factory=Score, metadata={"compare": False})
    kickoff_utc: Optional[datetime] = field(default=None, metadata={"compare": False})
    stadium: Optional[str] = field(default=None, metadata={"compare": False})
    duration_minutes: int = field(default=90, metadata={"compare": False})

    def __post_init__(self) -> None:
        if self.local_team_id == self.away_team_id:
            raise ValueError("local_team_id and away_team_id must differ")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")

    @property
    def is_finished(self) -> bool:
        return self.score.is_final

    def result_for_team(self, team_id: TeamId) -> Optional[TeamResult]:
        """W/D/L desde la perspectiva de team_id."""
        if team_id not in (self.local_team_id, self.away_team_id):
            raise ValueError("team_id is not part of this match")
        return self.score.result_for(team_is_home=(team_id == self.local_team_id))

    def points_for_team(self, team_id: TeamId) -> int:
        """3/1/0 para team_id; 0 si no hay marcador."""
        if team_id not in (self.local_team_id, self.away_team_id):
            raise ValueError("team_id is not part of this match")
        return self.score.points_for(team_is_home=(team_id == self.local_team_id))

@dataclass(frozen=True)
class Player:
    player_id: PlayerId = field(metadata={"compare": True})
    player_name: str = field(metadata={"compare": False})

    def __repr__(self) -> str:
        return f"Player(id={int(self.player_id)}, name={self.player_name!r})"

@dataclass(frozen=True)
class Participation:
    """Participación de un jugador en un partido."""
    match_id: MatchId = field(metadata={"compare": True})
    player_id: PlayerId = field(metadata={"compare": True})
    status: Optional[Status] = field(default=None, metadata={"compare": False})
    position: Optional[Position] = field(default=None, metadata={"compare": False})

    def __repr__(self) -> str:
        return f"Participation(match={int(self.match_id)}, player={int(self.player_id)})"

@dataclass(frozen=True)
class Event:
    event_id: EventId = field(metadata={"compare": True})
    match_id: MatchId = field(metadata={"compare": False})
    event_type: EventType = field(metadata={"compare": False})
    minute: Optional[int] = field(default=None, metadata={"compare": False})
    main_player_id: Optional[PlayerId] = field(default=None, metadata={"compare": False})
    extra_player_id: Optional[PlayerId] = field(default=None, metadata={"compare": False})
    team_id: Optional[TeamId] = field(default=None, metadata={"compare": False})

    def __post_init__(self) -> None:
        if self.minute is not None and (self.minute < 0 or self.minute > 200):
            # margen amplio por tiempos añadidos/prórrogas
            raise ValueError("minute must be between 0 and 200")

    def __repr__(self) -> str:
        return f"Event(id={int(self.event_id)}, type={self.event_type}, match={int(self.match_id)})"

# ---------- Estadísticas base por jugador/partido ----------
@dataclass(frozen=True)
class BasicStats:
    """Métricas base por jugador y partido (core.basic_stats)."""
    basic_stats_id: BasicStatsId = field(metadata={"compare": True})
    match_id: MatchId = field(metadata={"compare": False})
    player_id: PlayerId = field(metadata={"compare": False})
    minutes: Optional[int] = field(default=None, metadata={"compare": False})
    goals: Optional[int] = field(default=None, metadata={"compare": False})
    assists: Optional[int] = field(default=None, metadata={"compare": False})

    def __post_init__(self) -> None:
        for name, val in (("minutes", self.minutes), ("goals", self.goals), ("assists", self.assists)):
            if val is not None and val < 0:
                raise ValueError(f"{name} must be >= 0")

# ---------- Derivadas de rol (opcional v1; útiles para KPIs de portero) ----------
@dataclass(frozen=True)
class GoalkeeperStats:
    """Estadísticas específicas de portero (stats.goalkeeper_stats), enlazadas por basic_stats_id."""
    basic_stats_id: BasicStatsId = field(metadata={"compare": True})
    saves: Optional[int] = field(default=None, metadata={"compare": False})
    goals_conceded: Optional[int] = field(default=None, metadata={"compare": False})
    goals_prevented: Optional[float] = field(default=None, metadata={"compare": False})
    xgot_against: Optional[float] = field(default=None, metadata={"compare": False})

    def __post_init__(self) -> None:
        for name, val in (("saves", self.saves), ("goals_conceded", self.goals_conceded)):
            if val is not None and val < 0:
                raise ValueError(f"{name} must be >= 0")

# ---------- Agregados de lectura (shapes útiles para services/queries) ----------
# Nota: Estos NO acceden a la BD; son contenedores inmutables para devolver datos a application/UI.

@dataclass(frozen=True)
class StandingRow:
    team_id: TeamId = field(metadata={"compare": True})
    team_name: str = field(metadata={"compare": False})
    MP: int = field(metadata={"compare": False})
    Pts: int = field(metadata={"compare": False})
    GF: int = field(metadata={"compare": False})
    GA: int = field(metadata={"compare": False})
    GD: int = field(metadata={"compare": False})

@dataclass(frozen=True)
class TeamFormRow:
    match_id: MatchId = field(metadata={"compare": True})
    matchday_number: int = field(metadata={"compare": False})
    home_team_id: TeamId = field(metadata={"compare": False})
    away_team_id: TeamId = field(metadata={"compare": False})
    local_score: Optional[int] = field(default=None, metadata={"compare": False})
    away_score: Optional[int] = field(default=None, metadata={"compare": False})
    result: Optional[TeamResult] = field(default=None, metadata={"compare": False})  # W/D/L desde la perspectiva del equipo consultado

@dataclass(frozen=True)
class TeamSplit:
    home_ppg: float = field(metadata={"compare": False})
    away_ppg: float = field(metadata={"compare": False})
    home_gf: int = field(metadata={"compare": False})
    home_ga: int = field(metadata={"compare": False})
    away_gf: int = field(metadata={"compare": False})
    away_ga: int = field(metadata={"compare": False})
    home_gd: int = field(metadata={"compare": False})
    away_gd: int = field(metadata={"compare": False})

@dataclass(frozen=True)
class ScorerRow:
    player_id: PlayerId = field(metadata={"compare": True})
    player_name: str = field(metadata={"compare": False})
    goals: int = field(metadata={"compare": False})

@dataclass(frozen=True)
class AssisterRow:
    player_id: PlayerId = field(metadata={"compare": True})
    player_name: str = field(metadata={"compare": False})
    assists: int = field(metadata={"compare": False})

@dataclass(frozen=True)
class KeeperKPI:
    player_id: PlayerId = field(metadata={"compare": True})
    player_name: str = field(metadata={"compare": False})
    goalkeeper_saves: Optional[int] = field(default=None, metadata={"compare": False})
    goals_prevented: Optional[float] = field(default=None, metadata={"compare": False})
    goals_conceded: Optional[int] = field(default=None, metadata={"compare": False})

# ---------- API de módulo ----------
__all__ = [
    # IDs
    "TeamId", "PlayerId", "CompetitionId", "SeasonId", "MatchdayId", "MatchId", "BasicStatsId", "EventId",
    # Enums
    "EventType", "Position", "Status", "TeamResult",
    # VO
    "Score",
    # Entidades
    "Team", "Competition", "Season", "Matchday", "Match", "Player", "Participation", "Event", "BasicStats", "GoalkeeperStats",
    # DTOs/Agregados de lectura
    "StandingRow", "TeamFormRow", "TeamSplit", "ScorerRow", "AssisterRow", "KeeperKPI",
]
