from __future__ import annotations
from typing import Sequence

from application.dto import SeasonDTO
from application.services import CompetitionService

class GetSeasonsByCompetitionQuery:
    """Caso de uso: listar temporadas de una competición."""

    def __init__(self, svc: CompetitionService) -> None:
        self._svc = svc

    def execute(self, competition_id: int) -> Sequence[SeasonDTO]:
        return self._svc.list_seasons(competition_id)
