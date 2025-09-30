from collections import defaultdict
from domain.entities.stats import StandingRow

def compute_standings(season_id, matches):
    agg = defaultdict(lambda: {"MP":0,"GF":0,"GA":0,"GD":0,"Pts":0})
    for m in matches:
        if m.score is None:
            continue
        ht, at = m.home_team_id, m.away_team_id
        hs, as_ = m.score.home, m.score.away

        agg[ht]["MP"] += 1; agg[at]["MP"] += 1
        agg[ht]["GF"] += hs; agg[ht]["GA"] += as_; agg[ht]["GD"] += hs - as_
        agg[at]["GF"] += as_; agg[at]["GA"] += hs; agg[at]["GD"] += as_ - hs

        if hs > as_:
            agg[ht]["Pts"] += 3
        elif hs < as_:
            agg[at]["Pts"] += 3
        else:
            agg[ht]["Pts"] += 1
            agg[at]["Pts"] += 1

    rows = [
        StandingRow(
            team_id=tid,
            MP=v["MP"], GF=v["GF"], GA=v["GA"], GD=v["GD"], Pts=v["Pts"],
        )
        for tid, v in agg.items()
    ]
    # if you assign positions elsewhere, just return rows; otherwise sort and compute
    rows.sort(key=lambda r: (-r.Pts, -r.GD, -r.GF, int(r.team_id)))
    return rows
