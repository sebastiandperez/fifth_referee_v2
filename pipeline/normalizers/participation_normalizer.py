import pandas as pd

def normalize_participation_df(participation_df):
    """
    Normalizes position and status columns in participation_df:
    - Maps 'position' according to position_map.
    - Sets 'position' to 'MNG' if status == 5.
    - Maps numeric 'status' to enum values.

    Args:
        participation_df (pd.DataFrame): DataFrame to normalize.

    Returns:
        pd.DataFrame: Normalized DataFrame.
    """
    # 1. Map position
    position_map = {
        "Attacker": "FW",
        "Midfielder": "MF",
        "Defender": "DF",
        "Goalkeeper": "GK",
        'Management': "MNG"
    }
    participation_df['position'] = participation_df['position'].astype(str).replace(position_map)

    # 2. Set position to 'MNG' where status == 5
    participation_df.loc[participation_df['status'] == 5, 'position'] = 'MNG'

    # 3. Map status to enum
    status_map = {
        1: 'starter',
        2: 'substitute',
        3: 'unused',
        4: 'other',
        5: 'starter'
    }
    participation_df['status'] = participation_df['status'].map(status_map).fillna('other')

    return participation_df
