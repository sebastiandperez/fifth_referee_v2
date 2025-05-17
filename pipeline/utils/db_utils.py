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
        port=db_config.get("DB_PORT"),
        database=db_config["DB_NAME"]
    )

def resolve_competition_and_season_ids(competition_name, season_label, db_config):
    """
    Abre la conexión, extrae competition_id y season_id y la cierra.
    Retorna (competition_id, season_id)
    """
    with get_connection(db_config) as conn:
        competition_id = get_competition_id(conn, competition_name)
        if not competition_id:
            raise ValueError(f"Competition '{competition_name}' not found in DB.")

        season_id = get_season_id(conn, competition_id, season_label)
        if not season_id:
            raise ValueError(f"Season '{season_label}' for competition '{competition_name}' not found.")

        return competition_id, season_id

def get_competition_id(conn, competition_name):
    with conn.cursor() as cur:
        cur.execute("SELECT reference.get_competition_id_by_name(%s)", (competition_name,))
        result = cur.fetchone()
        return result[0] if result else None

def get_season_id(conn, competition_id, season_label):
    with conn.cursor() as cur:
        cur.execute("SELECT core.get_season_id(%s, %s)", (season_label, competition_id))
        result = cur.fetchone()
        return result[0] if result else None


