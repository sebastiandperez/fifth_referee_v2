import os
import json
def replace(text):
    """
    Reemplaza caracteres especiales y espacios en blanco por guiones bajos.
    Parametro: text (str)
    Retorna: text (str) con los caracteres reemplazados.
    """
    text = text.lower()
    text = text.replace("á", "a")
    text = text.replace("é", "e")
    text = text.replace("í", "i")
    text = text.replace("ó", "o")
    text = text.replace("ú", "u")
    text = text.replace("Á", "A")
    text = text.replace("É", "E")
    text = text.replace("Í", "I")
    text = text.replace("Ó", "O")
    text = text.replace("Ú", "U")
    text = text.replace("ñ", "n")
    text = text.replace("Ñ", "N")
    text = text.replace(" ", "_")
    text = text.replace("(", "")
    text = text.replace(")", "")
    return text

def load_schema_types(schema_path):
    with open(schema_path, "r") as f:
        schema = json.load(f)
    return schema

def cast_df_with_schema(df, schema_path):
    dtype_dict = load_schema_types(schema_path)
    return df.astype(dtype_dict)

def extract_and_flatten(results, key):
    return [item for result in results for item in result.get(key, [])]

def load_event_type_map(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_unique_stat_names(player_stats):
    """
    Returns a sorted list of unique stat_name values in player_stats.
    
    player_stats: list of dicts with 'stat_name' key
    """
    stat_names = {stat['stat_name'] for stat in player_stats}
    return sorted(stat_names)
import re

def standardize_basic_stats_columns(df):
    """
    Renames normalized columns from <base>_completed/<base>_total
    to <base> (for _completed) and <base>_total (for _total),
    matching loader/database expectation.
    """
    new_columns = {}
    # List of stat bases you want to standardize (add/remove as needed)
    bases = [
        'passes_completed',
        'aerial_duels_won',
        'ground_duels_won'
    ]

    for base in bases:
        completed_col = f"{base}_completed"
        total_col = f"{base}_total"

        # For <base>_completed → <base>
        if completed_col in df.columns:
            new_columns[completed_col] = base
        # For <base>_total → replace _completed with _total in base name
        if total_col in df.columns:
            new_columns[total_col] = base.replace('completed', 'total').replace('won', 'total')

    return df.rename(columns=new_columns)
