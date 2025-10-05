from __future__ import annotations
from enum import Enum

class Position(str, Enum):
    GK = "GK"
    DF = "DF"
    MF = "MF"
    FW = "FW"
    # add granular roles (RB/LB/CB/AM/RW/LW/ST etc.) if you like

class Side(str, Enum):
    HOME = "HOME"
    AWAY = "AWAY"

class Result(str, Enum):
    WIN  = "W"
    DRAW = "D"
    LOSS = "L"

class EventType(str, Enum):
    GOAL          = "GOAL"
    OWN_GOAL      = "OWN_GOAL"
    PENALTY_GOAL  = "PENALTY_GOAL"
    MISSED_PEN    = "MISSED_PENALTY"
    YELLOW_CARD   = "YELLOW_CARD"
    RED_CARD      = "RED_CARD"
    SUBSTITUTION  = "SUBSTITUTION"
    START         = "START"
    END           = "END"

__all__ = ["Position", "Side", "Result", "EventType"]
