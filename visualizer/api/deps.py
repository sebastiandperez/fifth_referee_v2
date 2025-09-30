from __future__ import annotations
from typing import Any, List, Optional
from fastapi import HTTPException
from domain.ids import SeasonId
from infrastructure.postgres.adapters import get_conn, PgMatchAdapter
from .schemas import TeamItem, StandingRowAPI

def _get(row: Any, *keys: Any) -> Any:
    mapping = getattr(row, "_mapping", None)
    if mapping:
        for k in keys:
            if k in mapping:
                return mapping[k]
    if isinstance(row, dict):
        for k in keys:
            if k in row:
                return row[k]
    for k in keys:
        if isinstance(k, int):
            try:
                return row[k]
            except Exception:
                pass
    for k in keys:
        if isinstance(k, str) and hasattr(row, k):
            return getattr(row, k)
    return None

def get_adapter() -> PgMatchAdapter:
    return PgMatchAdapter()

def _ensure_season(season_id: int) -> None:
    sql = "SELECT 1 FROM core.season WHERE season_id = %s"
    with get_conn() as conn:
        row = conn.execute(sql, [season_id]).fetchone()
    if not row:
        raise HTTPException(404, detail="season not found")

def _list_teams(season_id: int) -> List[TeamItem]:
    sql = """
    SELECT t.team_id, t.team_name, t.team_city, t.team_stadium
    FROM registry.season_team st
    JOIN reference.team t ON t.team_id = st.team_id
    WHERE st.season_id = %s
    ORDER BY t.team_name
    """
    with get_conn() as conn:
        rows = conn.execute(sql, [season_id]).fetchall()
    return [
        TeamItem(
            team_id=int(_get(r, 0, "team_id")),
            team_name=str(_get(r, 1, "team_name")),
            team_city=(str(_get(r, 2, "team_city")) if _get(r, 2, "team_city") is not None else None),
            team_stadium=(str(_get(r, 3, "team_stadium")) if _get(r, 3, "team_stadium") is not None else None),
        )
        for r in rows
    ]

def _team_name_map(season_id: int) -> dict[int, str]:
    return {t.team_id: t.team_name for t in _list_teams(season_id)}

def _wdl_by_team(season_id: int, adapter: PgMatchAdapter) -> dict[int, dict[str, int]]:
    out: dict[int, dict[str, int]] = {}
    matches = adapter.list_by_season(SeasonId(season_id), only_finalized=True)
    for m in matches:
        if m.score is None:
            continue
        ht, at = int(m.home_team_id), int(m.away_team_id)
        hs, as_ = int(m.score.home), int(m.score.away)
        for tid in (ht, at):
            out.setdefault(tid, {"win": 0, "draw": 0, "loss": 0})
        if hs > as_:
            out[ht]["win"] += 1; out[at]["loss"] += 1
        elif hs < as_:
            out[ht]["loss"] += 1; out[at]["win"] += 1
        else:
            out[ht]["draw"] += 1; out[at]["draw"] += 1
    return out

def _compute_standings_fallback(season_id: int, win: int, draw: int, loss: int) -> list[StandingRowAPI]:
    teams = _list_teams(season_id)
    if not teams:
        return []
    sql = """
    SELECT m.local_team_id  AS home_team_id,
           m.away_team_id   AS away_team_id,
           m.local_score    AS home_score,
           m.away_score     AS away_score
    FROM core.match m
    JOIN core.matchday md ON md.matchday_id = m.matchday_id
    WHERE md.season_id = %s
    """
    with get_conn() as conn:
        rows = conn.execute(sql, [season_id]).fetchall()
    by_team: dict[int, dict[str, int]] = {
        int(t.team_id): {"played": 0, "win": 0, "draw": 0, "loss": 0, "gf": 0, "ga": 0}
        for t in teams
    }
    for r in rows:
        hs = _get(r, "home_score")
        as_ = _get(r, "away_score")
        if hs is None or as_ is None:
            continue
        ht = int(_get(r, "home_team_id"))
        at = int(_get(r, "away_team_id"))
        hs = int(hs); as_ = int(as_)
        by_team[ht]["played"] += 1; by_team[at]["played"] += 1
        by_team[ht]["gf"] += hs; by_team[ht]["ga"] += as_
        by_team[at]["gf"] += as_; by_team[at]["ga"] += hs
        if hs > as_:
            by_team[ht]["win"] += 1; by_team[at]["loss"] += 1
        elif hs < as_:
            by_team[ht]["loss"] += 1; by_team[at]["win"] += 1
        else:
            by_team[ht]["draw"] += 1; by_team[at]["draw"] += 1
    name_map = _team_name_map(season_id)
    out: list[StandingRowAPI] = []
    for tid, agg in by_team.items():
        gd = agg["gf"] - agg["ga"]
        pts = agg["win"] * win + agg["draw"] * draw + agg["loss"] * loss
        out.append(StandingRowAPI(
            team_id=tid,
            team_name=name_map.get(tid),
            played=agg["played"],
            win=agg["win"], draw=agg["draw"], loss=agg["loss"],
            gf=agg["gf"], ga=agg["ga"], gd=gd, points=pts, position=0
        ))
    out.sort(key=lambda x: (-x.points, -x.gd, -x.gf, x.team_name or ""))
    for i, r in enumerate(out, start=1):
        r.position = i
    return out
