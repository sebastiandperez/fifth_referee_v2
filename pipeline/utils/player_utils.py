from utils.db_utils import get_player_ids_by_season_team_ids, get_season_team_ids, get_player_ids_by_match_ids
from utils.utils import cast_df_with_schema
import pandas as pd

def player_df_from_dict(player_dicts):
    if not player_dicts:
        columns = ['match_id', 'team_id', 'player_id', 'player_name', 'jersey_number', 'position', 'status']
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(player_dicts)

    return df

def get_match_ids(df_match):
    """
    Returns a list of unique match_id values from the matches DataFrame.

    Args:
        df_match (pd.DataFrame): DataFrame with at least a 'match_id' column.

    Returns:
        list: List of unique match_id values.
    """
    match_id_list = df_match['match_id'].drop_duplicates().tolist()
    return match_id_list


def drop_duplicate_participations(conn, player_df, match_id_list):
    """
    Removes rows from player_df where match_id is in match_id_list.

    Args:
        player_df (pd.DataFrame): DataFrame with at least a 'match_id' column.
        match_id_list (list or set): Collection of match_id values to drop.

    Returns:
        pd.DataFrame: Filtered DataFrame with specified match_ids removed.
    """
    players_registered = get_player_ids_by_match_ids(conn, match_id_list)
    mask = ~player_df['player_id'].isin(players_registered)
    return player_df[mask].reset_index(drop=True)

def build_clean_player_df(conn, player_dicts, match_id_list, schema_path="pipeline/config/player_schema.json"):
    """
    Builds a clean pandas DataFrame from a list of player participation dictionaries,
    filters by valid match_ids, removes duplicates, and applies external schema casting.

    Args:
        conn: DB connection, if needed for filtering.
        player_dicts (list of dict): List of player participation dictionaries.
        match_id_list: List or DataFrame for valid match_ids.
        schema_path (str): Path to JSON schema file for column types.

    Returns:
        pd.DataFrame: Cleaned and type-casted DataFrame for further processing.
    """
    player_df = player_df_from_dict(player_dicts)
    match_id_list = get_match_ids(match_id_list)
    filtered_df = drop_duplicate_participations(conn, player_df, match_id_list)
    filtered_df = cast_df_with_schema(filtered_df, schema_path)
    return filtered_df

def build_team_player (conn, player_df, season_id):
    team_ids = player_df['team_id'].drop_duplicates().tolist()
    season_team_id = get_season_team_ids(conn, season_id, team_ids)
    players_in = get_player_ids_by_season_team_ids(conn, season_team_id)
    player_df = player_df[~player_df['player_id'].isin(players_in)]
    return player_df

def build_player_df(df_players, existing_player_ids):
    """
    Filters out players whose player_id is already present in the existing_player_ids list/set.

    Args:
        df_players (pd.DataFrame): DataFrame with at least a 'player_id' column.
        existing_player_ids (set or list): Collection of player_id values to exclude.

    Returns:
        pd.DataFrame: DataFrame with only new players (player_id not in existing_player_ids).
    """
    mask = ~df_players['player_id'].isin(existing_player_ids)
    return df_players[mask].reset_index(drop=True)


