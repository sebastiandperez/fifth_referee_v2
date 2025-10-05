import pytest
from domain.services.standings import compute_standings
from domain.entities.match import Match
from domain.value_objects import Score
from domain.ids import MatchId, SeasonId, TeamId

def _match(mid: str, season: str, home: str, away: str, hs: int, as_: int, finalized=True):
    m = Match(
        match_id=MatchId(mid),
        season_id=SeasonId(season),
        matchday_id=None,
        home_team_id=TeamId(home),
        away_team_id=TeamId(away),
    )
    m.set_score(Score(home=hs, away=as_), finalized=finalized)
    return m

def test_compute_standings_basic_two_matches():
    # Use numeric-like TeamIds to avoid the current int(...) cast landmine in standings
    ms = [
        _match("M1", "S1", "1", "2", 2, 0, True),  # home win
        _match("M2", "S1", "1", "2", 1, 1, True),  # draw
    ]
    rows = compute_standings(SeasonId("S1"), ms)

    assert [str(r.team_id) for r in rows] == ["1", "2"]
    t1, t2 = rows
    assert (t1.MP, t1.GF, t1.GA, t1.GD, t1.Pts) == (2, 3, 1,  2, 4)  # 3+1 points
    assert (t2.MP, t2.GF, t2.GA, t2.GD, t2.Pts) == (2, 1, 3, -2, 1)  # 1 point

def test_non_finalized_matches_are_ignored():
    ms = [
        _match("M1", "S1", "1", "2", 1, 0, True),
        _match("M2", "S1", "1", "2", 0, 0, False),  # should be ignored
    ]
    rows = compute_standings(SeasonId("S1"), ms)
    # Only one completed game => each team MP increases once
    assert sum(r.MP for r in rows) == 2
    assert rows[0].Pts == 3

@pytest.mark.xfail(reason="compute_standings currently ignores season_id and counts all seasons", strict=True)
def test_should_filter_by_season_id():
    ms = [
        _match("M1", "S1", "1", "2", 1, 0, True),
        _match("M2", "OTHER", "1", "2", 0, 1, True),  # different season
    ]
    rows = compute_standings(SeasonId("S1"), ms)
    # Expect only the S1 match to count, but current implementation will include both.
    assert rows[0].Pts == 3 and rows[1].Pts == 0

@pytest.mark.xfail(reason="standings uses int(r.team_id): non-numeric TeamId will crash on some platforms", strict=True)
def test_non_numeric_team_id_breaks_current_tiebreak():
    ms = [
        _match("M1", "S1", "TEAM-A", "TEAM-B", 2, 0, True),
    ]
    # Will raise ValueError/TypeError inside int(r.team_id)
    compute_standings(SeasonId("S1"), ms)
