import pandas as pd
from rapidfuzz import process, fuzz

def emparejar_equipos(df1, df2, columna_df1, columna_df2, umbral_similitud=50):
    """
    Empareja nombres de equipos de dos DataFrames usando RapidFuzz (token_sort_ratio).
    Devuelve un DataFrame con los nombres emparejados y la puntuación de similitud.

    Args:
        df1 (pd.DataFrame): Primer DataFrame que contiene nombres de equipos.
        df2 (pd.DataFrame): Segundo DataFrame con nombres de equipos.
        columna_df1 (str): Nombre de la columna en df1 con los nombres de equipos.
        columna_df2 (str): Nombre de la columna en df2 con los nombres de equipos.
        umbral_similitud (int): Valor mínimo de similitud para considerar una coincidencia (0-100).

    Returns:
        pd.DataFrame: DataFrame con los nombres emparejados y la puntuación de similitud.
    """
    resultados = []
    nombres_df2 = df2[columna_df2].tolist()

    for nombre1 in df1[columna_df1]:
        mejor_coincidencia = process.extractOne(
            nombre1, nombres_df2, scorer=fuzz.token_sort_ratio
        )
        if mejor_coincidencia and mejor_coincidencia[1] >= umbral_similitud:
            resultados.append({
                columna_df1: nombre1,
                columna_df2: mejor_coincidencia[0],
                'similitud': mejor_coincidencia[1]
            })
        else:
            # Puedes guardar casos no emparejados para revisión manual
            resultados.append({
                columna_df1: nombre1,
                columna_df2: None,
                'similitud': 0
            })

    return pd.DataFrame(resultados)
