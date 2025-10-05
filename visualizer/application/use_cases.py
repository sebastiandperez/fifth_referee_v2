from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from domain.ids import SeasonId, TeamId
from domain.entities.match import Match
from domain.entities.stats import StandingRow, TeamFormRow, TeamSplit
from domain.services.standings import compute_standings
from domain.services.analytics import compute_team_form, compute_team_splits
from domain.ports import StandingsPort, TeamAnalyticsPort

__all__ = [
    "SeasonStandingsDTO",
    "get_season_standings",
    "TeamDashboardDTO",
    "get_team_dashboard",
]


# ---------- Standings ----------

@dataclass(frozen=True, slots=True)
class SeasonStandingsDTO:
    rows: Sequence[StandingRow]


def get_season_standings(
    season_id: SeasonId,
    standings_port: StandingsPort,
) -> SeasonStandingsDTO:
    """
    Orchestrates standings computation from finalized results.
    The port returns domain Matches; we keep all domain logic inside services.
    """
    matches: Sequence[Match] = standings_port.list_finalized_matches(season_id)
    rows: Sequence[StandingRow] = compute_standings(season_id, matches)
    return SeasonStandingsDTO(rows=rows)


# ---------- Team Dashboard ----------

@dataclass(frozen=True, slots=True)
class TeamDashboardDTO:
    form: Sequence[TeamFormRow]
    split: TeamSplit


def get_team_dashboard(
    season_id: SeasonId,
    team_id: TeamId,
    port: TeamAnalyticsPort,
    *,
    n: int = 5,
) -> TeamDashboardDTO:
    """
    Builds a small “dashboard” bundle using analytics services.
    `n` controls the form window (last N matches).
    """
    matches: Sequence[Match] = port.list_results_for_team(season_id, team_id)
    return TeamDashboardDTO(
        form=compute_team_form(matches, team_id, n=n),
        split=compute_team_splits(matches, team_id),
    )
