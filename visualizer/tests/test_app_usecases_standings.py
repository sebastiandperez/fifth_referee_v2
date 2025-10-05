from typing import Sequence
from domain.services.standings import compute_standings
from domain.ports import StandingsPort
from domain.entities.match import Match
from domain.value_objects import Score
from domain.ids import SeasonId, MatchId, TeamId

class InMemoryStandingsPort(StandingsPort):
    def __init__(self, rows: Sequence[tuple[int,int,int,int,int,bool]]):
        # (mid, season, home, away, home_goals, away_goals, finalized)
        self._rows = rows
    def list_finalized_matches(self, season_id: SeasonId) -> Sequence[Match]:
        out = []
        for mid, season, home, away, hs, as_, fin in self._rows:
            m = Match(MatchId(mid), SeasonId(season), None, TeamId(home), TeamId(away))
            if fin:
                m.set_score(Score(hs, as_), finalized=True)
            out.append(m)
        return out

def test_get_season_standings_usecase_like_flow():
    rows = [
        (1, 2025, 1, 2, 2, 0, True),
        (2, 2025, 1, 2, 1, 1, True),
        (3, 9999, 1, 2, 0, 3, True),  # different season; domain standings currently ignores filter
    ]
    port = InMemoryStandingsPort(rows)
    # App layer would filter by season using the port; simulate that here:
    matches_2025 = [m for m in port.list_finalized_matches(SeasonId(2025)) if m.season_id == SeasonId(2025)]
    table = compute_standings(SeasonId(2025), matches_2025)
    assert [int(r.team_id) for r in table] == [1, 2]
    t1, t2 = table
    assert (t1.MP, t1.Pts, t1.GD) == (2, 4, 2)
    assert (t2.MP, t2.Pts, t2.GD) == (2, 1, -2)
