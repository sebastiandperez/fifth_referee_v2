# tests/test_pg_connection_explicit_path.py
from pathlib import Path
try:
    from infrastructure.postgres.connection import get_conn, CONFIG_PATH, _resolve_config_file
except ImportError:
    from infrastructure.postgres.connection import get_conn, CONFIG_PATH, _resolve_config_file

def test_connection_select_1():
    # Skip if config file is missing inside the directory
    try:
        _resolve_config_file(CONFIG_PATH)
    except RuntimeError as e:
        import pytest
        pytest.skip(str(e))
    with get_conn() as conn:
        row = conn.execute("SELECT 1 AS one").fetchone()
        assert row["one"] == 1
