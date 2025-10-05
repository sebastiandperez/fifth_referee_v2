import pytest
from domain.entities.match import Match, Participation, Event
from domain.value_objects import Score, Minute
from domain.enums import Side, EventType
from domain.ids import MatchId, SeasonId, TeamId, PlayerId

def _mk_match():
    return Match(
        match_id=MatchId(1),
        season_id=SeasonId(2025),
        matchday_id=None,
        home_team_id=TeamId(10),
        away_team_id=TeamId(20),
    )

def test_participations_invariants_and_storage():
    m = _mk_match()
    pH = Participation(m.match_id, m.home_team_id, PlayerId(100), Side.HOME, starter=True, minutes_played=90)
    pA = Participation(m.match_id, m.away_team_id, PlayerId(200), Side.AWAY, minutes_played=45)
    m.add_participation(pH); m.add_participation(pA)
    assert [p.player_id for p in m.participations] == [PlayerId(100), PlayerId(200)]

    bad_side = Participation(m.match_id, m.away_team_id, PlayerId(201), Side.HOME)
    with pytest.raises(ValueError):
        m.add_participation(bad_side)

    with pytest.raises(ValueError):
        m.add_participation(Participation(m.match_id, m.home_team_id, PlayerId(300), Side.HOME, minutes_played=-1))

def test_events_and_score_and_result_side_strings():
    m = _mk_match()
    any_type = EventType.GOAL
    m.add_event(Event(match_id=m.match_id, minute=Minute(5), type=any_type, team_id=m.home_team_id))
    assert len(m.events) == 1

    assert m.result_side() is None
    m.set_score(Score(1,1))
    assert m.result_side() == "DRAW"
    m.set_score(Score(2,1))
    assert m.result_side() == "HOME"
    with pytest.raises(ValueError):
        m.set_score(Score(-1,0))
