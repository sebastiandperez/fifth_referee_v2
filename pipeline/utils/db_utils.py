import psycopg2
import json

def load_db_config(config_path="credentials.json"):
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_connection(db_config):
    return psycopg2.connect(
        user=db_config["DB_USER"],
        password=db_config["DB_PASSWORD"],
        host=db_config["DB_HOST"],
        port=db_config.get("DB_PORT", 5432),   # Default port
        database=db_config["DB_NAME"]
    )

def get_competition_id(conn, competition_name):
    with conn.cursor() as cur:
        cur.execute("SELECT core.get_competition_id(%s)", (competition_name,))
        result = cur.fetchone()
        return result[0] if result else None

def get_season_id(conn, competition_id, season_label):
    with conn.cursor() as cur:
        cur.execute("SELECT core.get_season_id(%s, %s)", (season_label, competition_id))
        result = cur.fetchone()
        return result[0] if result else None
