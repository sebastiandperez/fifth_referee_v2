import pandas as pd
from utils.utils import cast_df_with_schema
from utils.db_utils import match_has_events, get_all_player_ids
from normalizers.event_type_normalizer import normalize_event_types

def build_raw_event_df(events_list):
    """
    Converts a list of event dicts to a standardized DataFrame.
    """
    if not events_list:
        return pd.DataFrame(columns=[
            'match_id', 'event_type', 'minute',
            'main_player_id', 'extra_player_id', 'team_id'
        ])
    df = pd.DataFrame(events_list)
    df['main_player_id'] = df['player_id']
    df = df.drop(columns=['player_id'])
    cols = ['match_id', 'event_type', 'minute', 'main_player_id', 'extra_player_id', 'team_id']
    return df[cols]

def cast_events_df(df, schema_path):
    """
    Casts DataFrame columns according to the schema.
    """
    return cast_df_with_schema(df, schema_path)

def validate_event_minutes(df, min_allowed=0, max_allowed=150, drop_invalid=True, verbose=True):
    """
    Validates and (optionally) drops events with minute outside allowed range.
    """
    invalid_mask = (df['minute'] < min_allowed) | (df['minute'] > max_allowed)
    if invalid_mask.any():
        if verbose:
            print(f"Warning: {invalid_mask.sum()} events with minute out of [{min_allowed}, {max_allowed}].")
            print(df.loc[invalid_mask, ['match_id', 'event_type', 'minute']])
        if drop_invalid:
            df = df.loc[~invalid_mask].copy()
            if verbose:
                print(f"Dropped {invalid_mask.sum()} invalid events.")
    elif verbose:
        print("All event minutes are within the valid range.")
    return df

def filter_events_new_matches(conn, events_df):
    """
    Keeps only events whose match_id has no events registered in the DB.
    """
    if events_df.empty:
        return events_df
    new_events_mask = events_df['match_id'].apply(lambda mid: not match_has_events(conn, mid))
    num_skipped = (~new_events_mask).sum()
    if num_skipped > 0:
        print(f"Skipped {num_skipped} matches (already have events in DB).")
    return events_df.loc[new_events_mask].copy()

def build_event_entity(
    conn,
    events_list,
    schema_path="pipeline/config/event_schema.json",
    validate_minutes=True,
    minute_max=150
):
    """
    Orchestrates the event building pipeline:
    - Builds raw event DataFrame.
    - Filters out events for matches that already have events in DB.
    - Casts types and validates minutes.

    Returns:
        pd.DataFrame: Ready-to-insert events DataFrame.
    """
    df = build_raw_event_df(events_list)
    if df.empty:
        return df
    df = filter_events_new_matches(conn, df)
    if df.empty:
        print("No new events to insert.")
        return df
    df = cast_events_df(df, schema_path)
    if validate_minutes and not df.empty:
        df = validate_event_minutes(df, max_allowed=minute_max)
    df = df.fillna(0)
    df = normalize_event_types(df)
    player_ids_set = get_all_player_ids(conn)
    df = df[df['main_player_id'].isin(player_ids_set)]
    return df
