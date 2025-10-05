from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

# ---- Domain imports
from domain.ids import (
    CompetitionId, SeasonId, MatchdayId, MatchId, TeamId, PlayerId,
)
from domain.value_objects import Name, DateTimeUTC, Minute, Score
from domain.enums import Position as PosEnum, EventType as EvtEnum, Side
from domain.entities.competition import Competition
from domain.entities.matchday import Matchday
from domain.entities.player import Player
from domain.entities.season import Season, SeasonTeam
from domain.entities.match import Match, Participation, Event
# If you have Team/TeamPlayer dataclasses and want to map them here, you can import them too:
from domain.entities.team import Team, TeamPlayer


# =============================================================================
# Helpers
# =============================================================================

def _first(d: Dict[str, Any], *candidates: str, default: Any = None) -> Any:
    """Return the first present key's value from the dict (or default)."""
    for k in candidates:
        if k in d and d[k] is not None:
            return d[k]
    return default

def _tz(dt: Optional[datetime]) -> Optional[DateTimeUTC]:
    """Ensure datetime is wrapped as DateTimeUTC (assumes UTC if naive)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return DateTimeUTC(dt)


# =============================================================================
# DB <-> Domain enum label mappings
# =============================================================================

# DB -> Domain Position
# DB labels: GK, DF, MF, FW, MNG (manager)
POSITION_MAP = {
    "GK": PosEnum.GK,
    "DF": PosEnum.DF,
    "MF": PosEnum.MF,
    "FW": PosEnum.FW,
    # "MNG": no Position in domain; we return None
}

def map_db_position(label: Optional[str]) -> Optional[PosEnum]:
    if not label:
        return None
    return POSITION_MAP.get(label, None)

# DB -> Domain EventType
# DB labels (examples): Goal, Own goal, Penalty, Penalty missed, Yellow card, Red card, Substitution, Woodwork, Disallowed goal
# Domain lacks "Woodwork" and "Disallowed goal" -> we skip them unless strict=True.
EVENT_TYPE_MAP = {
    "Goal":            EvtEnum.GOAL,
    "Own goal":        EvtEnum.OWN_GOAL,
    "Penalty":         EvtEnum.PENALTY_GOAL,
    "Penalty missed":  EvtEnum.MISSED_PEN,
    "Yellow card":     EvtEnum.YELLOW_CARD,
    "Red card":        EvtEnum.RED_CARD,
    "Substitution":    EvtEnum.SUBSTITUTION,
}

def map_db_event_type(label: str, *, strict: bool = False) -> Optional[EvtEnum]:
    evt = EVENT_TYPE_MAP.get(label)
    if evt is None and strict:
        raise ValueError(f"Unsupported event_type from DB: {label!r}")
    return evt


# =============================================================================
# Row -> Domain mappers (pure, no I/O)
# =============================================================================

def row_to_competition(r: Dict[str, Any]) -> Competition:
    # Accept either "name" or "competition_name"
    name = _first(r, "name", "competition_name")
    return Competition(
        competition_id=CompetitionId(int(_first(r, "competition_id"))),
        name=Name(str(name)),
        country=_first(r, "country", "competition_country"),
    )

def row_to_season(r: Dict[str, Any]) -> Season:
    return Season(
        season_id=SeasonId(int(_first(r, "season_id"))),
        competition_id=CompetitionId(int(_first(r, "competition_id"))),
        label=Name(str(_first(r, "label", "season_label"))),
    )

def row_to_matchday(r: Dict[str, Any]) -> Matchday:
    return Matchday(
        matchday_id=MatchdayId(int(_first(r, "matchday_id"))),
        season_id=SeasonId(int(_first(r, "season_id"))),
        number=int(_first(r, "number", "round_number")),
    )

def row_to_player(r: Dict[str, Any]) -> Player:
    # Accept either "name" or "player_name", position as DB enum text
    pos_label = _first(r, "position", "position_enum", "position_text")
    return Player(
        player_id=PlayerId(int(_first(r, "player_id"))),
        name=Name(str(_first(r, "name", "player_name"))),
        position=map_db_position(pos_label),
        nationality=_first(r, "nationality", "country"),
    )

def row_to_season_team(r: Dict[str, Any]) -> SeasonTeam:
    return SeasonTeam(
        season_id=SeasonId(int(_first(r, "season_id"))),
        team_id=TeamId(int(_first(r, "team_id"))),
        seed_number=_first(r, "seed_number"),
        status=_first(r, "status"),
    )

def row_to_match(r: Dict[str, Any]) -> Match:
    """
    Expected columns (you can supply via SQL aliases):
      match_id,
      season_id              -- via JOIN matchday
      matchday_id,
      home_team_id           -- alias of local_team_id
      away_team_id,
      home_score             -- alias of local_score
      away_score,
      kickoff_utc (optional)

    Everything else is derived (finalized = both scores present).
    """
    hs = _first(r, "home_score", "local_score")
    as_ = _first(r, "away_score")
    score = None
    if hs is not None and as_ is not None:
        score = Score(int(hs), int(as_))

    return Match(
        match_id=MatchId(int(_first(r, "match_id"))),
        season_id=SeasonId(int(_first(r, "season_id"))),
        matchday_id=int(_first(r, "matchday_id")) if _first(r, "matchday_id") is not None else None,
        home_team_id=TeamId(int(_first(r, "home_team_id", "local_team_id"))),
        away_team_id=TeamId(int(_first(r, "away_team_id"))),
        kickoff_utc=_tz(_first(r, "kickoff_utc")),
        score=score,
        finalized=(score is not None),
    )

def row_to_participation(r: Dict[str, Any]) -> Participation:
    """
    Expected columns (via the SQL I suggested):
      match_id, player_id, team_id,
      side ('HOME'/'AWAY'),
      starter (bool),
      minutes_played (int),
      position_hint (text, optional)
    """
    side_text = str(_first(r, "side")).upper()
    return Participation(
        match_id=MatchId(int(_first(r, "match_id"))),
        team_id=TeamId(int(_first(r, "team_id"))),
        player_id=PlayerId(int(_first(r, "player_id"))),
        side=Side(side_text),  # safe because Domain Side is a str-Enum with HOME/AWAY
        starter=bool(_first(r, "starter", default=False)),
        minutes_played=int(_first(r, "minutes_played", "minutes", default=0)),
        position_hint=_first(r, "position_hint"),
    )

def row_to_event(r: Dict[str, Any], *, strict_events: bool = False) -> Optional[Event]:
    """
    Expected columns:
      match_id, minute, event_type (text),
      team_id (nullable), main_player_id (nullable), extra_player_id (nullable),
      comment (optional)

    Unknown DB event types (e.g., 'Woodwork') are skipped unless strict_events=True.
    """
    # Be tolerant: allow 'event_type' or 'type'
    raw_type = _first(r, "event_type", "type")
    etype = map_db_event_type(str(raw_type), strict=strict_events)
    if etype is None:
        return None  # skip unsupported events

    team_id = _first(r, "team_id")
    main_player = _first(r, "main_player_id", "player_id")
    extra_player = _first(r, "extra_player_id", "secondary_player_id")

    return Event(
        match_id=MatchId(int(_first(r, "match_id"))),
        minute=Minute(int(_first(r, "minute"))),
        type=etype,
        team_id=TeamId(int(team_id)) if team_id is not None else None,
        player_id=PlayerId(int(main_player)) if main_player is not None else None,
        secondary_player_id=PlayerId(int(extra_player)) if extra_player is not None else None,
        comment=_first(r, "comment"),
    )


# -----------------------------------------------------------------------------
# BasicStats / role stats mappers (DB rows -> domain entities, 1:1 with schema)
# -----------------------------------------------------------------------------

from domain.entities.stats import (
    BasicStats, GoalkeeperStats, DefenderStats, MidfielderStats, ForwardStats
)

def _int_or_none(v):
    return None if v is None else int(v)

def _float_or_none(v):
    return None if v is None else float(v)

def row_to_basic_stats(r: Dict[str, Any]) -> BasicStats:
    """
    Mirrors core.basic_stats:
      basic_stats_id, match_id, player_id, minutes, goals, assists, touches,
      passes_total, passes_completed, ball_recoveries, possessions_lost,
      aerial_duels_won, aerial_duels_total, ground_duels_won, ground_duels_total
    """
    return BasicStats(
        basic_stats_id = int(_first(r, "basic_stats_id")),
        match_id       = MatchId(int(_first(r, "match_id"))),
        player_id      = PlayerId(int(_first(r, "player_id"))),
        minutes        = int(_first(r, "minutes", default=0)),
        goals          = int(_first(r, "goals", default=0)),
        assists        = int(_first(r, "assists", default=0)),
        touches        = int(_first(r, "touches", default=0)),
        passes_total   = int(_first(r, "passes_total", default=0)),
        passes_completed = int(_first(r, "passes_completed", default=0)),
        ball_recoveries  = int(_first(r, "ball_recoveries", default=0)),
        possessions_lost = int(_first(r, "possessions_lost", default=0)),
        aerial_duels_won   = int(_first(r, "aerial_duels_won", default=0)),
        aerial_duels_total = int(_first(r, "aerial_duels_total", default=0)),
        ground_duels_won   = int(_first(r, "ground_duels_won", default=0)),
        ground_duels_total = int(_first(r, "ground_duels_total", default=0)),
    )

def row_to_goalkeeper_stats(r: Dict[str, Any]) -> GoalkeeperStats:
    """
    Mirrors stats.goalkeeper_stats (all nullable except key):
      basic_stats_id, goalkeeper_saves, saves_inside_box, goals_conceded,
      xg_on_target_against, goals_prevented, punches_cleared, high_claims,
      clearances, penalties_received, penalties_saved, interceptions, times_dribbled_past
    """
    return GoalkeeperStats(
        basic_stats_id        = int(_first(r, "basic_stats_id")),
        goalkeeper_saves      = _int_or_none(_first(r, "goalkeeper_saves")),
        saves_inside_box      = _int_or_none(_first(r, "saves_inside_box")),
        goals_conceded        = _int_or_none(_first(r, "goals_conceded")),
        xg_on_target_against  = _float_or_none(_first(r, "xg_on_target_against")),
        goals_prevented       = _float_or_none(_first(r, "goals_prevented")),
        punches_cleared       = _int_or_none(_first(r, "punches_cleared")),
        high_claims           = _int_or_none(_first(r, "high_claims")),
        clearances            = _int_or_none(_first(r, "clearances")),
        penalties_received    = _int_or_none(_first(r, "penalties_received")),
        penalties_saved       = _int_or_none(_first(r, "penalties_saved")),
        interceptions         = _int_or_none(_first(r, "interceptions")),
        times_dribbled_past   = _int_or_none(_first(r, "times_dribbled_past")),
    )

def row_to_defender_stats(r: Dict[str, Any]) -> DefenderStats:
    """
    Mirrors stats.defender_stats:
      basic_stats_id, tackles_won, interceptions, clearances, times_dribbled_past,
      errors_leading_to_goal, errors_leading_to_shot, possessions_won_final_third,
      fouls_committed, tackles_total
    """
    return DefenderStats(
        basic_stats_id               = int(_first(r, "basic_stats_id")),
        tackles_won                  = _int_or_none(_first(r, "tackles_won")),
        interceptions                = _int_or_none(_first(r, "interceptions")),
        clearances                   = _int_or_none(_first(r, "clearances")),
        times_dribbled_past          = _int_or_none(_first(r, "times_dribbled_past")),
        errors_leading_to_goal       = _int_or_none(_first(r, "errors_leading_to_goal")),
        errors_leading_to_shot       = _int_or_none(_first(r, "errors_leading_to_shot")),
        possessions_won_final_third  = _int_or_none(_first(r, "possessions_won_final_third")),
        fouls_committed              = _int_or_none(_first(r, "fouls_committed")),
        tackles_total                = _int_or_none(_first(r, "tackles_total")),
    )

def row_to_forward_stats(r: Dict[str, Any]) -> ForwardStats:
    """
    Mirrors stats.forward_stats:
      basic_stats_id, expected_assists, expected_goals, xg_from_shots_on_target,
      shots_total, shots_on_target, shots_off_target, big_chances, big_chances_missed,
      big_chances_scored, penalties_won, penalties_missed, offside, key_passes,
      dribbles_completed, dribbles_total, times_dribbled_past, fouls_committed,
      fouls_suffered, woodwork
    """
    return ForwardStats(
        basic_stats_id            = int(_first(r, "basic_stats_id")),
        expected_assists          = _float_or_none(_first(r, "expected_assists")),
        expected_goals            = _float_or_none(_first(r, "expected_goals")),
        xg_from_shots_on_target   = _float_or_none(_first(r, "xg_from_shots_on_target")),
        shots_total               = _int_or_none(_first(r, "shots_total")),
        shots_on_target           = _int_or_none(_first(r, "shots_on_target")),
        shots_off_target          = _int_or_none(_first(r, "shots_off_target")),
        big_chances               = _int_or_none(_first(r, "big_chances")),
        big_chances_missed        = _int_or_none(_first(r, "big_chances_missed")),
        big_chances_scored        = _int_or_none(_first(r, "big_chances_scored")),
        penalties_won             = _int_or_none(_first(r, "penalties_won")),
        penalties_missed          = _int_or_none(_first(r, "penalties_missed")),
        offside                   = _int_or_none(_first(r, "offside")),
        key_passes                = _int_or_none(_first(r, "key_passes")),
        dribbles_completed        = _int_or_none(_first(r, "dribbles_completed")),
        dribbles_total            = _int_or_none(_first(r, "dribbles_total")),
        times_dribbled_past       = _int_or_none(_first(r, "times_dribbled_past")),
        fouls_committed           = _int_or_none(_first(r, "fouls_committed")),
        fouls_suffered            = _int_or_none(_first(r, "fouls_suffered")),
        woodwork                  = _int_or_none(_first(r, "woodwork")),
    )

def row_to_midfielder_stats(r: Dict[str, Any]) -> MidfielderStats:
    """
    Mirrors stats.midfielder_stats:
      basic_stats_id, expected_assists, tackles_won, tackles_total, crosses,
      fouls_committed, fouls_suffered, expected_goals, xg_from_shots_on_target,
      big_chances, big_chances_missed, big_chances_scored, interceptions,
      key_passes, passes_in_final_third, back_passes, long_passes_completed, woodwork,
      possessions_won_final_third, times_dribbled_past, dribbles_completed, dribbles_total,
      long_passes_total, crosses_total, shots_off_target, shots_on_target, shots_total
    """
    return MidfielderStats(
        basic_stats_id              = int(_first(r, "basic_stats_id")),
        expected_assists            = _float_or_none(_first(r, "expected_assists")),
        tackles_won                 = _int_or_none(_first(r, "tackles_won")),
        tackles_total               = _int_or_none(_first(r, "tackles_total")),
        crosses                     = _int_or_none(_first(r, "crosses")),
        fouls_committed             = _int_or_none(_first(r, "fouls_committed")),
        fouls_suffered              = _int_or_none(_first(r, "fouls_suffered")),
        expected_goals              = _float_or_none(_first(r, "expected_goals")),
        xg_from_shots_on_target     = _float_or_none(_first(r, "xg_from_shots_on_target")),
        big_chances                 = _int_or_none(_first(r, "big_chances")),
        big_chances_missed          = _int_or_none(_first(r, "big_chances_missed")),
        big_chances_scored          = _int_or_none(_first(r, "big_chances_scored")),
        interceptions               = _int_or_none(_first(r, "interceptions")),
        key_passes                  = _int_or_none(_first(r, "key_passes")),
        passes_in_final_third       = _int_or_none(_first(r, "passes_in_final_third")),
        back_passes                 = _int_or_none(_first(r, "back_passes")),
        long_passes_completed       = _int_or_none(_first(r, "long_passes_completed")),
        woodwork                    = _int_or_none(_first(r, "woodwork")),
        possessions_won_final_third = _int_or_none(_first(r, "possessions_won_final_third")),
        times_dribbled_past         = _int_or_none(_first(r, "times_dribbled_past")),
        dribbles_completed          = _int_or_none(_first(r, "dribbles_completed")),
        dribbles_total              = _int_or_none(_first(r, "dribbles_total")),
        long_passes_total           = _int_or_none(_first(r, "long_passes_total")),
        crosses_total               = _int_or_none(_first(r, "crosses_total")),
        shots_off_target            = _int_or_none(_first(r, "shots_off_target")),
        shots_on_target             = _int_or_none(_first(r, "shots_on_target")),
        shots_total                 = _int_or_none(_first(r, "shots_total")),
    )

# Handy aggregators for services/adapters

def index_role_stats_by_basic_id(rows, mapper):
    """
    Build {basic_stats_id: domain_obj} from a list of DB rows and a row->obj mapper.
    Later joins become O(1) lookups.
    """
    out = {}
    for r in rows:
        obj = mapper(r)
        out[getattr(obj, "basic_stats_id")] = obj
    return out
