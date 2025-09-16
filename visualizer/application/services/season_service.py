from __future__ import annotations
from typing import Sequence

from domain.ports import SeasonPort, NotFoundError
from application.dto import (
    SeasonDTO, MatchdayDTO, TeamDTO,
    to_season_dto, to_matchday_dto, to_team_dto,
)

class SeasonService:
    """Servicios de temporada: datos base, jornadas y equipos inscritos."""

    def __init__(self, season_port: SeasonPort) -> None:
        self._season_port = season_port

    def get_season(self, season_id: int) -> SeasonDTO:
        season = self._season_port.get_season(season_id)
        return to_season_dto(season)

    def list_matchdays(self, season_id: int) -> Sequence[MatchdayDTO]:
        mds = self._season_port.list_matchdays(season_id)
        return [to_matchday_dto(x) for x in mds]

    def list_teams(self, season_id: int) -> Sequence[TeamDTO]:
        teams = self._season_port.list_teams(season_id)
        return [to_team_dto(t) for t in teams]
