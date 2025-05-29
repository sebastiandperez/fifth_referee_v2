from utils.player_utils import build_clean_player_df, get_match_ids, build_team_player, build_player_df
from normalizers.participation_normalizer import normalize_participation_df
from normalizers.team_player_normalizer import normalize_team_player_df
from utils.db_utils import get_all_player_ids

def build_player_entities(
    conn,
    all_players,
    match_df,
    season_id
):
    """
    Builds all player-related entities DataFrames:
    - participation_df
    - team_player_df
    - player_df (only new players)

    Args:
        conn: Active DB connection.
        all_players (list of dict): Raw player participations.
        match_df (pd.DataFrame): DataFrame of matches.
        season_id (int): Season id for current context.

    Returns:
        (participation_df, team_player_df, player_df)
    """
    required_columns = ['player_id', 'player_name', 'status', 'position']
    player_df = build_clean_player_df(conn, all_players, match_df)
    player_df = player_df.dropna(subset=required_columns)

    # 1. participation DataFrame
    participation_df = normalize_participation_df(player_df.drop(columns=['team_id', 'player_name', 'jersey_number'], errors='ignore'))

    # 2. team_player DataFrame
    team_player_full_df = build_team_player(conn, player_df, season_id)
    team_player_full_df = normalize_team_player_df(conn, team_player_full_df, season_id)
    team_player_df = team_player_full_df.drop(
        columns=['team_id', 'player_name', 'match_id', "position", "status"],
        errors='ignore'
    )

    all_player_ids = get_all_player_ids(conn)
    player_df_final = build_player_df(player_df, all_player_ids)
    player_df = player_df_final[['player_id', 'player_name']]
    team_player_df = team_player_df.drop_duplicates(subset=['season_team_id', 'player_id', 'jersey_number'])

    return participation_df, team_player_df, player_df
