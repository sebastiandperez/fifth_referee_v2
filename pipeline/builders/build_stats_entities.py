import json
from utils.db_utils import get_participations_without_stats_by_season, get_basic_stats_keys_by_season
import pandas as pd
from utils.utils import load_event_type_map
def fetch_participations_and_existing_basic_stats(conn, season_id):
    """
    Devuelve un tuple (participation_df, existing_keys_df) con los DataFrames necesarios.
    """
    participation_df = get_participations_without_stats_by_season(conn, season_id)
    existing_keys_df = get_basic_stats_keys_by_season(conn, season_id)
    if participation_df.empty:
        return participation_df

    if not existing_keys_df.empty:
        filtered_df = participation_df.merge(
            existing_keys_df,
            on=['match_id', 'player_id'],
            how='left',
            indicator=True
        )
        filtered_df = filtered_df[filtered_df['_merge'] == 'left_only'].drop(columns=['_merge'])
        return filtered_df.reset_index(drop=True)
    else:
        return participation_df.reset_index(drop=True)
    return participation_df, existing_keys_df

def build_basic_stats_df(raw_player_stats, participations_df):
    stats_df = pd.DataFrame(raw_player_stats)
    stats_df.to_csv("mi_archivo.csv", index=False, encoding="utf-8")    

    stat_name_map = load_event_type_map('pipeline/config/stats_name_map.json')
    
    stats_df['stat_name_eng'] = stats_df['stat_name'].map(stat_name_map)
    stats_pivot = stats_df.pivot_table(
        index=['match_id', 'player_id'],
        columns='stat_name_eng',
        values='stat_value',
        aggfunc='first'
    ).reset_index()
    merged_df = participations_df.merge(
        stats_pivot, on=['match_id', 'player_id'], how='left'
    )

    for col in [
        'minutes', 'goals', 'assists', 'touches', 'passes_total',
        'passes_completed', 'ball_recoveries', 'possessions_lost',
        'aerial_duels_won', 'aerial_duels_total', 'ground_duels_won', 'ground_duels_total'
    ]:
        if col not in merged_df.columns:
            merged_df[col] = 0
        else:
            merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce').fillna(0).astype(int)

    final_columns = [
        'match_id', 'player_id', 'minutes', 'goals', 'assists', 'touches',
        'passes_total', 'passes_completed', 'ball_recoveries', 'possessions_lost',
        'aerial_duels_won', 'aerial_duels_total', 'ground_duels_won', 'ground_duels_total'
    ]
    basic_stats_df = merged_df[final_columns]
    return basic_stats_df