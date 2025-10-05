import pytest
from domain.entities.season import Season, SeasonTeam, SeasonSchedule
from domain.entities.matchday import Matchday
from domain.value_objects import Name
from domain.ids import SeasonId, CompetitionId, TeamId, MatchdayId

def _season():
    return Season(season_id=SeasonId(2025), competition_id=CompetitionId(1), label=Name("2025"))

def test_add_team_unique_and_same_season():
    season = _season()
    sch = SeasonSchedule(season=season)
    sch.add_team(SeasonTeam(season_id=season.season_id, team_id=TeamId(1)))
    sch.add_team(SeasonTeam(season_id=season.season_id, team_id=TeamId(2)))
    with pytest.raises(ValueError):
        sch.add_team(SeasonTeam(season_id=season.season_id, team_id=TeamId(1)))
    with pytest.raises(ValueError):
        sch.add_team(SeasonTeam(season_id=SeasonId(999), team_id=TeamId(3)))

def test_add_matchday_unique_number_and_same_season():
    season = _season()
    sch = SeasonSchedule(season=season)
    md1 = Matchday(matchday_id=MatchdayId(1), season_id=season.season_id, number=1)
    md2 = Matchday(matchday_id=MatchdayId(2), season_id=season.season_id, number=2)
    sch.add_matchday(md1); sch.add_matchday(md2)
    with pytest.raises(ValueError):
        sch.add_matchday(Matchday(matchday_id=MatchdayId(3), season_id=season.season_id, number=2))
    with pytest.raises(ValueError):
        sch.add_matchday(Matchday(matchday_id=MatchdayId(4), season_id=SeasonId(999), number=3))
