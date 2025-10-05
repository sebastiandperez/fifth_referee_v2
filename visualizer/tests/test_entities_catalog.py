import dataclasses
import pytest
from domain.entities.competition import Competition
from domain.entities.matchday import Matchday
from domain.entities.player import Player
from domain.value_objects import Name
from domain.ids import CompetitionId, MatchdayId, SeasonId, PlayerId

def test_competition_frozen():
    c = Competition(competition_id=CompetitionId(1), name=Name("Liga 1"), country="CO")
    with pytest.raises(dataclasses.FrozenInstanceError):
        c.name = Name("Other")  # type: ignore

def test_matchday_frozen():
    md = Matchday(matchday_id=MatchdayId(1), season_id=SeasonId(2025), number=3)
    with pytest.raises(dataclasses.FrozenInstanceError):
        md.number = 4  # type: ignore

def test_player_frozen():
    p = Player(player_id=PlayerId(99), name=Name("Alex Morgan"))
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.name = Name("Other")  # type: ignore
