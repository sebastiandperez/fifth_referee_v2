from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

from .ids import MatchId

@dataclass(frozen=True)
class MatchFinalized:
    match_id: MatchId
    occurred_at: datetime
