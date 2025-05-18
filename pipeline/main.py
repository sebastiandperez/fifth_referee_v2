from utils.file_utils import build_matchday_queues
from utils.utils import replace
from utils.db_utils import get_competition_id, get_season_id, get_connection, load_config, resolve_competition_and_season_ids
from utils.team_matching import match_teams_progressive
from batch.batch_json import BatchExtractor
from batch.multi_batch_extractor import MultiBatchExtractor
from builders.team_builder import build_team_dataframe_from_matches, build_teams_from_footdata_API, build_team_dataframe


if __name__ == "__main__":
    config = load_config("pipeline/config/config.json")
    json_data_root = config["json_data_root"]

    competition_name = "la_liga" ##replace(input("Competition name: "))
    season_label = "2024_2025"##replace(input("Season label (e.g., 2024_2025): "))

    competition_id, season_id = resolve_competition_and_season_ids(competition_name, season_label, config)
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
    
    build_team_dataframe(all_matches, competition_name, config['X-Auth-Token'])
