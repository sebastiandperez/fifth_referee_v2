from __future__ import annotations
from typing import Sequence

from sqlalchemy import text
from sqlalchemy.engine import Engine

from domain.ports import SeasonPort, NotFoundError
from domain.models import Season, Matchday, Team
from .connection import connect
from .tables import T_SEASON, T_MATCHDAY, T_SEASON_TEAM, T_TEAM
from ._mappers import row_season, row_matchday, row_team

class SeasonRepo(SeasonPort):
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def get_season(self, season_id: int) -> Season:
        sql = text(f"""
            SELECT season_id, competition_id, season_label, is_completed
            FROM {T_SEASON}
            WHERE season_id = :sid
        """)
        with connect(self.engine) as conn:
            r = conn.execute(sql, {"sid": season_id}).mappings().first()
        if not r:
            raise NotFoundError(f"season_id {season_id} no existe")
        return row_season(r)

    def list_matchdays(self, season_id: int) -> Sequence[Matchday]:
        sql = text(f"""
            SELECT matchday_id, season_id, matchday_number
            FROM {T_MATCHDAY}
            WHERE season_id = :sid
            ORDER BY matchday_number
        """)
        with connect(self.engine) as conn:
            rows = conn.execute(sql, {"sid": season_id}).mappings().all()
        return [row_matchday(r) for r in rows]

    def list_teams(self, season_id: int) -> Sequence[Team]:
        sql = text(f"""
            SELECT t.team_id, t.team_name, t.team_city, t.team_stadium
            FROM {T_SEASON_TEAM} st
            JOIN {T_TEAM} t ON t.team_id = st.team_id
            WHERE st.season_id = :sid
            ORDER BY t.team_name
        """)
        with connect(self.engine) as conn:
            rows = conn.execute(sql, {"sid": season_id}).mappings().all()
        return [row_team(r) for r in rows]
