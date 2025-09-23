from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

@dataclass(frozen=True)
class Name:
    value: str

    def __post_init__(self) -> None:
        v = (self.value or "").strip()
        if not v:
            raise ValueError("Name cannot be empty")
        object.__setattr__(self, "value", v)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class DateRange:
    start: datetime
    end:   Optional[datetime] = None  # abierto si None

    def __post_init__(self) -> None:
        if self.end is not None and self.end < self.start:
            raise ValueError("DateRange.end cannot be earlier than start")

    def contains(self, dt: datetime) -> bool:
        if self.end is None:
            return dt >= self.start
        return self.start <= dt <= self.end

    def overlaps(self, other: "DateRange") -> bool:
        a1, a2 = self.start, self.end
        b1, b2 = other.start, other.end

        a2_inf = a2 is None
        b2_inf = b2 is None

        if a2_inf and b2_inf:
            return max(a1, b1) <= max(a1, b1)
        if a2_inf:
            return a1 <= (b2 or b1) and (b1 <= (a2 or b1))  # a2 = +inf
        if b2_inf:
            return b1 <= (a2 or a1) and (a1 <= (b2 or a1))  # b2 = +inf

        return (a1 <= b2) and (b1 <= a2)


@dataclass(frozen=True)
class Minute:
    """Minuto de partido (0..130 aprox. por prórrogas)."""
    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("Minute cannot be negative")
        if self.value > 130:
            # Ajusta si manejas límites distintos
            raise ValueError("Minute is unrealistically large")

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True)
class DateTimeUTC:
    """Instante en UTC; fuerza tz=UTC para coherencia."""
    value: datetime

    def __post_init__(self) -> None:
        if self.value.tzinfo is None:
            # Si viene naive, forzamos UTC (ajusta si prefieres rechazar naive)
            object.__setattr__(self, "value", self.value.replace(tzinfo=timezone.utc))
        else:
            # Reconvierte a UTC
            object.__setattr__(self, "value", self.value.astimezone(timezone.utc))

    def __str__(self) -> str:
        return self.value.isoformat()


@dataclass(frozen=True)
class Score:
    home: int
    away: int

    def __post_init__(self) -> None:
        if self.home < 0 or self.away < 0:
            raise ValueError("Score values cannot be negative")

    @property
    def diff(self) -> int:
        return self.home - self.away

    def winner_side(self) -> Optional[str]:
        if self.home > self.away:
            return "HOME"
        if self.home < self.away:
            return "AWAY"
        return None  # empate

    def as_tuple(self) -> tuple[int, int]:
        return (self.home, self.away)


__all__ = ["Name", "DateRange", "Minute", "DateTimeUTC", "Score"]
