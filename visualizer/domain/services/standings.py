from __future__ import annotations
from collections import defaultdict
from typing import Sequence, Dict

from ..ids import SeasonId, TeamId
from ..entities.match import Match
from ..entities.stats import StandingRow
from .policies import PointsPolicy, TieBreakPolicy


def compute_standings(
    season_id: SeasonId,
    matches: Sequence[Match],
    points_policy: PointsPolicy = PointsPolicy(),
    tiebreak: TieBreakPolicy = TieBreakPolicy(),
) -> Sequence[StandingRow]:
    table: Dict[TeamId, StandingRow] = {}

    def ensure(team_id: TeamId) -> StandingRow:
        if team_id not in table:
            table[team_id] = StandingRow(team_id=team_id, MP=0, GF=0, GA=0, GD=0, Pts=0)
        return table[team_id]

    for m in matches:
        if not m.finalized or m.score is None:
            continue
        home = ensure(m.home_team_id)
        away = ensure(m.away_team_id)

        home.MP += 1
        away.MP += 1
        home.GF += m.score.home
        home.GA += m.score.away
        away.GF += m.score.away
        away.GA += m.score.home
        home.GD = home.GF - home.GA
        away.GD = away.GF - away.GA

        pts_home = points_policy.points(m.score.home, m.score.away)
        pts_away = points_policy.points(m.score.away, m.score.home)
        home.Pts += pts_home
        away.Pts += pts_away

    # sort by policy (Pts → GD → GF)
    rows = list(table.values())
    rows.sort(key=lambda r: tiebreak.compare_key(r.Pts, r.GD, r.GF, int(r.team_id)))
    return rows
