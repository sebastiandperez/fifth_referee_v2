from .base_loader import BaseLoader

from typing import Iterable, Tuple
import math

import pandas as pd
from psycopg2.extras import execute_values
import pandas as pd
class MatchLoader(BaseLoader):
    def __init__(self, conn):
        super().__init__(conn, log_name="match_loader")

    def insert_matches(
        self,
        match_df: pd.DataFrame,
        *,
        allowed_durations: Iterable[int] = (90, 120),
        stadium_maxlen: int | None = None,
        chunk_size: int = 1000,
        coerce_duration: bool = True,
    ) -> int:
        """
        Inserta filas en core.match, ignorando duplicados por match_id.
        - Coacciona duration a allowed_durations (por defecto {90,120}).
        - Deduplica por match_id dentro del DataFrame.
        - Inserta por lotes con execute_values.

        Returns:
            int: cantidad estimada de filas insertadas (rowcount agregado).
        """
        required_cols = [
            "match_id",
            "matchday_id",
            "local_team_id",
            "away_team_id",
            "local_score",
            "away_score",
            "duration",
            "stadium",
        ]

        # 0) DataFrame vacío
        if match_df is None or match_df.empty:
            self.log_info("No new matches to insert.")
            return 0

        # 1) Columnas requeridas
        missing = [c for c in required_cols if c not in match_df.columns]
        if missing:
            msg = f"Missing columns in match_df: {missing}"
            self.log_error(msg)
            raise ValueError(msg)

        df = match_df[required_cols].copy()

        # 2) Deduplicar por match_id (última gana)
        before = len(df)
        df = df.drop_duplicates(subset=["match_id"], keep="last")
        dupes = before - len(df)
        if dupes:
            self.log_info(f"Deduplicated {dupes} duplicate match_id rows in-memory.")

        # 3) Coaccionar duration
        allowed_set = set(int(x) for x in allowed_durations)

        def _coerce_dur(x) -> int:
            try:
                v = int(x)
            except Exception:
                # Fallback razonable
                return 90 if 90 in allowed_set else min(allowed_set) if allowed_set else 90
            # Heurística simple: ≥105 -> 120, 80–100 -> 90; luego clamp a dominio
            if v >= 105:
                v = 120
            elif 80 <= v <= 100:
                v = 90
            # Clamp final a dominio permitido
            if v not in allowed_set:
                # elige el permitido más cercano
                v = min(allowed_set, key=lambda a: abs(a - v)) if allowed_set else v
            return v

        if coerce_duration:
            mask_bad = ~df["duration"].astype(str).isin([str(x) for x in allowed_set])
            if mask_bad.any():
                # Loguea una muestra de los raros antes de corregir
                sample = df.loc[mask_bad, ["match_id", "duration"]].head(10).to_string(index=False)
                self.log_info(f"[WARN] Coercing out-of-domain durations. Sample:\n{sample}")
            df["duration"] = df["duration"].apply(_coerce_dur)

        # 4) Sanitizar stadium
        df["stadium"] = df["stadium"].astype(object)  # asegura tipo objeto
        df["stadium"] = df["stadium"].where(pd.notna(df["stadium"]), None)
        if stadium_maxlen:
            df["stadium"] = df["stadium"].apply(
                lambda s: (str(s)[:stadium_maxlen] if s is not None else None)
            )

        # 5) Convertir NaN→None y castear ints para psycopg2
        def _int_or_none(v):
            if v is None:
                return None
            # Pandas puede traer NaN/NA
            try:
                if isinstance(v, float) and math.isnan(v):
                    return None
            except Exception:
                pass
            try:
                return int(v)
            except Exception:
                return None

        df["match_id"] = df["match_id"].apply(_int_or_none)
        df["matchday_id"] = df["matchday_id"].apply(_int_or_none)
        df["local_team_id"] = df["local_team_id"].apply(_int_or_none)
        df["away_team_id"] = df["away_team_id"].apply(_int_or_none)
        df["local_score"] = df["local_score"].apply(_int_or_none)
        df["away_score"] = df["away_score"].apply(_int_or_none)
        df["duration"] = df["duration"].apply(_int_or_none)

        # Guardrail final: no permitas None en claves obligatorias
        for col in ["match_id", "matchday_id", "local_team_id", "away_team_id", "duration"]:
            bad = df[col].isna()
            if bad.any():
                sample = df.loc[bad, ["match_id", "matchday_id", "local_team_id", "away_team_id", "duration"]].head(10)
                msg = f"Nulls in required column '{col}'. Sample:\n{sample.to_string(index=False)}"
                self.log_error(msg)
                raise ValueError(msg)

        rows = list(df.itertuples(index=False, name=None))

        if not rows:
            self.log_info("No new matches to insert after cleaning.")
            return 0

        cols_sql = ", ".join(required_cols)
        template = "(" + ", ".join(["%s"] * len(required_cols)) + ")"
        sql = f"""
            INSERT INTO core.match ({cols_sql})
            VALUES %s
            ON CONFLICT (match_id) DO NOTHING
        """

        inserted = 0
        with self.conn.cursor() as cur:
            for i in range(0, len(rows), chunk_size):
                chunk = rows[i : i + chunk_size]
                # execute_values arma el VALUES (%s,%s,...) por lote
                execute_values(cur, sql, chunk, template=template, page_size=len(chunk))
                # rowcount suele reflejar filas insertadas (las omitidas por conflicto no suman)
                if cur.rowcount is not None and cur.rowcount > 0:
                    inserted += cur.rowcount

        self.log_info(f"Inserted approximately {inserted} new matches (out of {len(rows)} candidates).")
        return inserted

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
