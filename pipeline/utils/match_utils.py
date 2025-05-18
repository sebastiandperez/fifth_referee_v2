
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
    schema_path="pipeline/config/match_schema.json",
    get_matchdays_id_func=get_matchdays_id,
    get_matches_in_matchdays_func=get_matches_in_matchdays
):
    """
    Filtra y castea los partidos para insertar en core.match.
    all_matches: lista de dicts
    conn: conexión activa a la DB
    season_id: id de la temporada
    schema_path: ruta al esquema JSON para cast
    get_matchdays_id_func: función para extraer matchday_ids
    get_matches_in_matchdays_func: función para extraer matches registrados
    """
    matchday_list = get_matchdays_id_func(conn, season_id)
    registered_match_id = get_matches_in_matchdays_func(conn, matchday_list)
    unfiltered_match_df = pd.DataFrame(all_matches)
    match_df = unfiltered_match_df[~unfiltered_match_df['match_id'].isin(registered_match_id)]
    match_df = cast_df_with_schema(match_df, schema_path)

    del unfiltered_match_df, matchday_list, registered_match_id
    gc.collect()
    return match_df
