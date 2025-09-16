from __future__ import annotations
from typing import Sequence

from domain.ports import CompetitionPort, NotFoundError
from application.dto import (
    CompetitionDTO, SeasonDTO,
    to_competition_dto, to_season_dto,
)

class CompetitionService:
    """Servicios para competencias y temporadas (catálogo)."""

    def __init__(self, competition_port: CompetitionPort) -> None:
        self._competition_port = competition_port

    def list_competitions(self) -> Sequence[CompetitionDTO]:
        comps = self._competition_port.list_competitions()
        return [to_competition_dto(c) for c in comps]

    def list_seasons(self, competition_id: int) -> Sequence[SeasonDTO]:
        seasons = self._competition_port.list_seasons(competition_id)
        return [to_season_dto(s) for s in seasons]
