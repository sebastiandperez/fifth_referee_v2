# tests_app/test_pg_adapters_smoke.py
import pytest

from infrastructure.postgres.adapters import PgMatchAdapter
from infrastructure.postgres.connection import get_conn
from domain.ids import SeasonId
from domain.enums import EventType, Side

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
def test_list_by_season_and_participations_and_events_smoke():
    season_val = _find_any_season_id()
    season = SeasonId(season_val)

    adapter = PgMatchAdapter()

    # matches
    matches = adapter.list_by_season(season, only_finalized=False)
    assert isinstance(matches, list) and len(matches) >= 1

    m = matches[0]
    assert m.season_id == season
    assert m.home_team_id != m.away_team_id
    # finalized if both scores present
    if m.score is not None:
        assert m.finalized is True

    # participations
    parts = adapter.list_participations(m.match_id)
    assert all(p.match_id == m.match_id for p in parts)
    assert all(p.side in (Side.HOME, Side.AWAY) for p in parts)
    assert all(p.minutes_played >= 0 for p in parts)
    assert all(isinstance(p.starter, bool) for p in parts)

    # events (unknown types are filtered)
    events = adapter.list_events(m.match_id)
    assert all(isinstance(e.type, EventType) for e in events)
