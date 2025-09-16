from __future__ import annotations
from typing import Sequence

from application.dto import StandingRowDTO
from application.services import StandingsService

class GetStandingsQuery:
    """Caso de uso: obtener tabla de posiciones por temporada."""

    def __init__(self, svc: StandingsService) -> None:
        self._svc = svc

    def execute(self, season_id: int) -> Sequence[StandingRowDTO]:
        return self._svc.get_standings(season_id)
