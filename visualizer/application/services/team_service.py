from __future__ import annotations
from typing import Sequence

from domain.ports import StandingsPort
from application.dto import StandingRowDTO, to_standing_row_dto

class StandingsService:
    """Servicios para standings (tabla de posiciones)."""

    def __init__(self, standings_port: StandingsPort) -> None:
        self._standings_port = standings_port

    def get_standings(self, season_id: int) -> Sequence[StandingRowDTO]:
        rows = self._standings_port.get_standings(season_id)
        # Asegura orden Pts -> GD -> GF por si el adapter no lo hace
        rows_sorted = sorted(rows, key=lambda r: (r.Pts, r.GD, r.GF), reverse=True)
        return [to_standing_row_dto(r) for r in rows_sorted]
