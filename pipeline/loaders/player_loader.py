from .base_loader import BaseLoader
from psycopg2.extras import execute_values
from psycopg2 import errors

class PlayerLoader(BaseLoader):
    def __init__(self, conn):
        super().__init__(conn, log_name="player_loader")

    def insert_players(self, players_df):
        """
        Inserts new players into reference.player table.
        Only players not already present (by player_id) will be inserted.

        Args:
            players_df (pd.DataFrame): Must have 'player_id' and 'player_name'.
        """
        if players_df.empty:
            self.log_info("No new players to insert.")
            return
        with self.conn.cursor() as cur:
            insert_query = """
            INSERT INTO reference.player (player_id, player_name)
            VALUES (%s, %s)
            ON CONFLICT (player_id) DO NOTHING
            """
            cur.executemany(insert_query, players_df[['player_id', 'player_name']].values.tolist())
        self.log_info(f"Inserted {len(players_df)} new players.")

    def insert_team_players(self, team_player_df):
        """
        Inserts (season_team_id, player_id, jersey_number) into registry.team_player.
        Only new pairs will be inserted.

        Args:
            team_player_df (pd.DataFrame): Must have 'season_team_id', 'player_id', 'jersey_number'.
        """
        if team_player_df.empty:
            self.log_info("No new team-player pairs to insert.")
            return
        with self.conn.cursor() as cur:
            insert_query = """
            INSERT INTO registry.team_player (season_team_id, player_id, jersey_number)
            VALUES (%s, %s, %s)
            ON CONFLICT (season_team_id, player_id) DO NOTHING
            """
            cur.executemany(insert_query, team_player_df[['season_team_id', 'player_id', 'jersey_number']].values.tolist())
        self.log_info(f"Inserted {len(team_player_df)} new team-player pairs.")



    # def insert_participations(self, participation_df):
    #     """
    #     Inserta participations (match_id, player_id, position, status) en core.participation.
    #     - Filtra en SQL filas con FKs inexistentes (no insertarlas).
    #     - ON CONFLICT (match_id, player_id) DO NOTHING.
    #     - Loguea cuántas se saltaron por FK y cuántas chocaron por conflicto.
    #     """
    #     if participation_df.empty:
    #         self.log_info("No new participations to insert.")
    #         return

    #     required_cols = ['match_id', 'player_id', 'position', 'status']
    #     missing = [c for c in required_cols if c not in participation_df.columns]
    #     if missing:
    #         msg = f"Missing columns in participation_df: {missing}"
    #         self.log_error(msg)
    #         raise ValueError(msg)

    #     rows = participation_df[required_cols].values.tolist()
    #     total = len(rows)

    #     # 1) Detectar filas inválidas (FK inexistente) sin romper:
    #     #    LEFT JOIN; si m.id o p.id es NULL, esa fila es inválida.
    #     bad_rows_sql = """
    #         WITH v(match_id, player_id, position, status) AS (
    #             VALUES %s
    #         )
    #         SELECT v.match_id, v.player_id, v.position, v.status
    #         FROM v
    #         LEFT JOIN core.match  m ON m.match_id = v.match_id
    #         LEFT JOIN reference.player p ON p.player_id = v.player_id
    #         WHERE m.match_id IS NULL OR p.player_id IS NULL
    #     """

    #     # 2) Insertar solo válidas (JOIN inner) con ON CONFLICT DO NOTHING
    #     insert_sql = """
    #         WITH v(match_id, player_id, position, status) AS (
    #             VALUES %s
    #         )
    #         INSERT INTO core.participation (match_id, player_id, position, status)
    #         SELECT v.match_id, v.player_id, v.position, v.status
    #         FROM v
    #         JOIN core.match  m ON m.match_id = v.match_id
    #         JOIN reference.player p ON p.player_id = v.player_id
    #         ON CONFLICT (match_id, player_id) DO NOTHING
    #     """

    #     try:
    #         with self.conn.cursor() as cur:
    #             # bad rows
    #             execute_values(cur, bad_rows_sql, rows, template="(%s,%s,%s,%s)", page_size=1000)
    #             bad = cur.fetchall()  # lista de tuplas inválidas
    #             bad_count = len(bad)

    #             # insert valid
    #             execute_values(cur, insert_sql, rows, template="(%s,%s,%s,%s)", page_size=1000)
    #             inserted = cur.rowcount  # filas que realmente se insertaron
    #         self.conn.commit()

    #         conflict_or_existing = (total - bad_count) - inserted  # válidas pero ya existían
    #         if bad_count:
    #             sample = bad[:20]
    #             self.log_warn(f"Skipping {bad_count} participations due to invalid FKs. Sample(20): {sample}")

    #         self.log_info(
    #             f"Participations batch -> received={total}, invalid_fks={bad_count}, "
    #             f"inserted={inserted}, skipped_conflicts={conflict_or_existing}"
    #         )

    #     except Exception as e:
    #         # Si algo raro falla (no FK), no reventamos el pipeline: registramos y seguimos
    #         self.conn.rollback()
    #         self.log_error(f"Unexpected error in insert_participations (filtered mode): {e}")



    def insert_participations(self, participation_df):
        """
        Inserta participations (match_id, player_id, position, status) en core.participation.
        - Filtra en SQL filas con FKs inexistentes (no insertarlas).
        - ON CONFLICT (match_id, player_id) DO NOTHING.
        - Loguea cuántas se saltaron por FK y cuántas chocaron por conflicto.
        """
        if participation_df is None or participation_df.empty:
            self.log_info("No new participations to insert.")
            return

        required_cols = ["match_id", "player_id", "position", "status"]
        missing = [c for c in required_cols if c not in participation_df.columns]
        if missing:
            msg = f"Missing columns in participation_df: {missing}"
            self.log_error(msg)
            raise ValueError(msg)

        rows = participation_df[required_cols].values.tolist()
        total = len(rows)

        # CTE simple, el tipado lo hace el template
        bad_rows_sql = """
            WITH v(match_id, player_id, position, status) AS (VALUES %s)
            SELECT v.match_id, v.player_id, v.position, v.status
            FROM v
            LEFT JOIN core.match        m ON m.match_id  = v.match_id
            LEFT JOIN reference.player  p ON p.player_id = v.player_id
            WHERE m.match_id IS NULL OR p.player_id IS NULL
        """

        insert_sql = """
            WITH v(match_id, player_id, position, status) AS (VALUES %s)
            INSERT INTO core.participation (match_id, player_id, position, status)
            SELECT v.match_id, v.player_id, v.position, v.status
            FROM v
            JOIN core.match        m ON m.match_id  = v.match_id
            JOIN reference.player  p ON p.player_id = v.player_id
            ON CONFLICT (match_id, player_id) DO NOTHING
        """

        # Cast explícito de enums
        tmpl = "(%s::bigint,%s::bigint,%s::reference.position_enum,%s::reference.status_enum)"

        try:
            with self.conn.cursor() as cur:
                # Filas inválidas (FKs que no existen)
                execute_values(cur, bad_rows_sql, rows, template=tmpl, page_size=1000)
                bad = cur.fetchall()
                bad_count = len(bad)

                # Insertar válidas
                execute_values(cur, insert_sql, rows, template=tmpl, page_size=1000)
                inserted = cur.rowcount

            self.conn.commit()

            conflicts = (total - bad_count) - inserted
            if bad_count:
                self.log_info(f"Skipping {bad_count} participations due to invalid FKs. Sample(20): {bad[:20]}")

            self.log_info(
                f"Participations batch -> received={total}, invalid_fks={bad_count}, "
                f"inserted={inserted}, skipped_conflicts={conflicts}"
            )

            return {
                "received": total,
                "invalid_fks": bad_count,
                "inserted": inserted,
                "skipped_conflicts": conflicts,
            }

        except Exception as e:
            self.conn.rollback()
            self.log_error(f"Unexpected error in insert_participations (filtered mode): {e}")
            raise



    def insert_player_block(self, player_df, team_player_df,participation_df):
        """
        Inserts players, team_players, participations, and basic_stats entities in a single transaction (atomic).
        """
        try:
            with self.conn:
                self.insert_players(player_df)
                self.insert_team_players(team_player_df)
                self.insert_participations(participation_df)
            self.log_info("All player entities inserted successfully.")
        except Exception as e:
            self.log_error(f"Error during player entity insertion: {e}")
            raise


