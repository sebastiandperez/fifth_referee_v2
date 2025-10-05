from __future__ import annotations
from typing import Optional, Literal, List, Any
from fastapi import APIRouter, Query
from ..schemas import MatchList, MatchAPI, MatchEvent, ParticipationAPI
from ..deps import _ensure_season, get_conn, _get

router = APIRouter(tags=["matches"])

@router.get("/seasons/{season_id}/matches", response_model=MatchList)
def list_matches(
    season_id: int,
    matchday_from: Optional[int] = Query(None, ge=1),
    matchday_to: Optional[int] = Query(None, ge=1),
    matchday: Optional[int] = Query(None, ge=1),
    team_id: Optional[int] = Query(None, ge=1),
    opponent_id: Optional[int] = Query(None, ge=1),
    finalized: Optional[bool] = Query(None),
    include: Optional[Literal["events", "participations", "events,participations"]] = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    _ensure_season(season_id)
    where = ["md.season_id = %s"]
    params: List[Any] = [season_id]
    if matchday is not None:
        where.append("md.matchday_number = %s"); params.append(matchday)
    else:
        if matchday_from is not None:
            where.append("md.matchday_number >= %s"); params.append(matchday_from)
        if matchday_to is not None:
            where.append("md.matchday_number <= %s"); params.append(matchday_to)
    if team_id is not None:
        where.append("(m.local_team_id = %s OR m.away_team_id = %s)")
        params.extend([team_id, team_id])
    if opponent_id is not None:
        where.append("(m.local_team_id = %s OR m.away_team_id = %s)")
        params.extend([opponent_id, opponent_id])
    if finalized is not None:
        where.append("m.local_score IS NOT NULL AND m.away_score IS NOT NULL" if finalized
                     else "m.local_score IS NULL OR m.away_score IS NULL")
    base_sql = f"""
    FROM core.match m
    JOIN core.matchday md ON md.matchday_id = m.matchday_id
    WHERE {' AND '.join(where)}
    """
    count_sql = f"SELECT COUNT(*) {base_sql}"
    list_sql = f"""
    SELECT m.match_id, m.matchday_id, m.local_team_id, m.away_team_id,
           m.local_score, m.away_score, m.duration, m.stadium
    {base_sql}
    ORDER BY md.matchday_number, m.match_id
    LIMIT %s OFFSET %s
    """
    with get_conn() as conn:
        total_row = conn.execute(count_sql, params).fetchone()
        total = int(_get(total_row, 0, "count")) if total_row else None
        rows = conn.execute(list_sql, [*params, limit, offset]).fetchall()
        items = [
            MatchAPI(
                match_id=int(_get(r, 0, "match_id")),
                matchday_id=int(_get(r, 1, "matchday_id")),
                local_team_id=int(_get(r, 2, "local_team_id")),
                away_team_id=int(_get(r, 3, "away_team_id")),
                local_score=(int(_get(r, 4, "local_score")) if _get(r, 4, "local_score") is not None else None),
                away_score=(int(_get(r, 5, "away_score")) if _get(r, 5, "away_score") is not None else None),
                duration=int(_get(r, 6, "duration")),
                stadium=(str(_get(r, 7, "stadium")) if _get(r, 7, "stadium") is not None else None),
            )
            for r in rows
        ]
        if include:
            ids = [int(m.match_id) for m in items]
            if ids:
                if "events" in include:
                    ev_sql = """
                    SELECT e.event_id, e.match_id, e.event_type, e.minute,
                           e.main_player_id, e.extra_player_id, e.team_id
                    FROM core.event e
                    WHERE e.match_id = ANY(%s)
                    ORDER BY e.match_id, e.event_id
                    """
                    ev_rows = conn.execute(ev_sql, [ids]).fetchall()
                    by_ev: dict[int, list[MatchEvent]] = {}
                    for r in ev_rows:
                        e = MatchEvent(
                            event_id=int(_get(r, 0, "event_id")),
                            match_id=int(_get(r, 1, "match_id")),
                            event_type=str(_get(r, 2, "event_type")),
                            minute=(int(_get(r, 3, "minute")) if _get(r, 3, "minute") is not None else None),
                            main_player_id=(int(_get(r, 4, "main_player_id")) if _get(r, 4, "main_player_id") is not None else None),
                            extra_player_id=(int(_get(r, 5, "extra_player_id")) if _get(r, 5, "extra_player_id") is not None else None),
                            team_id=(int(_get(r, 6, "team_id")) if _get(r, 6, "team_id") is not None else None),
                        )
                        by_ev.setdefault(e.match_id, []).append(e)
                    for m in items:
                        m.events = by_ev.get(int(m.match_id), [])
                if "participations" in include:
                    pr_sql = """
                    SELECT p.match_id, p.player_id, p.status, p.position
                    FROM core.participation p
                    WHERE p.match_id = ANY(%s)
                    ORDER BY p.match_id, p.player_id
                    """
                    pr_rows = conn.execute(pr_sql, [ids]).fetchall()
                    by_pr: dict[int, list[ParticipationAPI]] = {}
                    for r in pr_rows:
                        p = ParticipationAPI(
                            match_id=int(_get(r, 0, "match_id")),
                            player_id=int(_get(r, 1, "player_id")),
                            status=str(_get(r, 2, "status")),
                            position=str(_get(r, 3, "position")),
                        )
                        by_pr.setdefault(p.match_id, []).append(p)
                    for m in items:
                        m.participations = by_pr.get(int(m.match_id), [])
    return MatchList(items=items, limit=limit, offset=offset, total=total)
