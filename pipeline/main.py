from utils.utils import replace
from utils.db_utils import resolve_competition_and_season_ids, get_all_player_ids
from loaders.loader import DataBaseLoader
from extractors.extract_raw_data import extract_all_entities
from setup import initialize_pipeline
from builders.build_match_entities import build_match_entities
from builders.build_player_entities import build_player_entities
from builders.event_builder import build_event_entity

if __name__ == "__main__":
    config, json_data_root, conn, competition_name, season_label = initialize_pipeline()
    competition_id, season_id = resolve_competition_and_season_ids(conn ,competition_name, season_label)
    print(f"ID's Competitor: {competition_id} ID's Season: {season_id}")

    all_matches, all_events, all_players, all_player_stats = extract_all_entities(json_data_root, competition_name, season_label)

    ## Working
    match_df, team_df, season_team_df = build_match_entities(conn, all_matches, competition_name, season_id, config['X-Auth-Token'], config)

    ## Working
    participation_df, team_player_df, player_df = build_player_entities(conn, all_players, match_df, season_id)

    ## Events
    event_df = build_event_entity(
    conn,
    all_events,
    schema_path="pipeline/config/event_schema.json"
)
    print(event_df)
    
    loader = DataBaseLoader(conn)
    loader.load_all_entities(
    team_df=team_df,
    player_df=player_df,
    match_df=match_df,
    season_team_df=season_team_df,
    team_player_df=team_player_df,
    participation_df=participation_df
)