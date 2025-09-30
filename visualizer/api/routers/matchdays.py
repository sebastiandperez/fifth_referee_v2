from __future__ import annotations
from fastapi import APIRouter
from ..schemas import MatchdayList, MatchdayItem
from ..deps import _ensure_season, get_conn, _get

router = APIRouter(tags=["matchdays"])

@router.get("/seasons/{season_id}/matchdays", response_model=MatchdayList)
def list_matchdays(season_id: int):
    _ensure_season(season_id)
    sql = """
    SELECT matchday_id, matchday_number
    FROM core.matchday
    WHERE season_id = %s
    ORDER BY matchday_number
    """
    with get_conn() as conn:
        rows = conn.execute(sql, [season_id]).fetchall()
    items = [MatchdayItem(matchday_id=int(_get(r, 0, "matchday_id")),
                          matchday_number=int(_get(r, 1, "matchday_number"))) for r in rows]
    return MatchdayList(items=items)
