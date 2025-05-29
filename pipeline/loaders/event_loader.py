from .base_loader import BaseLoader

class EventLoader(BaseLoader):
    def __init__(self, conn):
        super().__init__(conn, log_name="event_loader")

    def insert_events(self, event_df):
        """
        Inserts new events into core.event table.
        Only the relevant columns are inserted.

        Args:
            event_df (pd.DataFrame): DataFrame with required columns.
        """
        if event_df.empty:
            self.log_info("No new events to insert.")
            return

        required_cols = [
            'match_id',
            'event_type',
            'minute',
            'main_player_id',
            'extra_player_id',
            'team_id'
        ]
        missing = [col for col in required_cols if col not in event_df.columns]
        if missing:
            self.log_error(f"Missing columns in event_df: {missing}")
            raise ValueError(f"Missing columns in event_df: {missing}")

        filtered_df = event_df[required_cols]

        with self.conn.cursor() as cur:
            insert_query = f"""
                INSERT INTO core.event ({', '.join(required_cols)})
                VALUES ({', '.join(['%s'] * len(required_cols))})
                ON CONFLICT DO NOTHING
            """
            cur.executemany(insert_query, filtered_df.values.tolist())
        self.conn.commit()
        self.log_info(f"Inserted {len(filtered_df)} new events.")
