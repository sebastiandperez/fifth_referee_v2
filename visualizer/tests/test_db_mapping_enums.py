from infrastructure.postgres.mappers import map_db_position, map_db_event_type
from domain.enums import Position, EventType

def test_position_map_handles_all_values_and_mng_to_none():
    assert map_db_position("GK") == Position.GK
    assert map_db_position("DF") == Position.DF
    assert map_db_position("MF") == Position.MF
    assert map_db_position("FW") == Position.FW
    assert map_db_position("MNG") is None
    assert map_db_position(None) is None

def test_event_map_supported_and_unsupported():
    assert map_db_event_type("Goal") == EventType.GOAL
    assert map_db_event_type("Own goal") == EventType.OWN_GOAL
    assert map_db_event_type("Penalty") == EventType.PENALTY_GOAL
    assert map_db_event_type("Penalty missed") == EventType.MISSED_PEN
    assert map_db_event_type("Yellow card") == EventType.YELLOW_CARD
    assert map_db_event_type("Red card") == EventType.RED_CARD
    assert map_db_event_type("Substitution") == EventType.SUBSTITUTION
    assert map_db_event_type("Woodwork") is None
    assert map_db_event_type("Disallowed goal") is None

def test_event_map_strict_mode_raises_on_unknown():
    import pytest
    with pytest.raises(ValueError):
        map_db_event_type("Woodwork", strict=True)
