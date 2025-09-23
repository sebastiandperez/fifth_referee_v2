# interfaces/api.py
from __future__ import annotations

from typing import List, Optional, Sequence, Literal, Iterable, Any
from dataclasses import asdict
from inspect import signature
from fastapi import FastAPI, Depends, Query, HTTPException
from pydantic import BaseModel, Field

# --- Domain / Application wiring
from domain.ids import SeasonId, TeamId
from domain.entities.match import Match
from domain.entities.stats import StandingRow, TeamFormRow, TeamSplit
from application.use_cases import (
    get_season_standings,
    get_team_dashboard,
)

# --- Infra adapter
from infrastructure.postgres.adapters import PgMatchAdapter, get_conn

api = FastAPI(title="Fifth Referee API", version="1.0")

# -----------------------------------------------------------------------------
# Dependencies
# -----------------------------------------------------------------------------
def get_adapter() -> PgMatchAdapter:
    return PgMatchAdapter()

# -----------------------------------------------------------------------------
# Pydantic models (API DTOs)
# -----------------------------------------------------------------------------
class SeasonLabelList(BaseModel):
    items: List[str]

class CompetitionItem(BaseModel):
    id: int
    name: str

class CompetitionList(BaseModel):
    items: List[CompetitionItem]

class SeasonResolveResult(BaseModel):
    season_id: int

class SeasonSummary(BaseModel):
    season_id: int
    season_label: str
    competition_id: int
    competition_name: str
    team_count: int
    matchday_min: Optional[int] = None
    matchday_max: Optional[int] = None
    last_finalized_matchday: Optional[int] = None

class StandingRowAPI(BaseModel):
    team_id: int
    team_name: Optional[str] = None
    mp: int
    gf: int
    ga: int
    gd: int
    pts: int
    position: int

class SeasonStandingsDTOAPI(BaseModel):
    rows: List[StandingRowAPI]

class TeamFormRowAPI(BaseModel):
    match_id: int
    result: Literal["WIN", "DRAW", "LOSS"]

class TeamSplitAPI(BaseModel):
    home_ppg: float
    away_ppg: float
    home_gf: int
    away_gf: int
    home_ga: int
    away_ga: int

class TeamDashboardDTOAPI(BaseModel):
    form: List[TeamFormRowAPI]
    split: TeamSplitAPI

class MatchEvent(BaseModel):
    event_id: int
    match_id: int
    event_type: str
    minute: Optional[int] = None
    main_player_id: Optional[int] = None
    extra_player_id: Optional[int] = None
    team_id: Optional[int] = None

class MatchParticipation(BaseModel):
    match_id: int
    player_id: int
    team_id: int
    role: Optional[str] = None
    minute_in: Optional[int] = None
    minute_out: Optional[int] = None

class MatchAPI(BaseModel):
    match_id: int
    matchday_id: int
    home_team_id: int
    away_team_id: int
    home_score: Optional[int]
    away_score: Optional[int]
    duration: Optional[int]
    events: Optional[List[MatchEvent]] = None

class TeamItem(BaseModel):
    team_id: int
    team_name: str

class TeamList(BaseModel):
    items: List[TeamItem]

class ParticipationAPI(BaseModel):
    match_id: int
    player_id: int
    team_id: int
    role: Optional[str] = None
    minute_in: Optional[int] = None
    minute_out: Optional[int] = None

# -----------------------------------------------------------------------------
# Helpers (small, read-only SQLs kept here to avoid tight coupling)
# For large codebases, move these to the adapter.
# -----------------------------------------------------------------------------

# --- Helpers: fixed SQLs ---

def _get(row, *keys):
    """
    Robustly extract a value from a DB row that may be:
    - tuple/list (positional)
    - mapping/dict-like (string keys)
    - SQLAlchemy Row (use ._mapping)
    - object with attributes
    Returns the first successful key/attr in *keys.
    """
    # SQLAlchemy Row has _mapping for dict-like access
    mapping = getattr(row, "_mapping", None)
    if mapping:
        for k in keys:
            if k in mapping:
                return mapping[k]
    # Regular dict-like
    if isinstance(row, dict):
        for k in keys:
            if k in row:
                return row[k]
    # Positional access (first numeric key wins)
    for k in keys:
        if isinstance(k, int):
            try:
                return row[k]  # tuple/list-like
            except Exception:
                pass
    # Attribute access fallback
    for k in keys:
        if isinstance(k, str) and hasattr(row, k):
            return getattr(row, k)
    raise KeyError(f"None of {keys} found in row of type {type(row)}")

# -----------------------------------------------------------------------------
# Helpers (SQL) — replace the bodies that index rows positionally
# -----------------------------------------------------------------------------

def _list_season_labels() -> List[str]:
    sql = "SELECT DISTINCT season_label FROM core.season ORDER BY season_label DESC"
    with get_conn() as conn:
        rows = conn.execute(sql).fetchall()
    return [str(_get(r, 0, "season_label")) for r in rows]

def _list_competitions_for_label(season_label: str) -> List[CompetitionItem]:
    sql = """
    SELECT DISTINCT c.competition_id, c.competition_name
    FROM core.season s
    JOIN reference.competition c ON c.competition_id = s.competition_id
    WHERE s.season_label = %s
    ORDER BY c.competition_name
    """
    with get_conn() as conn:
        rows = conn.execute(sql, [season_label]).fetchall()
    return [CompetitionItem(
        id=int(_get(r, 0, "competition_id")),
        name=str(_get(r, 1, "competition_name"))
    ) for r in rows]

def _resolve_season_id(season_label: str, competition_id: int) -> Optional[int]:
    sql = """
    SELECT season_id FROM core.season
    WHERE season_label = %s AND competition_id = %s
    ORDER BY season_id LIMIT 1
    """
    with get_conn() as conn:
        row = conn.execute(sql, [season_label, competition_id]).fetchone()
    return int(_get(row, 0, "season_id")) if row else None

def _season_summary(season_id: int) -> SeasonSummary:
    meta_sql = """
    SELECT s.season_id, s.season_label, c.competition_id, c.competition_name
    FROM core.season s
    JOIN reference.competition c ON c.competition_id = s.competition_id
    WHERE s.season_id = %s
    """
    team_sql = "SELECT COUNT(*) AS cnt FROM registry.season_team WHERE season_id = %s"
    md_sql = """
    SELECT MIN(md.matchday_number) AS mn, MAX(md.matchday_number) AS mx
    FROM core.matchday md
    WHERE md.season_id = %s
    """
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

        team_count_row = conn.execute(team_sql, [season_id]).fetchone()
        md_minmax_row = conn.execute(md_sql, [season_id]).fetchone()
        last_md_row   = conn.execute(last_sql, [season_id]).fetchone()

    team_count = int(_get(team_count_row, 0, "cnt"))
    md_min = _get(md_minmax_row, 0, "mn")
    md_max = _get(md_minmax_row, 1, "mx")
    last_md = _get(last_md_row, 0, "last_md")

    return SeasonSummary(
        season_id=season_id,
        season_label=str(_get(meta, 1, "season_label")),
        competition_id=int(_get(meta, 2, "competition_id")),
        competition_name=str(_get(meta, 3, "competition_name")),
        team_count=team_count,
        matchday_min=(int(md_min) if md_min is not None else None),
        matchday_max=(int(md_max) if md_max is not None else None),
        last_finalized_matchday=(int(last_md) if last_md is not None else None),
    )

def _list_teams(season_id: int) -> List[TeamItem]:
    sql = """
    SELECT t.team_id, t.team_name
    FROM registry.season_team st
    JOIN reference.team t ON t.team_id = st.team_id
    WHERE st.season_id = %s
    ORDER BY t.team_name
    """
    with get_conn() as conn:
        rows = conn.execute(sql, [season_id]).fetchall()
    return [TeamItem(team_id=int(_get(r, 0, "team_id")), team_name=str(_get(r, 1, "team_name"))) for r in rows]

def _team_name_map(season_id: int) -> dict[int, str]:
    return {t.team_id: t.team_name for t in _list_teams(season_id)}

def _normalize_competitions(rows: Iterable[Any]) -> list[CompetitionItem]:
    items: list[CompetitionItem] = []
    for r in rows:
        # object with attributes (id, name)
        if hasattr(r, "id") and hasattr(r, "name"):
            items.append(CompetitionItem(id=int(getattr(r, "id")), name=str(getattr(r, "name"))))
        # mapping/dict-ish
        elif isinstance(r, dict) and ("id" in r and "name" in r):
            items.append(CompetitionItem(id=int(r["id"]), name=str(r["name"])))
        # 2-tuple/list like (id, name)
        elif isinstance(r, (tuple, list)) and len(r) >= 2:
            items.append(CompetitionItem(id=int(r[0]), name=str(r[1])))
        else:
            # last-resort duck typing
            items.append(CompetitionItem(id=int(getattr(r, "competition_id", getattr(r, "id"))),
                                         name=str(getattr(r, "competition_name", getattr(r, "name")))))
    return items


# -----------------------------------------------------------------------------
# V1: Discovery
# -----------------------------------------------------------------------------
@api.get("/v1/season-labels", response_model=SeasonLabelList)
def list_season_labels():
    return SeasonLabelList(items=_list_season_labels())

@api.get("/v1/season-labels/{season_label:path}/competitions", response_model=CompetitionList)
def competitions_for_label(season_label: str):
    normalized = season_label.replace("/", "_")
    rows = _list_competitions_for_label(normalized)
    return CompetitionList(items=_normalize_competitions(rows))

@api.get("/v1/seasons/resolve", response_model=SeasonResolveResult)
def resolve_season(season_label: str = Query(...), competition_id: int = Query(...)):
    sid = _resolve_season_id(season_label, competition_id)
    if sid is None:
        raise HTTPException(404, detail="season not found for (label, competition)")
    return SeasonResolveResult(season_id=sid)

# -----------------------------------------------------------------------------
# V1: Season Summary
# -----------------------------------------------------------------------------
@api.get("/v1/seasons/{season_id}/summary", response_model=SeasonSummary)
def season_summary(season_id: int):
    return _season_summary(season_id)

# -----------------------------------------------------------------------------
# V1: Standings (kept compatible with your tests)
# -----------------------------------------------------------------------------
@api.get("/v1/seasons/{season_id}/standings", response_model=SeasonStandingsDTOAPI)
def standings(
    season_id: int,
    # Puedes dejar la política aquí para el futuro; hoy no la usamos:
    win: int = Query(3, ge=0, le=10),
    draw: int = Query(1, ge=0, le=10),
    loss: int = Query(0, ge=0, le=10),
    until_matchday: Optional[int] = Query(None, ge=1),
    adapter: PgMatchAdapter = Depends(get_adapter),
):
    # Llama a tu caso de uso tal como está hoy
    dto = get_season_standings(SeasonId(season_id), adapter)

    name_map = _team_name_map(season_id)
    rows: List[StandingRowAPI] = []

    # Map directo 1:1 con el dominio
    for r in dto.rows:
        rows.append(StandingRowAPI(
            team_id=int(r.team_id),
            team_name=name_map.get(int(r.team_id)),
            mp=int(r.MP),
            gf=int(r.GF),
            ga=int(r.GA),
            gd=int(r.GD),
            pts=int(r.Pts),
            position=0,  # lo ajustamos luego
        ))

    # Orden si el dominio no lo trae: Pts desc, GD desc, GF desc
    rows.sort(key=lambda x: (x.pts, x.gd, x.gf), reverse=True)
    for i, row in enumerate(rows, start=1):
        row.position = i

    return SeasonStandingsDTOAPI(rows=rows)

# -----------------------------------------------------------------------------
# V1: Teams & Dashboard (kept compatible)
# -----------------------------------------------------------------------------
@api.get("/v1/seasons/{season_id}/teams", response_model=TeamList)
def list_teams(season_id: int):
    return TeamList(items=_list_teams(season_id))

@api.get("/v1/seasons/{season_id}/teams/{team_id}/dashboard", response_model=TeamDashboardDTOAPI)
def team_dashboard(
    season_id: int,
    team_id: int,
    form_n: int = Query(5, ge=1, le=10, description="Length of recent-form window"),
    adapter: PgMatchAdapter = Depends(get_adapter),
):
    # Use-case currently has fixed n=5; if you add n later, pass it through.
    d = get_team_dashboard(SeasonId(season_id), TeamId(team_id), adapter)
    # Map domain DTOs
    form = [TeamFormRowAPI(match_id=int(r.match_id), result=r.result.name) for r in d.form]
    split = TeamSplitAPI(
        home_ppg=d.split.home_ppg,
        away_ppg=d.split.away_ppg,
        home_gf=d.split.home_gf,
        away_gf=d.split.away_gf,
        home_ga=d.split.home_ga,
        away_ga=d.split.away_ga,
    )
    return TeamDashboardDTOAPI(form=form, split=split)

# -----------------------------------------------------------------------------
# V1: Matches (+ include=events,participations) & single-match resources
# -----------------------------------------------------------------------------
@api.get("/v1/seasons/{season_id}/matches", response_model=List[MatchAPI])
def list_matches(
    season_id: int,
    matchday: Optional[int] = Query(None, ge=1),
    team_id: Optional[int] = Query(None, ge=1),
    opponent_id: Optional[int] = Query(None, ge=1),
    finalized: Optional[bool] = Query(None),
    include: Optional[str] = Query(None, pattern=r"^(events|participations|events,participations)$"),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    adapter: PgMatchAdapter = Depends(get_adapter),
):
    # We assume adapter has: list_matches_filtered(...)
    # If not, implement a tight SQL in adapter using these filters + LIMIT/OFFSET.
    matches: Sequence[Match] = adapter.list_matches_filtered(
        season_id=SeasonId(season_id),
        matchday=matchday,
        team_id=team_id,
        opponent_id=opponent_id,
        finalized=finalized,
        limit=limit,
        offset=offset,
    )

    include_events = include in ("events", "events,participations")
    include_parts = include in ("participations", "events,participations")

    # Optional bulk prefetch to avoid N+1
    events_by_match: dict[int, List[MatchEvent]] = {}
    parts_by_match: dict[int, List[MatchParticipation]] = {}

    if include_events:
        evs = adapter.list_events_for_matches([int(m.match_id) for m in matches])
        for e in evs:
            events_by_match.setdefault(int(e.match_id), []).append(MatchEvent(
                event_id=int(e.event_id),
                match_id=int(e.match_id),
                event_type=str(e.event_type),
                minute=(int(e.minute) if e.minute is not None else None),
                main_player_id=(int(e.main_player_id) if e.main_player_id is not None else None),
                extra_player_id=(int(e.extra_player_id) if e.extra_player_id is not None else None),
                team_id=(int(e.team_id) if e.team_id is not None else None),
            ))

    if include_parts:
        ps = adapter.list_participations_for_matches([int(m.match_id) for m in matches])
        for p in ps:
            parts_by_match.setdefault(int(p.match_id), []).append(MatchParticipation(
                match_id=int(p.match_id),
                player_id=int(p.player_id),
                team_id=int(p.team_id),
                role=p.role,
                minute_in=p.minute_in,
                minute_out=p.minute_out,
            ))

    out: List[MatchAPI] = []
    for m in matches:
        item = MatchAPI(
            match_id=int(m.match_id),
            matchday_id=int(m.matchday_id),
            home_team_id=int(m.home_team_id),
            away_team_id=int(m.away_team_id),
            home_score=(int(m.score.home) if m.score else None),
            away_score=(int(m.score.away) if m.score else None),
            duration=m.duration,
        )
        if include_events:
            item.events = events_by_match.get(int(m.match_id), [])
        # (You can also attach participations as a sibling field if you prefer.)
        out.append(item)
    return out

@api.get("/v1/matches/{match_id}/events", response_model=List[MatchEvent])
def match_events(match_id: int, adapter: PgMatchAdapter = Depends(get_adapter)):
    rows = adapter.list_events_for_match(match_id)
    return [
        MatchEvent(
            event_id=int(r.event_id),
            match_id=int(r.match_id),
            event_type=str(r.event_type),
            minute=(int(r.minute) if r.minute is not None else None),
            main_player_id=(int(r.main_player_id) if r.main_player_id is not None else None),
            extra_player_id=(int(r.extra_player_id) if r.extra_player_id is not None else None),
            team_id=(int(r.team_id) if r.team_id is not None else None),
        )
        for r in rows
    ]

@api.get("/v1/matches/{match_id}/participations", response_model=List[ParticipationAPI])
def get_match_participations(
    match_id: int,
    adapter: PgMatchAdapter = Depends(get_adapter),
):
    rows = adapter.list_participations_for_match(match_id)
    # Safety filter in case the adapter returns extra rows
    rows = [r for r in rows if int(getattr(r, "match_id", match_id)) == match_id]
    return [
        ParticipationAPI(
            match_id=r.match_id,
            player_id=r.player_id,
            team_id=r.team_id,
            role=getattr(r, "role", None),
            minute_in=getattr(r, "minute_in", None),
            minute_out=getattr(r, "minute_out", None),
        )
        for r in rows
    ]
