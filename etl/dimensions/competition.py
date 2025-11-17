from __future__ import annotations

import re
from typing import Any, Dict, Optional

try:
    from psycopg2.extensions import connection as PGConnection
except ImportError:  # pragma: no cover - allows running unit tests without psycopg2
    PGConnection = Any  # type: ignore

from .exceptions import MissingDimensionData


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^0-9a-z]+", "_", value.lower()).strip("_")
    return normalized


class CompetitionResolver:
    """Resolves raw competition strings into reference.competition IDs."""

    def __init__(self, mapping: Optional[Dict[str, int]] = None) -> None:
        self._explicit = {_slugify(k): int(v) for k, v in (mapping or {}).items()}
        self._cache: Dict[str, int] = {}
        self._db_cache: Optional[Dict[str, int]] = None

    def resolve(self, conn: PGConnection, raw_competition: str) -> int:
        slug = _slugify(raw_competition)
        if slug in self._cache:
            return self._cache[slug]

        if slug in self._explicit:
            comp_id = self._explicit[slug]
            self._cache[slug] = comp_id
            return comp_id

        db_map = self._load_db_map(conn)
        if slug not in db_map:
            raise MissingDimensionData(
                f"Competition '{raw_competition}' is not mapped to reference.competition"
            )

        comp_id = db_map[slug]
        self._cache[slug] = comp_id
        return comp_id

    def _load_db_map(self, conn: PGConnection) -> Dict[str, int]:
        if self._db_cache is not None:
            return self._db_cache

        with conn.cursor() as cur:
            cur.execute(
                "SELECT competition_id, competition_name FROM reference.competition"
            )
            rows = cur.fetchall()

        db_map: Dict[str, int] = {}
        for row in rows:
            slug = _slugify(row["competition_name"])
            db_map[slug] = row["competition_id"]

        self._db_cache = db_map
        return db_map
