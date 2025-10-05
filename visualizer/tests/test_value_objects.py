import dataclasses
import pytest
from datetime import datetime, timedelta, timezone

from domain.value_objects import Name, DateRange, Minute, DateTimeUTC, Score

def test_name_strips_and_non_empty():
    with pytest.raises(ValueError):
        Name("   ")
    n = Name("  Alpha  ")
    assert n.value == "Alpha"
    assert str(n) == "Alpha"

def test_date_range_contains_and_overlaps():
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    later = now + timedelta(days=1)
    dr1 = DateRange(start=now, end=later)
    dr2 = DateRange(start=now - timedelta(hours=1), end=now + timedelta(hours=1))
    assert dr1.contains(now) and dr1.contains(later)
    assert dr1.overlaps(dr2) is True

    open_end = DateRange(start=now)
    assert open_end.contains(now + timedelta(days=365))
    assert open_end.overlaps(dr2) is True

def test_minute_bounds_and_dunder_int():
    with pytest.raises(ValueError):
        Minute(-1)
    with pytest.raises(ValueError):
        Minute(1000)
    m = Minute(90)
    assert int(m) == 90

def test_datetimeutc_normalizes_tz():
    naive = datetime(2025, 1, 1, 12, 0, 0)  # naive
    aware = DateTimeUTC(naive)
    assert aware.value.tzinfo == timezone.utc
    # If non-UTC provided, it's converted
    bogota = datetime(2025, 1, 1, 7, 0, 0, tzinfo=timezone(timedelta(hours=-5)))
    aware2 = DateTimeUTC(bogota)
    assert aware2.value.utcoffset() == timedelta(0)

def test_score_validates_and_helpers():
    with pytest.raises(ValueError):
        Score(home=-1, away=0)
    s = Score(2, 1)
    assert s.diff == 1
    assert s.as_tuple() == (2, 1)
    assert s.winner_side() == "HOME"
    assert Score(0, 0).winner_side() is None
