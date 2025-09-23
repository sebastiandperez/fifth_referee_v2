from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from ..ids import CompetitionId
from ..value_objects import Name

__all__ = ["Competition"]


@dataclass(frozen=True)
class Competition:
    """Catalog entity for a competition (e.g., LaLiga, Premier League)."""
    competition_id: CompetitionId
    name: Name
    country: Optional[str] = None
