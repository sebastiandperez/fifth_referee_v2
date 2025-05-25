from utils.db_utils import get_connection, load_config

def initialize_pipeline(config_path="pipeline/config/config.json", competition=None, season=None):
    """
    Loads config, sets up DB connection and returns key pipeline variables.
    Optionally allows for dynamic competition/season selection.

    Returns:
        config, json_data_root, conn, competition_name, season_label
    """
    config = load_config(config_path)
    json_data_root = config["json_data_root"]
    conn = get_connection(config)
    competition_name = competition or config.get("competition_name") or "la_liga"
    season_label = season or config.get("season_label") or "2024_2025"
    return config, json_data_root, conn, competition_name, season_label
