import pytest
from domain.services.standings import compute_standings
from domain.value_objects import Score
from domain.entities.match import Match
from domain.ids import MatchId, SeasonId, TeamId

def _m(mid, season, home, away, hs, as_, finalized=True):
    m = Match(
        match_id=MatchId(mid),
        season_id=SeasonId(season),
        matchday_id=None,
        home_team_id=TeamId(home),
        away_team_id=TeamId(away),
    )
    m.set_score(Score(hs, as_), finalized=finalized)
    return m

def test_standings_basic_two_games_same_season_numeric_ids():
    ms = [
        _m(1, 2025, 1, 2, 2, 0, True),
        _m(2, 2025, 1, 2, 1, 1, True),
    ]
    rows = compute_standings(SeasonId(2025), ms)
    assert [int(r.team_id) for r in rows] == [1, 2]
    t1, t2 = rows
    assert (t1.MP, t1.GF, t1.GA, t1.GD, t1.Pts) == (2, 3, 1, 2, 4)
    assert (t2.MP, t2.GF, t2.GA, t2.GD, t2.Pts) == (2, 1, 3, -2, 1)

@pytest.mark.xfail(reason="compute_standings currently ignores season_id and counts all seasons", strict=True)
def test_should_filter_by_season_id_but_does_not_yet():
    ms = [
        _m(1, 2025, 1, 2, 1, 0, True),
        _m(2, 9999, 1, 2, 0, 3, True),  # different season, should be ignored
    ]
    rows = compute_standings(SeasonId(2025), ms)
    assert rows[0].Pts == 3 and rows[1].Pts == 0

@pytest.mark.xfail(reason="tiebreak casts int(team_id); non-numeric IDs will explode", strict=True)
def test_non_numeric_team_id_breaks_current_tiebreak():
    ms = [
        _m(1, 2025, "TEAM-A", "TEAM-B", 2, 0, True),  # misuse: TeamId expects int
    ]
    compute_standings(SeasonId(2025), ms)
