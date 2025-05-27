import json
from utils.db_utils import get_participations_by_season, get_basic_stats_keys_by_season
import pandas as pd
from utils.utils import load_event_type_map, standardize_basic_stats_columns
from normalizers.basic_stats_normalizer import normalize_basic_stats_df, cast_basic_stats_df
import gc

def fetch_participations_and_existing_basic_stats(conn, season_id):
    participation_df = get_participations_by_season(conn, season_id)
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
        del existing_keys_df, participation_df
        filtered_df = filtered_df[filtered_df['_merge'] == 'left_only'].drop(columns=['_merge'])
        return filtered_df.reset_index(drop=True)
    else:
        return participation_df.reset_index(drop=True)
    return participation_df, existing_keys_df

def value_selector(row):
    if row['stat_name_eng'] in row and pd.notnull(row[row['stat_name_eng']]):
        return row[row['stat_name_eng']]
    return row['stat_value']

def build_df(raw_player_stats, participations_df):
    stats_df = pd.DataFrame(raw_player_stats)
    stat_name_map = load_event_type_map('pipeline/config/stats_name_map.json')
    stats_df['stat_name_eng'] = stats_df['stat_name'].map(stat_name_map)

    stats_pivot = stats_df.pivot_table(
        index=['match_id', 'player_id'],
        columns='stat_name_eng',
        values='stat_value',
        aggfunc='first'
    )

    split_cols = [
        "passes_completed", "passes_total", "long_passes_completed", "long_passes_total",
        "dribbles_completed", "dribbles_total", "crosses_completed", "crosses_total",
        "tackles_won", "tackles_total", "aerial_duels_won", "aerial_duels_total",
        "ground_duels_won", "ground_duels_total"
    ]

    for col in split_cols:
        if col in stats_df.columns:
            stats_pivot[col] = stats_df.groupby(['match_id', 'player_id'])[col].first().values

    stats_pivot = stats_pivot.reset_index()
    merged_df = participations_df.merge(
        stats_pivot, on=['match_id', 'player_id'], how='left'
    )
    merged_df = normalize_basic_stats_df(merged_df)
    merged_df = merged_df[merged_df['minutes'] > 0].reset_index(drop=True)
    merged_df = cast_basic_stats_df(merged_df)
    merged_df = standardize_basic_stats_columns(merged_df)
    print(merged_df.columns)

    del stats_df,stat_name_map, stats_pivot, split_cols
    return merged_df

def build_basic_stats_for_season(conn, season_id, all_player_stats):
    participations_df = fetch_participations_and_existing_basic_stats(conn, season_id)
    basic_stats_df = build_df(all_player_stats, participations_df)
    del participations_df
    return basic_stats_df

