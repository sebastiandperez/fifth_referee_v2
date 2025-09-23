from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from ..ids import PlayerId, MatchId, TeamId
from ..enums import Position, Result

__all__ = [
    "BasicStats",
    "GoalkeeperStats", "DefenderStats", "MidfielderStats", "ForwardStats", "StandingRow", "TeamFormRow", "TeamSplit",
]

@dataclass
class StandingRow:
    team_id: TeamId
    MP: int
    GF: int
    GA: int
    GD: int
    Pts: int


@dataclass(frozen=True)
class TeamFormRow:
    match_id: MatchId
    result: Result  # W / D / L


@dataclass(frozen=True)
class TeamSplit:
    home_ppg: float
    away_ppg: float
    home_gf: int
    away_gf: int
    home_ga: int
    away_ga: int



@dataclass(frozen=True)
class BasicStats:
    """
    Core per-player-per-match stats. Attach this to a Participation.
    Keep fields minimal and extensible.
    """
    player_id: PlayerId
    match_id: MatchId
    minutes: int = 0
    goals: int = 0
    assists: int = 0
    shots: int = 0
    shots_on_target: int = 0
    yellow_cards: int = 0
    red_cards: int = 0
    position: Optional[Position] = None


# Role-specific add-ons (compose with BasicStats)
@dataclass(frozen=True)
class GoalkeeperStats:
    player_id: PlayerId
    match_id: MatchId
    saves: int = 0
    goals_conceded: int = 0
    goals_prevented: Optional[float] = None  # if you compute/model this KPI


@dataclass(frozen=True)
class DefenderStats:
    player_id: PlayerId
    match_id: MatchId
    tackles: int = 0
    interceptions: int = 0
    clearances: int = 0


@dataclass(frozen=True)
class MidfielderStats:
    player_id: PlayerId
    match_id: MatchId
    key_passes: int = 0
    chances_created: int = 0
    progressive_passes: int = 0


@dataclass(frozen=True)
class ForwardStats:
    player_id: PlayerId
    match_id: MatchId
    xg: Optional[float] = None
    xa: Optional[float] = None
