from __future__ import annotations
from typing import Sequence

from sqlalchemy import text
from sqlalchemy.engine import Engine

from domain.ports import EventPort
from domain.models import Event
from .connection import connect
from .tables import T_EVENT
from ._mappers import row_event

class EventRepo(EventPort):
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def list_events(self, match_id: int) -> Sequence[Event]:
        sql = text(f"""
            SELECT event_id, match_id, event_type, minute,
                   main_player_id, extra_player_id, team_id
            FROM {T_EVENT}
            WHERE match_id = :mid
            ORDER BY COALESCE(minute, 1000), event_id
        """)
        with connect(self.engine) as conn:
            rows = conn.execute(sql, {"mid": match_id}).mappings().all()
        return [row_event(r) for r in rows]
