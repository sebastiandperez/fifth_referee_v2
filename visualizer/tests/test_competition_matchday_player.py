import pytest

from domain.entities.competition import Competition
from domain.entities.matchday import Matchday
from domain.entities.player import Player
from domain.value_objects import Name
from domain.ids import CompetitionId, MatchdayId, SeasonId, PlayerId
import dataclasses


def test_competition_is_frozen_and_fields():
    c = Competition(competition_id=CompetitionId("LIGA"), name=Name("Liga 1"), country="CO")
    assert c.name == Name("Liga 1")
    with pytest.raises(dataclasses.FrozenInstanceError):
        c.name = Name("Other")  # type: ignore[attr-defined]

def test_matchday_is_frozen_and_number():
    md = Matchday(matchday_id=MatchdayId("MD1"), season_id=SeasonId("2025"), number=1)
    assert md.number == 1
    import dataclasses
    with pytest.raises(dataclasses.FrozenInstanceError):
        md.number = 2  # type: ignore[attr-defined]

def test_player_is_frozen_and_basic_fields():
    p = Player(player_id=PlayerId("P1"), name=Name("Ada Lovelace"))
    assert p.name == Name("Ada Lovelace")
    import dataclasses
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.name = Name("Grace Hopper")  # type: ignore[attr-defined]
