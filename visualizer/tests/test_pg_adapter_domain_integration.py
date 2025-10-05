import pytest

from infrastructure.postgres.adapters import PgMatchAdapter
from infrastructure.postgres.connection import get_conn
from domain.ids import SeasonId, TeamId
from domain.services.standings import compute_standings
from domain.services.analytics import compute_team_form, compute_team_splits
from domain.enums import Result

def _find_any_season_id():
    q = """
    SELECT md.season_id, COUNT(*) AS n
    FROM core.match m
    JOIN core.matchday md USING (matchday_id)
    GROUP BY md.season_id
    ORDER BY n DESC
    LIMIT 1
    """
    with get_conn() as conn:
        row = conn.execute(q).fetchone()
        return int(row["season_id"]) if row else None

@pytest.mark.skipif(_find_any_season_id() is None, reason="No seasons with matches in DB")
def test_standings_and_team_analytics_pipeline():
    season_val = _find_any_season_id()
    season = SeasonId(season_val)

    adapter = PgMatchAdapter()
    matches = adapter.list_by_season(season, only_finalized=True)
    assert matches, "Expected finalized matches in historical DB"

    # Standings (note: your domain impl ignores season_id; we pass only this season’s matches)
    table = compute_standings(season, matches)
    assert len(table) >= 2
    assert all(r.MP >= 0 and r.Pts >= 0 for r in table)

    # Pick a team from first match and compute analytics
    team: TeamId = matches[0].home_team_id
    form = compute_team_form(matches, team, n=5)
    split = compute_team_splits(matches, team)

    # Sanity assertions (don’t assume results, just types and ranges)
    assert all(r.result in (Result.WIN, Result.DRAW, Result.LOSS) for r in form)
    assert split.home_ppg >= 0.0 and split.away_ppg >= 0.0
