# api/routers/events.py
from __future__ import annotations

from typing import Optional, List, Any
from fastapi import APIRouter, Query

from ..schemas import MatchEvent, ParticipationAPI
from ..deps import _ensure_season, get_conn, _get

router = APIRouter(tags=["events"])


# -----------------------------
# Helpers de casteo tolerantes
# -----------------------------

def _int_or_none(x) -> Optional[int]:
    try:
        return int(x) if x is not None else None
    except Exception:
        return None

def _str_or_none(x) -> Optional[str]:
    try:
        return str(x) if x is not None else None
    except Exception:
        return None

def _row_to_dict(r):
    """Normaliza cualquier tipo de fila a dict con las claves del SELECT."""
    if isinstance(r, dict):
        return r
    m = getattr(r, "_mapping", None)
    if m is not None:
        return dict(m)
    # fallback: tupla/sequence en el mismo orden del SELECT
    return {
        "event_id": r[0],
        "match_id": r[1],
        "event_type": r[2],
        "minute": r[3],
        "main_player_id": r[4],
        "extra_player_id": r[5],
        "team_id": r[6],
    }

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
    """
    Lista eventos de una temporada. Castea ENUM a texto y tolera filas dict/Row/tupla.
    Descarta filas sin (event_id, match_id, event_type).
    """
    _ensure_season(season_id)

    where = ["md.season_id = %s"]
    params: List[Any] = [season_id]

    if team_id is not None:
        where.append("e.team_id = %s")
        params.append(team_id)
    if match_id is not None:
        where.append("e.match_id = %s")
        params.append(match_id)
    if event_type is not None:
        where.append("e.event_type::text = %s")  # ENUM → TEXT en filtro
        params.append(event_type)
    if minute_from is not None:
        where.append("e.minute >= %s")
        params.append(minute_from)
    if minute_to is not None:
        where.append("e.minute <= %s")
        params.append(minute_to)

    where.extend([
        "e.event_id IS NOT NULL",
        "e.match_id IS NOT NULL",
        "e.event_type IS NOT NULL",
    ])

    sql = f"""
        SELECT
            e.event_id         AS event_id,
            e.match_id         AS match_id,
            e.event_type::text AS event_type,  -- ENUM → TEXT ✅
            e.minute           AS minute,
            e.main_player_id   AS main_player_id,
            e.extra_player_id  AS extra_player_id,
            e.team_id          AS team_id
        FROM core.event e
        JOIN core.match m     ON m.match_id = e.match_id
        JOIN core.matchday md ON md.matchday_id = m.matchday_id
        WHERE {' AND '.join(where)}
        ORDER BY e.match_id, e.event_id
        LIMIT %s OFFSET %s
    """
    params.extend([limit, offset])

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()

    out: List[MatchEvent] = []
    dropped = 0

    for r in rows:
        try:
            d = _row_to_dict(r)
            eid = _int_or_none(d.get("event_id"))
            mid = _int_or_none(d.get("match_id"))
            ety = _str_or_none(d.get("event_type"))
            if eid is None or mid is None or ety is None:
                dropped += 1
                continue

            out.append(MatchEvent(
                event_id=eid,
                match_id=mid,
                event_type=ety,  # ya es str por el cast
                minute=_int_or_none(d.get("minute")),
                main_player_id=_int_or_none(d.get("main_player_id")),
                extra_player_id=_int_or_none(d.get("extra_player_id")),
                team_id=_int_or_none(d.get("team_id")),
            ))
        except Exception as e:
            print(f"[events] WARN row parse failed: {e!r} | row={r!r}")
            dropped += 1
            continue

    print(f"[events] season={season_id} rows={len(rows)} out={len(out)} dropped={dropped}")
    return out


# ------------------------------------------------------------------
# /v1/seasons/{season_id}/participations
# ------------------------------------------------------------------
@router.get("/seasons/{season_id}/participations", response_model=List[ParticipationAPI])
def season_participations(
    season_id: int,
    team_id: Optional[int] = Query(None, ge=1),
    player_id: Optional[int] = Query(None, ge=1),
    matchday: Optional[int] = Query(None, ge=1),
    limit: int = Query(1000, ge=1, le=5000),
    offset: int = Query(0, ge=0),
):
    """
    Participaciones por temporada, con filtros básicos.
    Devuelve pares (match_id, player_id) + status/position tal cual DB.
    """
    _ensure_season(season_id)

    where = ["md.season_id = %s"]
    params: List[Any] = [season_id]

    if team_id is not None:
        where.append("(m.local_team_id = %s OR m.away_team_id = %s)")
        params.extend([team_id, team_id])
    if player_id is not None:
        where.append("p.player_id = %s")
        params.append(player_id)
    if matchday is not None:
        where.append("md.matchday_number = %s")
        params.append(matchday)

    sql = f"""
    SELECT
        p.match_id,
        p.player_id,
        p.status,
        p.position
    FROM core.participation p
    JOIN core.match m     ON m.match_id = p.match_id
    JOIN core.matchday md ON md.matchday_id = m.matchday_id
    WHERE {' AND '.join(where)}
    ORDER BY p.match_id, p.player_id
    LIMIT %s OFFSET %s
    """
    params.extend([limit, offset])

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()

    out: List[ParticipationAPI] = []
    for r in rows:
        out.append(ParticipationAPI(
            match_id=_int_or_none(_get(r, 0)) or 0,
            player_id=_int_or_none(_get(r, 1)) or 0,
            status=_str_or_none(_get(r, 2)) or "",
            position=_str_or_none(_get(r, 3)) or "",
        ))
    return out
