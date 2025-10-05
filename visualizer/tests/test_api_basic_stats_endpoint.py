# test_api_basic_stats_endpoint.py
import re
import pytest
from starlette.testclient import TestClient
import visualizer.interfaces.__ap as api_mod  # your FastAPI app module

SEASON_ID = 1

BASIC_ROWS = [
    (10, 101, 1001, 90, 1, 0, 50, 42, 38, 8, 9, 3, 5, 7, 12),
    (11, 101, 1002, 75, 0, 1, 47, 40, 35, 6, 7, 2, 4, 6, 10),
    # include NULLs to verify COALESCE behavior
    (12, 102, 1003, None, None, None, None, None, None, None, None, None, None, None, None),
]

class _Result:
    def __init__(self, rows): self._rows = rows
    def fetchone(self): return self._rows[0] if self._rows else None
    def fetchall(self): return list(self._rows)

class _Conn:
    def __enter__(self): return self
    def __exit__(self, *exc): return False

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        params = params or []

        # existence check
        if re.search(r"SELECT 1 FROM core\.season WHERE season_id = %s", s):
            return _Result([(1,)] if params and params[0] == SEASON_ID else [])

        # count(*) for basic stats
        if s.startswith("SELECT COUNT(*) FROM core.basic_stats"):
            return _Result([(len(BASIC_ROWS),)])

        # SELECT list for basic stats (simulate COALESCE by zero-filling None)
        if s.startswith("SELECT bs.basic_stats_id, bs.match_id, bs.player_id"):
            limit = params[-2]; offset = params[-1]
            sliced = BASIC_ROWS[offset: offset + limit]
            coalesced = []
            for row in sliced:
                r = list(row)
                for i in range(3, len(r)):           # minutes .. ground_duels_total
                    if r[i] is None:
                        r[i] = 0
                coalesced.append(tuple(r))
            return _Result(coalesced)

        return _Result([])

class _DBCtxMgr:
    def __call__(self): return _Conn()

@pytest.fixture(autouse=True)
def patch_db(monkeypatch):
    monkeypatch.setattr("interfaces.api.get_conn", _DBCtxMgr())
    yield

@pytest.fixture
def client(): return TestClient(api_mod.api)

def test_basic_stats_happy_path(client):
    r = client.get(f"/v1/seasons/{SEASON_ID}/stats/basic",
                   params={"limit": 1000, "offset": 0})
    assert r.status_code == 200
    payload = r.json()
    assert payload["total"] == len(BASIC_ROWS)
    items = payload["items"]
    assert len(items) == len(BASIC_ROWS)
    ids = [it["basic_stats_id"] for it in items]
    assert ids == sorted(ids)

    it0 = items[0]
    assert it0["basic_stats_id"] == 10
    assert it0["match_id"] == 101
    assert it0["player_id"] == 1001
    assert it0["minutes"] == 90
    assert it0["goals"] == 1
    assert it0["passes_total"] == 42
    assert it0["passes_completed"] == 38
    assert it0["aerial_duels_won"] == 3
    assert it0["aerial_duels_total"] == 5

    it_nulls = [it for it in items if it["basic_stats_id"] == 12][0]
    numeric_fields = [
        "minutes","goals","assists","touches","passes_total","passes_completed",
        "ball_recoveries","possessions_lost","aerial_duels_won","aerial_duels_total",
        "ground_duels_won","ground_duels_total"
    ]
    assert all(it_nulls[f] == 0 for f in numeric_fields)

def test_basic_stats_pagination(client):
    r = client.get(f"/v1/seasons/{SEASON_ID}/stats/basic",
                   params={"limit": 1, "offset": 1})
    assert r.status_code == 200
    payload = r.json()
    assert payload["total"] == len(BASIC_ROWS)
    assert len(payload["items"]) == 1
    assert payload["items"][0]["basic_stats_id"] == 11

def test_basic_stats_accepts_filters(client):
    r = client.get(
        f"/v1/seasons/{SEASON_ID}/stats/basic",
        params={"team_id": 999, "player_id": 1002, "matchday_from": 1, "matchday_to": 99}
    )
    assert r.status_code == 200
    payload = r.json()
    assert "items" in payload and isinstance(payload["items"], list)
    assert payload["total"] == len(BASIC_ROWS)
