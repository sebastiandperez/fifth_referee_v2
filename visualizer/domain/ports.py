from __future__ import annotations
from typing import Protocol, Sequence, Optional
from datetime import datetime

from .ids import (
    CompetitionId, SeasonId, MatchdayId, MatchId, TeamId, PlayerId
)
from .entities.competition import Competition
from .entities.season import Season, SeasonTeam
from .entities.matchday import Matchday
from .entities.match import Match, Participation, Event
from .entities.team import Team, TeamPlayer
from .entities.player import Player
from .entities.stats import (
    BasicStats, GoalkeeperStats, DefenderStats, MidfielderStats, ForwardStats,
    StandingRow, TeamFormRow, TeamSplit
)


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


# ---- Stats-centric (read models used by analytics/standings) ----

class StandingsPort(Protocol):
    """Provides finalized match results or a precomputed standing dataset."""
    def list_finalized_matches(self, season_id: SeasonId) -> Sequence[Match]: ...


class TeamAnalyticsPort(Protocol):
    """Provides data needed to compute team form and splits."""
    def list_results_for_team(self, season_id: SeasonId, team_id: TeamId) -> Sequence[Match]: ...


class PlayerStatsPort(Protocol):
    """If you have read models for top scorers, assisters, keepers, etc."""
    def list_basic_stats_by_season(self, season_id: SeasonId) -> Sequence[BasicStats]: ...
    # You can add role-specific queries if precomputed