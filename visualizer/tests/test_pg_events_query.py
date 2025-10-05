import pytest
from infrastructure.postgres.adapters import PgMatchAdapter
from infrastructure.postgres.connection import get_conn
from domain.ids import SeasonId

def _any_match_id():
    q = "SELECT match_id FROM core.match ORDER BY match_id LIMIT 1"
    with get_conn() as c:
        r = c.execute(q).fetchone()
        return r and int(r["match_id"])

@pytest.mark.skipif(_any_match_id() is None, reason="No matches in DB")
def test_events_query_matches_schema():
    adapter = PgMatchAdapter()
    mid = _any_match_id()
    evs = adapter.list_events(mid)
    # Should not crash; all events mapped or filtered
    assert isinstance(evs, list)
