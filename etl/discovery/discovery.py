from __future__ import annotations
from typing import List, Dict, Any
from psycopg2.extensions import connection as PGConnection

CHECKPOINT_NAME: str = "max_match_id_processed"

def get_last_checkpoint(conn: PGConnection) -> int:
    """
    Obtiene el último valor de checkpoint para el ETL.

    Actualmente usamos un único checkpoint:
      - checkpoint_name = 'max_match_id_processed'
      - last_value = match_id máximo procesado de forma exitosa

    Args:
        conn: Conexión psycopg2 ya abierta.

    Returns:
        int: Último match_id procesado, o 0 si aún no existe el checkpoint.
    """
    query: str = """
        SELECT COALESCE(
            (SELECT last_value::int
             FROM etl.checkpoint
             WHERE checkpoint_name = %s),
            0
        ) AS last_match_id
    """

    with conn.cursor() as cur:
        cur.execute(query, (CHECKPOINT_NAME,))
        row: Dict[str, Any] = cur.fetchone()

    last_id: int = int(row["last_match_id"])
    return last_id


def update_checkpoint(conn: PGConnection, new_max_match_id: int) -> None:
    """
    Actualiza el checkpoint con el nuevo match_id máximo procesado.

    Usa un upsert sobre etl.checkpoint para mantener un único registro
    por checkpoint_name.

    Args:
        conn: Conexión psycopg2 ya abierta (se espera que el caller maneje la transacción).
        new_max_match_id: Nuevo valor máximo de match_id procesado en este run/batch.

    Returns:
        None
    """
    query: str = """
        INSERT INTO etl.checkpoint(checkpoint_name, last_value, updated_at, note)
        VALUES (%s, %s, now(), 'updated by ETL')
        ON CONFLICT (checkpoint_name)
        DO UPDATE SET
            last_value = EXCLUDED.last_value,
            updated_at = EXCLUDED.updated_at,
            note       = EXCLUDED.note
    """

    with conn.cursor() as cur:
        cur.execute(query, (CHECKPOINT_NAME, str(new_max_match_id)))


def discover_pending_matches(conn: PGConnection, batch_size: int) -> List[int]:
    """
    Descubre qué partidos están pendientes por procesar.

    Criterios:
      - Existen en raw.match.
      - NO existen todavía en core.match.
      - Tienen match_id > checkpoint actual (modo incremental).

    El resultado está limitado por batch_size para procesar en lotes.

    Args:
        conn: Conexión psycopg2 ya abierta.
        batch_size: Tamaño máximo del lote de match_id a devolver.

    Returns:
        List[int]: Lista de match_id pendientes, ordenados de menor a mayor.
    """
    last_id: int = get_last_checkpoint(conn)

    query: str = """
        SELECT rm.match_id
        FROM raw.match AS rm
        LEFT JOIN core.match AS m
          ON m.match_id = rm.match_id
        WHERE m.match_id IS NULL
          AND rm.match_id > %s
        ORDER BY rm.match_id
        LIMIT %s
    """

    with conn.cursor() as cur:
        cur.execute(query, (last_id, batch_size))
        rows: List[Dict[str, Any]] = cur.fetchall()

    pending_ids: List[int] = [int(r["match_id"]) for r in rows]
    return pending_ids
