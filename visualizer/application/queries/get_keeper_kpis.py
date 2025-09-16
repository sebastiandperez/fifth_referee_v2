from __future__ import annotations
from typing import Sequence

from application.dto import KeeperKPIDTO
from application.services import PlayerStatsService

class GetKeeperKPIsQuery:
    """Caso de uso: KPIs de porteros para la temporada."""

    def __init__(self, svc: PlayerStatsService) -> None:
        self._svc = svc

    def execute(self, season_id: int, top: int = 10) -> Sequence[KeeperKPIDTO]:
        return self._svc.get_keeper_kpis(season_id, top=top)
