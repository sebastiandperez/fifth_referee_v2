from __future__ import annotations
from typing import Sequence

from application.dto import CompetitionDTO
from application.services import CompetitionService

class GetCompetitionsQuery:
    """Caso de uso: obtener todas las competiciones."""

    def __init__(self, svc: CompetitionService) -> None:
        self._svc = svc

    def execute(self) -> Sequence[CompetitionDTO]:
        return self._svc.list_competitions()
