from __future__ import annotations

import unittest

from etl.dimensions.competition import CompetitionResolver
from etl.dimensions.exceptions import MissingDimensionData


class _FakeCursor:
    def __init__(self, rows):
        self._rows = rows

    def execute(self, *_args, **_kwargs):
        return None

    def fetchall(self):
        return self._rows

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeConnection:
    def __init__(self, rows):
        self._rows = rows

    def cursor(self):
        return _FakeCursor(self._rows)


class CompetitionResolverTests(unittest.TestCase):
    def test_uses_explicit_mapping_if_available(self):
        resolver = CompetitionResolver({"premier_league": 7})
        conn = _FakeConnection(rows=[])

        comp_id = resolver.resolve(conn, "Premier League")

        self.assertEqual(7, comp_id)

    def test_falls_back_to_database(self):
        rows = [{"competition_id": 9, "competition_name": "La Liga"}]
        resolver = CompetitionResolver()
        conn = _FakeConnection(rows=rows)

        comp_id = resolver.resolve(conn, "la liga")

        self.assertEqual(9, comp_id)

    def test_unknown_slug_raises(self):
        resolver = CompetitionResolver()
        conn = _FakeConnection(rows=[])

        with self.assertRaises(MissingDimensionData):
            resolver.resolve(conn, "unknown_competition")


if __name__ == "__main__":
    unittest.main()
