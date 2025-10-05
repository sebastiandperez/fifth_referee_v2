from functools import lru_cache
from typing import Sequence, List

@lru_cache(maxsize=64)
def _has_column_cached(schema: str, table: str, column: str) -> bool:
    from .connection import get_conn
    q = """
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = %s AND table_name = %s AND column_name = %s
    """
    with get_conn() as conn:
        return bool(conn.execute(q, (schema, table, column)).fetchone())

def _has_column(conn, schema: str, table: str, column: str) -> bool:
    # keep signature the same; delegate to cached variant
    return _has_column_cached(schema, table, column)

# ---- Ports / Domain
from domain.ports import (
    CompetitionPort, SeasonPort, TeamPort, PlayerPort,
    MatchPort, StandingsPort, TeamAnalyticsPort,
)
from domain.entities.competition import Competition
from domain.entities.season import Season, SeasonTeam
from domain.entities.matchday import Matchday
from domain.entities.match import Match, Participation, Event
from domain.entities.player import Player
from domain.ids import (
    CompetitionId, SeasonId, MatchId, TeamId, PlayerId,
)

# ---- DB + mappers
from .connection import get_conn
from .mappers import (
    row_to_competition, row_to_season, row_to_matchday, row_to_player,
    row_to_season_team, row_to_match, row_to_participation, row_to_event,
)

# =============================================================================
# Internal helpers
# =============================================================================

def _has_column(conn, schema: str, table: str, column: str) -> bool:
    q = """
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = %s AND table_name = %s AND column_name = %s
    """
    return bool(conn.execute(q, (schema, table, column)).fetchone())

def _match_select(conn) -> str:
    """
    Build a SELECT that tolera drift de esquema:
      - kickoff_utc si existe; si no, NULL::timestamptz AS kickoff_utc
      - duration si existe; si no, NULL::int AS duration
      - alias local_* -> home_*
    """
    kickoff_sel = "m.kickoff_utc" if _has_column(conn, "core", "match", "kickoff_utc") else "NULL::timestamptz"
    duration_sel = "m.duration"   if _has_column(conn, "core", "match", "duration")     else "NULL::int"

    return f"""
    SELECT
      m.match_id,
      md.season_id,
      m.matchday_id,
      m.local_team_id  AS home_team_id,
      m.away_team_id,
      m.local_score    AS home_score,
      m.away_score     AS away_score,
      {duration_sel}   AS duration,
      {kickoff_sel}    AS kickoff_utc
    FROM core.match m
    JOIN core.matchday md ON md.matchday_id = m.matchday_id
    """

def _match_order_clause(conn) -> str:
    """
    Prefer round order by md.number if present; else fall back to md.matchday_id.
    Always tie-break by m.match_id for determinism.
    """
    if _has_column(conn, "core", "matchday", "number"):
        return " ORDER BY md.number ASC, m.match_id ASC"
    return " ORDER BY md.matchday_id ASC, m.match_id ASC"

# =============================================================================
# Catalog adapters
# =============================================================================

class PgCompetitionAdapter(CompetitionPort):
    def list_competitions(self) -> Sequence[Competition]:
        sql = """
        SELECT
          competition_id,
          competition_name AS name,
          continent::text  AS country
        FROM reference.competition
        """
        with get_conn() as conn:
            rows = conn.execute(sql).fetchall()
        return [row_to_competition(r) for r in rows]

    def list_seasons(self, competition_id: CompetitionId) -> Sequence[Season]:
        sql = """
        SELECT s.season_id, s.competition_id, s.season_label AS label
        FROM core.season s
        WHERE s.competition_id = %s
        ORDER BY s.season_id
        """
        with get_conn() as conn:
            rows = conn.execute(sql, (int(competition_id),)).fetchall()
        return [row_to_season(r) for r in rows]

class PgSeasonAdapter(SeasonPort):
    def get(self, season_id: SeasonId) -> Season:
        sql = "SELECT season_id, competition_id, season_label AS label FROM core.season WHERE season_id=%s"
        with get_conn() as conn:
            r = conn.execute(sql, (int(season_id),)).fetchone()
        if not r:
            raise KeyError(season_id)
        return row_to_season(r)

    def list_matchdays(self, season_id: SeasonId) -> Sequence[Matchday]:
        sql = """
        SELECT matchday_id, season_id, number
        FROM core.matchday
        WHERE season_id=%s
        ORDER BY COALESCE(number, matchday_id) ASC
        """
        with get_conn() as conn:
            rows = conn.execute(sql, (int(season_id),)).fetchall()
        return [row_to_matchday(r) for r in rows]

    def list_teams(self, season_id: SeasonId):
        """
        Minimal shape until a Team dataclass mapping is finalized.
        """
        sql = """
        SELECT t.team_id, t.team_name AS name
        FROM registry.season_team st
        JOIN reference.team t USING (team_id)
        WHERE st.season_id = %s
        ORDER BY t.team_id
        """
        with get_conn() as conn:
            rows = conn.execute(sql, (int(season_id),)).fetchall()
        return [(int(r["team_id"]), r["name"]) for r in rows]

    def list_season_teams(self, season_id: SeasonId) -> Sequence[SeasonTeam]:
        sql = """
        SELECT season_id, team_id, seed_number, status
        FROM registry.season_team
        WHERE season_id=%s
        """
        with get_conn() as conn:
            rows = conn.execute(sql, (int(season_id),)).fetchall()
        return [row_to_season_team(r) for r in rows]

class PgTeamAdapter(TeamPort):
    def get(self, team_id: TeamId):
        sql = "SELECT team_id, team_name AS name FROM reference.team WHERE team_id=%s"
        with get_conn() as conn:
            r = conn.execute(sql, (int(team_id),)).fetchone()
        if not r:
            raise KeyError(team_id)
        return (int(r["team_id"]), r["name"])

    def list_roster(self, team_id: TeamId):
        sql = """
        SELECT DISTINCT tp.player_id
        FROM registry.team_player tp
        JOIN registry.season_team st USING (season_team_id)
        WHERE st.team_id = %s
        ORDER BY tp.player_id
        """
        with get_conn() as conn:
            rows = conn.execute(sql, (int(team_id),)).fetchall()
        return [PlayerId(int(r["player_id"])) for r in rows]

class PgPlayerAdapter(PlayerPort):
    def get(self, player_id: PlayerId) -> Player:
        sql = """
        SELECT
          player_id,
          player_name AS name,
          position::text AS position,
          nationality
        FROM reference.player
        WHERE player_id=%s
        """
        with get_conn() as conn:
            r = conn.execute(sql, (int(player_id),)).fetchone()
        if not r:
            raise KeyError(player_id)
        return row_to_player(r)

# =============================================================================
# Matches / Standings / Analytics
# =============================================================================

class PgMatchAdapter(MatchPort, StandingsPort, TeamAnalyticsPort):
    def get(self, match_id: MatchId) -> Match:
        with get_conn() as conn:
            sql = _match_select(conn) + " WHERE m.match_id=%s"
            r = conn.execute(sql, (int(match_id),)).fetchone()
        if not r:
            raise KeyError(match_id)
        return row_to_match(r)

    def list_by_season(self, season_id: SeasonId, only_finalized: bool = False) -> Sequence[Match]:
        with get_conn() as conn:
            sql = _match_select(conn) + " WHERE md.season_id=%s"
            params = [int(season_id)]
            if only_finalized:
                sql += " AND m.local_score IS NOT NULL AND m.away_score IS NOT NULL"
            sql += _match_order_clause(conn)
            rows = conn.execute(sql, params).fetchall()
        return [row_to_match(r) for r in rows]

    def list_for_team(self, season_id: SeasonId, team_id: TeamId) -> Sequence[Match]:
        with get_conn() as conn:
            sql = _match_select(conn) + """
            WHERE md.season_id=%s
              AND (m.local_team_id=%s OR m.away_team_id=%s)
            """
            sql += _match_order_clause(conn)
            rows = conn.execute(sql, (int(season_id), int(team_id), int(team_id))).fetchall()
        return [row_to_match(r) for r in rows]

    def list_participations(self, match_id: MatchId) -> Sequence[Participation]:
        """
        Convocations with team & side inferred via the season roster.
        Minutes from core.basic_stats; starter from status='starter'.
        """
        sql = """
        WITH mm AS (
          SELECT m.match_id, m.local_team_id AS home_team_id, m.away_team_id, md.season_id
          FROM core.match m
          JOIN core.matchday md ON md.matchday_id = m.matchday_id
          WHERE m.match_id = %s
        )
        SELECT
          p.match_id,
          p.player_id,
          st.team_id,
          CASE WHEN st.team_id = mm.home_team_id THEN 'HOME' ELSE 'AWAY' END AS side,
          (p.status::text = 'starter') AS starter,
          COALESCE(bs.minutes, 0) AS minutes_played,
          p.position::text AS position_hint
        FROM core.participation p
        JOIN mm ON mm.match_id = p.match_id
        JOIN registry.team_player tp ON tp.player_id = p.player_id
        JOIN registry.season_team st ON st.season_team_id = tp.season_team_id
                                     AND st.season_id = mm.season_id
        LEFT JOIN core.basic_stats bs ON bs.match_id = p.match_id AND bs.player_id = p.player_id
        ORDER BY p.player_id
        """
        with get_conn() as conn:
            rows = conn.execute(sql, (int(match_id),)).fetchall()
        return [row_to_participation(r) for r in rows]

    def list_events(self, match_id: MatchId) -> Sequence[Event]:
        """
        core.event columns:
          event_id, match_id, event_type, minute, main_player_id, extra_player_id, team_id
        """
        sql = """
        SELECT
          e.match_id,
          e.minute,
          e.event_type::text AS event_type,
          e.team_id,
          e.main_player_id,
          e.extra_player_id
        FROM core.event e
        WHERE e.match_id=%s
        ORDER BY e.minute NULLS LAST, e.event_id
        """
        with get_conn() as conn:
            rows = conn.execute(sql, (int(match_id),)).fetchall()
        out: List[Event] = []
        for r in rows:
            evt = row_to_event(r, strict_events=False)  # filters unsupported types
            if evt:
                out.append(evt)
        return out

    # ---- Ports composed on top ----
    def list_finalized_matches(self, season_id: SeasonId) -> Sequence[Match]:
        return self.list_by_season(season_id, only_finalized=True)

    def list_results_for_team(self, season_id: SeasonId, team_id: TeamId) -> Sequence[Match]:
        return self.list_for_team(season_id, team_id)

    def list_matches_filtered(
        self,
        season_id: SeasonId,
        matchday: int | None = None,
        team_id: int | None = None,
        opponent_id: int | None = None,
        finalized: bool | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[Match]:
        with get_conn() as conn:
            base = _match_select(conn)
            where = ["md.season_id = %s"]
            params = [int(season_id)]

            if matchday is not None:
                where.append("md.number = %s" if _has_column(conn, "core", "matchday", "number") else "md.matchday_id = %s")
                params.append(int(matchday))

            if team_id is not None:
                where.append("(m.local_team_id = %s OR m.away_team_id = %s)")
                params.extend([int(team_id), int(team_id)])

            if opponent_id is not None:
                where.append("(m.local_team_id = %s OR m.away_team_id = %s)")
                params.extend([int(opponent_id), int(opponent_id)])

            if finalized is True:
                where.append("m.local_score IS NOT NULL AND m.away_score IS NOT NULL")
            elif finalized is False:
                where.append("m.local_score IS NULL OR m.away_score IS NULL")

            sql = f"""{base}
            WHERE {' AND '.join(where)}
            {_match_order_clause(conn)}
            LIMIT %s OFFSET %s"""
            params.extend([int(limit), int(offset)])

            rows = conn.execute(sql, params).fetchall()
        return [row_to_match(r) for r in rows]

    def list_matches_filtered(
        self,
        season_id: SeasonId,
        matchday: int | None = None,
        team_id: int | None = None,
        opponent_id: int | None = None,
        finalized: bool | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[Match]:
        with get_conn() as conn:
            base = _match_select(conn)
            where = ["md.season_id = %s"]
            params: list[int] = [int(season_id)]

            # matchday puede ser md.number si existe; si no, hacemos fallback a matchday_id “equivalente” (no perfecto)
            if matchday is not None:
                if _has_column(conn, "core", "matchday", "number"):
                    where.append("md.number = %s")
                    params.append(int(matchday))
                else:
                    # fallback conservador: aproxima con rango por id si es que tu UI lo usa poco
                    where.append("md.matchday_id = %s")
                    params.append(int(matchday))

            if team_id is not None:
                where.append("(m.local_team_id = %s OR m.away_team_id = %s)")
                params.extend([int(team_id), int(team_id)])

            if opponent_id is not None:
                where.append("(m.local_team_id = %s OR m.away_team_id = %s)")
                params.extend([int(opponent_id), int(opponent_id)])

            if finalized is True:
                where.append("m.local_score IS NOT NULL AND m.away_score IS NOT NULL")
            elif finalized is False:
                where.append("m.local_score IS NULL OR m.away_score IS NULL")

            sql = f"""{base}
            WHERE {' AND '.join(where)}
            {_match_order_clause(conn)}
            LIMIT %s OFFSET %s
            """
            params.extend([int(limit), int(offset)])

            rows = conn.execute(sql, params).fetchall()
        return [row_to_match(r) for r in rows]
