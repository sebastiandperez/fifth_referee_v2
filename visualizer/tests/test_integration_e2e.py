from domain.entities.season import Season, SeasonTeam, SeasonSchedule
from domain.entities.matchday import Matchday
from domain.entities.match import Match
from domain.value_objects import Name, Score
from domain.services.standings import compute_standings
from domain.services.analytics import compute_team_form, compute_team_splits
from domain.enums import Result
from domain.ids import SeasonId, CompetitionId, TeamId, MatchdayId, MatchId

def test_end_to_end_season_standings_and_analytics():
    # Season + schedule
    season = Season(season_id=SeasonId(2025), competition_id=CompetitionId(1), label=Name("2025"))
    sched = SeasonSchedule(season=season)
    sched.add_team(SeasonTeam(season_id=season.season_id, team_id=TeamId(1)))
    sched.add_team(SeasonTeam(season_id=season.season_id, team_id=TeamId(2)))
    md1 = Matchday(matchday_id=MatchdayId(1), season_id=season.season_id, number=1)
    md2 = Matchday(matchday_id=MatchdayId(2), season_id=season.season_id, number=2)
    sched.add_matchday(md1); sched.add_matchday(md2)

    # Matches (finalized)
    m1 = Match(MatchId(1), season.season_id, md1.matchday_id, TeamId(1), TeamId(2))
    m1.set_score(Score(2, 0), finalized=True)
    m2 = Match(MatchId(2), season.season_id, md2.matchday_id, TeamId(2), TeamId(1))
    m2.set_score(Score(1, 1), finalized=True)

    matches = [m1, m2]

    # Standings (note: current impl ignores season filter, but we're passing only same-season)
    table = compute_standings(season.season_id, matches)
    assert [int(r.team_id) for r in table] == [1, 2]
    t1, t2 = table
    assert (t1.MP, t1.Pts, t1.GD) == (2, 4, 2)
    assert (t2.MP, t2.Pts, t2.GD) == (2, 1, -2)

    # Analytics: team 1 form and splits
    form1 = compute_team_form(matches, TeamId(1), n=2)
    assert [row.result for row in form1] == [Result.WIN, Result.DRAW]

    split1 = compute_team_splits(matches, TeamId(1))
    # Home: 1 match, win -> 3/1 = 3.0, GF/GA=(2,0) ; Away: 1 match, draw -> 1/1 = 1.0, GF/GA=(1,1)
    assert split1.home_ppg == 3.0 and split1.away_ppg == 1.0
    assert (split1.home_gf, split1.home_ga, split1.away_gf, split1.away_ga) == (2, 0, 1, 1)
