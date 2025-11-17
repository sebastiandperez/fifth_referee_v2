from __future__ import annotations

from typing import Any, Dict, Optional

from psycopg2.extensions import connection as PGConnection

LOCK_KEY: int = 1_234_567_890
LOCK_NAME: str = "main_etl_lock"


def start_run(
    conn: PGConnection,
    trigger_source: str,
    etl_version: str,
    source_context: Optional[Dict[str, Any]] = None,
) -> int:
    query = """
        SELECT etl.start_run(
            trigger_source => %s,
            etl_version    => %s,
            source_context => %s
        ) AS run_id
    """
    with conn.cursor() as cur:
        cur.execute(query, (trigger_source, etl_version, source_context))
        row: Dict[str, Any] = cur.fetchone()
    run_id: int = int(row["run_id"])
    return run_id


def finish_run(
    conn: PGConnection,
    run_id: int,
    status: str,
    error_summary: Optional[str] = None,
) -> None:
    query = "SELECT etl.finish_run(%s, %s, %s)"
    with conn.cursor() as cur:
        cur.execute(query, (run_id, status, error_summary))


def register_match_status(
    conn: PGConnection,
    run_id: int,
    match_id: int,
    stage: str,
    status: str,
    tries: Optional[int] = None,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
    rows_inserted_core: Optional[int] = None,
    rows_updated_core: Optional[int] = None,
    rows_inserted_stats: Optional[int] = None,
    rows_updated_stats: Optional[int] = None,
) -> None:
    query = """
        SELECT etl.register_match_status(
            run_id              => %s,
            match_id            => %s,
            stage               => %s,
            status              => %s,
            tries               => %s,
            error_code          => %s,
            error_message       => %s,
            rows_inserted_core  => %s,
            rows_updated_core   => %s,
            rows_inserted_stats => %s,
            rows_updated_stats  => %s
        )
    """
    params = (
        run_id,
        match_id,
        stage,
        status,
        tries,
        error_code,
        error_message,
        rows_inserted_core,
        rows_updated_core,
        rows_inserted_stats,
        rows_updated_stats,
    )
    with conn.cursor() as cur:
        cur.execute(query, params)


def log_error(
    conn: PGConnection,
    run_id: Optional[int],
    run_match_id: Optional[int],
    match_id: Optional[int],
    stage: Optional[str],
    message: str,
    detail: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    query = """
        INSERT INTO etl.error_log(
            run_id, run_match_id, match_id, stage,
            created_at, message, detail, context
        )
        VALUES (%s, %s, %s, %s, now(), %s, %s, %s)
    """
    with conn.cursor() as cur:
        cur.execute(
            query,
            (run_id, run_match_id, match_id, stage, message, detail, context),
        )


def acquire_etl_lock(conn: PGConnection, owner: str, run_id: int) -> bool:
    with conn.cursor() as cur:
        # Paso 1: advisory lock
        cur.execute("SELECT pg_try_advisory_lock(%s) AS got_lock", (LOCK_KEY,))
        row = cur.fetchone()
        got_lock: bool = bool(row["got_lock"])
        if not got_lock:
            return False

        # Paso 2: registro en tabla etl.lock
        cur.execute(
            """
            INSERT INTO etl.lock(lock_name, acquired_at, run_id, owner)
            VALUES (%s, now(), %s, %s)
            ON CONFLICT (lock_name) DO NOTHING
            """,
            (LOCK_NAME, run_id, owner),
        )
        inserted: bool = cur.rowcount == 1

        if not inserted:
            # No pudimos registrar el lock en la tabla;
            # liberamos el advisory lock para no dejarlo colgado.
            cur.execute("SELECT pg_advisory_unlock(%s)", (LOCK_KEY,))
            return False

        return True


def release_etl_lock(conn: PGConnection) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT pg_advisory_unlock(%s)", (LOCK_KEY,))
        cur.execute(
            "DELETE FROM etl.lock WHERE lock_name = %s",
            (LOCK_NAME,),
        )
