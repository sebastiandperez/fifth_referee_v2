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

    def insert_basic_stats(self, basic_stats_df):
        """
        Inserts new player basic stats into core.basic_stats table.
        Only rows not already present (by match_id, player_id) will be inserted.
        """
        if basic_stats_df.empty:
            self.log_info("No new basic stats to insert.")
            return

        required_cols = [
            'match_id', 'player_id', 'minutes', 'goals', 'assists', 'touches',
            'passes_total', 'passes_completed', 'ball_recoveries', 'possessions_lost',
            'aerial_duels_won', 'aerial_duels_total', 'ground_duels_won', 'ground_duels_total'
        ]
        missing = [col for col in required_cols if col not in basic_stats_df.columns]
        if missing:
            self.log_error(f"Missing columns in basic_stats_df: {missing}")
            raise ValueError(f"Missing columns in basic_stats_df: {missing}")

        values = basic_stats_df[required_cols].values.tolist()
        with self.conn.cursor() as cur:
            insert_query = """
            INSERT INTO core.basic_stats (
                match_id, player_id, minutes, goals, assists, touches,
                passes_total, passes_completed, ball_recoveries, possessions_lost,
                aerial_duels_won, aerial_duels_total, ground_duels_won, ground_duels_total
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (match_id, player_id) DO NOTHING
            """
            cur.executemany(insert_query, values)
        self.log_info(f"Inserted {len(values)} new basic stats.")

    def insert_match_block(self, match_df, participation_df, basic_stats_df):
        """
        Inserts matches, participations, and basic stats in a single transaction (atomic).
        """
        try:
            with self.conn:
                self.insert_matches(match_df)
                self.insert_participations(participation_df)
                self.insert_basic_stats(basic_stats_df)
            self.log_info("All match-related entities inserted successfully.")
        except Exception as e:
            self.log_error(f"Error during match entity insertion: {e}")
            raise
