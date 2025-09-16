from __future__ import annotations
from typing import Sequence

from application.dto import ScorerDTO
from application.services import PlayerStatsService

class GetTopScorersQuery:
    """Caso de uso: ranking de goleadores de la temporada."""

    def __init__(self, svc: PlayerStatsService) -> None:
        self._svc = svc

    def execute(self, season_id: int, top: int = 10) -> Sequence[ScorerDTO]:
        return self._svc.get_top_scorers(season_id, top=top)
