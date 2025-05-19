class DataBaseLoader:
    """
    Loader class for inserting DataFrames into the database.
    Each method inserts a specific entity (teams, players, matches, season_team).
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
            INSERT INTO reference.team (team_id, team_name)
            VALUES (%s, %s)
            ON CONFLICT (team_id) DO NOTHING
            """
            cur.executemany(insert_query, team_df[['team_id', 'team_name']].values.tolist())
        self.conn.commit()

    def insert_players(self, players_df):
        """
        Inserts new players into the appropriate table.
        You must implement this logic based on your schema.

        Args:
            players_df (pd.DataFrame): Player info DataFrame.
        """
        # TODO: Implement player insertion logic
        pass

    def insert_matches(self, match_df):
        """
        Inserts matches into core.match table.
        Only matches not already present (by match_id) will be inserted.

        Args:
            match_df (pd.DataFrame): Columns must correspond to the match table.
        """
        if match_df.empty:
            return
        with self.conn.cursor() as cur:
            cols = match_df.columns.tolist()
            insert_query = f"""
            INSERT INTO core.match ({', '.join(cols)})
            VALUES ({', '.join(['%s'] * len(cols))})
            ON CONFLICT (match_id) DO NOTHING
            """
            cur.executemany(insert_query, match_df.values.tolist())
        self.conn.commit()

    def insert_season_teams(self, season_team_df):
        """
        Inserts (season_id, team_id) pairs into registry.season_team table.
        Only new pairs will be inserted.

        Args:
            season_team_df (pd.DataFrame): Must have 'season_id' and 'team_id'.
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

    def load_all(self, team_df, players_df, match_df, season_team_df):
        """
        Orchestrates insertion of all entities in order.
        If any step fails, rolls back the transaction.

        Args:
            team_df, players_df, match_df, season_team_df: DataFrames to insert.
        """
        try:
            self.insert_teams(team_df)
            self.insert_players(players_df)
            self.insert_matches(match_df)
            self.insert_season_teams(season_team_df)
            print("All data loaded successfully.")
        except Exception as e:
            print("Error during loading process:", e)
            self.conn.rollback()
            raise
