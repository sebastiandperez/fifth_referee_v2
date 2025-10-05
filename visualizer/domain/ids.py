from __future__ import annotations
from typing import NewType

# Typed IDs (alias fuertes para evitar confusiones entre enteros distintos)
CompetitionId = NewType("CompetitionId", int)
SeasonId      = NewType("SeasonId", int)
MatchdayId    = NewType("MatchdayId", int)
MatchId       = NewType("MatchId", int)

TeamId        = NewType("TeamId", int)
PlayerId      = NewType("PlayerId", int)

__all__ = [
    "CompetitionId", "SeasonId", "MatchdayId", "MatchId",
    "TeamId", "PlayerId",
]
