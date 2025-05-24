from utils.db_utils import get_basic_stats_ids_by_season, get_all_registered_basic_stat_ids
from normalizers.specific_stats_normalizer import goalkeeper_normalizer,defender_normalizer,midfielder_normalizer,forward_normalized
import pandas as pd 
import json

def fetch_for_specific_stats_id(conn, season_id):
    basic_stats_df = get_basic_stats_ids_by_season(conn, season_id)
    existing_keys = set(get_all_registered_basic_stat_ids(conn))
    filtered_basic_stats = basic_stats_df[~basic_stats_df['basic_stats_id'].isin(existing_keys)].copy()
    return filtered_basic_stats

def pivot_dictionary(all_player_stats):
    stats_df = pd.DataFrame(all_player_stats)
    if 'stat_name' not in stats_df.columns:
        raise ValueError("Falta la columna 'stat_name' en los datos de entrada.")
    pivoted = stats_df.pivot_table(
        index=['match_id', 'player_id'],
        columns='stat_name',
        values='stat_value',
        aggfunc='first'
    ).reset_index()
    return pivoted

def merge_participation_stats(universe_df, stats_pivot):
    merged = universe_df.merge(stats_pivot, on=['match_id', 'player_id'], how='left')
    return merged

def separate_specific_stats_df(universe_df):
    gk_df = universe_df[universe_df["position"] == "GK"].copy()
    df_df = universe_df[universe_df["position"] == "DF"].copy()
    mf_df = universe_df[universe_df["position"] == "MF"].copy()
    fw_df = universe_df[universe_df["position"] == "FW"].copy()
    return gk_df, df_df,mf_df,fw_df

def build_specific_stats_df(conn, season_id, all_player_stats):
    filtered_df = fetch_for_specific_stats_id(conn, season_id)
    pivot = pivot_dictionary (all_player_stats)
    full_specific_stats_df = merge_participation_stats(filtered_df, pivot)
    gk_df, df_df,mf_df,fw_df = separate_specific_stats_df(full_specific_stats_df)
    goalkeeper_df = goalkeeper_normalizer(gk_df)
    defender_df =defender_normalizer(df_df)
    midfielder_df = midfielder_normalizer(mf_df)
    forward_df = forward_normalized(fw_df)
    dfs = [goalkeeper_df, defender_df, midfielder_df, forward_df]
    pd.set_option('future.no_silent_downcasting', True)
    for df in dfs:
        df.fillna(0, inplace=True)
        df.infer_objects(copy=False)
    return goalkeeper_df, defender_df, midfielder_df, forward_df