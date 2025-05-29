from .base_loader import BaseLoader

class MatchLoader(BaseLoader):
    def __init__(self, conn):
        super().__init__(conn, log_name="match_loader")

    def insert_matches(self, match_df):
        """
        Inserts matches into core.match table.
        Only matches not already present (by match_id) will be inserted.
        """
        if match_df.empty:
            self.log_info("No new matches to insert.")
            return

        required_cols = [
            'match_id',
            'matchday_id',
            'local_team_id',
            'away_team_id',
            'local_score',
            'away_score',
            'duration',
            'stadium'
        ]
        missing = [col for col in required_cols if col not in match_df.columns]
        if missing:
            self.log_error(f"Missing columns in match_df: {missing}")
            raise ValueError(f"Missing columns in match_df: {missing}")

        filtered_df = match_df[required_cols]
        with self.conn.cursor() as cur:
            insert_query = f"""
            INSERT INTO core.match ({', '.join(required_cols)})
            VALUES ({', '.join(['%s'] * len(required_cols))})
            ON CONFLICT (match_id) DO NOTHING
            """
            cur.executemany(insert_query, filtered_df.values.tolist())
        self.log_info(f"Inserted {len(filtered_df)} new matches.")

    def insert_match_block(self, match_df):
        """
        Inserts matches, participations, and basic stats in a single transaction (atomic).
        """
        try:
            with self.conn:
                self.insert_matches(match_df)
            self.log_info("All match-related entities inserted successfully.")
        except Exception as e:
            self.log_error(f"Error during match entity insertion: {e}")
            raise
