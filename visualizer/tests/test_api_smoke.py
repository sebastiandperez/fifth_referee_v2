# tests_api/test_api_smoke.py
from fastapi.testclient import TestClient
import types

from interfaces.api2 import app

def test_health_route_exists():
    client = TestClient(app)
    # can't guarantee DB here—just check route is mounted
    r = client.get("/health")
    assert r.status_code in (200, 500)

def test_standings_endpoint_monkeypatched(monkeypatch):
    # Build a fake adapter object with the method the use-case needs
    class FakeAdapter:
        def list_finalized_matches(self, season_id):  # use-case asks this
            from domain.entities.match import Match
            from domain.ids import MatchId, SeasonId, TeamId
            from domain.value_objects import Score
            # two finalized matches => a tiny table
            m1 = Match(MatchId(1), SeasonId(2025), 1, TeamId(1), TeamId(2))
            m1.set_score(Score(2,1), finalized=True)
            m2 = Match(MatchId(2), SeasonId(2025), 1, TeamId(3), TeamId(1))
            m2.set_score(Score(0,0), finalized=True)
            return [m1, m2]
    # Patch the app route to use our FakeAdapter in place of PgMatchAdapter
    import interfaces.api2 as api_mod
    monkeypatch.setattr(api_mod, "PgMatchAdapter", lambda: FakeAdapter())

    client = TestClient(app)
    r = client.get("/seasons/2025/standings")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list) and len(body) == 3
