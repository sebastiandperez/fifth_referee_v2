from __future__ import annotations
from typing import Sequence

from sqlalchemy import text
from sqlalchemy.engine import Engine

from domain.ports import StandingsPort
from domain.models import StandingRow
from .connection import connect
from .tables import T_MATCH, T_MATCHDAY, T_TEAM
from ._mappers import row_standing

class StandingsRepo(StandingsPort):
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def get_standings(self, season_id: int) -> Sequence[StandingRow]:
        sql = text(f"""
            WITH finalized AS (
              SELECT m.*
              FROM {T_MATCH} m
              JOIN {T_MATCHDAY} md ON md.matchday_id = m.matchday_id
              WHERE md.season_id = :sid
                AND m.local_score IS NOT NULL AND m.away_score IS NOT NULL
            ),
            home AS (
              SELECT local_team_id AS team_id,
                     1 AS MP,
                     local_score AS gf,
                     away_score  AS ga,
                     CASE WHEN local_score > away_score THEN 3
                          WHEN local_score = away_score THEN 1
                          ELSE 0 END AS pts
              FROM finalized
            ),
            away AS (
              SELECT away_team_id AS team_id,
                     1 AS MP,
                     away_score AS gf,
                     local_score AS ga,
                     CASE WHEN away_score > local_score THEN 3
                          WHEN away_score = local_score THEN 1
                          ELSE 0 END AS pts
              FROM finalized
            ),
            agg AS (
              SELECT team_id,
                     SUM(MP) AS MP,
                     SUM(pts) AS Pts,
                     SUM(gf) AS GF,
                     SUM(ga) AS GA,
                     SUM(gf - ga) AS GD
              FROM (
                SELECT * FROM home
                UNION ALL
                SELECT * FROM away
              ) s
              GROUP BY team_id
            )
            SELECT a.team_id, t.team_name, a.MP, a.Pts, a.GF, a.GA, a.GD
            FROM agg a
            JOIN {T_TEAM} t ON t.team_id = a.team_id
            ORDER BY a.Pts DESC, a.GD DESC, a.GF DESC, t.team_name
        """)
        with connect(self.engine) as conn:
            rows = conn.execute(sql, {"sid": season_id}).mappings().all()
        return [row_standing(r) for r in rows]
