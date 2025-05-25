from utils.db_utils import get_matchdays_id, get_matches_in_matchdays
from utils.utils import cast_df_with_schema
import pandas as pd
import gc

def filter_new_matches_by_registered(all_matches, registered_match_ids):
    """
    Devuelve una lista de diccionarios con los partidos que NO están registrados.
    """
    registered_set = set(registered_match_ids)  # Para búsqueda eficiente O(1)
    filtered_matches = [m for m in all_matches if m['match_id'] not in registered_set]
    return filtered_matches

def build_clean_match_df(
    conn,
    all_matches,
    season_id,
    schema_path="pipeline/config/match_schema.json"
):
    """
    Builds a clean, type-casted DataFrame of matches ready for DB insertion.

    Args:
        conn: Active DB connection.
        all_matches (list of dict): Raw matches.
        season_id (int): Season identifier.
        schema_path (str): Path to JSON schema for dtype casting.

    Returns:
        pd.DataFrame: Cleaned DataFrame for insertion into core.match.
    """
    # 1. Raw DataFrame from list of matches
    match_df_raw = pd.DataFrame(all_matches)
    if match_df_raw.empty:
        return match_df_raw
    
    matchday_df = get_matchdays_id(conn, season_id)  # Expects DataFrame with matchday_id, matchday_number
    # 3. Merge to get correct matchday_id in each match by matchday_number
    match_df = match_df_raw.merge(matchday_df, on="matchday", how="left")
    match_df = match_df.dropna(subset=['match_id'])
    registered_match_ids = get_matches_in_matchdays(conn, matchday_df['matchday_id'].tolist())
    match_df = match_df[~match_df['match_id'].isin(registered_match_ids)]
    match_df = cast_df_with_schema(match_df, schema_path)
    match_df = match_df.drop(columns=['matchday'])
    del match_df_raw, matchday_df
    gc.collect()

    return match_df
