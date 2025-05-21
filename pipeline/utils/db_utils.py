import psycopg2
import json
import pandas as pd
def load_config(config_path="credentials.json"):
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

def resolve_competition_and_season_ids(conn, competition_name, season_label):
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

def get_matchdays_id(conn, season_id):
    """
    Returns a DataFrame with matchday_id and matchday_number for the given season.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM core.get_matchday_ids_in_season(%s);", (season_id,))
        rows = cur.fetchall()
    return pd.DataFrame(rows, columns=["matchday_id", "matchday"])

def get_matches_in_matchdays(conn, matchday_ids):
    with conn.cursor() as cur:
        cur.execute("SELECT match_id FROM core.get_matches_in_matchdays(%s)", (matchday_ids,))
        return [row[0] for row in cur.fetchall()]

def get_teams_in_season(conn, season_id):
    with conn.cursor() as cur:
        cur.execute("SELECT team_id FROM registry.get_teams_in_season(%s)", (season_id,))
        return [row[0] for row in cur.fetchall()]

def get_team_ids_in_season(conn, season_id):
    with conn.cursor() as cur:
        cur.execute("SELECT team_id FROM registry.get_team_ids_in_season(%s)", (season_id,))
        return [row[0] for row in cur.fetchall()]

def get_all_team_ids(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT team_id FROM reference.get_all_team_ids()")
        return [row[0] for row in cur.fetchall()]

def get_player_ids_by_match_ids(conn, match_ids):
    """
    Devuelve una lista de player_id que participaron en los match_id dados.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT player_id FROM core.get_player_ids_by_match_ids(%s)", 
            (match_ids,)
        )
        return [row[0] for row in cur.fetchall()]

def get_season_team_ids(conn, season_id, team_ids):
    """
    Devuelve una lista de season_team_id para una temporada y lista de team_id.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT season_team_id FROM registry.get_season_team_ids(%s, %s);",
            (season_id, team_ids)
        )
        return [row[0] for row in cur.fetchall()]

def get_all_player_ids(conn):
    """
    Devuelve una lista de todos los player_id existentes en reference.player.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT player_id FROM reference.get_all_player_ids();")
        return [row[0] for row in cur.fetchall()]

def get_player_ids_by_season_team_ids(conn, season_team_id_list):
    """
    Devuelve una lista de player_id para una lista de season_team_id.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT player_id FROM registry.get_player_ids_by_season_team_ids(%s)",
            (season_team_id_list,)
        )
        return [row[0] for row in cur.fetchall()]

def get_season_team_table(conn, season_id):
    """
    Retrieves the full registry.season_team table for a given season_id.

    Args:
        conn: Active DB connection (psycopg2).
        season_id (int): The season to filter.

    Returns:
        pd.DataFrame: DataFrame with columns ['season_team_id', 'team_id', 'season_id']
    """
    with conn.cursor() as cur:
        cur.execute("""
            SELECT season_team_id, team_id, season_id
            FROM registry.season_team
            WHERE season_id = %s
        """, (season_id,))
        rows = cur.fetchall()
    return pd.DataFrame(rows, columns=['season_team_id', 'team_id', 'season_id'])


def match_has_events(conn, match_id):
    """
    Calls the DB function to check if a match has any registered events.

    Args:
        conn: Active DB connection.
        match_id (int): The match to check.

    Returns:
        bool: True if at least one event exists for the match, else False.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT core.match_has_events(%s);", (match_id,))
        result, = cur.fetchone()
    return result
