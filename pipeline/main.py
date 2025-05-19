from utils.file_utils import build_matchday_queues
from utils.utils import replace, load_schema_types, cast_df_with_schema
from utils.db_utils import get_competition_id, get_season_id, get_connection, load_config, resolve_competition_and_season_ids, get_all_player_ids
from utils.match_utils import filter_new_matches_by_registered, build_clean_match_df,build_clean_match_df
from utils.team_matching import match_teams_progressive
from utils.registry_utils import build_season_team_df
from batch.batch_json import BatchExtractor
from batch.multi_batch_extractor import MultiBatchExtractor
from builders.team_builder import build_team_dataframe_from_matches, build_teams_from_footdata_API, build_team_dataframe, filter_new_teams
from utils.player_utils import build_clean_player_df, get_match_ids, build_team_player, build_player_df
from loaders.database_loader import DataBaseLoader

if __name__ == "__main__":
    config = load_config("pipeline/config/config.json")
    json_data_root = config["json_data_root"]
    conn = get_connection(config)
    competition_name = "la_liga" ##replace(input("Competition name: "))
    season_label = "2024_2025"##replace(input("Season label (e.g., 2024_2025): "))

    competition_id, season_id = resolve_competition_and_season_ids(conn ,competition_name, season_label)
    print(f"ID's Competitor: {competition_id} ID's Season: {season_id}")

    queue_matchdays = build_matchday_queues(json_data_root, competition_name, season_label)
    print(f"Found {queue_matchdays.qsize()} jornadas.")

    multi_extractor = MultiBatchExtractor(queue_matchdays, max_workers=7)
    results = multi_extractor.process_all_matchdays()

    all_matches, all_events, all_players, all_player_stats = [], [], [], []
    for result in results:
        all_matches.extend(result['match'])
        all_events.extend(result['events'])
        all_players.extend(result['players'])
        all_player_stats.extend(result['player_stats'])


    match_df = build_clean_match_df(conn, all_matches, season_id)
    total_teams_df = build_team_dataframe_from_matches(match_df)
    match_season_team = build_season_team_df(conn, total_teams_df,  season_id)
    incomplete_team_df = filter_new_teams(conn, total_teams_df)
    team_df = build_team_dataframe(incomplete_team_df, competition_name, config['X-Auth-Token'])
    print(match_season_team)

    unfiltered_player_df = build_clean_player_df(conn, all_players, match_df)
    participation_df = unfiltered_player_df.copy()
    drop_from_participation = ['team_id', 'player_name', 'jersey_number']
    participation_df.drop(columns=drop_from_participation, inplace=True)
    unfiltered_team_player_df = build_team_player(conn, unfiltered_player_df, season_id)
    drop_from_team_player = ['team_id', 'player_name', 'match_id', "position","status","team_id"]
    team_player_df = unfiltered_team_player_df.copy()
    team_player_df.drop(columns=drop_from_team_player, inplace=True)
    player_df = build_player_df(unfiltered_team_player_df, get_all_player_ids(conn))
    print(team_player_df.columns)
    

