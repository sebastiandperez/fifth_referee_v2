import pandas as pd
import json

def goalkeeper_normalizer(gk_df):
    with open('pipeline/config/stat_maps/goalkeeper_map.json', 'r', encoding='utf-8') as f:
        gk_map = json.load(f)
    columns = list(gk_map.keys())
    df_gk_filtered = gk_df[columns].copy()
    df_gk_filtered = split_n_m_column(df_gk_filtered, "Penales atajados", "Penales atajados", "Penales recibidos")
    return df_gk_filtered

def defender_normalizer(defender_df):
    with open('pipeline/config/stat_maps/defender_map.json', 'r', encoding='utf-8') as f:
        defender_map = json.load(f)
    columns = list(defender_map.keys())
    df_def_filtered = defender_df[columns].copy()
    df_def_filtered = split_n_m_column(df_def_filtered, "Barridas ganadas", "Barridas ganadas", "Barridas totales")
    df_def_filtered.to_csv("df.csv")
    return df_def_filtered

def midfielder_normalizer(midfielder_df):
    with open('pipeline/config/stat_maps/midfielder_map.json', 'r', encoding='utf-8') as f:
        midfielder_map = json.load(f)
    columns = list(midfielder_map.keys())
    midfielder_df = midfielder_df[columns].copy()
    cols_to_split = [
        ("Barridas ganadas", "Barridas ganadas", "Barridas totales"),
        ("Pases largos completados", "Pases largos completados", "Pases largos totales"),
        ("Regates", "Regates", "Regates totales"),
        ("Centros", "Centros", "Centros totales"),
    ]
    for orig, col_n, col_m in cols_to_split:
        midfielder_df = split_n_m_column(midfielder_df, orig, col_n, col_m)
    return midfielder_df

def forward_normalized(forward_df):
    with open('pipeline/config/stat_maps/forward_map.json', 'r', encoding='utf-8') as f:
        forward_map = json.load(f)
    columns = list(forward_map.keys())
    forward_df = forward_df[columns].copy()
    forward_df = split_n_m_column(forward_df, "Regates", "Regates", "Regates totales")
    col = forward_df["Goles"].fillna("0(0Pen)").astype(str)
    forward_df["Goles"] = col.str.extract(r"^(\d+)").astype('Int16')
    forward_df["Penalties anotados"] = col.str.extract(r"\((\d+)Pen\)").astype('Int16')
    return forward_df


def split_n_m_column(df, col_name, out_n, out_m, fill_value="0/0"):
    """
    Extrae los valores n y m de columnas tipo 'n/m (xx%)' y los asigna a dos columnas nuevas.
    - df: DataFrame a modificar
    - col_name: nombre de la columna tipo 'n/m (xx%)'
    - out_n: nombre de la nueva columna para n
    - out_m: nombre de la nueva columna para m
    - fill_value: valor por defecto si hay NaN
    """
    col = df[col_name].fillna(fill_value).astype(str)
    nm = col.str.extract(r"^(\d+/\d+)")
    split_cols = nm[0].str.split("/", expand=True)
    df.loc[:, out_n] = split_cols[0].astype('Int16')
    df.loc[:, out_m] = split_cols[1].astype('Int16')
    return df