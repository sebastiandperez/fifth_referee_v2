from .base_loader import BaseLoader

class StatsLoader(BaseLoader):
    def __init__(self, conn):
        super().__init__(conn, log_name="stats_loader")

    def insert_goalkeepers(self, gk_df):
        """
        Inserts goalkeeper stats into the stats.goalkeeper_stats table.
        Only inserts rows not already present (by primary key).
        """
        if gk_df.empty:
            self.log_info("No new goalkeeper stats to insert.")
            return
        required_cols = [
            'basic_stats_id', 'Salvadas de Portero', 'Salvadas en el área', 'Goles recibidos',
            'Goles esperados al arco concedidos', 'Goles esperados evitados', 'Despeje con los puños',
            'Despejes por alto', 'Despejes', 'Penales atajados', 'Intercepciones', 'Regateado', 'Penales recibidos'
        ]
        missing = [col for col in required_cols if col not in gk_df.columns]
        if missing:
            self.log_error(f"Missing columns in goalkeeper_df: {missing}")
            raise ValueError(f"Missing columns in goalkeeper_df: {missing}")
        with self.conn.cursor() as cur:
            insert_query = """
            INSERT INTO stats.goalkeeper_stats 
            (basic_stats_id, goalkeeper_saves, saves_inside_box, goals_conceded, xg_on_target_against, goals_prevented,
            punches_cleared, high_claims, clearances, penalties_saved, interceptions, times_dribbled_past, penalties_received)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (basic_stats_id) DO NOTHING
            """
            cur.executemany(insert_query, gk_df[required_cols].values.tolist())
        self.log_info(f"Inserted {len(gk_df)} new goalkeeper stats.")

    def insert_defenders(self, def_df):
        """
        Inserts defender stats into the stats.defender_stats table.
        """
        if def_df.empty:
            self.log_info("No new defender stats to insert.")
            return
        required_cols = [
            'basic_stats_id', 'Barridas ganadas', 'Intercepciones', 'Despejes', 'Regateado',
            'Error que llevó al gol', 'Errores que terminan el disparo', 'Posesiones ganadas en el último tercio',
            'Faltas cometidas', 'Barridas totales'
        ]
        missing = [col for col in required_cols if col not in def_df.columns]
        if missing:
            self.log_error(f"Missing columns in defender_df: {missing}")
            raise ValueError(f"Missing columns in defender_df: {missing}")
        with self.conn.cursor() as cur:
            insert_query = """
            INSERT INTO stats.defender_stats
            (basic_stats_id , tackles_won, interceptions, clearances, times_dribbled_past,
            errors_leading_to_goal, errors_leading_to_shot, possessions_won_final_third,
            fouls_committed, tackles_total)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (basic_stats_id) DO NOTHING
            """
            cur.executemany(insert_query, def_df[required_cols].values.tolist())
        self.log_info(f"Inserted {len(def_df)} new defender stats.")

    def insert_midfielders(self, mid_df):
        """
        Inserts midfielder stats into the stats.midfielder_stats table.
        """
        if mid_df.empty:
            self.log_info("No new midfielder stats to insert.")
            return
        required_cols = [
            'basic_stats_id', 'Asistencias esperadas', 'Barridas ganadas', 'Centros', 'Faltas cometidas', 'Faltas recibidas',
            'Goles esperados', 'Goles esperados de remates al arco', 'Grandes chances', 'Grandes chances perdidas',
            'Grandes ocasiones convertidas', 'Intercepciones', 'Pases claves', 'Pases en el último tercio',
            'Pases hacia atrás', 'Pases largos completados', 'Pelotas al poste', 'Posesiones ganadas en el último tercio',
            'Regateado', 'Regates', 'Regates totales', 'Remates Fuera', 'Remates al arco', 'Total Remates',
            'Barridas totales', 'Pases largos totales', 'Centros totales'
        ]
        missing = [col for col in required_cols if col not in mid_df.columns]
        if missing:
            self.log_error(f"Missing columns in midfielder_df: {missing}")
            raise ValueError(f"Missing columns in midfielder_df: {missing}")
        with self.conn.cursor() as cur:
            insert_query = """
            INSERT INTO stats.midfielder_stats
            (basic_stats_id, expected_assists, tackles_won, crosses, fouls_committed, fouls_suffered, expected_goals,
            xg_from_shots_on_target, big_chances, big_chances_missed, big_chances_scored, interceptions, key_passes,
            passes_in_final_third, back_passes, long_passes_completed, woodwork, possessions_won_final_third,
            times_dribbled_past, dribbles_completed, dribbles_total, shots_off_target, shots_on_target, shots_total,
            tackles_total, long_passes_total, crosses_total)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (basic_stats_id) DO NOTHING
            """
            cur.executemany(insert_query, mid_df[required_cols].values.tolist())
        self.log_info(f"Inserted {len(mid_df)} new midfielder stats.")

    def insert_forwards(self, fwd_df):
        """
        Inserts forward stats into the stats.forward_stats table.
        """
        if fwd_df.empty:
            self.log_info("No new forward stats to insert.")
            return
        required_cols = [
            'basic_stats_id', 'Asistencias esperadas', 'Goles esperados', 'Goles esperados de remates al arco',
            'Total Remates', 'Remates al arco', 'Remates Fuera', 'Grandes chances', 'Grandes chances perdidas',
            'Grandes ocasiones convertidas', 'Penalties anotados', 'Penal fallado', 'Fueras de Juego', 'Pases claves',
            'Regates', 'Regateado', 'Faltas cometidas', 'Faltas recibidas', 'Pelotas al poste', 'Regates totales'
        ]
        missing = [col for col in required_cols if col not in fwd_df.columns]
        if missing:
            self.log_error(f"Missing columns in forward_df: {missing}")
            raise ValueError(f"Missing columns in forward_df: {missing}")
        with self.conn.cursor() as cur:
            insert_query = """
            INSERT INTO stats.forward_stats
            (basic_stats_id, expected_assists, expected_goals, xg_from_shots_on_target, shots_total, shots_on_target,
            shots_off_target, big_chances, big_chances_missed, big_chances_scored, penalties_won, penalties_missed,
            offside, key_passes, dribbles_completed, times_dribbled_past, fouls_committed, fouls_suffered, woodwork,
            dribbles_total)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (basic_stats_id) DO NOTHING
            """
            cur.executemany(insert_query, fwd_df[required_cols].values.tolist())
        self.log_info(f"Inserted {len(fwd_df)} new forward stats.")

    def insert_stats_block(self, goalkeeper_df, defender_df, midfielder_df, forward_df):
        """
        Inserts all specific stats entities (goalkeeper, defender, midfielder, forward) in a single transaction (atomic).
        No insertion order required.
        """
        try:
            with self.conn:
                self.insert_goalkeepers(goalkeeper_df)
                self.insert_defenders(defender_df)
                self.insert_midfielders(midfielder_df)
                self.insert_forwards(forward_df)
            self.log_info("All specific stats-related entities inserted successfully.")
        except Exception as e:
            self.log_error(f"Error during specific stats entity insertion: {e}")
            raise
