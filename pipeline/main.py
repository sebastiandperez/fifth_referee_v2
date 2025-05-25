from utils.utils import replace, get_unique_stat_names
from utils.db_utils import resolve_competition_and_season_ids
from loaders.loader import DataBaseLoader
from extractors.extract_raw_data import extract_all_entities
from setup import initialize_pipeline
from builders.build_match_entities import build_match_entities
from builders.build_player_entities import build_player_entities
from builders.event_builder import build_event_entity
from builders.build_stats_entities import build_basic_stats_for_season
from builders.build_specific_stats_entities import build_specific_stats_df

if __name__ == "__main__":
    config, json_data_root, conn, competition_name, season_label = initialize_pipeline(competition='Primeira Liga', season='2024_2025')
    competition_id, season_id = resolve_competition_and_season_ids(conn ,competition_name, season_label)
    print(f"ID's Competitor: {competition_id} ID's Season: {season_id}")
    
    loader = DataBaseLoader(conn)
    all_matches, all_events, all_players, all_player_stats = extract_all_entities(json_data_root, competition_name, season_label)

    match_df, team_df, season_team_df = build_match_entities(conn, all_matches, competition_name, season_id, config['X-Auth-Token'], config)
    loader.load_match_entities(match_df, team_df, season_team_df)

    participation_df, team_player_df, player_df = build_player_entities(conn, all_players, match_df, season_id)
    event_df = build_event_entity(conn,  all_events, schema_path="pipeline/config/event_schema.json")
    basic_stats_df = build_basic_stats_for_season(conn, season_id, all_player_stats)
    loader.load_player_entities(participation_df, team_player_df, player_df, event_df, basic_stats_df)

    goalkeeper_df, defender_df, midfielder_df, forward_df = build_specific_stats_df(conn, season_id, all_player_stats)
    loader.load_stats_entities(goalkeeper_df, defender_df, midfielder_df, forward_df)