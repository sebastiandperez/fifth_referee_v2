import os
import pytest
from infrastructure.postgres.adapters import PgMatchAdapter
from application.use_cases import get_season_standings, get_team_dashboard
from domain.ids import SeasonId, TeamId

pytestmark = pytest.mark.skipif(
    not os.environ.get("POSTGRES_DSN"),
    reason="POSTGRES_DSN not set; skipping PG adapter tests",
)

def test_pg_list_and_use_cases_smoke():
    adapter = PgMatchAdapter()
    # Pick an existing season id in your DB; if unknown, this still should not raise
    season = SeasonId(2025)
    matches = adapter.list_by_season(season, only_finalized=False)
    assert isinstance(matches, list)

    # Standings use-case
    standings = get_season_standings(season, adapter)
    assert hasattr(standings, "rows")

    # Team dashboard use-case: pick a likely team id (or loop first)
    team = None
    if matches:
        first = matches[0]
        team = first.home_team_id
    if team is None:
        team = TeamId(1)
    dashboard = get_team_dashboard(season, team, adapter)
    assert hasattr(dashboard.split, "home_ppg")
