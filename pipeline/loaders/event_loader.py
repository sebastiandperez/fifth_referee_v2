from .base_loader import BaseLoader
import math
import pandas as pd

class EventLoader(BaseLoader):
    def __init__(self, conn):
        super().__init__(conn, log_name="event_loader")

    def _py(self, v):
        # pd.NA o NaN -> None
        if v is None:
            return None
        # cuidado: pd.isna(None) es True, por eso chequeo antes
        if isinstance(v, float) and math.isnan(v):
            return None
        try:
            # pd.isna cubre pd.NA y NaN
            if pd.isna(v):
                return None
        except Exception:
            pass
        # numpy -> tipos nativos
        try:
            import numpy as np
            if isinstance(v, np.integer):
                return int(v)
            if isinstance(v, np.floating):
                return float(v)
        except Exception:
            pass
        return v

    def insert_events(self, event_df):
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

        # 1) Asegura enteros para minute
        if 'minute' in event_df.columns:
            event_df['minute'] = event_df['minute'].round().astype('Int64')

        # 2) Convierte pd.NA -> None para columnas FK
        for c in ('main_player_id', 'extra_player_id', 'team_id'):
            if c in event_df.columns:
                # fuerza dtype object para permitir None
                event_df[c] = event_df[c].astype('object')
                # pd.NA / NaN -> None
                event_df.loc[event_df[c].isna(), c] = None

        filtered_df = event_df[required_cols]

        # 3) Construye filas puramente Python (sin pd.NA ni numpy raros)
        rows = [
            tuple(self._py(filtered_df.iloc[i, j]) for j in range(len(required_cols)))
            for i in range(len(filtered_df))
        ]

        with self.conn.cursor() as cur:
            insert_query = f"""
                INSERT INTO core.event ({', '.join(required_cols)})
                VALUES ({', '.join(['%s'] * len(required_cols))})
                ON CONFLICT DO NOTHING
            """
            cur.executemany(insert_query, rows)

        self.conn.commit()
        self.log_info(f"Inserted {len(rows)} new events.")
