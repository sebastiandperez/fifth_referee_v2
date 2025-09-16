from __future__ import annotations
from typing import Sequence

from application.dto import AssisterDTO
from application.services import PlayerStatsService

class GetTopAssistersQuery:
    """Caso de uso: ranking de asistentes de la temporada."""

    def __init__(self, svc: PlayerStatsService) -> None:
        self._svc = svc

    def execute(self, season_id: int, top: int = 10) -> Sequence[AssisterDTO]:
        return self._svc.get_top_assisters(season_id, top=top)
