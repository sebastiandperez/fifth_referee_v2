from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Query, Depends, HTTPException
from domain.ids import SeasonId
from application.use_cases import get_season_standings
from infrastructure.postgres.adapters import PgMatchAdapter
from ..schemas import SeasonStandingsDTOAPI, StandingRowAPI
from ..deps import get_adapter, _team_name_map, _wdl_by_team, _compute_standings_fallback

router = APIRouter(tags=["standings"])

@router.get("/seasons/{season_id}/standings", response_model=SeasonStandingsDTOAPI)
def standings(
    season_id: int,
    win: int = Query(3, ge=0, le=10),
    draw: int = Query(1, ge=0, le=10),
    loss: int = Query(0, ge=0, le=10),
    until_matchday: Optional[int] = Query(None, ge=1),
    adapter: PgMatchAdapter = Depends(get_adapter),
):
    try:
        dto = get_season_standings(SeasonId(season_id), adapter)
        wdl = _wdl_by_team(season_id, adapter)
        name_map = _team_name_map(season_id)
        out: list[StandingRowAPI] = []
        for r in dto.rows:
            tid = int(r.team_id)
            w = int(wdl.get(tid, {}).get("win", 0))
            d = int(wdl.get(tid, {}).get("draw", 0))
            l = int(wdl.get(tid, {}).get("loss", 0))
            pts_domain = int(getattr(r, "Pts", getattr(r, "points", 0)))
            pts = (w * win + d * draw + l * loss) if (w or d or l) else pts_domain
            out.append(StandingRowAPI(
                team_id=tid,
                team_name=name_map.get(tid),
                played=int(getattr(r, "MP", getattr(r, "mp", 0))),
                win=w, draw=d, loss=l,
                gf=int(getattr(r, "GF", getattr(r, "gf", 0))),
                ga=int(getattr(r, "GA", getattr(r, "ga", 0))),
                gd=int(getattr(r, "GD", getattr(r, "gd", 0))),
                points=pts,
                position=int(getattr(r, "position", 0)),
            ))
        out.sort(key=lambda x: (-x.points, -x.gd, -x.gf, x.team_name or ""))
        for i, row in enumerate(out, start=1):
            row.position = i
        return SeasonStandingsDTOAPI(rows=out)
    except HTTPException as e:
        if e.status_code != 404:
            raise
        rows = _compute_standings_fallback(season_id, win, draw, loss)
        return SeasonStandingsDTOAPI(rows=rows)
