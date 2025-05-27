from .base_loader import BaseLoader

class TeamLoader(BaseLoader):
    def __init__(self, conn):
        super().__init__(conn, log_name="team_loader")

    def insert_teams(self, team_df):
        if team_df.empty:
            self.log_info("No new teams to insert.")
            return
        with self.conn.cursor() as cur:
            insert_query = """
                INSERT INTO reference.team (team_id, team_name, team_city, team_stadium)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (team_id) DO NOTHING
            """
            cur.executemany(insert_query, team_df[['team_id', 'team_name', 'team_city', 'team_stadium']].values.tolist())
        self.log_info(f"Inserted {len(team_df)} new teams.")

    def insert_season_teams(self, season_team_df):
        if season_team_df.empty:
            self.log_info("No new season-team pairs to insert.")
            return
        with self.conn.cursor() as cur:
            insert_query = """
                INSERT INTO registry.season_team (season_id, team_id)
                VALUES (%s, %s)
                ON CONFLICT (season_id, team_id) DO NOTHING
            """
            cur.executemany(insert_query, season_team_df[['season_id', 'team_id']].values.tolist())
        self.log_info(f"Inserted {len(season_team_df)} new season-team pairs.")

    def insert_team_block(self, team_df, season_team_df):
        """
        Inserts teams and season_team entities in a single transaction (atomic).
        """
        try:
            with self.conn:
                self.insert_teams(team_df)
                self.insert_season_teams(season_team_df)
            self.log_info("All team entities inserted successfully.")
        except Exception as e:
            self.log_error(f"Error during team entity insertion: {e}")
            raise
