from typing import List
from domain.models import Season, Team, Matchday
from domain.ports import SeasonRepository
import pandas as pd

class SeasonService:
    def __init__(self, repo: SeasonRepository):
        self.repo = repo

    def load_teams(self, season: Season) -> List[Team]:
        df = self.repo.fetch_teams(season.season_id)
        teams = [
            Team(
                team_id=int(r.team_id),
                team_name=str(r.team_name),
                team_stadium=(None if pd.isna(r.team_stadium) else str(r.team_stadium)),
                team_city=(None if pd.isna(r.team_city) else str(r.team_city)),
            )
            for r in df.itertuples(index=False)
        ]
        season._set_teams(teams)
        return teams

    def load_matchdays(self, season: Season) -> List[Matchday]:
        df = self.repo.fetch_matchdays(season.season_id)
        mds = [
            Matchday(matchday_id=int(r.matchday_id), matchday_number=int(r.matchday_number))
            for r in df.itertuples(index=False)
        ]
        season._set_matchdays(mds)
        return mds
