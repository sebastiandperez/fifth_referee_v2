from utils.db_utils import get_season_team_table
import pandas as pd

def normalize_team_player_df(conn, team_player_full_df, season_id):
    """
    Normalizes the team_player DataFrame by joining with registry.season_team to get season_team_id.
    Drops any rows with null player_id.

    Args:
        conn: Active DB connection.
        team_player_full_df (pd.DataFrame): DataFrame with team_id, season_id, player_id, jersey_number.
        season_id (int): The global season_id for filtering.

    Returns:
        pd.DataFrame: Normalized DataFrame with season_team_id, player_id, jersey_number.
    """
    season_team_df = get_season_team_table(conn, season_id)
    merged_df = team_player_full_df.merge(
        season_team_df,
        on=["team_id"],
        how="left"
    )

    result_df = merged_df[['season_team_id', 'player_id', 'jersey_number']]

    result_df = result_df.dropna(subset=['player_id'])

    result_df['season_team_id'] = result_df['season_team_id'].astype('int64')
    result_df['player_id'] = result_df['player_id'].astype('int64')
    result_df['jersey_number'] = result_df['jersey_number'].astype('int8')

    return result_df
