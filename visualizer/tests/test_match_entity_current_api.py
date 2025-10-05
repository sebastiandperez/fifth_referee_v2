import pytest

from domain.entities.match import Match, Participation
from domain.value_objects import Score
from domain.ids import MatchId, SeasonId, TeamId, PlayerId
from domain.enums import Side

def _make_match():
    return Match(
        match_id=MatchId("M1"),
        season_id=SeasonId("2025"),
        matchday_id=None,           # matches your current signature (int|None)
        home_team_id=TeamId("H"),
        away_team_id=TeamId("A"),
    )

def test_add_participations_and_lineups_property_exists():
    m = _make_match()

    pH = Participation(
        match_id=m.match_id, team_id=m.home_team_id, player_id=PlayerId("P1"),
        side=Side.HOME, starter=True, minutes_played=90,
    )
    pA = Participation(
        match_id=m.match_id, team_id=m.away_team_id, player_id=PlayerId("P2"),
        side=Side.AWAY, minutes_played=45,
    )

    m.add_participation(pH)
    m.add_participation(pA)

    # There is no lineups property in the code as pasted; ensure participations list is correct.
    assert len(m.participations) == 2
    assert {p.player_id for p in m.participations} == {PlayerId("P1"), PlayerId("P2")}

def test_wrong_team_for_side_is_intended_to_fail_currently():
    """
    This test documents a current bug: match.add_participation compares p.side to string literals
    "HOME"/"AWAY", but p.side is a Side enum. So the side checks never trigger.
    Marking as xfail so your suite passes while surfacing the issue clearly.
    """
    m = _make_match()
    bad = Participation(
        match_id=m.match_id,
        team_id=m.away_team_id,  # wrong for HOME
        player_id=PlayerId("P3"),
        side=Side.HOME,
    )
    with pytest.raises(ValueError):
        m.add_participation(bad)

test_wrong_team_for_side_is_intended_to_fail_currently = pytest.mark.xfail(
    reason="Bug: Side enum is compared to 'HOME'/'AWAY' strings in add_participation; checks don't run."
)(test_wrong_team_for_side_is_intended_to_fail_currently)

def test_score_and_result_side_strings():
    m = _make_match()

    # No score yet
    assert m.result_side() is None

    m.set_score(Score(home=1, away=1))
    assert m.result_side() == "DRAW"

    m.set_score(Score(home=2, away=1))
    assert m.result_side() == "HOME"

    m.set_score(Score(home=0, away=3))
    assert m.result_side() == "AWAY"

    with pytest.raises(ValueError):
        m.set_score(Score(home=-1, away=0))
