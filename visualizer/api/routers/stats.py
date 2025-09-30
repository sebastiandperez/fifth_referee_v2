from __future__ import annotations
from typing import Optional, List, Any
from fastapi import APIRouter, Query, HTTPException
from ..schemas import (
    PagedBasicStats, BasicStatsAPI,
    PagedRoleStats, GoalkeeperStatsAPI, DefenderStatsAPI, MidfielderStatsAPI, ForwardStatsAPI
)
from ..deps import _ensure_season, get_conn, _get

router = APIRouter(tags=["stats"])

@router.get("/seasons/{season_id}/stats/basic", response_model=PagedBasicStats)
def season_basic_stats(
    season_id: int,
    team_id: Optional[int] = Query(None, ge=1),
    player_id: Optional[int] = Query(None, ge=1),
    matchday_from: Optional[int] = Query(None, ge=1),
    matchday_to: Optional[int] = Query(None, ge=1),
    limit: int = Query(1000, ge=1, le=5000),
    offset: int = Query(0, ge=0),
):
    _ensure_season(season_id)

    where = ["md.season_id = %s"]
    params: list[Any] = [season_id]
    if team_id is not None:
        where.append("(m.local_team_id = %s OR m.away_team_id = %s)")
        params += [team_id, team_id]
    if player_id is not None:
        where.append("bs.player_id = %s")
        params.append(player_id)
    if matchday_from is not None:
        where.append("md.matchday_number >= %s")
        params.append(matchday_from)
    if matchday_to is not None:
        where.append("md.matchday_number <= %s")
        params.append(matchday_to)

    base = f"""
    FROM core.basic_stats bs
    JOIN core.match m     ON m.match_id = bs.match_id
    JOIN core.matchday md ON md.matchday_id = m.matchday_id
    WHERE {' AND '.join(where)}
    """

    count_sql = f"SELECT COUNT(*) AS count {base}"

    list_sql = f"""
    SELECT
      bs.basic_stats_id                         AS basic_stats_id,
      bs.match_id                               AS match_id,
      bs.player_id                              AS player_id,
      COALESCE(bs.minutes,0)                    AS minutes,
      COALESCE(bs.goals,0)                      AS goals,
      COALESCE(bs.assists,0)                    AS assists,
      COALESCE(bs.touches,0)                    AS touches,
      COALESCE(bs.passes_total,0)               AS passes_total,
      COALESCE(bs.passes_completed,0)           AS passes_completed,
      COALESCE(bs.ball_recoveries,0)            AS ball_recoveries,
      COALESCE(bs.possessions_lost,0)           AS possessions_lost,
      COALESCE(bs.aerial_duels_won,0)           AS aerial_duels_won,
      COALESCE(bs.aerial_duels_total,0)         AS aerial_duels_total,
      COALESCE(bs.ground_duels_won,0)           AS ground_duels_won,
      COALESCE(bs.ground_duels_total,0)         AS ground_duels_total
    {base}
    ORDER BY bs.basic_stats_id
    LIMIT %s OFFSET %s
    """

    with get_conn() as conn:
        total_row = conn.execute(count_sql, params).fetchone()
        rows = conn.execute(list_sql, [*params, limit, offset]).fetchall()

    total = int(_get(total_row, 0, "count") or 0)

    items: list[BasicStatsAPI] = []
    for r in rows:
        bs_id = _get(r, 0, "basic_stats_id")
        mid   = _get(r, 1, "match_id")
        pid   = _get(r, 2, "player_id")
        if bs_id is None or mid is None or pid is None:
            # Si llega a pasar, tus datos tienen PKs nulas o el driver no expone nombres.
            # Puedes raise o saltar la fila. Aquí hacemos raise para detectar el caso.
            raise HTTPException(status_code=500, detail="Row with NULL ids in core.basic_stats query")

        items.append(BasicStatsAPI(
            basic_stats_id=int(bs_id),
            match_id=int(mid),
            player_id=int(pid),
            minutes=int(_get(r, 3, "minutes") or 0),
            goals=int(_get(r, 4, "goals") or 0),
            assists=int(_get(r, 5, "assists") or 0),
            touches=int(_get(r, 6, "touches") or 0),
            passes_total=int(_get(r, 7, "passes_total") or 0),
            passes_completed=int(_get(r, 8, "passes_completed") or 0),
            ball_recoveries=int(_get(r, 9, "ball_recoveries") or 0),
            possessions_lost=int(_get(r,10, "possessions_lost") or 0),
            aerial_duels_won=int(_get(r,11, "aerial_duels_won") or 0),
            aerial_duels_total=int(_get(r,12, "aerial_duels_total") or 0),
            ground_duels_won=int(_get(r,13, "ground_duels_won") or 0),
            ground_duels_total=int(_get(r,14, "ground_duels_total") or 0),
        ))

    return PagedBasicStats(items=items, limit=limit, offset=offset, total=total)

@router.get("/seasons/{season_id}/stats/goalkeeper", response_model=PagedRoleStats)
def season_goalkeeper_stats(season_id: int, limit: int = Query(1000, ge=1, le=5000), offset: int = Query(0, ge=0)):
    _ensure_season(season_id)
    sql = """
    SELECT gk.*
    FROM stats.goalkeeper_stats gk
    JOIN core.basic_stats bs ON bs.basic_stats_id = gk.basic_stats_id
    JOIN core.match m ON m.match_id = bs.match_id
    JOIN core.matchday md ON md.matchday_id = m.matchday_id
    WHERE md.season_id = %s
    ORDER BY gk.basic_stats_id
    LIMIT %s OFFSET %s
    """
    with get_conn() as conn:
        rows = conn.execute(sql, [season_id, limit, offset]).fetchall()
    items = [GoalkeeperStatsAPI(**{
        "basic_stats_id": int(_get(r, 0, "basic_stats_id") or 0),
        "goalkeeper_saves": _get(r, "goalkeeper_saves"),
        "saves_inside_box": _get(r, "saves_inside_box"),
        "goals_conceded": _get(r, "goals_conceded"),
        "xg_on_target_against": _get(r, "xg_on_target_against"),
        "goals_prevented": _get(r, "goals_prevented"),
        "punches_cleared": _get(r, "punches_cleared"),
        "high_claims": _get(r, "high_claims"),
        "clearances": _get(r, "clearances"),
        "penalties_received": _get(r, "penalties_received"),
        "penalties_saved": _get(r, "penalties_saved"),
        "interceptions": _get(r, "interceptions"),
        "times_dribbled_past": _get(r, "times_dribbled_past"),
    }) for r in rows]
    return PagedRoleStats(items=items, limit=limit, offset=offset, total=None)

@router.get("/seasons/{season_id}/stats/defender", response_model=PagedRoleStats)
def season_defender_stats(season_id: int, limit: int = Query(1000, ge=1, le=5000), offset: int = Query(0, ge=0)):
    _ensure_season(season_id)
    sql = """
    SELECT d.*
    FROM stats.defender_stats d
    JOIN core.basic_stats bs ON bs.basic_stats_id = d.basic_stats_id
    JOIN core.match m ON m.match_id = bs.match_id
    JOIN core.matchday md ON md.matchday_id = m.matchday_id
    WHERE md.season_id = %s
    ORDER BY d.basic_stats_id
    LIMIT %s OFFSET %s
    """
    with get_conn() as conn:
        rows = conn.execute(sql, [season_id, limit, offset]).fetchall()
    items = [DefenderStatsAPI(**{
        "basic_stats_id": int(_get(r, 0, "basic_stats_id") or 0),
        "tackles_won": _get(r, "tackles_won"),
        "interceptions": _get(r, "interceptions"),
        "clearances": _get(r, "clearances"),
        "times_dribbled_past": _get(r, "times_dribbled_past"),
        "errors_leading_to_goal": _get(r, "errors_leading_to_goal"),
        "errors_leading_to_shot": _get(r, "errors_leading_to_shot"),
        "possessions_won_final_third": _get(r, "possessions_won_final_third"),
        "fouls_committed": _get(r, "fouls_committed"),
        "tackles_total": _get(r, "tackles_total"),
    }) for r in rows]
    return PagedRoleStats(items=items, limit=limit, offset=offset, total=None)

@router.get("/seasons/{season_id}/stats/midfielder", response_model=PagedRoleStats)
def season_midfielder_stats(season_id: int, limit: int = Query(1000, ge=1, le=5000), offset: int = Query(0, ge=0)):
    _ensure_season(season_id)
    sql = """
    SELECT mfs.*
    FROM stats.midfielder_stats mfs
    JOIN core.basic_stats bs ON bs.basic_stats_id = mfs.basic_stats_id
    JOIN core.match m ON m.match_id = bs.match_id
    JOIN core.matchday md ON md.matchday_id = m.matchday_id
    WHERE md.season_id = %s
    ORDER BY mfs.basic_stats_id
    LIMIT %s OFFSET %s
    """
    with get_conn() as conn:
        rows = conn.execute(sql, [season_id, limit, offset]).fetchall()
    items = [MidfielderStatsAPI(**{
        "basic_stats_id": int(_get(r, 0, "basic_stats_id") or 0),
        "expected_assists": _get(r, "expected_assists"),
        "expected_goals": _get(r, "expected_goals"),
        "xg_from_shots_on_target": _get(r, "xg_from_shots_on_target"),
        "tackles_won": _get(r, "tackles_won"),
        "tackles_total": _get(r, "tackles_total"),
        "crosses": _get(r, "crosses"),
        "fouls_committed": _get(r, "fouls_committed"),
        "fouls_suffered": _get(r, "fouls_suffered"),
        "big_chances": _get(r, "big_chances"),
        "big_chances_missed": _get(r, "big_chances_missed"),
        "big_chances_scored": _get(r, "big_chances_scored"),
        "interceptions": _get(r, "interceptions"),
        "key_passes": _get(r, "key_passes"),
        "passes_in_final_third": _get(r, "passes_in_final_third"),
        "back_passes": _get(r, "back_passes"),
        "long_passes_completed": _get(r, "long_passes_completed"),
        "woodwork": _get(r, "woodwork"),
        "possessions_won_final_third": _get(r, "possessions_won_final_third"),
        "times_dribbled_past": _get(r, "times_dribbled_past"),
        "dribbles_completed": _get(r, "dribbles_completed"),
        "dribbles_total": _get(r, "dribbles_total"),
        "long_passes_total": _get(r, "long_passes_total"),
        "crosses_total": _get(r, "crosses_total"),
        "shots_off_target": _get(r, "shots_off_target"),
        "shots_on_target": _get(r, "shots_on_target"),
        "shots_total": _get(r, "shots_total"),
    }) for r in rows]
    return PagedRoleStats(items=items, limit=limit, offset=offset, total=None)

@router.get("/seasons/{season_id}/stats/forward", response_model=PagedRoleStats)
def season_forward_stats(season_id: int, limit: int = Query(1000, ge=1, le=5000), offset: int = Query(0, ge=0)):
    _ensure_season(season_id)
    sql = """
    SELECT fs.*
    FROM stats.forward_stats fs
    JOIN core.basic_stats bs ON bs.basic_stats_id = fs.basic_stats_id
    JOIN core.match m ON m.match_id = bs.match_id
    JOIN core.matchday md ON md.matchday_id = m.matchday_id
    WHERE md.season_id = %s
    ORDER BY fs.basic_stats_id
    LIMIT %s OFFSET %s
    """
    with get_conn() as conn:
        rows = conn.execute(sql, [season_id, limit, offset]).fetchall()
    items = [ForwardStatsAPI(**{
        "basic_stats_id": int(_get(r, 0, "basic_stats_id") or 0),
        "expected_assists": _get(r, "expected_assists"),
        "expected_goals": _get(r, "expected_goals"),
        "xg_from_shots_on_target": _get(r, "xg_from_shots_on_target"),
        "shots_total": _get(r, "shots_total"),
        "shots_on_target": _get(r, "shots_on_target"),
        "shots_off_target": _get(r, "shots_off_target"),
        "big_chances": _get(r, "big_chances"),
        "big_chances_missed": _get(r, "big_chances_missed"),
        "big_chances_scored": _get(r, "big_chances_scored"),
        "penalties_won": _get(r, "penalties_won"),
        "penalties_missed": _get(r, "penalties_missed"),
        "offside": _get(r, "offside"),
        "key_passes": _get(r, "key_passes"),
        "dribbles_completed": _get(r, "dribbles_completed"),
        "dribbles_total": _get(r, "dribbles_total"),
        "times_dribbled_past": _get(r, "times_dribbled_past"),
        "fouls_committed": _get(r, "fouls_committed"),
        "fouls_suffered": _get(r, "fouls_suffered"),
        "woodwork": _get(r, "woodwork"),
    }) for r in rows]
