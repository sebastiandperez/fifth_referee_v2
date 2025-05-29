from .base_loader import BaseLoader

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

    def insert_participations(self, participation_df):
        """
        Inserts participations (match_id, player_id, position, status) into core.participation.
        Only new records will be inserted.
        """
        if participation_df.empty:
            self.log_info("No new participations to insert.")
            return

        required_cols = ['match_id', 'player_id', 'position', 'status']
        missing = [col for col in required_cols if col not in participation_df.columns]
        if missing:
            self.log_error(f"Missing columns in participation_df: {missing}")
            raise ValueError(f"Missing columns in participation_df: {missing}")

        with self.conn.cursor() as cur:
            insert_query = """
            INSERT INTO core.participation (match_id, player_id, position, status)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (match_id, player_id) DO NOTHING
            """
            cur.executemany(insert_query, participation_df[required_cols].values.tolist())
        self.log_info(f"Inserted {len(participation_df)} new participations.")

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


