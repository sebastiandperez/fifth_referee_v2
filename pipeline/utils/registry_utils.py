from utils.db_utils import get_team_ids_in_season
import pandas as pd

def build_season_team_df(conn, unfiltered_team_df, season_id):
    team_ids_in_season = set(get_team_ids_in_season(conn, season_id))
    new_teams_df = unfiltered_team_df[['team_id']].drop_duplicates()
    new_teams_df = new_teams_df[~new_teams_df['team_id'].isin(team_ids_in_season)]
    new_teams_df['season_id'] = season_id

    del team_ids_in_season
    return new_teams_df
