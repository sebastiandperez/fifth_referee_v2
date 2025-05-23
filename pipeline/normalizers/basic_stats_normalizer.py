import re
import pandas as pd
import numpy as np


def cast_basic_stats_df(df):
    exclude_cols = {'match_id', 'player_id', 'position', 'minutes','touches', 'passes_completed_total'}
    df['touches'] = pd.to_numeric(df['touches'], errors='coerce').fillna(0). astype(np.int16)
    for col in df.columns:
        if col not in exclude_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(np.int8)
    if 'minutes' in df.columns:
        df['minutes'] = pd.to_numeric(df['minutes'], errors='coerce').fillna(0).astype(np.int16)
    return df

def normalize_basic_stats_df(df):
    if 'minutes' in df.columns:
        df['minutes'] = (
            df['minutes']
            .astype(str)
            .str.replace("'", "", regex=False)
            .str.extract(r'(\d+)')[0]
        )
        df['minutes'] = pd.to_numeric(df['minutes'], errors='coerce').fillna(0).astype(int)

    split_pattern = re.compile(r'(?P<completed>\d+)\s*/\s*(?P<total>\d+)')

    for col in df.columns:
        if df[col].dropna().astype(str).str.contains('/').any():
            completed = []
            total = []
            for val in df[col].astype(str):
                m = split_pattern.match(val)
                if m:
                    completed.append(int(m.group("completed")))
                    total.append(int(m.group("total")))
                else:
                    completed.append(0 if val == 'nan' else val)
                    total.append(0 if val == 'nan' else val)
            df[col + "_completed"] = completed
            df[col + "_total"] = total
            df.drop(columns=[col], inplace=True)

    for col in df.columns:
        if col not in ["match_id", "player_id", "position"]:
            try:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            except Exception:
                pass

    return df
