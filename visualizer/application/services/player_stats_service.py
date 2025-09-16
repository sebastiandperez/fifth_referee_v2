from __future__ import annotations
from typing import Sequence

from domain.ports import PlayerStatsPort
from application.dto import (
    ScorerDTO, AssisterDTO, KeeperKPIDTO,
    to_scorer_dto, to_assister_dto, to_keeper_kpi_dto,
)

class PlayerStatsService:
    """Servicios de rankings y KPIs por jugador."""

    def __init__(self, player_stats_port: PlayerStatsPort) -> None:
        self._player_stats_port = player_stats_port

    def get_top_scorers(self, season_id: int, top: int = 10) -> Sequence[ScorerDTO]:
        rows = self._player_stats_port.get_top_scorers(season_id, top=top)
        return [to_scorer_dto(r) for r in rows]

    def get_top_assisters(self, season_id: int, top: int = 10) -> Sequence[AssisterDTO]:
        rows = self._player_stats_port.get_top_assisters(season_id, top=top)
        return [to_assister_dto(r) for r in rows]

    def get_keeper_kpis(self, season_id: int, top: int = 10) -> Sequence[KeeperKPIDTO]:
        rows = self._player_stats_port.get_keeper_kpis(season_id, top=top)
        return [to_keeper_kpi_dto(r) for r in rows]
