from dataclasses import dataclass
from typing import Sequence

from application.use_cases import get_season_standings, get_team_dashboard
from domain.entities.match import Match
from domain.value_objects import Score
from domain.ids import MatchId, SeasonId, TeamId
from domain.ports import StandingsPort, TeamAnalyticsPort


# ---------- Fakes ----------

@dataclass
class _FakeStandingsPort(StandingsPort):
    def list_finalized_matches(self, season_id: SeasonId) -> Sequence[Match]:
        # Season 42: two matches between teams 1 and 2
        m1 = Match(MatchId(1), SeasonId(42), 1, TeamId(1), TeamId(2))
        m1.set_score(Score(2, 1), finalized=True)
        m2 = Match(MatchId(2), SeasonId(42), 2, TeamId(2), TeamId(1))
        m2.set_score(Score(0, 0), finalized=True)
        return [m1, m2]


@dataclass
class _FakeTeamAnalyticsPort(TeamAnalyticsPort):
    data: dict[tuple[int, int], list[Match]]  # (season, team) -> matches

    def list_results_for_team(self, season_id: SeasonId, team_id: TeamId) -> Sequence[Match]:
        return self.data.get((int(season_id), int(team_id)), [])


# ---------- Tests ----------

def test_get_season_standings_points_and_totals():
    dto = get_season_standings(SeasonId(42), _FakeStandingsPort())
    rows = list(dto.rows)
    # There should be exactly 2 teams (1 and 2)
    team_ids = {int(r.team_id) for r in rows}
    assert team_ids == {1, 2}
    # Sum of MP must be 2 * number of finalized matches (2 matches -> 4 MP)
    assert sum(r.MP for r in rows) == 4
    # Team 1: W + D = 4 pts; Team 2: L + D = 1 pt
    pts = {int(r.team_id): r.Pts for r in rows}
    assert pts[1] == 4
    assert pts[2] == 1


def test_get_team_dashboard_respects_n_and_splits():
    season = SeasonId(7)
    team = TeamId(10)

    # Build four finalized matches for team 10:
    #  - home win  (3 pts home)
    #  - home draw (1 pt  home)
    #  - away loss (0 pts away)
    #  - away draw (1 pt  away)
    m1 = Match(MatchId(1), season, 1, TeamId(10), TeamId(20)); m1.set_score(Score(2, 0), True)
    m2 = Match(MatchId(2), season, 2, TeamId(10), TeamId(21)); m2.set_score(Score(1, 1), True)
    m3 = Match(MatchId(3), season, 3, TeamId(22), TeamId(10)); m3.set_score(Score(3, 1), True)
    m4 = Match(MatchId(4), season, 4, TeamId(23), TeamId(10)); m4.set_score(Score(0, 0), True)

    port = _FakeTeamAnalyticsPort({(int(season), int(team)): [m1, m2, m3, m4]})

    # n=3 → last three results
    dash3 = get_team_dashboard(season, team, port, n=3)
    assert len(dash3.form) == 3

    # n=1 → only last
    dash1 = get_team_dashboard(season, team, port, n=1)
    assert len(dash1.form) == 1

    # Splits: home PPG = (3+1)/2 = 2.0, away PPG = (0+1)/2 = 0.5
    assert dash3.split.home_ppg == 2.0
    assert dash3.split.away_ppg == 0.5
