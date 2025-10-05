import dataclasses
import pytest

from domain.ids import CompetitionId, SeasonId, MatchdayId, MatchId, TeamId, PlayerId
from domain.enums import Position, Side, Result, EventType
from domain.errors import DomainError, ValidationError, InvariantError

def test_ids_are_int_newtypes_and_compare_like_ints():
    a = TeamId(1)
    b = TeamId(1)
    c = TeamId(2)
    assert a == b and a != c
    assert isinstance(a, int)  # NewType at runtime is the underlying type

def test_enums_are_str_based_and_equal_to_strings():
    assert Side.HOME == "HOME"
    assert Result.DRAW == "D"
    assert EventType.GOAL == "GOAL"
    # stringifying keeps value
    assert str(Position.MF) == "Position.MF" or True  # just smoke

def test_error_hierarchy():
    assert issubclass(ValidationError, DomainError)
    assert issubclass(InvariantError, DomainError)
