import dataclasses
import pytest
from datetime import datetime, timezone
from domain.events import MatchFinalized
from domain.ids import MatchId

def test_match_finalized_is_frozen_and_has_fields():
    ev = MatchFinalized(match_id=MatchId(10), occurred_at=datetime(2025,1,1,tzinfo=timezone.utc))
    assert ev.match_id == 10
    with pytest.raises(dataclasses.FrozenInstanceError):
        ev.match_id = MatchId(11)  # type: ignore
