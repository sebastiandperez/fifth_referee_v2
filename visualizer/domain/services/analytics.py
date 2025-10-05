from __future__ import annotations
from typing import Sequence, List

from ..ids import TeamId
from ..entities.match import Match
from ..entities.stats import TeamFormRow, TeamSplit
from ..enums import Result

def _form_sort_key(m: Match):
    """
    Stable ordering for 'last N' form:
      1) kickoff_utc if present (future-proof)
      2) else matchday_id (round order)
      3) else match_id (deterministic)
    The adapter already orders by matchday.number, but this keeps us safe.
    """
    if m.kickoff_utc:
        return (0, m.kickoff_utc.value)
    return (1, (m.matchday_id if m.matchday_id is not None else int(m.match_id)))

def compute_team_form(matches_for_team: Sequence[Match], team_id: TeamId, n: int = 5) -> Sequence[TeamFormRow]:
    finalized = [m for m in matches_for_team if m.finalized and m.score is not None]
    finalized.sort(key=_form_sort_key)  # Python sort is stable
    last = finalized[-n:]

    out: List[TeamFormRow] = []
    for m in last:
        if m.home_team_id == team_id:
            res = Result.WIN if m.score.home > m.score.away else Result.DRAW if m.score.home == m.score.away else Result.LOSS
        else:
            res = Result.WIN if m.score.away > m.score.home else Result.DRAW if m.score.away == m.score.home else Result.LOSS
        out.append(TeamFormRow(match_id=m.match_id, result=res))
    return out

def compute_team_splits(matches_for_team: Sequence[Match], team_id: TeamId) -> TeamSplit:
    home_pts = home_mp = home_gf = home_ga = 0
    away_pts = away_mp = away_gf = away_ga = 0

    for m in matches_for_team:
        if not m.finalized or m.score is None:
            continue

        if m.home_team_id == team_id:
            home_mp += 1
            home_gf += m.score.home
            home_ga += m.score.away
            if m.score.home > m.score.away:
                home_pts += 3
            elif m.score.home == m.score.away:
                home_pts += 1
        elif m.away_team_id == team_id:
            away_mp += 1
            away_gf += m.score.away
            away_ga += m.score.home
            if m.score.away > m.score.home:
                away_pts += 3
            elif m.score.away == m.score.home:
                away_pts += 1

    def ppg(pts: int, mp: int) -> float:
        return pts / mp if mp else 0.0

    return TeamSplit(
        home_ppg=ppg(home_pts, home_mp),
        away_ppg=ppg(away_pts, away_mp),
        home_gf=home_gf, away_gf=away_gf,
        home_ga=home_ga, away_ga=away_ga,
    )
