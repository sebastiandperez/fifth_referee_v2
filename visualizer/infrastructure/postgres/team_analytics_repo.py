from __future__ import annotations
from typing import Sequence

from sqlalchemy import text
from sqlalchemy.engine import Engine

from domain.ports import TeamAnalyticsPort
from domain.models import TeamFormRow, TeamSplit
from .connection import connect
from .tables import T_MATCH, T_MATCHDAY
from ._mappers import row_team_form, row_team_split

class TeamAnalyticsRepo(TeamAnalyticsPort):
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def get_team_form(self, season_id: int, team_id: int, *, n: int = 5) -> Sequence[TeamFormRow]:
        sql = text(f"""
            SELECT m.match_id, md.matchday_number,
                   m.local_team_id AS home_team_id,
                   m.away_team_id AS away_team_id,
                   m.local_score, m.away_score
            FROM {T_MATCH} m
            JOIN {T_MATCHDAY} md ON md.matchday_id = m.matchday_id
            WHERE md.season_id = :sid
              AND (m.local_team_id = :tid OR m.away_team_id = :tid)
              AND m.local_score IS NOT NULL AND m.away_score IS NOT NULL
            ORDER BY md.matchday_number DESC, m.match_id DESC
            LIMIT :lim
        """)
        with connect(self.engine) as conn:
            rows = conn.execute(sql, {"sid": season_id, "tid": team_id, "lim": n}).mappings().all()
        # devolver en orden cronológico ascendente para la UI
        rows = list(reversed(rows))
        return [row_team_form(r, perspective_team_id=team_id) for r in rows]

    def get_team_splits(self, season_id: int, team_id: int) -> TeamSplit:
        sql = text(f"""
            SELECT
              COALESCE(SUM(CASE WHEN local_team_id = :tid THEN
                    CASE WHEN local_score > away_score THEN 3
                         WHEN local_score = away_score THEN 1
                         ELSE 0 END END), 0) AS home_pts,
              COALESCE(SUM(CASE WHEN away_team_id = :tid THEN
                    CASE WHEN away_score > local_score THEN 3
                         WHEN away_score = local_score THEN 1
                         ELSE 0 END END), 0) AS away_pts,
              COALESCE(COUNT(CASE WHEN local_team_id = :tid THEN 1 END), 0) AS home_mp,
              COALESCE(COUNT(CASE WHEN away_team_id = :tid THEN 1 END), 0) AS away_mp,
              COALESCE(SUM(CASE WHEN local_team_id = :tid THEN local_score END), 0) AS home_gf,
              COALESCE(SUM(CASE WHEN local_team_id = :tid THEN away_score END), 0) AS home_ga,
              COALESCE(SUM(CASE WHEN away_team_id = :tid THEN away_score END), 0) AS away_gf,
              COALESCE(SUM(CASE WHEN away_team_id = :tid THEN local_score END), 0) AS away_ga
            FROM {T_MATCH} m
            JOIN {T_MATCHDAY} md ON md.matchday_id = m.matchday_id
            WHERE md.season_id = :sid
              AND m.local_score IS NOT NULL AND m.away_score IS NOT NULL
              AND (m.local_team_id = :tid OR m.away_team_id = :tid)
        """)
        with connect(self.engine) as conn:
            r = conn.execute(sql, {"sid": season_id, "tid": team_id}).mappings().first()

        home_mp = int(r["home_mp"]) or 0
        away_mp = int(r["away_mp"]) or 0
        home_ppg = (float(r["home_pts"]) / home_mp) if home_mp > 0 else 0.0
        away_ppg = (float(r["away_pts"]) / away_mp) if away_mp > 0 else 0.0

        return row_team_split(
            home_ppg=round(home_ppg, 3),
            away_ppg=round(away_ppg, 3),
            home_gf=int(r["home_gf"]),
            home_ga=int(r["home_ga"]),
            away_gf=int(r["away_gf"]),
            away_ga=int(r["away_ga"]),
        )
