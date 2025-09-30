from __future__ import annotations
from fastapi import APIRouter
from ..schemas import TeamList, TeamItem
from ..deps import get_conn, _get, _ensure_season

router = APIRouter(tags=["teams"])

@router.get("/seasons/{season_id}/teams", response_model=TeamList)
def list_teams(season_id: int):
    _ensure_season(season_id)
    sql = """
    SELECT t.team_id, t.team_name, t.team_city, t.team_stadium
    FROM registry.season_team st
    JOIN reference.team t ON t.team_id = st.team_id
    WHERE st.season_id = %s
    ORDER BY t.team_name
    """
    with get_conn() as conn:
        rows = conn.execute(sql, [season_id]).fetchall()
    items = [
        TeamItem(
            team_id=int(_get(r, 0, "team_id")),
            team_name=str(_get(r, 1, "team_name")),
            team_city=(str(_get(r, 2, "team_city")) if _get(r, 2, "team_city") is not None else None),
            team_stadium=(str(_get(r, 3, "team_stadium")) if _get(r, 3, "team_stadium") is not None else None),
        )
        for r in rows
    ]
    return TeamList(items=items)
