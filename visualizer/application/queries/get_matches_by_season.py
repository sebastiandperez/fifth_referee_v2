from __future__ import annotations
from typing import Sequence

from domain.ports import MatchPort
from application.dto import MatchDTO, to_match_dto

class GetMatchesBySeasonQuery:
    def __init__(self, match_port: MatchPort) -> None:
        self._port = match_port

    def execute(self, season_id: int, only_finalized: bool = False) -> Sequence[MatchDTO]:
        matches = self._port.list_matches_by_season(season_id, only_finalized=only_finalized)
        return [to_match_dto(m) for m in matches]
