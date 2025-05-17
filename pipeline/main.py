from utils.file_utils import build_matchday_queues
from utils.utils import replace
from utils.db_utils import get_competition_id, get_season_id, get_connection, load_db_config, resolve_competition_and_season_ids


if __name__ == "__main__":
    db_config = load_db_config("pipeline/config/config.json")
    json_data_root = db_config["json_data_root"]

    competition_name = replace(input("Competition name: "))
    season_label = replace(input("Season label (e.g., 2024_2025): "))

    competition_id, season_id = resolve_competition_and_season_ids(competition_name, season_label, db_config)

    print(f"ID's Competitor: {competition_id} ID's Season: {season_id}")
    queue_jornadas = build_matchday_queues(json_data_root, competition_name, season_label)
    print(f"Found {queue_jornadas.qsize()} jornadas.")