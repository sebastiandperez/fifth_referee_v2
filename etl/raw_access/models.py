from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class RawMatchRecord:
    match_id: int
    competition: str
    season: str
    matchday: Optional[int]
    local_team_id: int
    away_team_id: int
    local_score: Optional[int]
    away_score: Optional[int]
    stadium: Optional[str]
    duration: Optional[int]
    source_system: Optional[str]
    source_url: Optional[str]
    ran_at: Optional[datetime]
    raw_run_id: str


@dataclass(frozen=True)
class RawParticipationRecord:
    match_id: int
    player_id: int
    team_id: int
    jersey_number: Optional[int]
    position: Optional[str]
    status: Optional[int]


@dataclass(frozen=True)
class RawPlayerStatRecord:
    match_id: int
    player_id: int
    stat_name: str
    raw_value: str
    value_numeric: Optional[float]
    value_ratio_num: Optional[int]
    value_ratio_den: Optional[int]


@dataclass(frozen=True)
class RawMatchBundle:
    match: RawMatchRecord
    participations: Tuple[RawParticipationRecord, ...]
    stats: Tuple[RawPlayerStatRecord, ...]

    def participations_by_team(self) -> Dict[int, List[RawParticipationRecord]]:
        grouped: Dict[int, List[RawParticipationRecord]] = {}
        for part in self.participations:
            grouped.setdefault(part.team_id, []).append(part)
        return grouped

    def stats_by_player(self) -> Dict[int, List[RawPlayerStatRecord]]:
        grouped: Dict[int, List[RawPlayerStatRecord]] = {}
        for stat in self.stats:
            grouped.setdefault(stat.player_id, []).append(stat)
        return grouped
