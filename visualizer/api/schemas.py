from __future__ import annotations
from typing import Any, List, Optional
try:
    from pydantic import BaseModel, Field, ConfigDict
    _PD_V2 = True
except Exception:
    from pydantic import BaseModel, Field  # type: ignore
    ConfigDict = None  # type: ignore
    _PD_V2 = False


# ---- Discovery ----
class CompetitionItem(BaseModel):
    id: int
    name: str

class CompetitionList(BaseModel):
    items: List[CompetitionItem]

class SeasonLabelList(BaseModel):
    items: List[str]

class SeasonResolveResult(BaseModel):
    season_id: int


# ---- Season summary/snapshot ----
class SeasonSummary(BaseModel):
    season_id: int
    season_label: str
    competition_id: int
    competition_name: str
    team_count: int
    matchday_min: Optional[int] = None
    matchday_max: Optional[int] = None
    last_finalized_matchday: Optional[int] = None


# ---- Teams / Players / Matchdays ----
class TeamItem(BaseModel):
    team_id: int
    team_name: str
    team_city: str | None = None
    team_stadium: str | None = None

class TeamList(BaseModel):
    items: List[TeamItem]

class PlayerItem(BaseModel):
    player_id: int
    player_name: str
    team_id: int
    team_name: str
    season_team_id: int
    jersey_number: Optional[int] = None

class PlayerList(BaseModel):
    items: List[PlayerItem]

class MatchdayItem(BaseModel):
    matchday_id: int
    matchday_number: int

class MatchdayList(BaseModel):
    items: List[MatchdayItem]


# ---- Matches (+ expansions) ----
class MatchEvent(BaseModel):
    event_id: int
    match_id: int
    event_type: str
    minute: Optional[int] = None
    main_player_id: Optional[int] = None
    extra_player_id: Optional[int] = None
    team_id: Optional[int] = None

class ParticipationAPI(BaseModel):
    match_id: int
    player_id: int
    status: str
    position: str

class MatchAPI(BaseModel):
    match_id: int
    matchday_id: int
    home_team_id: int = Field(..., alias="local_team_id")
    away_team_id: int
    home_score: Optional[int] = Field(None, alias="local_score")
    away_score: Optional[int] = Field(None, alias="away_score")
    duration: int
    stadium: Optional[str] = None
    # expansions
    events: Optional[List[MatchEvent]] = None
    participations: Optional[List[ParticipationAPI]] = None

    if _PD_V2:
        model_config = ConfigDict(populate_by_name=True)

class MatchList(BaseModel):
    items: List[MatchAPI]
    limit: int
    offset: int
    total: Optional[int] = None


# ---- Standings ----
class StandingRowAPI(BaseModel):
    model_config = ConfigDict(populate_by_name=True) if _PD_V2 else {}
    team_id: int
    team_name: str | None = None
    played: int = Field(..., alias="mp")
    win: int | None = None
    draw: int | None = None
    loss: int | None = None
    gf: int
    ga: int
    gd: int
    points: int = Field(..., alias="pts")
    position: int

class SeasonStandingsDTOAPI(BaseModel):
    rows: List[StandingRowAPI]


# ---- Stats: basic + role
class BasicStatsAPI(BaseModel):
    basic_stats_id: int
    match_id: int
    player_id: int
    minutes: int
    goals: int
    assists: int
    touches: int
    passes_total: int
    passes_completed: int
    ball_recoveries: int
    possessions_lost: int
    aerial_duels_won: int
    aerial_duels_total: int
    ground_duels_won: int
    ground_duels_total: int

class BasicStatsListAPI(BaseModel):
    total: int
    items: List[BasicStatsAPI]

class PagedBasicStats(BaseModel):
    items: List[BasicStatsAPI]
    limit: int
    offset: int
    total: int | None = None

class GoalkeeperStatsAPI(BaseModel):
    basic_stats_id: int
    goalkeeper_saves: int | None = None
    saves_inside_box: int | None = None
    goals_conceded: int | None = None
    xg_on_target_against: float | None = None
    goals_prevented: float | None = None
    punches_cleared: int | None = None
    high_claims: int | None = None
    clearances: int | None = None
    penalties_received: int | None = None
    penalties_saved: int | None = None
    interceptions: int | None = None
    times_dribbled_past: int | None = None

class DefenderStatsAPI(BaseModel):
    basic_stats_id: int
    tackles_won: int | None = None
    interceptions: int | None = None
    clearances: int | None = None
    times_dribbled_past: int | None = None
    errors_leading_to_goal: int | None = None
    errors_leading_to_shot: int | None = None
    possessions_won_final_third: int | None = None
    fouls_committed: int | None = None
    tackles_total: int | None = None

class MidfielderStatsAPI(BaseModel):
    basic_stats_id: int
    expected_assists: float | None = None
    tackles_won: int | None = None
    tackles_total: int | None = None
    crosses: int | None = None
    fouls_committed: int | None = None
    fouls_suffered: int | None = None
    expected_goals: float | None = None
    xg_from_shots_on_target: float | None = None
    big_chances: int | None = None
    big_chances_missed: int | None = None
    big_chances_scored: int | None = None
    interceptions: int | None = None
    key_passes: int | None = None
    passes_in_final_third: int | None = None
    back_passes: int | None = None
    long_passes_completed: int | None = None
    woodwork: int | None = None
    possessions_won_final_third: int | None = None
    times_dribbled_past: int | None = None
    dribbles_completed: int | None = None
    dribbles_total: int | None = None
    long_passes_total: int | None = None
    crosses_total: int | None = None
    shots_off_target: int | None = None
    shots_on_target: int | None = None
    shots_total: int | None = None

class ForwardStatsAPI(BaseModel):
    basic_stats_id: int
    expected_assists: float | None = None
    expected_goals: float | None = None
    xg_from_shots_on_target: float | None = None
    shots_total: int | None = None
    shots_on_target: int | None = None
    shots_off_target: int | None = None
    big_chances: int | None = None
    big_chances_missed: int | None = None
    big_chances_scored: int | None = None
    penalties_won: int | None = None
    penalties_missed: int | None = None
    offside: int | None = None
    key_passes: int | None = None
    dribbles_completed: int | None = None
    dribbles_total: int | None = None
    times_dribbled_past: int | None = None
    fouls_committed: int | None = None
    fouls_suffered: int | None = None
    woodwork: int | None = None

class PagedRoleStats(BaseModel):
    items: List[Any]
    limit: int
    offset: int
    total: Optional[int] = None


# ---- Season snapshot ----
class SeasonSnapshot(BaseModel):
    summary: SeasonSummary
    teams: List[TeamItem] = []
    players: List[PlayerItem] = []
    matchdays: List[MatchdayItem] = []
    matches: List[MatchAPI] = []
