from __future__ import annotations
from typing import Sequence

from sqlalchemy import text
from sqlalchemy.engine import Engine

from domain.ports import PlayerStatsPort
from domain.models import ScorerRow, AssisterRow, KeeperKPI
from .connection import connect
from .tables import T_BASIC_STATS, T_PLAYER, T_MATCH, T_MATCHDAY, T_GK_STATS
from ._mappers import row_scorer, row_assister, row_keeper_kpi

class PlayerStatsRepo(PlayerStatsPort):
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def get_top_scorers(self, season_id: int, *, top: int = 10) -> Sequence[ScorerRow]:
        sql = text(f"""
            SELECT bs.player_id, p.player_name, SUM(COALESCE(bs.goals, 0)) AS goals
            FROM {T_BASIC_STATS} bs
            JOIN {T_PLAYER} p ON p.player_id = bs.player_id
            JOIN {T_MATCH} m ON m.match_id = bs.match_id
            JOIN {T_MATCHDAY} md ON md.matchday_id = m.matchday_id
            WHERE md.season_id = :sid
            GROUP BY bs.player_id, p.player_name
            HAVING SUM(COALESCE(bs.goals, 0)) > 0
            ORDER BY goals DESC, p.player_name
            LIMIT :lim
        """)
        with connect(self.engine) as conn:
            rows = conn.execute(sql, {"sid": season_id, "lim": top}).mappings().all()
        return [row_scorer(r) for r in rows]

    def get_top_assisters(self, season_id: int, *, top: int = 10) -> Sequence[AssisterRow]:
        sql = text(f"""
            SELECT bs.player_id, p.player_name, SUM(COALESCE(bs.assists, 0)) AS assists
            FROM {T_BASIC_STATS} bs
            JOIN {T_PLAYER} p ON p.player_id = bs.player_id
            JOIN {T_MATCH} m ON m.match_id = bs.match_id
            JOIN {T_MATCHDAY} md ON md.matchday_id = m.matchday_id
            WHERE md.season_id = :sid
            GROUP BY bs.player_id, p.player_name
            HAVING SUM(COALESCE(bs.assists, 0)) > 0
            ORDER BY assists DESC, p.player_name
            LIMIT :lim
        """)
        with connect(self.engine) as conn:
            rows = conn.execute(sql, {"sid": season_id, "lim": top}).mappings().all()
        return [row_assister(r) for r in rows]

    def get_keeper_kpis(self, season_id: int, *, top: int = 10) -> Sequence[KeeperKPI]:
        sql = text(f"""
            SELECT bs.player_id, p.player_name,
                   SUM(COALESCE(gk.saves, 0)) AS saves,
                   SUM(COALESCE(gk.goals_prevented, 0)) AS goals_prevented,
                   SUM(COALESCE(gk.goals_conceded, 0)) AS goals_conceded
            FROM {T_BASIC_STATS} bs
            JOIN {T_GK_STATS} gk ON gk.basic_stats_id = bs.basic_stats_id
            JOIN {T_PLAYER} p ON p.player_id = bs.player_id
            JOIN {T_MATCH} m ON m.match_id = bs.match_id
            JOIN {T_MATCHDAY} md ON md.matchday_id = m.matchday_id
            WHERE md.season_id = :sid
            GROUP BY bs.player_id, p.player_name
            ORDER BY saves DESC NULLS LAST, goals_prevented DESC NULLS LAST
            LIMIT :lim
        """)
        with connect(self.engine) as conn:
            rows = conn.execute(sql, {"sid": season_id, "lim": top}).mappings().all()
        return [row_keeper_kpi(r) for r in rows]
