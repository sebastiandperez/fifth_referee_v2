from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from ..ids import TeamId, PlayerId
from ..value_objects import Name, DateRange
from ..enums import Position


__all__ = ["Team", "TeamPlayer"]


@dataclass(frozen=True)
class Team:
    """Catalog entity for a team (stable identity)."""
    team_id: TeamId
    name: Name
    city: Optional[str] = None
    stadium: Optional[str] = None


@dataclass
class TeamPlayer:
    """
    Association entity: a player's spell at a team (team-centric roster history).
    Use DateRange to constrain validity. Invariants:
      - date_range.start <= date_range.end
    """
    team_id: TeamId
    player_id: PlayerId
    date_range: DateRange
    position: Optional[Position] = None
    shirt_number: Optional[int] = None

    def overlaps(self, other: "TeamPlayer") -> bool:
        """True if both entries are for the same player in the same team and date ranges intersect."""
        if self.team_id != other.team_id or self.player_id != other.player_id:
            return False
        return self.date_range.overlaps(other.date_range)


@dataclass
class TeamRoster:
    """
    Optional helper aggregate (not mandatory for your app layer):
    Manage a team's roster entries and validate overlaps.
    """
    team: Team
    members: List[TeamPlayer] = field(default_factory=list)

    def add_member(self, tp: TeamPlayer) -> None:
        if tp.team_id != self.team.team_id:
            raise ValueError("TeamPlayer.team_id does not match Team.team_id")
        for existing in self.members:
            if existing.player_id == tp.player_id and existing.overlaps(tp):
                raise ValueError("Overlapping roster spells for the same player in this team")
        self.members.append(tp)

    def remove_member(self, player_id: PlayerId) -> None:
        self.members = [m for m in self.members if m.player_id != player_id]
