from __future__ import annotations

from typing import Any, Iterable, List, Optional, Sequence, Tuple

try:
    from psycopg2.extensions import connection as PGConnection
except ImportError:  # pragma: no cover
    PGConnection = Any  # type: ignore

from .models import (
    RawMatchBundle,
    RawMatchRecord,
    RawParticipationRecord,
    RawPlayerStatRecord,
)


class RawAccessRepository:
    """
    Provides typed accessors for raw.match, raw.player_match y raw.player_match_stat.
    """

    def __init__(self, conn: PGConnection) -> None:
        self._conn = conn

    def load_match_bundle(self, match_id: int) -> Optional[RawMatchBundle]:
        match = self._fetch_match(match_id)
        if match is None:
            return None

        participations = self._fetch_participations(match_id)
        stats = self._fetch_stats(match_id)
        return RawMatchBundle(
            match=match,
            participations=tuple(participations),
            stats=tuple(stats),
        )

    def load_match_bundles(
        self, match_ids: Sequence[int]
    ) -> List[RawMatchBundle]:
        if not match_ids:
            return []

        matches = self._fetch_matches(match_ids)
        bundles: List[RawMatchBundle] = []
        parts_by_match = self._fetch_participations_grouped(match_ids)
        stats_by_match = self._fetch_stats_grouped(match_ids)

        for match in matches:
            bundles.append(
                RawMatchBundle(
                    match=match,
                    participations=tuple(parts_by_match.get(match.match_id, ())),
                    stats=tuple(stats_by_match.get(match.match_id, ())),
                )
            )
        return bundles

    # ------------------------------------------------------------
    # Internal fetchers
    # ------------------------------------------------------------

    def _fetch_match(self, match_id: int) -> Optional[RawMatchRecord]:
        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT match_id, competition, season, matchday,
                       local_team_id, away_team_id,
                       local_score, away_score,
                       stadium, duration,
                       source_system, source_url,
                       ran_at, raw_run_id
                FROM raw.match
                WHERE match_id = %s
                """,
                (match_id,),
            )
            row = cur.fetchone()

        return self._row_to_match(row) if row else None

    def _fetch_matches(self, match_ids: Sequence[int]) -> List[RawMatchRecord]:
        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT match_id, competition, season, matchday,
                       local_team_id, away_team_id,
                       local_score, away_score,
                       stadium, duration,
                       source_system, source_url,
                       ran_at, raw_run_id
                FROM raw.match
                WHERE match_id = ANY(%s)
                ORDER BY match_id
                """,
                (list(match_ids),),
            )
            rows = cur.fetchall()

        return [self._row_to_match(row) for row in rows]

    def _fetch_participations(self, match_id: int) -> List[RawParticipationRecord]:
        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT match_id, player_id, team_id,
                       jersey_number, position, status
                FROM raw.player_match
                WHERE match_id = %s
                """,
                (match_id,),
            )
            rows = cur.fetchall()

        return [self._row_to_participation(row) for row in rows]

    def _fetch_participations_grouped(
        self, match_ids: Sequence[int]
    ) -> dict[int, Tuple[RawParticipationRecord, ...]]:
        if not match_ids:
            return {}

        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT match_id, player_id, team_id,
                       jersey_number, position, status
                FROM raw.player_match
                WHERE match_id = ANY(%s)
                ORDER BY match_id
                """,
                (list(match_ids),),
            )
            rows = cur.fetchall()

        grouped: dict[int, List[RawParticipationRecord]] = {}
        for row in rows:
            part = self._row_to_participation(row)
            grouped.setdefault(part.match_id, []).append(part)
        return {k: tuple(v) for k, v in grouped.items()}

    def _fetch_stats(self, match_id: int) -> List[RawPlayerStatRecord]:
        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT match_id, player_id, stat_name,
                       raw_value, value_numeric,
                       value_ratio_num, value_ratio_den
                FROM raw.player_match_stat
                WHERE match_id = %s
                """,
                (match_id,),
            )
            rows = cur.fetchall()

        return [self._row_to_stat(row) for row in rows]

    def _fetch_stats_grouped(
        self, match_ids: Sequence[int]
    ) -> dict[int, Tuple[RawPlayerStatRecord, ...]]:
        if not match_ids:
            return {}

        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT match_id, player_id, stat_name,
                       raw_value, value_numeric,
                       value_ratio_num, value_ratio_den
                FROM raw.player_match_stat
                WHERE match_id = ANY(%s)
                ORDER BY match_id
                """,
                (list(match_ids),),
            )
            rows = cur.fetchall()

        grouped: dict[int, List[RawPlayerStatRecord]] = {}
        for row in rows:
            stat = self._row_to_stat(row)
            grouped.setdefault(stat.match_id, []).append(stat)
        return {k: tuple(v) for k, v in grouped.items()}

    # ------------------------------------------------------------
    # Row converters
    # ------------------------------------------------------------

    @staticmethod
    def _row_to_match(row: dict) -> RawMatchRecord:
        return RawMatchRecord(
            match_id=int(row["match_id"]),
            competition=str(row["competition"]),
            season=str(row["season"]),
            matchday=row.get("matchday"),
            local_team_id=int(row["local_team_id"]),
            away_team_id=int(row["away_team_id"]),
            local_score=row.get("local_score"),
            away_score=row.get("away_score"),
            stadium=row.get("stadium"),
            duration=row.get("duration"),
            source_system=row.get("source_system"),
            source_url=row.get("source_url"),
            ran_at=row.get("ran_at"),
            raw_run_id=str(row["raw_run_id"]),
        )

    @staticmethod
    def _row_to_participation(row: dict) -> RawParticipationRecord:
        jersey = row.get("jersey_number")
        return RawParticipationRecord(
            match_id=int(row["match_id"]),
            player_id=int(row["player_id"]),
            team_id=int(row["team_id"]),
            jersey_number=int(jersey) if jersey is not None else None,
            position=row.get("position"),
            status=row.get("status"),
        )

    @staticmethod
    def _row_to_stat(row: dict) -> RawPlayerStatRecord:
        return RawPlayerStatRecord(
            match_id=int(row["match_id"]),
            player_id=int(row["player_id"]),
            stat_name=str(row["stat_name"]),
            raw_value=str(row["raw_value"]),
            value_numeric=row.get("value_numeric"),
            value_ratio_num=row.get("value_ratio_num"),
            value_ratio_den=row.get("value_ratio_den"),
        )
