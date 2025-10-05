from utils.db_utils import get_connection, load_config

def initialize_pipeline(config_path="pipeline/config/config.json", competition=None, season=None):
    """
    Loads config, sets up DB connection and returns key pipeline variables.

    Returns:
        config, json_data_root, conn
    """
    config = load_config(config_path)
    json_data_root = config["json_data_root"]
    conn = get_connection(config)
    return config, json_data_root, conn
