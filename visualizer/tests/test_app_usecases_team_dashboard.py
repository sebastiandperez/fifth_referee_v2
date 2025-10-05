from typing import Sequence
from domain.services.analytics import compute_team_form, compute_team_splits
from domain.ports import TeamAnalyticsPort
from domain.entities.match import Match
from domain.value_objects import Score
from domain.enums import Result
from domain.ids import SeasonId, TeamId, MatchId

class InMemoryTeamAnalyticsPort(TeamAnalyticsPort):
    def __init__(self, rows: Sequence[tuple[int,int,int,int,int,bool]]):
        # (mid, home, away, hs, as, finalized)
        self._rows = rows
    def list_results_for_team(self, season_id: SeasonId, team_id: TeamId) -> Sequence[Match]:
        out = []
        for mid, home, away, hs, as_, fin in self._rows:
            m = Match(MatchId(mid), season_id, None, TeamId(home), TeamId(away))
            if fin:
                m.set_score(Score(hs, as_), finalized=True)
            out.append(m)
        return out

def test_get_team_dashboard_usecase_like_flow():
    port = InMemoryTeamAnalyticsPort([
        (1, 1, 2, 2, 0, True),  # T home win
        (2, 1, 2, 1, 1, True),  # T home draw
        (3, 2, 1, 2, 1, True),  # T away loss
    ])
    season = SeasonId(2025)
    team = TeamId(1)
    matches = port.list_results_for_team(season, team)
    form = compute_team_form(matches, team, n=2)
    split = compute_team_splits(matches, team)
    assert [row.result for row in form] == [Result.DRAW, Result.LOSS]
    assert split.home_ppg == 2.0 and split.away_ppg == 0.0
