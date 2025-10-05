import pandas as pd
import numpy as np
from utils.utils import cast_df_with_schema
from utils.db_utils import (
    # si tienes un “exists” por evento, úsalo; si no, comenta la línea
    # event_exists_in_db,
    get_all_player_ids
)
from normalizers.event_type_normalizer import normalize_event_types

OPTIONAL_FK_COLS = ("extra_player_id", "team_id")
REQUIRED_FK_COLS = ("main_player_id", )

def _nullify_sentinels(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = df[c].replace({0: None, 0.0: None, "0": None, "": None})
            if df[c].isna().any():
                # Asegura dtype "Int64" (nullable) para no forzar 0 al castear
                df[c] = df[c].astype("Int64")
    return df

def build_raw_event_df(events_list):
    if not events_list:
        return pd.DataFrame(columns=[
            'match_id', 'event_type', 'minute',
            'main_player_id', 'extra_player_id', 'team_id'
        ])
    df = pd.DataFrame(events_list)
    df['main_player_id'] = df['player_id']
    df = df.drop(columns=['player_id'])
    cols = ['match_id', 'event_type', 'minute', 'main_player_id', 'extra_player_id', 'team_id']
    return df[cols]

def cast_events_df(df, schema_path):
    # IMPORTANTE: tu schema debería usar tipos "nullable" para IDs (p. ej. pandas Int64)
    return cast_df_with_schema(df, schema_path)

def validate_event_minutes(df, min_allowed=0, max_allowed=150, drop_invalid=True, verbose=True):
    invalid_mask = (df['minute'] < min_allowed) | (df['minute'] > max_allowed)
    if invalid_mask.any():
        if verbose:
            print(f"Warning: {invalid_mask.sum()} events with minute out of [{min_allowed}, {max_allowed}].")
            print(df.loc[invalid_mask, ['match_id', 'event_type', 'minute']])
        if drop_invalid:
            df = df.loc[~invalid_mask].copy()
            if verbose:
                print(f"Dropped {invalid_mask.sum()} invalid events.")
    elif verbose:
        print("All event minutes are within the valid range.")
    return df

def _preflight_player_ids(conn, df):
    """Valida main/extra IDs. Si extra no existe, lo nulifica; si main no existe, descarta el evento."""
    if df.empty:
        return df
    catalog = get_all_player_ids(conn)

    # main_player_id es requerido: si no está en catálogo -> descartamos
    if "main_player_id" in df.columns:
        mask_main_ok = df["main_player_id"].isin(catalog)
        dropped = (~mask_main_ok).sum()
        if dropped:
            print(f"[events] Dropped {dropped} events due to unknown main_player_id.")
        df = df.loc[mask_main_ok].copy()

    # extra_player_id es opcional: si no está en catálogo y no es NA -> lo nulificamos
    if "extra_player_id" in df.columns:
        # Considera solo valores no nulos y >0
        mask_extra_bad = df["extra_player_id"].notna() & (df["extra_player_id"].astype("Int64") > 0) & (~df["extra_player_id"].isin(catalog))
        bad_count = mask_extra_bad.sum()
        if bad_count:
            print(f"[events] Nullified {bad_count} unknown extra_player_id.")
            df.loc[mask_extra_bad, "extra_player_id"] = pd.NA
    return df

# Si más adelante quieres evitar duplicados exactos contra DB, implementa esta función:
def _drop_exact_duplicates_in_df(df):
    # Duplicados dentro del propio batch
    key_cols = ["match_id", "event_type", "minute", "main_player_id", "extra_player_id", "team_id"]
    before = len(df)
    df = df.drop_duplicates(subset=key_cols).copy()
    after = len(df)
    if before != after:
        print(f"[events] Dropped {before-after} duplicated events in batch.")
    return df

def build_event_entity(
    conn,
    events_list,
    schema_path="pipeline/config/event_schema.json",
    validate_minutes=True,
    minute_max=150
):
    df = build_raw_event_df(events_list)
    if df.empty:
        return df

    # 1) normaliza tipos de evento
    df = normalize_event_types(df)

    # 2) casteo con schema (asegúrate de que IDs sean nullable Int64)
    df = cast_events_df(df, schema_path)

    # 3) Nulifica sentinelas (0/“0”/””) SOLO en FKs opcionales
    df = _nullify_sentinels(df, OPTIONAL_FK_COLS)

    # 4) Validación de minutos
    if validate_minutes and not df.empty:
        df = validate_event_minutes(df, max_allowed=minute_max)

    # 5) Preflight players: main requerido -> filtrar; extra opcional -> nulificar si no existe
    df = _preflight_player_ids(conn, df)

    # 6) (Opcional) Minimizamos duplicados en el propio batch
    df = _drop_exact_duplicates_in_df(df)

    # 7) NO uses un bloqueo por partido (match_has_events). Si quieres protección incremental,
    #    implementa un "exists por clave de evento" a nivel loader con ON CONFLICT o una unique parcial.
    return df
