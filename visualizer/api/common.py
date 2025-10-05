from __future__ import annotations
from typing import Any
from fastapi import HTTPException
from infrastructure.postgres.connection import get_conn  # ya lo tienes

def _get(row: Any, *keys: Any) -> Any:
    mapping = getattr(row, "_mapping", None)
    if mapping:
        for k in keys:
            if isinstance(k, str) and k in mapping:
                return mapping[k]
            if isinstance(k, int):
                # algunos drivers exponen por índice a través de mapping también
                try:
                    return list(mapping.values())[k]
                except Exception:
                    pass
    if isinstance(row, dict):
        for k in keys:
            if k in row:
                return row[k]
    for k in keys:
        if isinstance(k, int):
            try:
                return row[k]
            except Exception:
                pass
    for k in keys:
        if isinstance(k, str) and hasattr(row, k):
            return getattr(row, k)
    return None

def _ensure_season(season_id: int) -> None:
    sql = "SELECT 1 FROM core.season WHERE season_id = %s"
    with get_conn() as conn:
        row = conn.execute(sql, [season_id]).fetchone()
    if not row:
        raise HTTPException(404, detail="season not found")
