from __future__ import annotations

from application.dto import TeamSplitDTO
from application.services import TeamService

class GetTeamSplitsQuery:
    """Caso de uso: rendimiento de local vs visitante para un equipo."""

    def __init__(self, svc: TeamService) -> None:
        self._svc = svc

    def execute(self, season_id: int, team_id: int) -> TeamSplitDTO:
        return self._svc.get_team_splits(season_id, team_id)
