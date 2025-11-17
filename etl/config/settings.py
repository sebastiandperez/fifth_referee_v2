from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Settings:
    dsn: str
    batch_size: int
    etl_version: str
    log_sql: bool = False


_SETTINGS_CACHE: Optional[Settings] = None


def _get_env_int(name: str, default: int) -> int:
    raw: Optional[str] = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _get_env_bool(name: str, default: bool) -> bool:
    raw: Optional[str] = os.getenv(name)
    if raw is None:
        return default

    value = raw.strip().lower()
    if value in {"1", "true", "t", "yes", "y"}:
        return True
    if value in {"0", "false", "f", "no", "n"}:
        return False
    return default


def _build_dsn_from_parts() -> str:
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "postgres")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD")  # puede ser None

    if password:
        auth = f"{user}:{password}"
    else:
        auth = user

    return f"postgresql://{auth}@{host}:{port}/{name}"


def load_settings() -> Settings:
    global _SETTINGS_CACHE
    if _SETTINGS_CACHE is not None:
        return _SETTINGS_CACHE

    # Si el usuario define DB_DSN, respetamos eso.
    dsn_env = os.getenv("DB_DSN")
    if dsn_env:
        dsn = dsn_env
    else:
        # Si no, construimos el DSN a partir de las partes que da Docker.
        dsn = _build_dsn_from_parts()

    batch_size = _get_env_int("ETL_BATCH_SIZE", 100)
    etl_version = os.getenv("ETL_VERSION", "v1.0")
    log_sql = _get_env_bool("ETL_LOG_SQL", False)

    _SETTINGS_CACHE = Settings(
        dsn=dsn,
        batch_size=batch_size,
        etl_version=etl_version,
        log_sql=log_sql,
    )
    return _SETTINGS_CACHE
