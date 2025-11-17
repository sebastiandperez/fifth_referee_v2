from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from psycopg2.extensions import connection as PGConnection

from etl.db.connection import get_connection


@contextmanager
def db_connection() -> Iterator[PGConnection]:
    """
    Context manager para una conexión de DB.

    Ejemplo:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
    """
    conn: PGConnection = get_connection()
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def transaction(conn: PGConnection) -> Iterator[None]:
    """
    Context manager para manejar una transacción explícita.

    - Hace commit si el bloque interior termina sin excepción.
    - Hace rollback si se lanza una excepción.

    Ejemplo:
        with db_connection() as conn:
            with transaction(conn):
                # todas estas operaciones van en 1 transacción
                cur = conn.cursor()
                cur.execute(...)
    """
    try:
        yield
        conn.commit()
    except Exception:
        conn.rollback()
        raise
