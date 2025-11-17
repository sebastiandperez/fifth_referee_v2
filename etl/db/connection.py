from __future__ import annotations

from typing import Optional

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import connection as PGConnection

from etl.config.settings import load_settings, Settings


_SETTINGS: Optional[Settings] = None


def _get_settings() -> Settings:
    global _SETTINGS
    if _SETTINGS is None:
        _SETTINGS = load_settings()
    return _SETTINGS


def get_connection() -> PGConnection:
    """
    Crea y devuelve una conexión nueva a PostgreSQL usando psycopg2.

    Usa:
      - settings.dsn como cadena de conexión.
      - RealDictCursor para que fetchone()/fetchall() devuelvan dicts.
    """
    settings = _get_settings()
    conn: PGConnection = psycopg2.connect(
        settings.dsn,
        cursor_factory=RealDictCursor,
    )
    return conn
