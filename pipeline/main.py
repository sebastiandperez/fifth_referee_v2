from config.config_loader import load_config
from utils.file_utils import build_matchday_queues
from utils.utils import reemplazar
# from utils.db_utils import get_competition_id, get_season_id

if __name__ == "__main__":
    config = load_config("config/config.json")
    json_data_root = config["json_data_root"]

    competition_name = reemplazar(input("Competition name: "))
    season_label = reemplazar(input("Season label (e.g., 2024_2025): "))

    queue_jornadas = build_matchday_queues(json_data_root, competition_name, season_label)
    print(f"Found {queue_jornadas.qsize()} jornadas.")

