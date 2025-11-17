from __future__ import annotations

from typing import Any, Dict, Optional

try:
    from psycopg2.extensions import connection as PGConnection
except ImportError:  # pragma: no cover
    PGConnection = Any  # type: ignore

from etl.config.settings import Settings, load_settings

from .competition import CompetitionResolver
from .context import DimensionsContext, SeasonTeamInfo, TeamPlayerInfo
from .exceptions import MissingDimensionData
from .repository import (
    ensure_player_exists,
    ensure_team_exists,
    fetch_raw_match,
    fetch_raw_players,
    upsert_matchday,
    upsert_season,
    upsert_season_team,
    upsert_team_player,
)

_resolver: Optional[CompetitionResolver] = None


def _get_competition_resolver(settings: Settings) -> CompetitionResolver:
    global _resolver
    if _resolver is None:
        _resolver = CompetitionResolver(settings.competition_map)
    return _resolver


def upsert_dimensions_for_match(
    conn: PGConnection, match_id: int, settings: Optional[Settings] = None
) -> DimensionsContext:
    """
    Garantiza que todas las dimensiones básicas estén creadas para el match_id dado.
    """
    settings = settings or load_settings()
    resolver = _get_competition_resolver(settings)

    raw_match = fetch_raw_match(conn, match_id)
    raw_players = fetch_raw_players(conn, match_id)

    competition_id = resolver.resolve(conn, str(raw_match["competition"]))
    season_label = str(raw_match["season"])
    season = upsert_season(conn, competition_id, season_label)

    matchday_number = raw_match.get("matchday")
    if matchday_number is None:
        raise MissingDimensionData(f"raw.match.matchday is NULL for match_id={match_id}")
    matchday = upsert_matchday(conn, season.season_id, int(matchday_number))

    team_ids = {
        int(raw_match["local_team_id"]),
        int(raw_match["away_team_id"]),
    }
    team_ids.update(int(row["team_id"]) for row in raw_players)

    for team_id in team_ids:
        ensure_team_exists(conn, team_id)

    season_teams: Dict[int, SeasonTeamInfo] = {}
    for team_id in sorted(team_ids):
        season_team = upsert_season_team(conn, season.season_id, team_id)
        season_teams[team_id] = season_team

    team_players: Dict[int, TeamPlayerInfo] = {}
    for row in raw_players:
        player_id = int(row["player_id"])
        ensure_player_exists(conn, player_id)

        team_id = int(row["team_id"])
        season_team = season_teams.get(team_id)
        if season_team is None:
            raise MissingDimensionData(
                f"Team {team_id} referenced by raw.player_match is not linked to season {season.season_id}"
            )

        jersey = row.get("jersey_number")
        jersey_number = int(jersey) if jersey is not None else None

        team_player = upsert_team_player(
            conn,
            season_team_id=season_team.season_team_id,
            player_id=player_id,
            jersey_number=jersey_number,
        )
        team_players[player_id] = team_player

    return DimensionsContext(
        competition_id=competition_id,
        season=season,
        matchday=matchday,
        season_teams=season_teams,
        team_players=team_players,
    )
