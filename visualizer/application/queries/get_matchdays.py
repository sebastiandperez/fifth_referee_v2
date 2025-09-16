from __future__ import annotations
from typing import Sequence
from application.dto import MatchdayDTO, to_matchday_dto
from application.services.season_service import SeasonService

class GetMatchdaysQuery:
    def __init__(self, svc: SeasonService) -> None:
        self._svc = svc

    def execute(self, season_id: int) -> Sequence[MatchdayDTO]:
        return self._svc.list_matchdays(season_id)
