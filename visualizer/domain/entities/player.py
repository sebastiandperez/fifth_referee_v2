from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from ..ids import PlayerId
from ..value_objects import Name
from ..enums import Position


__all__ = ["Player"]


@dataclass(frozen=True)
class Player:
    """Catalog entity for a player."""
    player_id: PlayerId
    name: Name
    position: Optional[Position] = None
    nationality: Optional[str] = None
