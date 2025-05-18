import json

class MatchJsonExtractor:
    def __init__(self, json_obj):
        self.json_obj = json_obj

    def extract_match(self):
        """Extrae los datos principales del partido (match)."""
        match = {
            "match_id": self.json_obj.get("match_id"),
            "matchday": self.json_obj.get("matchday"),
            "local_team_id": self.json_obj.get("local_team", {}).get("team_id"),
            "local_team_name": self.json_obj.get("local_team", {}).get("team_name"),
            "local_team_score": self.json_obj.get("local_team", {}).get("team_score"),
            "away_team_id": self.json_obj.get("away_team", {}).get("team_id"),
            "away_team_name": self.json_obj.get("away_team", {}).get("team_name"),
            "away_team_score": self.json_obj.get("away_team", {}).get("team_score"),
            "stadium": self.json_obj.get("stadium"),
            "duration": self.json_obj.get("duration"),
        }
        return [match]


    def extract_events(self):
        """Extrae la lista de eventos del partido."""
        match_id = self.json_obj.get("match_id")
        events = []
        for e in self.json_obj.get("events", []):
            events.append({
                "match_id": match_id,
                "team_id": e.get("team_id"),
                "minute": e.get("minute"),
                "event_type": e.get("eventType"),
                "player_id": e.get("player_id"),
                "extra_player_id": e.get("extra_player_id"),
            })
        return events

    def extract_players(self):
        """Extrae la lista de jugadores (con datos básicos)."""
        match_id = self.json_obj.get("match_id")
        players = []
        for p in self.json_obj.get("players", []):
            players.append({
                "match_id": match_id,
                "team_id": p.get("team_id"),
                "player_id": p.get("player_id"),
                "player_name": p.get("player_name"),
                "jersey_number": p.get("jersey_number"),
                "position": p.get("position") if "position" in p else None,
                "status": p.get("status") if "status" in p else None,
            })
        return players

    def extract_player_stats(self):
        """Extrae las estadísticas individuales de cada jugador."""
        match_id = self.json_obj.get("match_id")
        player_stats = []
        for p in self.json_obj.get("players", []):
            player_id = p.get("player_id")
            for s in p.get("stats", []):
                player_stats.append({
                    "match_id": match_id,
                    "player_id": player_id,
                    "stat_name": s.get("name"),
                    "stat_value": s.get("value"),
                })
        return player_stats

    def extract_all(self):
        """Orquesta todos los extractores y retorna un dict de listas."""
        return {
            "match": self.extract_match(),
            "events": self.extract_events(),
            "players": self.extract_players(),
            "player_stats": self.extract_player_stats(),
        }
