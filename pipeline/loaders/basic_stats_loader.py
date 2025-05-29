from .base_loader import BaseLoader

class BasicStatsLoader(BaseLoader):
    def __init__(self, conn):
        super().__init__(conn, log_name="basic_stats_loader")
  
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
