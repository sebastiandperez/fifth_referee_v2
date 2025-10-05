from domain.services.analytics import compute_team_form, compute_team_splits
from domain.enums import Result
from domain.value_objects import Score
from domain.entities.match import Match
from domain.ids import MatchId, SeasonId, TeamId
import pytest

def _m(mid, home, away, hs, as_, finalized=True):
    m = Match(
        match_id=MatchId(mid),
        season_id=SeasonId(2025),
        matchday_id=None,
        home_team_id=TeamId(home),
        away_team_id=TeamId(away),
    )
    m.set_score(Score(hs, as_), finalized=finalized)
    return m

def test_team_form_last_two_without_kickoff_uses_natural_order():
    T, O = 1, 2
    m1 = _m(1, T, O, 1, 1, True)   # draw
    m2 = _m(2, T, O, 2, 0, True)   # win
    m3 = _m(3, O, T, 3, 1, True)   # away loss
    form = compute_team_form([m1, m2, m3], TeamId(T), n=2)
    assert [row.result for row in form] == [Result.WIN, Result.LOSS]

def test_team_form_ignores_non_finalized():
    T, O = 1, 2
    m1 = _m(1, T, O, 1, 0, False)  # ignored
    m2 = _m(2, T, O, 0, 0, True)   # draw
    out = compute_team_form([m1, m2], TeamId(T), n=5)
    assert [row.result for row in out] == [Result.DRAW]

def test_team_splits_home_away_ppg_and_totals():
    T, O = 1, 2
    h1 = _m(1, T, O, 2, 0, True)  # home win (3)
    h2 = _m(2, T, O, 1, 1, True)  # home draw (1) => 4/2 = 2.0
    a1 = _m(3, O, T, 0, 1, True)  # away win (3)
    a2 = _m(4, O, T, 2, 1, True)  # away loss (0) => 3/2 = 1.5
    split = compute_team_splits([h1, h2, a1, a2], TeamId(T))
    assert split.home_ppg == pytest.approx(2.0)
    assert split.away_ppg == pytest.approx(1.5)
    assert (split.home_gf, split.home_ga) == (3, 1)
    assert (split.away_gf, split.away_ga) == (2, 2)
