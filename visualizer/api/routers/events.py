from __future__ import annotations
from typing import Optional, List, Any
from fastapi import APIRouter, Query
from ..schemas import MatchEvent, ParticipationAPI
from ..deps import _ensure_season, get_conn, _get

router = APIRouter(tags=["events"])

@router.get("/seasons/{season_id}/events", response_model=List[MatchEvent])
def season_events(
    season_id: int,
    team_id: Optional[int] = Query(None, ge=1),
    match_id: Optional[int] = Query(None, ge=1),
    event_type: Optional[str] = Query(None),
    minute_from: Optional[int] = Query(None, ge=0),
    minute_to: Optional[int] = Query(None, ge=0),
    limit: int = Query(1000, ge=1, le=5000),
    offset: int = Query(0, ge=0),
):
    _ensure_season(season_id)
    where = ["md.season_id = %s"]
    params: List[Any] = [season_id]
    if team_id is not None:
        where.append("e.team_id = %s"); params.append(team_id)
    if match_id is not None:
        where.append("e.match_id = %s"); params.append(match_id)
    if event_type is not None:
        where.append("e.event_type = %s"); params.append(event_type)
    if minute_from is not None:
        where.append("e.minute >= %s"); params.append(minute_from)
    if minute_to is not None:
        where.append("e.minute <= %s"); params.append(minute_to)
    sql = f"""
    SELECT e.event_id, e.match_id, e.event_type, e.minute,
           e.main_player_id, e.extra_player_id, e.team_id
    FROM core.event e
    JOIN core.match m   ON m.match_id = e.match_id
    JOIN core.matchday md ON md.matchday_id = m.matchday_id
    WHERE {' AND '.join(where)}
    ORDER BY e.match_id, e.event_id
    LIMIT %s OFFSET %s
    """
    params.extend([limit, offset])
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [
        MatchEvent(
            event_id=int(_get(r, 0)), match_id=int(_get(r, 1)), event_type=str(_get(r, 2)),
            minute=(int(_get(r, 3)) if _get(r, 3) is not None else None),
            main_player_id=(int(_get(r, 4)) if _get(r, 4) is not None else None),
            extra_player_id=(int(_get(r, 5)) if _get(r, 5) is not None else None),
            team_id=(int(_get(r, 6)) if _get(r, 6) is not None else None),
        )
        for r in rows
    ]

@router.get("/seasons/{season_id}/participations", response_model=List[ParticipationAPI])
def season_participations(
    season_id: int,
    team_id: Optional[int] = Query(None, ge=1),
    player_id: Optional[int] = Query(None, ge=1),
    matchday: Optional[int] = Query(None, ge=1),
    limit: int = Query(1000, ge=1, le=5000),
    offset: int = Query(0, ge=0),
):
    _ensure_season(season_id)
    where = ["md.season_id = %s"]
    params: List[Any] = [season_id]
    if team_id is not None:
        where.append("(m.local_team_id = %s OR m.away_team_id = %s)")
        params.extend([team_id, team_id])
    if player_id is not None:
        where.append("p.player_id = %s"); params.append(player_id)
    if matchday is not None:
        where.append("md.matchday_number = %s"); params.append(matchday)
    sql = f"""
    SELECT p.match_id, p.player_id, p.status, p.position
    FROM core.participation p
    JOIN core.match m   ON m.match_id = p.match_id
    JOIN core.matchday md ON md.matchday_id = m.matchday_id
    WHERE {' AND '.join(where)}
    ORDER BY p.match_id, p.player_id
    LIMIT %s OFFSET %s
    """
    params.extend([limit, offset])
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [
        ParticipationAPI(
            match_id=int(_get(r, 0)), player_id=int(_get(r, 1)),
            status=str(_get(r, 2)), position=str(_get(r, 3)),
        )
        for r in rows
    ]
