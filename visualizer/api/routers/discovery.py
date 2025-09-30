from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from ..schemas import SeasonLabelList, CompetitionList, CompetitionItem, SeasonResolveResult
from ..deps import get_conn, _get

router = APIRouter(tags=["discovery"])

@router.get("/season-labels", response_model=SeasonLabelList)
def list_season_labels():
    sql = "SELECT DISTINCT season_label FROM core.season ORDER BY season_label DESC"
    with get_conn() as conn:
        rows = conn.execute(sql).fetchall()
    return SeasonLabelList(items=[str(_get(r, 0, "season_label")) for r in rows])

@router.get("/season-labels/{season_label:path}/competitions", response_model=CompetitionList)
def competitions_for_label(season_label: str):
    sql = """
    SELECT DISTINCT c.competition_id, c.competition_name
    FROM core.season s
    JOIN reference.competition c ON c.competition_id = s.competition_id
    WHERE s.season_label = %s
    ORDER BY c.competition_name
    """
    with get_conn() as conn:
        rows = conn.execute(sql, [season_label]).fetchall()
    items = [CompetitionItem(id=int(_get(r, 0, "competition_id")), name=str(_get(r, 1, "competition_name"))) for r in rows]
    return CompetitionList(items=items)

@router.get("/seasons/resolve", response_model=SeasonResolveResult)
def resolve_season(season_label: str = Query(...), competition_id: int = Query(...)):
    sql = """
    SELECT season_id
    FROM core.season
    WHERE season_label = %s AND competition_id = %s
    ORDER BY season_id LIMIT 1
    """
    with get_conn() as conn:
        row = conn.execute(sql, [season_label, competition_id]).fetchone()
    if not row:
        raise HTTPException(404, detail="season not found for (label, competition)")
    return SeasonResolveResult(season_id=int(_get(row, 0, "season_id")))
