import json
import os
from normalizers.json_normalizer import normalize_member, normalize_lineup, normalize_stats, normalize_event,normalize_duration

## Document this part
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
FIELD_MAP_PATH = os.path.join(THIS_DIR, 'field_map.json')

with open(FIELD_MAP_PATH, 'r', encoding='utf-8') as f:
    FIELD_MAP = json.load(f)

def field(name):
    return FIELD_MAP.get(name, name)

def get_nested(d, keys, default=None):
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k, default)
        else:
            return default
    return d

def get_team_id(team_dict):
    if not team_dict:
        return None
    mapped_key = field("team_id")
    if mapped_key in team_dict:
        return team_dict[mapped_key]
    if "id" in team_dict:
        return team_dict["id"]
    for k, v in team_dict.items():
        if k.lower() == "id":
            return v
    return None

def extract_lineup(competitor):
    members = get_nested(competitor, [field("lineups"), field("members")], [])
    return [normalize_lineup(m) for m in members if m]

def join_members_and_lineups(members, lineup_members):
    members_by_id = {m.get("player_id"): m for m in members}
    lineup_by_id = {l.get("player_id"): l for l in lineup_members}
    return [{**members_by_id.get(pid, {}), **lineup_by_id.get(pid, {})}
            for pid in set(members_by_id) | set(lineup_by_id)]

def clean_match_data(raw):
    """Transforma el JSON bruto de un partido a estructura limpia."""
    local_team_dict = raw.get(field("local_team"), {})
    away_team_dict = raw.get(field("away_team"), {})

    lineup_members_home = extract_lineup(local_team_dict)
    lineup_members_away = extract_lineup(away_team_dict)

    members = [normalize_member(m) for m in raw.get(field("members"), [])]
    all_lineup_members = lineup_members_home + lineup_members_away

    merged_players = join_members_and_lineups(members, all_lineup_members)

    try:
        match_duration = normalize_duration(raw)
    except AttributeError:
        match_duration = 22

    return {
        "match_id": raw.get(field("player_id")) if "player_id" in FIELD_MAP else raw.get("id"),
        "matchday": raw.get(field("matchday")),
        "local_team": {
            "team_id": get_team_id(local_team_dict),
            "team_name": local_team_dict.get(field("player_name")),
            "team_score": local_team_dict.get("score")
        },
        "away_team": {
            "team_id": get_team_id(away_team_dict),
            "team_name": away_team_dict.get(field("player_name")),
            "team_score": away_team_dict.get("score")
        },
        "stadium": raw.get(field("stadium"), {}).get(field("player_name")),
        "duration": match_duration,
        "events": [normalize_event(e) for e in raw.get(field("events"), [])],
        "players": merged_players
    }