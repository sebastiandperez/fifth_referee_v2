import math
import pytest

from infrastructure.postgres.adapters import PgMatchAdapter
from infrastructure.postgres.connection import get_conn, CONFIG_PATH, _resolve_config_file

from domain.ids import SeasonId, TeamId
from domain.enums import Result
from application.use_cases import get_season_standings, get_team_dashboard


def _any_season_with_matches():
    q = """
    SELECT md.season_id, COUNT(*) AS n
    FROM core.match m
    JOIN core.matchday md USING (matchday_id)
    GROUP BY md.season_id
    HAVING COUNT(*) > 0
    ORDER BY n DESC, md.season_id DESC
    LIMIT 1
    """
    with get_conn() as c:
        r = c.execute(q).fetchone()
        return int(r["season_id"]) if r else None


def _any_team_in_season(season_id: int) -> int | None:
    q = "SELECT team_id FROM registry.season_team WHERE season_id=%s ORDER BY team_id LIMIT 1"
    with get_conn() as c:
        r = c.execute(q, (season_id,)).fetchone()
        return int(r["team_id"]) if r else None


@pytest.mark.skipif(
    (lambda: (not _resolve_config_file(CONFIG_PATH).exists()))(),
    reason="Config file not found / unreadable; update CONFIG_PATH or file contents.",
)
@pytest.mark.skipif(_any_season_with_matches() is None, reason="No seasons with matches in DB")
@pytest.mark.e2e
def test_e2e_standings_and_team_dashboard_properties():
    # ----- Discover a real season & team from DB
    season_val = _any_season_with_matches()
    assert season_val is not None
    season = SeasonId(season_val)

    team_val = _any_team_in_season(season_val)
    assert team_val is not None
    team = TeamId(team_val)

    adapter = PgMatchAdapter()

    # ----- Application use-case: standings (via domain service)
    standings_dto = get_season_standings(season, adapter)
    rows = list(standings_dto.rows)
    assert rows, "Expected at least one standing row"

    # Property: totals must make sense (sum(MP) = 2 * finalized_matches)
    finalized_matches = adapter.list_by_season(season, only_finalized=True)
    mp_sum = sum(r.MP for r in rows)
    assert mp_sum == 2 * len(finalized_matches), (
        f"Sum(MP)={mp_sum} should equal 2*finalized={2*len(finalized_matches)}"
    )

    # Property: Pts are consistent with GF/GA at least being non-negative
    assert all(r.GF >= 0 and r.GA >= 0 and r.Pts >= 0 for r in rows)

    # ----- Application use-case: team dashboard (form + splits)
    dashboard = get_team_dashboard(season, team, adapter)
    # Form: last N are all valid results
    assert all(x.result in (Result.WIN, Result.DRAW, Result.LOSS) for x in dashboard.form)

    # Splits: recompute naive PPG from matches and compare
    team_matches = adapter.list_for_team(season, team)
    pts_home = mp_home = pts_away = mp_away = 0
    for m in team_matches:
        if not m.finalized or m.score is None:
            continue
        if m.home_team_id == team:
            mp_home += 1
            if m.score.home > m.score.away: pts_home += 3
            elif m.score.home == m.score.away: pts_home += 1
        elif m.away_team_id == team:
            mp_away += 1
            if m.score.away > m.score.home: pts_away += 3
            elif m.score.away == m.score.home: pts_away += 1

    def ppg(pts, mp): return pts / mp if mp else 0.0

    assert math.isclose(dashboard.split.home_ppg, ppg(pts_home, mp_home), rel_tol=1e-9)
    assert math.isclose(dashboard.split.away_ppg, ppg(pts_away, mp_away), rel_tol=1e-9)
    assert dashboard.split.home_ppg >= 0.0 and dashboard.split.away_ppg >= 0.0


@pytest.mark.skipif(_any_season_with_matches() is None, reason="No seasons with matches in DB")
@pytest.mark.e2e
def test_e2e_events_and_participations_roundtrip():
    adapter = PgMatchAdapter()

    # Pick a match id that actually has events/participations
    with get_conn() as c:
        r = c.execute("SELECT match_id FROM core.event ORDER BY match_id LIMIT 1").fetchone()
        match_with_events = int(r["match_id"]) if r else None

        r2 = c.execute("SELECT match_id FROM core.participation ORDER BY match_id LIMIT 1").fetchone()
        match_with_parts = int(r2["match_id"]) if r2 else None

    # Events mapping should not crash; filters unknown types
    if match_with_events is not None:
        evs = adapter.list_events(match_with_events)
        assert isinstance(evs, list)

    # Participations mapping should provide side/starter/minutes coherently
    if match_with_parts is not None:
        parts = adapter.list_participations(match_with_parts)
        assert parts, "Expected at least one convocation"
        assert all(p.side.value in ("HOME", "AWAY") for p in parts)
        assert all(isinstance(p.starter, bool) for p in parts)
        assert all(p.minutes_played >= 0 for p in parts)
