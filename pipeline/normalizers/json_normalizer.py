from matchday_extractor.fieldmap import fmap
import re

def _get_nested(d, keys, default=None):
    cur = d
    for k in keys:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return default
    return cur

def normalize_member(member: dict) -> dict:
    jersey_key = fmap("jersey_number")
    jersey = member.get(jersey_key)
    try:
        jersey = int(jersey)
    except (ValueError, TypeError):
        jersey = -1

    return {
        "team_id":     member.get(fmap("team_id"))     or member.get("teamId")     or member.get("team_id"),
        "player_id":   member.get(fmap("player_id"))   or member.get("playerId")   or member.get("id"),
        "player_name": member.get(fmap("player_name")) or member.get("name"),
        "jersey_number": jersey,
    }

def normalize_stats(stats_list) -> list:
    if not isinstance(stats_list, list):
        return []
    cleaned = []
    for stat in stats_list:
        name  = stat.get("name")
        value = stat.get("value")
        if name is not None and value is not None:
            cleaned.append({"name": name, "value": value})
    return cleaned

def normalize_lineup(player: dict) -> dict:
    stats_key = fmap("stats")
    position_key = fmap("position")
    stats = normalize_stats(player.get(stats_key, []))
    # posición puede venir anidada o plana
    pos = player.get("position", {})
    position = pos.get(position_key) if isinstance(pos, dict) else player.get(position_key)
    return {
        "player_id": player.get(fmap("player_id")) or player.get("playerId") or player.get("id"),
        "position": position,
        "stats": stats,
        "status": player.get(fmap("status")) or player.get("status"),
    }

def normalize_event(event: dict) -> dict:
    team_id   = event.get(fmap("team_id")) or event.get("teamId") or event.get("team_id")
    minute    = event.get(fmap("minute"))  or event.get("minute")
    # event_type puede ser dict o string
    evtype_key = fmap("event_type")
    evtype_val = event.get(evtype_key)
    if isinstance(evtype_val, dict):
        event_type = evtype_val.get("name") or evtype_val.get("type") or evtype_val.get("code")
    else:
        event_type = evtype_val or event.get("eventType") or event.get("type")

    # player_id del evento: prueba varias claves comunes
    pid_event_key = fmap("player_id_event")
    player_id = (event.get(pid_event_key) or
                 event.get(fmap("player_id")) or
                 event.get("playerId") or
                 event.get("player_id") or
                 event.get("player"))

    normalized = {
        "team_id": team_id,
        "minute": minute,
        "event_type": event_type,
        "player_id": player_id,
    }

    if event_type == "Substitution":
        extra_key = fmap("extra_player_id")
        extra = event.get(extra_key)
        if isinstance(extra, list):
            normalized["extra_player_id"] = extra[0] if extra else None
        else:
            normalized["extra_player_id"] = extra or event.get("subInPlayerId") or event.get("inPlayerId")

    return normalized

def normalize_duration(raw: dict) -> int:
    """
    Devuelve 90 o 120. Nunca -1.
    Heurística:
    1) Usa campos de duración (numérico o string tipo '90:00'/'120:00').
    2) Palabras clave (AET/ET/Extra Time -> 120).
    3) Señal por eventos: minuto máximo >=105 -> 120; si hay eventos -> 90.
    4) Fallback seguro -> 90.
    """
    dur_key      = fmap("duration")
    dur_name_key = fmap("duration_name")
    dur_str_key  = fmap("duration_str")

    # Candidatos directos
    cand = (
        _get_nested(raw, [dur_key, dur_name_key, dur_str_key]) or
        _get_nested(raw, [dur_key, dur_str_key]) or
        raw.get(dur_key) or
        raw.get("matchDuration") or
        raw.get("duration") or
        ""
    )

    # 1) Numérico directo
    if isinstance(cand, (int, float)):
        v = int(cand)
        if v >= 105:
            return 120
        if 80 <= v <= 100:
            return 90
        return 90  # cualquier otra cosa rara: 90

    # 2) String: HH:MM o MM:SS
    s = str(cand)
    m = re.search(r'(\d{1,3}):\d{2}', s)
    if m:
        mins = int(m.group(1))
        return 120 if mins >= 105 else 90

    # 3) Palabras clave
    s_up = s.upper()
    if any(k in s_up for k in ("AET", "EXTRA", "ET")):
        return 120
    if any(k in s_up for k in ("FT", "FULL TIME", "90")):
        return 90

    # 4) Señal por eventos
    events = raw.get(fmap("events")) or raw.get("events") or []
    max_min = 0
    for e in events:
        m = e.get(fmap("minute")) or e.get("minute")
        if m is None:
            continue
        # soporta "90+5"
        if isinstance(m, str) and "+" in m:
            try:
                base, extra = m.split("+", 1)
                mm = int(base) + int(re.sub(r"\D", "", extra) or 0)
            except Exception:
                continue
        else:
            try:
                mm = int(m)
            except Exception:
                continue
        if mm > max_min:
            max_min = mm

    if max_min >= 105:
        return 120
    if max_min > 0:
        return 90

    # 5) Fallback seguro
    return 90
