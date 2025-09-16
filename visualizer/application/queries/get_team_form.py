from __future__ import annotations
from typing import Sequence

from application.dto import TeamFormRowDTO
from application.services import TeamService

class GetTeamFormQuery:
    """Caso de uso: últimos N partidos con W/D/L para un equipo."""

    def __init__(self, svc: TeamService) -> None:
        self._svc = svc

    def execute(self, season_id: int, team_id: int, n: int = 5) -> Sequence[TeamFormRowDTO]:
        return self._svc.get_team_form(season_id, team_id, n=n)
