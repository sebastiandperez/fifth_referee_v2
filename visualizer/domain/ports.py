from __future__ import annotations

from typing import Protocol, Sequence

from .ids import (
    CompetitionId, SeasonId, MatchdayId, MatchId, TeamId, PlayerId,
)
from .entities.competition import Competition
from .entities.season import Season, SeasonTeam
from .entities.matchday import Matchday
from .entities.match import Match, Participation, Event
from .entities.team import Team, TeamPlayer
from .entities.player import Player
from .entities.stats import (
    BasicStats, GoalkeeperStats, DefenderStats, MidfielderStats, ForwardStats,
    StandingRow, TeamFormRow, TeamSplit,
)

__all__ = [
    # Catalog / reference
    "CompetitionPort", "TeamPort", "PlayerPort",
    # Season-centric
    "SeasonPort",
    # Match-centric
    "MatchPort",
    # Read models for services
    "StandingsPort", "TeamAnalyticsPort", "PlayerStatsPort",
]


# ---- Catalog / reference ports ----

class CompetitionPort(Protocol):
    def list_competitions(self) -> Sequence[Competition]: ...
    def list_seasons(self, competition_id: CompetitionId) -> Sequence[Season]: ...


class TeamPort(Protocol):
    def get(self, team_id: TeamId) -> Team: ...
    def list_roster(self, team_id: TeamId) -> Sequence[TeamPlayer]: ...


class PlayerPort(Protocol):
    def get(self, player_id: PlayerId) -> Player: ...


# ---- Season-centric ----

class SeasonPort(Protocol):
    def get(self, season_id: SeasonId) -> Season: ...
    def list_matchdays(self, season_id: SeasonId) -> Sequence[Matchday]: ...
    def list_teams(self, season_id: SeasonId) -> Sequence[Team]: ...
    def list_season_teams(self, season_id: SeasonId) -> Sequence[SeasonTeam]: ...


# ---- Match-centric ----

class MatchPort(Protocol):
    def get(self, match_id: MatchId) -> Match: ...
    def list_by_season(self, season_id: SeasonId, only_finalized: bool = False) -> Sequence[Match]: ...
    def list_for_team(self, season_id: SeasonId, team_id: TeamId) -> Sequence[Match]: ...
    def list_participations(self, match_id: MatchId) -> Sequence[Participation]: ...
    def list_events(self, match_id: MatchId) -> Sequence[Event]: ...


# ---- Read models used by services ----
# Keep these laser-focused on what services need. Structural typing means your
# infrastructure adapter just needs to provide these call shapes.

class StandingsPort(Protocol):
    """Provides finalized match *results* for standings computation."""
    def list_finalized_matches(self, season_id: SeasonId) -> Sequence[Match]: ...


class TeamAnalyticsPort(Protocol):
    """Provides a team’s season results for analytics like form/splits."""
    def list_results_for_team(self, season_id: SeasonId, team_id: TeamId) -> Sequence[Match]: ...


class PlayerStatsPort(Protocol):
    """
    Aggregate player stats read model. Use only if an analytics feature needs it.
    Note: domain BasicStats is intentionally minimal. If you need the full DB shape,
    consider a separate read DTO instead of expanding the domain entity.
    """
    def list_basic_stats_by_season(self, season_id: SeasonId) -> Sequence[BasicStats]: ...
