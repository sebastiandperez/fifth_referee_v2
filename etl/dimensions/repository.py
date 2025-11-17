from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    from psycopg2.extensions import connection as PGConnection
except ImportError:  # pragma: no cover
    PGConnection = Any  # type: ignore

from .context import MatchdayInfo, SeasonInfo, SeasonTeamInfo, TeamPlayerInfo
from .exceptions import MissingDimensionData


RawMatchRow = Dict[str, object]
RawPlayerRow = Dict[str, object]


def fetch_raw_match(conn: PGConnection, match_id: int) -> RawMatchRow:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT match_id, competition, season, matchday,
                   local_team_id, away_team_id
            FROM raw.match
            WHERE match_id = %s
            """,
            (match_id,),
        )
        row = cur.fetchone()

    if row is None:
        raise MissingDimensionData(f"raw.match not found for match_id={match_id}")
    return row


def fetch_raw_players(conn: PGConnection, match_id: int) -> List[RawPlayerRow]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT match_id, player_id, team_id, jersey_number
            FROM raw.player_match
            WHERE match_id = %s
            """,
            (match_id,),
        )
        rows = cur.fetchall()

    return rows or []


def ensure_team_exists(conn: PGConnection, team_id: int) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT team_id FROM reference.team WHERE team_id = %s",
            (team_id,),
        )
        row = cur.fetchone()

    if row is None:
        raise MissingDimensionData(
            f"Team {team_id} does not exist in reference.team; load catalog data first."
        )


def ensure_player_exists(conn: PGConnection, player_id: int) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT player_id FROM reference.player WHERE player_id = %s",
            (player_id,),
        )
        row = cur.fetchone()

    if row is None:
        raise MissingDimensionData(
            f"Player {player_id} does not exist in reference.player; load catalog data first."
        )


def upsert_season(
    conn: PGConnection, competition_id: int, season_label: str
) -> SeasonInfo:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO core.season (competition_id, season_label)
            VALUES (%s, %s)
            ON CONFLICT (competition_id, season_label)
            DO UPDATE SET season_label = EXCLUDED.season_label
            RETURNING season_id, competition_id, season_label
            """,
            (competition_id, season_label),
        )
        row = cur.fetchone()

    return SeasonInfo(
        season_id=row["season_id"],
        competition_id=row["competition_id"],
        season_label=row["season_label"],
    )


def upsert_matchday(
    conn: PGConnection, season_id: int, matchday_number: int
) -> MatchdayInfo:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO core.matchday (season_id, matchday_number)
            VALUES (%s, %s)
            ON CONFLICT (season_id, matchday_number)
            DO UPDATE SET matchday_number = EXCLUDED.matchday_number
            RETURNING matchday_id, season_id, matchday_number
            """,
            (season_id, matchday_number),
        )
        row = cur.fetchone()

    return MatchdayInfo(
        matchday_id=row["matchday_id"],
        season_id=row["season_id"],
        matchday_number=row["matchday_number"],
    )


def upsert_season_team(
    conn: PGConnection, season_id: int, team_id: int
) -> SeasonTeamInfo:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO registry.season_team (season_id, team_id)
            VALUES (%s, %s)
            ON CONFLICT (season_id, team_id)
            DO UPDATE SET season_id = EXCLUDED.season_id
            RETURNING season_team_id, season_id, team_id
            """,
            (season_id, team_id),
        )
        row = cur.fetchone()

    return SeasonTeamInfo(
        season_team_id=row["season_team_id"],
        season_id=row["season_id"],
        team_id=row["team_id"],
    )


def upsert_team_player(
    conn: PGConnection, season_team_id: int, player_id: int, jersey_number: Optional[int]
) -> TeamPlayerInfo:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO registry.team_player (season_team_id, player_id, jersey_number)
            VALUES (%s, %s, %s)
            ON CONFLICT (season_team_id, player_id)
            DO UPDATE SET jersey_number = COALESCE(
                EXCLUDED.jersey_number,
                registry.team_player.jersey_number
            )
            RETURNING season_team_id, player_id, jersey_number
            """,
            (season_team_id, player_id, jersey_number),
        )
        row = cur.fetchone()

    return TeamPlayerInfo(
        season_team_id=row["season_team_id"],
        player_id=row["player_id"],
        jersey_number=row["jersey_number"],
    )
