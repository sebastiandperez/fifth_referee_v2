from utils.db_utils import resolve_competition_and_season_ids, ask_competition_and_season, fetch_min_match_and_max_matchday
from extractors.extract_raw_data import extract_all_entities
from matchday_extractor.matchdays_information import run_competition_window
from setup import initialize_pipeline

from builders.build_match_entities import build_match_entities
from builders.build_player_entities import build_player_entities
from builders.event_builder import build_event_entity
from builders.build_stats_entities import build_basic_stats_for_season
from builders.build_specific_stats_entities import build_specific_stats_df

from loaders.team_loader import TeamLoader
from loaders.player_loader import PlayerLoader
from loaders.match_loader import MatchLoader
from loaders.stats_loader import StatsLoader
from loaders.basic_stats_loader import BasicStatsLoader
from loaders.event_loader import EventLoader   # ⟵ NUEVO

if __name__ == "__main__":
    config, json_data_root, conn = initialize_pipeline()

    competition_name, season_label = ask_competition_and_season(conn)
    competition_id, season_id = resolve_competition_and_season_ids(conn, competition_name, season_label)
    min_match_id, max_matchday_number = fetch_min_match_and_max_matchday(conn, season_id)
    print(f"IDs: comp={competition_id} season={season_id} min_match={min_match_id} max_md={max_matchday_number}")

    # cuidado si max_matchday_number es 0/None en primera corrida
    jmin = max(1, (max_matchday_number or 1) - 1)
    jmax = (max_matchday_number or 1) + 1

    run_competition_window(
        competition_name=competition_name.replace(" ","_").capitalize(),
        jornada_min=jmin,
        jornada_max=jmax,
        season_label=season_label,
        threshold=10
    )

    team_loader   = TeamLoader(conn)
    player_loader = PlayerLoader(conn)
    match_loader  = MatchLoader(conn)
    stats_loader  = StatsLoader(conn)
    basic_stats   = BasicStatsLoader(conn)
    event_loader  = EventLoader(conn)

    # 1) Extraer todo
    all_matches, all_events, all_players, all_player_stats = extract_all_entities(
        json_data_root, competition_name, season_label
    )

    # 2) Construir entidades de partidos y equipos
    match_df, team_df, season_team_df = build_match_entities(
        conn, all_matches, competition_name, season_id, config['X-Auth-Token'], config
    )

    # 3) Cargar catálogos/equipos (padres)
    team_loader.insert_team_block(team_df, season_team_df)

    # 4) Cargar partidos (padres de participation/event)
    match_loader.insert_match_block(match_df)

    # 5) Construir jugadores + participation (hijos de match)
    participation_df, team_player_df, player_df = build_player_entities(
        conn, all_players, match_df, season_id
    )

    # 6) Cargar jugadores/nóminas + participation (ahora sí existen los match)
    player_loader.insert_player_block(player_df, team_player_df, participation_df)

    # 7) Stats básicas (FK a participation) y específicas (FK a basic_stats)
    basic_stats_df = build_basic_stats_for_season(conn, season_id, all_player_stats)
    basic_stats.insert_basic_stats(basic_stats_df)

    goalkeeper_df, defender_df, midfielder_df, forward_df = build_specific_stats_df(
        conn, season_id, all_player_stats
    )
    stats_loader.insert_stats_block(goalkeeper_df, defender_df, midfielder_df, forward_df)

    # 8) Eventos (FK a match y a players; ahora ambos existen)
    event_df = build_event_entity(conn, all_events, schema_path="pipeline/config/event_schema.json")
    event_loader.insert_events(event_df)   # ⟵ NUEVO

    conn.close()
