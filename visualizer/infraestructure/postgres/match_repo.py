from __future__ import annotations
from typing import Sequence

from sqlalchemy import text
from sqlalchemy.engine import Engine

from domain.ports import MatchPort
from domain.models import Match
from .connection import connect
from .tables import T_MATCH, T_MATCHDAY
from ._mappers import row_match

class MatchRepo(MatchPort):
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def list_matches_by_season(self, season_id: int, *, only_finalized: bool = True) -> Sequence[Match]:
        sql = text(f"""
            SELECT m.match_id, m.matchday_id, m.local_team_id, m.away_team_id,
                   m.local_score, m.away_score, m.kickoff_utc, m.stadium, m.duration_minutes
            FROM {T_MATCH} m
            JOIN {T_MATCHDAY} md ON md.matchday_id = m.matchday_id
            WHERE md.season_id = :sid
              AND (:fin = FALSE OR (m.local_score IS NOT NULL AND m.away_score IS NOT NULL))
            ORDER BY md.matchday_number, m.match_id
        """)
        with connect(self.engine) as conn:
            rows = conn.execute(sql, {"sid": season_id, "fin": only_finalized}).mappings().all()
        return [row_match(r) for r in rows]

    def list_matches_for_team(self, season_id: int, team_id: int, *, only_finalized: bool = True) -> Sequence[Match]:
        sql = text(f"""
            SELECT m.match_id, m.matchday_id, m.local_team_id, m.away_team_id,
                   m.local_score, m.away_score, m.kickoff_utc, m.stadium, m.duration_minutes
            FROM {T_MATCH} m
            JOIN {T_MATCHDAY} md ON md.matchday_id = m.matchday_id
            WHERE md.season_id = :sid
              AND (m.local_team_id = :tid OR m.away_team_id = :tid)
              AND (:fin = FALSE OR (m.local_score IS NOT NULL AND m.away_score IS NOT NULL))
            ORDER BY md.matchday_number, m.match_id
        """)
        with connect(self.engine) as conn:
            rows = conn.execute(sql, {"sid": season_id, "tid": team_id, "fin": only_finalized}).mappings().all()
        return [row_match(r) for r in rows]
