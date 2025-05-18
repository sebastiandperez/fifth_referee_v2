import json
from extractors.match_json_extractor import MatchJsonExtractor

class BatchExtractor:
    def __init__(self, match_queue):
        """
        match_queue: Queue con los paths a los archivos json de partidos (de una jornada)
        """
        self.match_queue = match_queue

    def process_all_files(self):
        all_matches = []
        all_events = []
        all_players = []
        all_player_stats = []

        while not self.match_queue.empty():
            file_path = self.match_queue.get()
            with open(file_path, "r", encoding="utf-8") as f:
                match_json = json.load(f)
            extractor = MatchJsonExtractor(match_json)
            result = extractor.extract_all()
            all_matches.extend(result["match"])
            all_events.extend(result["events"])
            all_players.extend(result["players"])
            all_player_stats.extend(result["player_stats"])

        return {
            "match": all_matches,
            "events": all_events,
            "players": all_players,
            "player_stats": all_player_stats
        }
