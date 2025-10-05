import pytest

from domain.services.analytics import compute_team_form, compute_team_splits
from domain.entities.match import Match
from domain.value_objects import Score
from domain.enums import Result
from domain.ids import MatchId, SeasonId, TeamId

def _m(mid, home, away, hs, as_, finalized=True):
    m = Match(
        match_id=MatchId(mid),
        season_id=SeasonId("S1"),
        matchday_id=None,
        home_team_id=TeamId(home),
        away_team_id=TeamId(away),
    )
    m.set_score(Score(home=hs, away=as_), finalized=finalized)
    return m

def test_compute_team_form_last_n_uses_natural_order_when_no_kickoff():
    # Natural order: M1, M2, M3 (no kickoff_utc set)
    T, O = TeamId("T"), TeamId("O")
    m1 = _m("M1", T, O, 1, 1)      # draw (T home)
    m2 = _m("M2", T, O, 2, 0)      # win  (T home)
    m3 = _m("M3", O, T, 3, 1)      # loss (T away)
    form = compute_team_form([m1, m2, m3], T, n=2)
    assert [row.result for row in form] == [Result.WIN, Result.LOSS]

def test_compute_team_form_ignores_non_finalized():
    T, O = TeamId("T"), TeamId("O")
    m1 = _m("M1", T, O, 1, 0, finalized=False)  # ignored
    m2 = _m("M2", T, O, 0, 0, finalized=True)   # draw
    form = compute_team_form([m1, m2], T, n=5)
    assert [row.result for row in form] == [Result.DRAW]

def test_compute_team_splits_home_away_ppg_and_totals():
    T, O = TeamId("T"), TeamId("O")
    # Home: win (3) + draw (1) => 4/2 = 2.0
    h1 = _m("H1", T, O, 2, 0)     # win
    h2 = _m("H2", T, O, 1, 1)     # draw
    # Away: win (3) + loss (0) => 3/2 = 1.5
    a1 = _m("A1", O, T, 0, 1)     # T away win
    a2 = _m("A2", O, T, 2, 1)     # T away loss

    split = compute_team_splits([h1, h2, a1, a2], T)
    assert split.home_ppg == pytest.approx(2.0)
    assert split.away_ppg == pytest.approx(1.5)
    # Totals: GF/GA by venue
    assert (split.home_gf, split.home_ga) == (3, 1)   # (2+1, 0+1)
    assert (split.away_gf, split.away_ga) == (2, 2)   # (1+1, 0+2)
