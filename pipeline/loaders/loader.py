class DataBaseLoader:
    """
    Loader class for inserting DataFrames into the database.
    Each method inserts a specific entity (teams, players, matches, season_team, team_player, participation).
    """

    def __init__(self, conn):
        """
        Initializes the loader with a database connection.

        Args:
            conn: An active database connection (e.g., psycopg2 connection).
        """
        self.conn = conn

    def insert_teams(self, team_df):
        """
        Inserts new teams into the reference.team table.
        Only teams not already present (by team_id) will be inserted.

        Args:
            team_df (pd.DataFrame): Must have at least 'team_id' and 'team_name'.
        """
        if team_df.empty:
            return
        with self.conn.cursor() as cur:
            insert_query = """
            INSERT INTO reference.team (team_id, team_name, team_city, team_stadium)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (team_id) DO NOTHING
            """
            cur.executemany(insert_query, team_df[['team_id', 'team_name', 'team_city', 'team_stadium']].values.tolist())
        self.conn.commit()

    def insert_players(self, players_df):
        """
        Inserts new players into reference.player table.
        Only players not already present (by player_id) will be inserted.

        Args:
            players_df (pd.DataFrame): Must have 'player_id' and 'player_name'.
        """
        if players_df.empty:
            return
        with self.conn.cursor() as cur:
            insert_query = """
            INSERT INTO reference.player (player_id, player_name)
            VALUES (%s, %s)
            ON CONFLICT (player_id) DO NOTHING
            """
            cur.executemany(insert_query, players_df[['player_id', 'player_name']].values.tolist())
        self.conn.commit()

    def insert_matches(self, match_df):
        """
        Inserts matches into core.match table.
        Only matches not already present (by match_id) will be inserted.

        Args:
            match_df (pd.DataFrame): DataFrame with at least the required match columns.
        """
        if match_df.empty:
            return

        # Define the exact columns needed for the DB (and in the correct order!)
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

        # Check all columns exist
        missing = [col for col in required_cols if col not in match_df.columns]
        if missing:
            raise ValueError(f"Missing columns in match_df: {missing}")

        # Select only the required columns
        filtered_df = match_df[required_cols]

        with self.conn.cursor() as cur:
            insert_query = f"""
            INSERT INTO core.match ({', '.join(required_cols)})
            VALUES ({', '.join(['%s'] * len(required_cols))})
            ON CONFLICT (match_id) DO NOTHING
            """
            cur.executemany(insert_query, filtered_df.values.tolist())
        self.conn.commit()


    def insert_season_teams(self, season_team_df):
        """
        Inserts (season_id, team_id) pairs into registry.season_team table.
        Only new pairs will be inserted.
        """
        if season_team_df.empty:
            return
        with self.conn.cursor() as cur:
            insert_query = """
            INSERT INTO registry.season_team (season_id, team_id)
            VALUES (%s, %s)
            ON CONFLICT (season_id, team_id) DO NOTHING
            """
            cur.executemany(insert_query, season_team_df[['season_id', 'team_id']].values.tolist())
        self.conn.commit()

    def insert_team_players(self, team_player_df):
        """
        Inserts (season_team_id, player_id, jersey_number) into registry.team_player.
        Only new pairs will be inserted.

        Args:
            team_player_df (pd.DataFrame): Must have 'season_team_id', 'player_id', 'jersey_number'.
        """
        if team_player_df.empty:
            return
        with self.conn.cursor() as cur:
            insert_query = """
            INSERT INTO registry.team_player (season_team_id, player_id, jersey_number)
            VALUES (%s, %s, %s)
            ON CONFLICT (season_team_id, player_id) DO NOTHING
            """
            cur.executemany(insert_query, team_player_df[['season_team_id', 'player_id', 'jersey_number']].values.tolist())
        self.conn.commit()

    def insert_participations(self, participation_df):
        """
        Inserts participations (match_id, player_id, position, status) into core.participation.
        Only new records will be inserted.

        Args:
            participation_df (pd.DataFrame): Must have 'match_id', 'player_id', 'position', 'status'.
        """
        if participation_df.empty:
            return
        with self.conn.cursor() as cur:
            insert_query = """
            INSERT INTO core.participation (match_id, player_id, position, status)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (match_id, player_id) DO NOTHING
            """
            cur.executemany(insert_query, participation_df[['match_id', 'player_id', 'position', 'status']].values.tolist())
        self.conn.commit()
        
    def insert_events(self, event_df):
        """
        Inserts new events into core.event table.
        Only the relevant columns are inserted.

        Args:
            event_df (pd.DataFrame): DataFrame with columns:
                ['match_id', 'event_type', 'minute', 'main_player_id', 'extra_player_id', 'team_id']
        """
        if event_df.empty:
            print("No new events to insert.")
            return

        required_cols = [
            'match_id',
            'event_type',
            'minute',
            'main_player_id',
            'extra_player_id',
            'team_id'
        ]

        # Check all required columns exist
        missing = [col for col in required_cols if col not in event_df.columns]
        if missing:
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
        print(f"Inserted {len(filtered_df)} new events into core.event.")

    def insert_basic_stats(self, basic_stats_df):
        """
        Inserts new player basic stats into core.basic_stats table.
        Only rows not already present (by match_id, player_id) will be inserted.

        Args:
            basic_stats_df (pd.DataFrame): DataFrame must have columns:
                'match_id', 'player_id', 'minutes', 'goals', 'assists',
                'touches', 'passes_total', 'passes_completed', 'ball_recoveries',
                'possessions_lost', 'aerial_duels_won', 'aerial_duels_total',
                'ground_duels_won', 'ground_duels_total'
        """
        if basic_stats_df.empty:
            return

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
        # Extrae solo las columnas necesarias y convierte a lista de listas
        values = basic_stats_df[
            [
                'match_id', 'player_id', 'minutes', 'goals', 'assists', 'touches',
                'passes_completed_total', 'passes_completed_completed', 'ball_recoveries', 'possessions_lost',
                'aerial_duels_won_completed', 'aerial_duels_won_total', 'ground_duels_won_completed', 'ground_duels_won_total'
            ]
        ].values.tolist()

        with self.conn.cursor() as cur:
            cur.executemany(insert_query, values)
        self.conn.commit()


    def load_all_entities(self, team_df, player_df, match_df, season_team_df, team_player_df, participation_df):
        """
        Loads all entities into the DB in the correct order.

        Args:
            team_df, player_df, match_df, season_team_df, team_player_df, participation_df: DataFrames to insert.
        """
        try:
            self.insert_teams(team_df)
            self.insert_players(player_df)
            self.insert_matches(match_df)
            self.insert_season_teams(season_team_df)
            self.insert_team_players(team_player_df)
            self.insert_participations(participation_df)
            self.insert_events(event_df)
            print("All entities inserted successfully.")
        except Exception as e:
            print("Error during entity insertion:", e)
            self.conn.rollback()
            raise
