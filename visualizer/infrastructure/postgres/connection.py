# visualizer/infrastructure/postgres/connection.py
import json
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Any, Iterable

import psycopg
from psycopg.rows import dict_row

CONFIG_PATH = "/home/sp3767/Projects/fifth_referee_v2/pipeline/config"

def _resolve_config_file(path: str) -> Path:
    """Accept a file or a directory. If directory, try common filenames."""
    p = Path(path)
    if p.is_file():
        return p
    if p.is_dir():
        candidates: Iterable[Path] = (p / "config.json", p / "config")
        for c in candidates:
            if c.is_file():
                return c
        tried = ", ".join(str(c) for c in candidates)
        raise RuntimeError(
            f"Config directory {p} found, but no config file inside. "
            f"Tried: {tried}"
        )
    raise RuntimeError(f"Config path does not exist: {p}")

def _load_config(path: str = CONFIG_PATH) -> Dict[str, Any]:
    cfg_file = _resolve_config_file(path)
    try:
        text = cfg_file.read_text(encoding="utf-8")
    except Exception as e:
        raise RuntimeError(f"Failed reading config at {cfg_file}") from e
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON in config at {cfg_file}") from e

def _dsn_from_cfg(cfg: Dict[str, Any]) -> str:
    host = cfg["DB_HOST"]
    port = int(cfg.get("DB_PORT", 5432))
    name = cfg["DB_NAME"]
    user = cfg.get("DB_USER", "postgres")
    password = cfg.get("DB_PASSWORD") or ""
    auth = f"{user}:{password}" if password else user  # omit ":" when empty
    return f"postgresql://{auth}@{host}:{port}/{name}"

def get_dsn(path: str = CONFIG_PATH) -> str:
    return _dsn_from_cfg(_load_config(path))

@contextmanager
def get_conn(path: str = CONFIG_PATH):
    dsn = get_dsn(path)
    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        yield conn
