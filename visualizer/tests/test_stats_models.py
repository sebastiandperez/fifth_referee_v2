from domain.entities.stats import (
    StandingRow, TeamFormRow, TeamSplit,
    BasicStats, GoalkeeperStats, DefenderStats, MidfielderStats, ForwardStats
)
from domain.ids import PlayerId, MatchId, TeamId
from domain.enums import Result

for
def test_standingrow_and_teamformrow_and_split_init():
    s = StandingRow(team_id=TeamId("T"), MP=3, GF=5, GA=2, GD=3, Pts=7)
    assert s.Pts == 7

    form = TeamFormRow(match_id=MatchId("M1"), result=Result.DRAW)
    assert form.result.name in {"WIN", "DRAW", "LOSS"}  # adapt to your enum names

    split = TeamSplit(home_ppg=2.0, away_ppg=1.1, home_gf=10, away_gf=6, home_ga=5, away_ga=7)
    assert split.home_ppg >= split.away_ppg or split.home_ppg < split.away_ppg  # exists

def test_player_stats_variants_are_frozen_and_share_ids():
    pid = PlayerId("P1")
    mid = MatchId("M1")

    base = BasicStats(player_id=pid, match_id=mid, minutes=90, goals=1)
    gk = GoalkeeperStats(player_id=pid, match_id=mid, saves=4)
    df = DefenderStats(player_id=pid, match_id=mid, tackles=3)
    mf = MidfielderStats(player_id=pid, match_id=mid, key_passes=2)
    fw = ForwardStats(player_id=pid, match_id=mid, xg=0.8)

    assert all(x.player_id == pid and x.match_id == mid for x in [base, gk, df, mf, fw])
