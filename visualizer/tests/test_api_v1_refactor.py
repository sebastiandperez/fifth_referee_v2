# tests_api/test_api_v1_refactor.py
from types import SimpleNamespace
from fastapi.testclient import TestClient

import interfaces.api2 as api2  # your FastAPI app module


client = TestClient(api2.api)


def _install_fakes(monkeypatch):
    # ---- Discovery helpers
    monkeypatch.setattr(api2, "_list_season_labels", lambda: ["2024/2025", "2023/2024"])
    monkeypatch.setattr(
        api2,
        "_list_competitions_for_label",
        lambda season_label: [
            api2.CompetitionItem(id=1, name="Premier League"),
            api2.CompetitionItem(id=2, name="Serie A"),
        ] if season_label == "2024/2025" else [],
    )
    monkeypatch.setattr(
        api2,
        "_resolve_season_id",
        lambda season_label, competition_id: 42 if (season_label, competition_id) == ("2024/2025", 1) else None,
    )
    monkeypatch.setattr(
        api2,
        "_season_summary",
        lambda season_id: api2.SeasonSummary(
            season_id=season_id,
            season_label="2024/2025",
            competition_id=1,
            competition_name="Premier League",
            team_count=3,
            matchday_min=1,
            matchday_max=38,
            last_finalized_matchday=12,
        ),
    )
    monkeypatch.setattr(
        api2,
        "_list_teams",
        lambda season_id: [
            api2.TeamItem(team_id=10, team_name="Alpha"),
            api2.TeamItem(team_id=20, team_name="Beta"),
            api2.TeamItem(team_id=30, team_name="Gamma"),
        ],
    )
    monkeypatch.setattr(
        api2,
        "_team_name_map",
        lambda season_id: {10: "Alpha", 20: "Beta", 30: "Gamma"},
    )

    # ---- Domain use-cases (standings & dashboard)
    class FakeStandingRow:
        def __init__(self, team_id, played, win, draw, loss, gf, ga, position):
            self.team_id = team_id
            self.played = played
            self.win = win
            self.draw = draw
            self.loss = loss
            self.gf = gf
            self.ga = ga
            self.position = position

    class FakeStandingsDTO:
        def __init__(self, rows):
            self.rows = rows

    def fake_get_season_standings(season_id, standings_port):
        rows = [
            FakeStandingRow(10, played=12, win=8, draw=3, loss=1, gf=20, ga=10, position=1),
            FakeStandingRow(20, played=12, win=6, draw=3, loss=3, gf=18, ga=12, position=2),
            FakeStandingRow(30, played=12, win=4, draw=4, loss=4, gf=14, ga=14, position=3),
        ]
        return FakeStandingsDTO(rows)

    monkeypatch.setattr(api2, "get_season_standings", fake_get_season_standings)

    class FakeTeamDashboard:
        def __init__(self):
            self.form = [
                SimpleNamespace(match_id=1001, result=SimpleNamespace(name="WIN")),
                SimpleNamespace(match_id=1002, result=SimpleNamespace(name="DRAW")),
                SimpleNamespace(match_id=1003, result=SimpleNamespace(name="LOSS")),
            ]
            self.split = SimpleNamespace(
                home_ppg=2.3, away_ppg=1.2, home_gf=12, away_gf=8, home_ga=5, away_ga=7
            )

    monkeypatch.setattr(api2, "get_team_dashboard", lambda season_id, team_id, port: FakeTeamDashboard())

    # ---- Fake Adapter for matches/events/participations
    class FakeMatch:
        def __init__(self, match_id, matchday_id, home_team_id, away_team_id, hs, as_, duration=None):
            self.match_id = match_id
            self.matchday_id = matchday_id
            self.home_team_id = home_team_id
            self.away_team_id = away_team_id
            self.duration = duration
            self.score = SimpleNamespace(home=hs, away=as_) if hs is not None and as_ is not None else None

    class FakeEvent:
        def __init__(self, event_id, match_id, event_type, minute, main_player_id=None, extra_player_id=None, team_id=None):
            self.event_id = event_id
            self.match_id = match_id
            self.event_type = event_type
            self.minute = minute
            self.main_player_id = main_player_id
            self.extra_player_id = extra_player_id
            self.team_id = team_id

    class FakeParticipation:
        def __init__(self, match_id, player_id, team_id, role=None, minute_in=None, minute_out=None):
            self.match_id = match_id
            self.player_id = player_id
            self.team_id = team_id
            self.role = role
            self.minute_in = minute_in
            self.minute_out = minute_out

    class FakeAdapter:
        def list_matches_filtered(self, season_id, matchday=None, team_id=None, opponent_id=None,
                                  finalized=None, limit=200, offset=0):
            all_matches = [
                FakeMatch(100, 12, 10, 20, 2, 1, 90),
                FakeMatch(101, 12, 30, 10, 0, 0, 90),
                FakeMatch(102, 13, 20, 30, None, None, 90),  # not finalized
            ]
            res = all_matches
            if matchday is not None:
                res = [m for m in res if m.matchday_id == matchday]
            if team_id is not None:
                res = [m for m in res if m.home_team_id == team_id or m.away_team_id == team_id]
            if opponent_id is not None:
                res = [m for m in res if opponent_id in (m.home_team_id, m.away_team_id)]
            if finalized is not None:
                def is_final(m): return m.score is not None
                res = [m for m in res if is_final(m) == finalized]
            return res[offset: offset + limit]

        def list_events_for_matches(self, match_ids):
            out = [
                FakeEvent(1, 100, "GOAL", 12, main_player_id=501, team_id=10),
                FakeEvent(2, 100, "YELLOW_CARD", 44, main_player_id=502, team_id=20),
                FakeEvent(3, 101, "GOAL", 77, main_player_id=601, team_id=10),
            ]
            return [e for e in out if e.match_id in match_ids]

        def list_participations_for_matches(self, match_ids):
            return [
                FakeParticipation(100, 501, 10, role="Starter", minute_in=0),
                FakeParticipation(100, 502, 20, role="Starter", minute_in=0),
                FakeParticipation(101, 601, 10, role="Sub", minute_in=60),
            ]

        def list_events_for_match(self, match_id):
            return [e for e in self.list_events_for_matches([match_id])]

        def list_participations_for_match(self, match_id):
            return [p for p in self.list_participations_for_matches([match_id])]

    # IMPORTANT: override dependency captured by Depends(get_adapter)
    api2.api.dependency_overrides[api2.get_adapter] = lambda: FakeAdapter()


# ---------------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------------
def test_discovery_and_summary(monkeypatch):
    _install_fakes(monkeypatch)

    r = client.get("/v1/season-labels")
    assert r.status_code == 200
    assert r.json()["items"][0] == "2024/2025"

    # URL-encode the slash to match {season_label} style routes
    r = client.get("/v1/season-labels/2024_2025/competitions")
    assert r.status_code == 200
    comps = r.json()["items"]
    assert any(c["name"] == "Premier League" for c in comps)

    r = client.get("/v1/seasons/resolve", params={"season_label": "2024/2025", "competition_id": 1})
    assert r.status_code == 200 and r.json()["season_id"] == 42

    r = client.get("/v1/seasons/42/summary")
    summary = r.json()
    assert r.status_code == 200
    assert summary["competition_name"] == "Premier League"
    assert summary["team_count"] == 3
    assert summary["last_finalized_matchday"] == 12

    r = client.get("/v1/seasons/42/teams")
    assert r.status_code == 200
    names = [t["team_name"] for t in r.json()["items"]]
    assert set(names) == {"Alpha", "Beta", "Gamma"}


def test_standings_dashboard_and_matches(monkeypatch):
    _install_fakes(monkeypatch)

    # standings with custom points
    r = client.get("/v1/seasons/42/standings?win=3&draw=1&loss=0")
    assert r.status_code == 200
    rows = r.json()["rows"]
    alpha = next(row for row in rows if row["team_id"] == 10)
    assert alpha["team_name"] == "Alpha"
    assert alpha["points"] == 27
    assert alpha["position"] == 1

    # team dashboard
    r = client.get("/v1/seasons/42/teams/10/dashboard?form_n=5")
    assert r.status_code == 200
    dash = r.json()
    assert len(dash["form"]) == 3
    assert dash["split"]["home_ppg"] == 2.3

    # matches filtered by matchday and include events
    r = client.get("/v1/seasons/42/matches?matchday=12&include=events,participations")
    assert r.status_code == 200
    matches = r.json()
    assert {m["match_id"] for m in matches} == {100, 101}
    m100 = next(m for m in matches if m["match_id"] == 100)
    assert m100["home_team_id"] == 10 and m100["away_team_id"] == 20
    assert m100["home_score"] == 2 and m100["away_score"] == 1
    assert len(m100["events"]) == 2

    # single-match resources
    r = client.get("/v1/matches/100/events")
    assert r.status_code == 200 and len(r.json()) == 2
    r = client.get("/v1/matches/100/participations")
    assert r.status_code == 200 and len(r.json()) == 2

    # finalized=false should only return the non-finalized one (match 102)
    r = client.get("/v1/seasons/42/matches?finalized=false")
    ids = {m["match_id"] for m in r.json()}
    assert ids == {102}
