from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from ..ids import MatchId, SeasonId, TeamId, PlayerId
from ..value_objects import Score, Minute, DateTimeUTC
from ..enums import Side, EventType
from .stats import BasicStats, GoalkeeperStats, DefenderStats, MidfielderStats, ForwardStats


__all__ = ["Match", "Participation", "Event", "Lineups"]


@dataclass
class Participation:
    """
    Association entity owned by Match: a player's involvement in this match.
    Attach stats objects as needed (basic + role-specific).
    Invariants to enforce at the Match level:
      - player belongs to home or away team roster at match date
      - minutes >= 0 and within match duration
    """
    match_id: MatchId
    team_id: TeamId
    player_id: PlayerId
    side: Side                      # HOME or AWAY
    starter: bool = False
    minutes_played: int = 0
    position_hint: Optional[str] = None
    basic: Optional[BasicStats] = None
    gk: Optional[GoalkeeperStats] = None
    def_stats: Optional[DefenderStats] = None
    mid_stats: Optional[MidfielderStats] = None
    fwd_stats: Optional[ForwardStats] = None


@dataclass(frozen=True)
class Event:
    """
    Timeline event within a match (goal, card, substitution, etc.)
    """
    match_id: MatchId
    minute: Minute
    type: EventType
    team_id: Optional[TeamId] = None
    player_id: Optional[PlayerId] = None
    secondary_player_id: Optional[PlayerId] = None  # e.g., assister, subbed player
    comment: Optional[str] = None


@dataclass
class Lineups:
    """Split participations into home/away views."""
    home: List[Participation] = field(default_factory=list)
    away: List[Participation] = field(default_factory=list)

@dataclass
class Match:
    """
    Aggregate root: a single fixture.
    Owns:
      - score (optional until finalized)
      - participations (lineups)
      - events (timeline)
    """
    match_id: MatchId
    season_id: SeasonId
    matchday_id: Optional[int]
    home_team_id: TeamId
    away_team_id: TeamId
    kickoff_utc: Optional[DateTimeUTC] = None
    score: Optional[Score] = None
    duration: Optional[int] = None
    finalized: bool = False

    participations: List[Participation] = field(default_factory=list)
    events: List[Event] = field(default_factory=list)

    # --- domain helpers / invariants (lightweight; heavy validation can live in domain services) ---

    def add_participation(self, p: Participation) -> None:
        if p.match_id != self.match_id:
            raise ValueError("Participation.match_id mismatch")
        if p.side == "HOME" and p.team_id != self.home_team_id:
            raise ValueError("HOME participation must use home_team_id")
        if p.side == "AWAY" and p.team_id != self.away_team_id:
            raise ValueError("AWAY participation must use away_team_id")
        if p.minutes_played < 0:
            raise ValueError("minutes_played cannot be negative")
        self.participations.append(p)

    def add_event(self, e: Event) -> None:
        if e.match_id != self.match_id:
            raise ValueError("Event.match_id mismatch")
        self.events.append(e)

    def set_score(self, score: Score, finalized: bool = False) -> None:
        if score.home < 0 or score.away < 0:
            raise ValueError("Score cannot be negative")
        self.score = score
        self.finalized = finalized

    def result_side(self) -> Optional[str]:
        """Return 'HOME' | 'AWAY' | 'DRAW' or None if no score."""
        if self.score is None:
            return None
        if self.score.home > self.score.away:
            return "HOME"
        if self.score.home < self.score.away:
            return "AWAY"
        return "DRAW"
