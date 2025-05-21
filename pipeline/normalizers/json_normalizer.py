import json
from normalizers.json_normalizer import normalize_member, normalize_lineup, normalize_stats, normalize_event,normalize_duration

def normalize_member(member):
    jersey = member.get(field("jersey_number"))
    try:
        jersey = int(jersey)
    except (ValueError, TypeError):
        jersey = -1

    return {
        "team_id": member.get(field("team_id")),
        "player_id": member.get(field("player_id")),
        "player_name": member.get(field("player_name")),
        "jersey_number": jersey
    }

def normalize_lineup(player):
    stats = normalize_stats(player.get(field("stats"), []))
    position = player.get("position", {}).get(field("position"))
    return {
        "player_id": player.get(field("player_id")),
        "position": position,
        "stats": stats,
        "status": player.get(field("status"))
    }

def normalize_stats(stats_list):
    if not isinstance(stats_list, list):
        return []
    cleaned = []
    for stat in stats_list:
        name = stat.get("name")
        value = stat.get("value")
        if name is not None and value is not None:
            cleaned.append({"name": name, "value": value})
    return cleaned

def normalize_event(event):
    normalized = {
        "team_id": event.get(field("team_id")),
        "minute": event.get(field("minute")),
        "event_type": event.get(field("event_type"), {}).get("name") if isinstance(event.get(field("event_type")), dict) else event.get(field("event_type")),
        "player_id": event.get(field("player_id_event")) if "player_id_event" in FIELD_MAP else event.get("playerId")
    }
    if normalized["event_type"] == "Substitution":
        extra_players = event.get(field("extra_player_id"), [])
        normalized["extra_player_id"] = extra_players[0] if extra_players else None
    return normalized

def normalize_duration(raw):
    try:
        name = get_nested(raw, [field("duration"), field("duration_name"), field("duration_str")])
        return int(name.split(" ")[2].split(":")[0])
    except (TypeError, IndexError, ValueError, AttributeError):
        return -1