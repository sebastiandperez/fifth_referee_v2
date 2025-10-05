from __future__ import annotations

# ---- IDs
from .ids import (
    CompetitionId, SeasonId, MatchdayId, MatchId,
    TeamId, PlayerId,
)

# ---- Enums
from .enums import Position, Side, Result, EventType

# ---- Value Objects
from .value_objects import Name, DateRange, Minute, DateTimeUTC, Score

# ---- Entities / Aggregates
from .entities.competition import Competition
from .entities.player import Player
from .entities.team import Team, TeamPlayer, TeamRoster
from .entities.matchday import Matchday
from .entities.season import Season, SeasonTeam, SeasonSchedule
from .entities.match import Match, Participation, Event, Lineups
from .entities.stats import (
    # standings / analytics aggregates
    StandingRow, TeamFormRow, TeamSplit,
    # per-player-per-match
    BasicStats, GoalkeeperStats, DefenderStats, MidfielderStats, ForwardStats,
)

# ---- Domain Services & Policies
from .services.policies import PointsPolicy, TieBreakPolicy
from .services.standings import compute_standings
from .services.analytics import compute_team_form, compute_team_splits

# ---- Errors
from .errors import DomainError, NotFound, ValidationError, InvariantError

__all__ = [
    # IDs
    "CompetitionId", "SeasonId", "MatchdayId", "MatchId", "TeamId", "PlayerId",
    # Enums
    "Position", "Side", "Result", "EventType",
    # VOs
    "Name", "DateRange", "Minute", "DateTimeUTC", "Score",
    # Entities / Aggregates
    "Competition", "Player", "Team", "TeamPlayer", "TeamRoster",
    "Matchday", "Season", "SeasonTeam", "SeasonSchedule",
    "Match", "Participation", "Event", "Lineups",
    "StandingRow", "TeamFormRow", "TeamSplit",
    "BasicStats", "GoalkeeperStats", "DefenderStats", "MidfielderStats", "ForwardStats",
    # Services & Policies
    "PointsPolicy", "TieBreakPolicy",
    "compute_standings", "compute_team_form", "compute_team_splits",
    # Errors
    "DomainError", "NotFound", "ValidationError", "InvariantError",
]
