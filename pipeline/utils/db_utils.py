import psycopg2
import json
import pandas as pd
from typing import List, Tuple, Optional
from dataclasses import dataclass

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

def get_participations_by_season(conn, season_id):
    """
    Calls the core.get_participations_by_season DB function
    and returns the result as a pandas DataFrame.
    """
    query = """
        SELECT * FROM core.get_participations_by_season(%s);
    """
    with conn.cursor() as cur:
        cur.execute(query, (season_id,))
        columns = [desc[0] for desc in cur.description]
        data = cur.fetchall()
    return pd.DataFrame(data, columns=columns)

def get_basic_stats_keys_by_season(conn, season_id):
    """
    Calls the core.get_basic_stats_keys_by_season function in the DB
    and returns a DataFrame with columns ['match_id', 'player_id'].
    """
    with conn.cursor() as cur:
        cur.execute("SELECT match_id, player_id FROM core.get_basic_stats_keys_by_season(%s)", (season_id,))
        rows = cur.fetchall()
    return pd.DataFrame(rows, columns=['match_id', 'player_id'])

def get_basic_stats_ids_by_season(conn, season_id):
    query = "SELECT * FROM core.get_basic_stats_ids_by_season(%s);"
    with conn.cursor() as cur:
        cur.execute(query, (season_id,))
        columns = [desc[0] for desc in cur.description]
        data = cur.fetchall()
    return pd.DataFrame(data, columns=columns)

def get_all_registered_basic_stat_ids(conn):
    query = "SELECT * FROM stats.get_all_registered_basic_stat_ids();"
    with conn.cursor() as cur:
        cur.execute(query)
        ids = [row[0] for row in cur.fetchall()]
    return set(ids)

COMP_TABLE = "reference.competition"
COMP_LABEL_COL = "competition_name"

SEASON_TABLE = "core.season"
SEASON_LABEL_COL = "season_label"

@dataclass(frozen=True)
class Choice:
    idx: int
    label: str

def _fetch_distinct_labels(conn, table: str, col: str) -> List[str]:
    sql = f"SELECT DISTINCT {col} FROM {table} WHERE {col} IS NOT NULL AND {col} <> '' ORDER BY {col} ASC;"
    with conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()
    return [r[0] for r in rows]

def _choose_from_list(title: str, options: List[str]) -> str:
    if not options:
        raise RuntimeError(f"No hay opciones para {title}.")
    items = [Choice(i+1, lbl) for i, lbl in enumerate(options)]
    while True:
        print(f"\n{title}")
        for it in items:
            print(f"  {it.idx:2d}. {it.label}")
        raw = input("> Selecciona por número o escribe texto para filtrar: ").strip()

        # elegir por índice
        if raw.isdigit():
            k = int(raw)
            if 1 <= k <= len(items):
                return items[k-1].label
            print("Índice fuera de rango. Intenta de nuevo.")
            continue

        # filtrar por substring (case-insensitive)
        q = raw.lower()
        filt = [it for it in items if q in it.label.lower()]
        if not filt:
            print("Sin coincidencias. Prueba otro filtro o un número.")
            continue
        # mostrar sólo filtradas y volver a pedir
        items = [Choice(i+1, it.label) for i, it in enumerate(filt)]

def ask_competition_and_season(conn) -> Tuple[str, str]:
    """
    1) Lista competitions (reference.competition.name) -> eliges una (competition_name)
    2) Lista seasons (core.season.label) -> eliges una (season_label)
    Retorna: (competition_name, season_label)
    """
    competitions = _fetch_distinct_labels(conn, COMP_TABLE, COMP_LABEL_COL)
    competition_name = _choose_from_list("Competencias disponibles", competitions)

    seasons = _fetch_distinct_labels(conn, SEASON_TABLE, SEASON_LABEL_COL)
    season_label = _choose_from_list("Temporadas disponibles", seasons)

    return competition_name, season_label

def fetch_min_match_and_max_matchday(conn, season_id: int) -> Tuple[Optional[int], Optional[int]]:
    """
    Retorna (min_match_id, max_matchday_number_representativo) para la season dada.

    - min_match_id: mínimo match_id en core.match JOIN core.matchday filtrado por season_id.
    - max_matchday_number_representativo:
        1) Cuenta partidos por matchday_number en la season.
        2) Toma el/los matchday_number con mayor conteo.
        3) Si hay empate, devuelve el máximo matchday_number entre esos.
    Si no hay datos, cualquiera puede ser None.
    """
    with conn.cursor() as cur:
        # 1) min(match_id) de la season (solo partidos de sus matchdays)
        cur.execute(
            """
            SELECT MIN(m.match_id) AS min_match_id
            FROM core.match m
            JOIN core.matchday md ON md.matchday_id = m.matchday_id
            WHERE md.season_id = %s;
            """,
            (season_id,)
        )
        row_min = cur.fetchone()
        min_match_id: Optional[int] = row_min[0] if row_min else None

        # 2) matchday_number "representativo": max entre los con mayor # de partidos
        cur.execute(
            """
            WITH counts AS (
                SELECT md.matchday_number, COUNT(m.match_id) AS cnt
                FROM core.matchday md
                JOIN core.match m ON m.matchday_id = md.matchday_id
                WHERE md.season_id = %s
                GROUP BY md.matchday_number
            )
            SELECT MAX(matchday_number)  -- "máximo entre los candidatos con mayor cnt"
            FROM counts
            WHERE cnt = (SELECT MAX(cnt) FROM counts);
            """,
            (season_id,)
        )
        row_max = cur.fetchone()
        max_matchday_number: Optional[int] = row_max[0] if row_max else None

    return min_match_id, max_matchday_number
