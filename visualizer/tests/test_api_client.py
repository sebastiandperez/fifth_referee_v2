# test_api_client.py
import json
from typing import Any, Dict, Tuple
import pytest
import pandas as pd

from visualizer.interfaces.Api_client import APIClient

# -----------------------------
# Fake HTTP plumbing
# -----------------------------

class _FakeResponse:
    def __init__(self, status_code: int, payload: Dict[str, Any] | None = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        # emulate requests.Response.json()
        return json.loads(json.dumps(self._payload))


class _RouterSession:
    """
    Minimal stand-in for requests.Session with a deterministic router.
    You can mutate self.calls to inspect requests made by the client.
    """
    def __init__(self):
        self.headers = {}
        self.calls = []  # list of (method, url, params, json)
        self._fail_once_paths = set()  # for retry test

    def request(self, method, url, params=None, json=None, timeout: Tuple[float, float] | None = None):
        self.calls.append((method, url, params or {}, json))
        path = url.split("://", 1)[-1].split("/", 1)[-1]  # strip scheme/host, keep path after first "/"

        # Simulate one transient failure for retry test
        if path.startswith("v1/season-labels") and ("fail-once" in self._fail_once_paths):
            self._fail_once_paths.remove("fail-once")
            return _FakeResponse(503, text="temporary outage")

        # ---- Discovery ----
        if path == "v1/season-labels":
            return _FakeResponse(200, {"items": ["2024_2025"]})

        if path.startswith("v1/season-labels/2024_2025/competitions"):
            return _FakeResponse(200, {"items": [{"id": 10, "name": "Premier League"}]})

        if path.startswith("v1/seasons/resolve"):
            assert params == {"season_label": "2024_2025", "competition_id": 10}
            return _FakeResponse(200, {"season_id": 1})

        # ---- Summary ----
        if path == "v1/seasons/1/summary":
            return _FakeResponse(200, {
                "season_id": 1, "season_label": "2024_2025",
                "competition_id": 10, "competition_name": "Premier League",
                "team_count": 2
            })

        # ---- Standings ----
        if path == "v1/seasons/1/standings":
            # server returns rows with expected keys
            rows = [
                {"team_id": 101, "team_name": "Alpha FC", "played": 2, "win": 2, "draw": 0, "loss": 0,
                 "gf": 4, "ga": 1, "gd": 3, "points": 6, "position": 1},
                {"team_id": 202, "team_name": "Beta United", "played": 2, "win": 1, "draw": 0, "loss": 1,
                 "gf": 3, "ga": 3, "gd": 0, "points": 3, "position": 2},
            ]
            return _FakeResponse(200, {"rows": rows})

        # ---- Teams/Players/Matchdays (minimal stubs) ----
        if path == "v1/seasons/1/teams":
            return _FakeResponse(200, {"items": [{"team_id": 101, "team_name": "Alpha FC"}]})
        if path == "v1/seasons/1/players":
            return _FakeResponse(200, {"items": [{"team_id": 101, "player_id": 1001, "player_name": "Ada"}]})
        if path == "v1/seasons/1/matchdays":
            return _FakeResponse(200, {"items": [{"matchday_id": 11, "matchday_number": 1}]})

        # ---- Matches ----
        if path == "v1/seasons/1/matches":
            # Just echo a single match; assert include param passes through
            inc = params.get("include")
            if inc is not None:
                assert inc in ("events", "participations", "events,participations")
            return _FakeResponse(200, [
                {"match_id": 5001, "matchday_id": 11, "home_team_id": 101, "away_team_id": 202,
                 "home_score": 2, "away_score": 1, "duration": 95}
            ])

        # ---- Stats: basic ----
        if path == "v1/seasons/1/stats/basic":
            # Return intentionally incomplete columns to test client _ensure_df
            items = [
                {"basic_stats_id": 10, "match_id": 5001, "player_id": 1001, "minutes": 90, "goals": 1, "assists": 0},
                {"basic_stats_id": 11, "match_id": 5001, "player_id": 1002, "minutes": 75, "goals": 0, "assists": 1},
            ]
            return _FakeResponse(200, {"items": items, "limit": params.get("limit", 2000),
                                       "offset": params.get("offset", 0), "total": len(items)})

        # ---- Stats: forward (basic shape) ----
        if path == "v1/seasons/1/stats/forward":
            items = [{"basic_stats_id": 10, "expected_goals": 0.6, "expected_assists": 0.2}]
            return _FakeResponse(200, {"items": items, "limit": 2000, "offset": 0, "total": 1})

        return _FakeResponse(404, text=f"no route for {path}")

# -----------------------------
# Fixtures
# -----------------------------

@pytest.fixture
def fake_session(monkeypatch):
    sess = _RouterSession()
    # Monkeypatch the Session factory so APIClient creates our fake
    monkeypatch.setattr("interfaces.api_client.requests.Session", lambda: sess)
    # Remove real sleeping during retries
    monkeypatch.setattr("interfaces.api_client.time.sleep", lambda *_args, **_kw: None)
    return sess

@pytest.fixture
def client(fake_session):
    # backoff=0 ensures no wait; max_retries=1 to exercise retry path quickly
    return APIClient(base_url="http://fake-host", max_retries=1, backoff=0)

# -----------------------------
# Tests
# -----------------------------

def test_discovery_and_resolve(client, fake_session):
    labels = client.season_labels()
    assert labels == ["2024_2025"]

    comps = client.competitions_for_label(labels[0])
    assert comps[0]["id"] == 10 and comps[0]["name"] == "Premier League"

    sid = client.resolve_season(labels[0], 10)
    assert sid == 1

    ssum = client.season_summary(1)
    assert ssum["team_count"] == 2

def test_standings_df_shape_and_types(client):
    df = client.standings_df(1)
    expected_cols = ["team_id","team_name","played","win","draw","loss","gf","ga","gd","points","position"]
    assert list(df.columns) == expected_cols
    assert df.loc[0, "team_name"] == "Alpha FC"
    # numeric coercion
    assert pd.api.types.is_numeric_dtype(df["played"])
    assert int(df["points"].sum()) == 9

def test_basic_stats_df_fills_missing_columns(client):
    df = client.stats_basic_df(1, limit=999, offset=0)
    # all enforced columns must exist
    expected = [
        "basic_stats_id","match_id","player_id","minutes","goals","assists","touches",
        "passes_total","passes_completed","ball_recoveries","possessions_lost",
        "aerial_duels_won","aerial_duels_total","ground_duels_won","ground_duels_total",
    ]
    assert list(df.columns) == expected
    # the router omitted many fields; they should be present (filled with None)
    assert df["touches"].isna().all()
    assert df["minutes"].tolist() == [90, 75]

def test_matches_includes_flag_passthrough(client):
    out = client.matches(1, include="events,participations")
    assert isinstance(out, list) and out and out[0]["match_id"] == 5001

def test_retries_and_backoff(client, fake_session):
    # configure router to fail once on season-labels; second attempt should succeed
    fake_session._fail_once_paths.add("fail-once")
    labels = client.season_labels()
    assert labels == ["2024_2025"]
    # ensure we actually attempted twice
    calls_for_labels = [c for c in fake_session.calls if c[1].endswith("/v1/season-labels")]
    assert len(calls_for_labels) >= 2
