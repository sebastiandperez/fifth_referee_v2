from utils.match_utils import build_clean_match_df
from builders.team_builder import build_team_dataframe_from_matches, filter_new_teams,build_team_dataframe
from utils.registry_utils import build_season_team_df
import gc

def build_match_entities(conn, all_matches, competition_name, season_id, api_token, config):
    """
    Builds the main entities (match, team, season_team) DataFrames from raw matches.

    Returns:
        match_df, team_df, match_season_team
    """
    
    match_df = build_clean_match_df(conn, all_matches, season_id)
    total_teams_df = build_team_dataframe_from_matches(match_df)
    match_season_team = build_season_team_df(conn, total_teams_df, season_id)
    incomplete_team_df = filter_new_teams(conn, total_teams_df)
    team_df = build_team_dataframe(incomplete_team_df, competition_name, api_token)
    del all_matches, incomplete_team_df
    return match_df, team_df, match_season_team
