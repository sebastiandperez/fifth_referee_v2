from fastapi.testclient import TestClient

import interfaces.api2 as api_mod  # so we can monkeypatch inside the module
from domain.entities.match import Match, Participation, Event
from domain.value_objects import Score, Minute
from domain.enums import Side, EventType
from domain.ids import MatchId, SeasonId, TeamId, PlayerId

client = TestClient(api_mod.app)


# --- Fake adapter that mimics the ports used by the API/use-cases ------------
class FakeAdapter:
    """
    Two finalized matches in season 99 involving teams 1, 2, 3:
      - Match 1: T1 (home) 2–1 T2
      - Match 2: T3 (home) 0–0 T1
    Enough to test standings, dashboard, fixtures, events, and participations.
    """
    def __init__(self):
        self._m1 = Match(MatchId(1), SeasonId(99), 1, TeamId(1), TeamId(2))
        self._m1.set_score(Score(2, 1), finalized=True)
        self._m2 = Match(MatchId(2), SeasonId(99), 2, TeamId(3), TeamId(1))
        self._m2.set_score(Score(0, 0), finalized=True)

    # StandingsPort
    def list_finalized_matches(self, season_id):
        assert int(season_id) == 99
        return [self._m1, self._m2]

    # TeamAnalyticsPort
    def list_results_for_team(self, season_id, team_id):
        assert int(season_id) == 99 and int(team_id) in (1, 2, 3)
        return [m for m in [self._m1, self._m2] if int(team_id) in (int(m.home_team_id), int(m.away_team_id))]

    # MatchPort
    def list_for_team(self, season_id, team_id):
        return self.list_results_for_team(season_id, team_id)

    def list_participations(self, match_id):
        assert int(match_id) in (1, 2)
        # For match 1, return 2 home + 2 away convocations
        if int(match_id) == 1:
            return [
                Participation(match_id=MatchId(1), team_id=TeamId(1), player_id=PlayerId(1001),
                              side=Side.HOME, starter=True, minutes_played=90, position_hint="MF"),
                Participation(match_id=MatchId(1), team_id=TeamId(1), player_id=PlayerId(1002),
                              side=Side.HOME, starter=False, minutes_played=25, position_hint="FW"),
                Participation(match_id=MatchId(1), team_id=TeamId(2), player_id=PlayerId(2001),
                              side=Side.AWAY, starter=True, minutes_played=90, position_hint="DF"),
                Participation(match_id=MatchId(1), team_id=TeamId(2), player_id=PlayerId(2002),
                              side=Side.AWAY, starter=False, minutes_played=10, position_hint="MF"),
            ]
        return []

    def list_events(self, match_id):
        assert int(match_id) == 1
        return [
            Event(match_id=MatchId(1), minute=Minute(10), type=EventType.GOAL,
                  team_id=TeamId(1), player_id=PlayerId(1001)),
            Event(match_id=MatchId(1), minute=Minute(75), type=EventType.YELLOW_CARD,
                  team_id=TeamId(2), player_id=PlayerId(2002)),
        ]


# --- Helpers to install fakes into the API module ----------------------------
def _install_fakes(monkeypatch):
    # Replace the adapter factory with our fake adapter
    monkeypatch.setattr(api_mod, "default_adapter_factory", lambda: FakeAdapter())
    # Replace team-name lookup so we don't hit the DB
    monkeypatch.setattr(api_mod, "season_team_names", lambda sid: {1: "Alpha", 2: "Beta", 3: "Gamma"})


# --- Tests -------------------------------------------------------------------

def test_standings_with_names_and_policy(monkeypatch):
    _install_fakes(monkeypatch)
    r = client.get("/v1/seasons/99/standings?win=3&draw=1&loss=0")
    assert r.status_code == 200
    rows = r.json()
    # Expect three teams present
    assert {row["team_name"] for row in rows} == {"Alpha", "Beta", "Gamma"}
    # Alpha (team 1) has W + D = 4 pts, others 1 and 0
    pts_map = {row["team_name"]: row["Pts"] for row in rows}
    assert pts_map["Alpha"] == 4
    assert set(pts_map.values()) == {4, 1, 0}
    # Sum(MP) must be 2 * number of finalized matches (2 matches -> 4 MP total)
    assert sum(row["MP"] for row in rows) == 4


def test_team_dashboard_and_matches(monkeypatch):
    _install_fakes(monkeypatch)
    # Dashboard for team 1
    r = client.get("/v1/seasons/99/teams/1/dashboard?form_n=5")
    assert r.status_code == 200
    dash = r.json()
    assert "form" in dash and "split" in dash
    # Splits should be: home PPG = 3.0 (win), away PPG = 1.0 (draw)
    assert dash["split"]["home_ppg"] == 3.0
    assert dash["split"]["away_ppg"] == 1.0

    # Matches list for team 1 (chronological)
    r2 = client.get("/v1/seasons/99/teams/1/matches")
    assert r2.status_code == 200
    ms = r2.json()
    assert len(ms) == 2
    # First match is Alpha vs Beta 2-1
    assert ms[0]["home_team_name"] == "Alpha"
    assert ms[0]["away_team_name"] == "Beta"
    assert ms[0]["score"] == "2-1"
    # Second match is Gamma vs Alpha 0-0
    assert ms[1]["home_team_name"] == "Gamma"
    assert ms[1]["score"] == "0-0"


def test_participations_and_events(monkeypatch):
    _install_fakes(monkeypatch)

    # Participations
    r = client.get("/v1/matches/1/participations")
    assert r.status_code == 200
    parts = r.json()
    assert len(parts) == 4
    assert {p["side"] for p in parts} == {"HOME", "AWAY"}
    assert all(isinstance(p["starter"], bool) for p in parts)
    assert all(p["minutes_played"] >= 0 for p in parts)

    # Events
    r2 = client.get("/v1/matches/1/events")
    assert r2.status_code == 200
    evs = r2.json()
    assert len(evs) == 2
    types = [e["type"] for e in evs]
    assert "GOAL" in types and "YELLOW_CARD" in types
