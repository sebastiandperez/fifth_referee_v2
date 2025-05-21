from batch.multi_batch_extractor import MultiBatchExtractor
from utils.file_utils import build_matchday_queues

def extract_all_entities(json_data_root, competition_name, season_label, max_workers=7):
    """
    Extracts all raw entities from JSON files for a given competition and season.

    Returns:
        all_matches, all_events, all_players, all_player_stats (lists)
    """
    queue_matchdays = build_matchday_queues(json_data_root, competition_name, season_label)
    print(f"Found {queue_matchdays.qsize()} jornadas.")

    multi_extractor = MultiBatchExtractor(queue_matchdays, max_workers=max_workers)
    results = multi_extractor.process_all_matchdays()

    # Generalize the flattening of results:
    entity_keys = ['match', 'events', 'players', 'player_stats']
    entities = {key: [] for key in entity_keys}
    for result in results:
        for key in entity_keys:
            entities[key].extend(result.get(key, []))

    return entities['match'], entities['events'], entities['players'], entities['player_stats']
