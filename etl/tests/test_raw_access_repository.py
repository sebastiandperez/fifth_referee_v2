from __future__ import annotations

import unittest
from datetime import datetime, timezone

from etl.raw_access import (
    RawAccessRepository,
    RawMatchBundle,
    RawMatchRecord,
    RawParticipationRecord,
    RawPlayerStatRecord,
)


class _FakeCursor:
    def __init__(self, responses):
        self._responses = responses
        self._current = None

    def execute(self, *_args, **_kwargs):
        if not self._responses:
            raise AssertionError("No response configured for execute")
        self._current = self._responses.pop(0)

    def fetchone(self):
        return self._current.get("fetchone")

    def fetchall(self):
        return self._current.get("fetchall", [])

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _FakeConnection:
    def __init__(self, responses):
        self._responses = responses

    def cursor(self):
        return _FakeCursor(self._responses)


class RawAccessRepositoryTests(unittest.TestCase):
    def test_load_match_bundle(self):
        responses = [
            {"fetchone": _match_row()},
            {"fetchall": [_participation_row(), _participation_row(team_id=20)]},
            {"fetchall": [_stat_row(), _stat_row(player_id=3, stat_name="passes")]},
        ]
        repo = RawAccessRepository(_FakeConnection(responses))

        bundle = repo.load_match_bundle(123)

        self.assertIsNotNone(bundle)
        assert bundle  # for mypy
        self.assertEqual(bundle.match.match_id, 10)
        self.assertEqual(len(bundle.participations), 2)
        team_groups = bundle.participations_by_team()
        self.assertEqual(set(team_groups.keys()), {10, 20})
        stats_groups = bundle.stats_by_player()
        self.assertEqual(len(stats_groups[2]), 1)
        self.assertEqual(len(stats_groups[3]), 1)

    def test_match_bundle_grouping_helpers(self):
        bundle = RawMatchBundle(
            match=RawMatchRecord(
                match_id=1,
                competition="liga",
                season="2024_2025",
                matchday=1,
                local_team_id=10,
                away_team_id=20,
                local_score=None,
                away_score=None,
                stadium=None,
                duration=None,
                source_system=None,
                source_url=None,
                ran_at=None,
                raw_run_id="abc",
            ),
            participations=(
                RawParticipationRecord(1, 2, 10, None, None, None),
                RawParticipationRecord(1, 3, 20, None, None, None),
                RawParticipationRecord(1, 4, 10, None, None, None),
            ),
            stats=(
                RawPlayerStatRecord(1, 2, "goals", "1", 1.0, None, None),
                RawPlayerStatRecord(1, 3, "goals", "0", 0.0, None, None),
            ),
        )

        teams = bundle.participations_by_team()
        self.assertEqual(len(teams[10]), 2)
        self.assertEqual(len(teams[20]), 1)

        stats = bundle.stats_by_player()
        self.assertEqual(len(stats[2]), 1)
        self.assertEqual(len(stats[3]), 1)


def _match_row():
    return {
        "match_id": 10,
        "competition": "liga",
        "season": "2024_2025",
        "matchday": 3,
        "local_team_id": 10,
        "away_team_id": 20,
        "local_score": 2,
        "away_score": 1,
        "stadium": "A",
        "duration": 96,
        "source_system": "365",
        "source_url": None,
        "ran_at": datetime.now(timezone.utc),
        "raw_run_id": "run-123",
    }


def _participation_row(team_id: int = 10):
    return {
        "match_id": 10,
        "player_id": 2 if team_id == 10 else 3,
        "team_id": team_id,
        "jersey_number": 7,
        "position": "FW",
        "status": 1,
    }


def _stat_row(player_id: int = 2, stat_name: str = "goals"):
    return {
        "match_id": 10,
        "player_id": player_id,
        "stat_name": stat_name,
        "raw_value": "1",
        "value_numeric": 1.0,
        "value_ratio_num": None,
        "value_ratio_den": None,
    }


if __name__ == "__main__":
    unittest.main()
