# from config.config_loader import load_config
from utils.file_utils import build_matchday_queues
from utils.utils import replace
from utils.db_utils import get_competition_id, get_season_id, load_db_config, get_connection


if __name__ == "__main__":
    db_config = load_db_config("pipeline/config/config.json")
    json_data_root = db_config["json_data_root"]

    competition_name = replace(input("Competition name: "))
    season_label = replace(input("Season label (e.g., 2024_2025): "))

    queue_jornadas = build_matchday_queues(json_data_root, competition_name, season_label)
    print(f"Found {queue_jornadas.qsize()} jornadas.")