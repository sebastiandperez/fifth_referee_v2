from __future__ import annotations
from typing import Optional, Literal
from fastapi import APIRouter, HTTPException, Query
from ..schemas import SeasonSummary, SeasonSnapshot, TeamItem, PlayerItem, MatchdayItem, MatchAPI, MatchList
from ..deps import get_conn, _get, _ensure_season
from .teams import list_teams
from .players import list_players
from .matchdays import list_matchdays
from .matches import list_matches

router = APIRouter(tags=["seasons"])

@router.get("/seasons/{season_id}/summary", response_model=SeasonSummary)
def season_summary(season_id: int):
    _ensure_season(season_id)
    meta_sql = """
    SELECT s.season_id, s.season_label, c.competition_id, c.competition_name
    FROM core.season s
    JOIN reference.competition c ON c.competition_id = s.competition_id
    WHERE s.season_id = %s
    """
    team_sql = "SELECT COUNT(*) AS cnt FROM registry.season_team WHERE season_id = %s"
    md_sql = "SELECT MIN(matchday_number) AS mn, MAX(matchday_number) AS mx FROM core.matchday WHERE season_id = %s"
    last_sql = """
    SELECT MAX(md.matchday_number) AS last_md
    FROM core.match m
    JOIN core.matchday md ON md.matchday_id = m.matchday_id
    WHERE md.season_id = %s AND m.local_score IS NOT NULL AND m.away_score IS NOT NULL
    """
    with get_conn() as conn:
        meta = conn.execute(meta_sql, [season_id]).fetchone()
        if not meta:
            raise HTTPException(404, detail="season not found")
        team_cnt = conn.execute(team_sql, [season_id]).fetchone()
        md_minmax = conn.execute(md_sql, [season_id]).fetchone()
        last_md = conn.execute(last_sql, [season_id]).fetchone()
    return SeasonSummary(
        season_id=season_id,
        season_label=str(_get(meta, 1, "season_label")),
        competition_id=int(_get(meta, 2, "competition_id")),
        competition_name=str(_get(meta, 3, "competition_name")),
        team_count=int(_get(team_cnt, 0, "cnt")),
        matchday_min=(int(_get(md_minmax, 0, "mn")) if _get(md_minmax, 0, "mn") is not None else None),
        matchday_max=(int(_get(md_minmax, 1, "mx")) if _get(md_minmax, 1, "mx") is not None else None),
        last_finalized_matchday=(int(_get(last_md, 0, "last_md")) if _get(last_md, 0, "last_md") is not None else None),
    )

@router.get("/seasons/{season_id}/snapshot", response_model=SeasonSnapshot)
def season_snapshot(
    season_id: int,
    include: Optional[str] = Query(None, pattern=r"^(teams|players|matchdays|matches)(,(teams|players|matchdays|matches))*$"),
    limit_matches: int = Query(500, ge=1, le=2000),
):
    parts = set((include or "").split(",")) if include else set()
    summ = season_summary(season_id)
    out = SeasonSnapshot(summary=summ)
    if not parts or "teams" in parts:
        out.teams = list_teams(season_id).items
    if not parts or "players" in parts:
        out.players = list_players(season_id).items
    if not parts or "matchdays" in parts:
        out.matchdays = list_matchdays(season_id).items
    if not parts or "matches" in parts:
        out.matches = list_matches(season_id, limit=limit_matches, offset=0).items
    return out
