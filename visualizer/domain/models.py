from dataclasses import dataclass, field
from typing import Optional, List

@dataclass(frozen=True)
class Team:
    team_id: int
    team_name: str
    team_stadium: Optional[str] = None
    team_city: Optional[str] = None

    def __repr__(self):
        city = self.team_city or "—"
        std  = self.team_stadium or "—"
        return f"Team(id={self.team_id}, name='{self.team_name}', city='{city}', stadium='{std}')"

@dataclass(frozen=True)
class Matchday:
    matchday_id: int
    matchday_number: int

    def __repr__(self):
        return f"Matchday(num={self.matchday_number}, id={self.matchday_id})"

@dataclass
class Season:
    season_id: int
    season_label: str
    competition_name: str
    _teams: Optional[List[Team]] = field(default=None, init=False, repr=False)
    _matchdays: Optional[List[Matchday]] = field(default=None, init=False, repr=False)

    def __repr__(self):
        n_teams = "?" if self._teams is None else len(self._teams)
        n_md    = "?" if self._matchdays is None else len(self._matchdays)
        return (f"Season(season_label='{self.season_label}', "
                f"competition='{self.competition_name}', id={self.season_id}, "
                f"teams={n_teams}, matchdays={n_md})")

    # setters internos controlados por el servicio
    def _set_teams(self, teams: List[Team]):      self._teams = teams
    def _set_matchdays(self, mds: List[Matchday]): self._matchdays = mds

    @property
    def teams(self) -> List[Team]:
        if self._teams is None:
            raise RuntimeError("Teams not loaded. Use SeasonService.load_teams().")
        return self._teams

    @property
    def matchdays(self) -> List[Matchday]:
        if self._matchdays is None:
            raise RuntimeError("Matchdays not loaded. Use SeasonService.load_matchdays().")
        return self._matchdays
