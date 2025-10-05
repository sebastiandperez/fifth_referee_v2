from __future__ import annotations
from typing import Optional, List, Any
from fastapi import APIRouter, Query
from ..schemas import PlayerList, PlayerItem
from ..deps import _ensure_season, get_conn, _get

router = APIRouter(tags=["players"])

@router.get("/seasons/{season_id}/players", response_model=PlayerList)
def list_players(season_id: int, team_id: Optional[int] = Query(None, ge=1)):
    _ensure_season(season_id)
    sql = """
    SELECT st.season_team_id,
           st.team_id,
           t.team_name,
           tp.player_id,
           p.player_name,
           tp.jersey_number
    FROM registry.season_team st
    JOIN reference.team t ON t.team_id = st.team_id
    JOIN registry.team_player tp ON tp.season_team_id = st.season_team_id
    JOIN reference.player p ON p.player_id = tp.player_id
    WHERE st.season_id = %s
    """
    params: List[Any] = [season_id]
    if team_id is not None:
        sql += " AND st.team_id = %s"
        params.append(team_id)
    sql += " ORDER BY t.team_name, p.player_name"
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    items = [
        PlayerItem(
            season_team_id=int(_get(r, 0, "season_team_id")),
            team_id=int(_get(r, 1, "team_id")),
            team_name=str(_get(r, 2, "team_name")),
            player_id=int(_get(r, 3, "player_id")),
            player_name=str(_get(r, 4, "player_name")),
            jersey_number=(int(_get(r, 5, "jersey_number")) if _get(r, 5, "jersey_number") is not None else None),
        )
        for r in rows
    ]
    return PlayerList(items=items)
