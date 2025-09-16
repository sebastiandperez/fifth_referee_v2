from __future__ import annotations
from typing import Sequence

from sqlalchemy import text
from sqlalchemy.engine import Engine

from domain.ports import CompetitionPort, NotFoundError
from domain.models import Competition, Season
from .connection import connect
from .tables import T_COMPETITION, T_SEASON
from ._mappers import row_competition, row_season

class CompetitionRepo(CompetitionPort):
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def list_competitions(self) -> Sequence[Competition]:
        sql = text(f"""
            SELECT competition_id, competition_name, default_matchdays, is_international, continent
            FROM {T_COMPETITION}
            ORDER BY competition_name
        """)
        with connect(self.engine) as conn:
            rows = conn.execute(sql).mappings().all()
        return [row_competition(r) for r in rows]

    def list_seasons(self, competition_id: int) -> Sequence[Season]:
        sql = text(f"""
            SELECT season_id, competition_id, season_label, is_completed
            FROM {T_SEASON}
            WHERE competition_id = :cid
            ORDER BY season_label
        """)
        with connect(self.engine) as conn:
            rows = conn.execute(sql, {"cid": competition_id}).mappings().all()
        return [row_season(r) for r in rows]
