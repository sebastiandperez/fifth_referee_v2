from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from ..ids import PlayerId, MatchId, TeamId
from ..enums import Result

__all__ = [
    "StandingRow", "TeamFormRow", "TeamSplit",
    "BasicStats",
    "GoalkeeperStats", "DefenderStats", "MidfielderStats", "ForwardStats",
]

# ---------------------------------------------------------------------------
# League/season summaries (unchanged semantics; API will alias names)
# ---------------------------------------------------------------------------

@dataclass
class StandingRow:
    """
    Domain-canonical league row. Keep classic names; API can alias to played/points/etc.
    """
    team_id: TeamId
    MP: int
    GF: int
    GA: int
    GD: int
    Pts: int

    def __post_init__(self):
        if any(v < 0 for v in (self.MP, self.GF, self.GA, self.Pts)):
            raise ValueError("MP/GF/GA/Pts must be >= 0")
        # keep GD coherent even if constructed loosely
        if self.GD != self.GF - self.GA:
            object.__setattr__(self, "GD", self.GF - self.GA)

@dataclass(frozen=True, slots=True)
class TeamFormRow:
    match_id: MatchId
    result: Result  # W / D / L

@dataclass(frozen=True, slots=True)
class TeamSplit:
    home_ppg: float
    away_ppg: float
    home_gf: int
    away_gf: int
    home_ga: int
    away_ga: int

    def __post_init__(self):
        if any(v < 0 for v in (self.home_gf, self.away_gf, self.home_ga, self.away_ga)):
            raise ValueError("Goals for/against must be >= 0")
        if self.home_ppg < 0 or self.away_ppg < 0:
            raise ValueError("PPG must be >= 0.0")

# ---------------------------------------------------------------------------
# Core per-player-per-match stats (exactly your core.basic_stats schema)
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class BasicStats:
    """
    Mirrors core.basic_stats exactly. This is the anchor row for role stats.
    """
    basic_stats_id: int
    match_id: MatchId
    player_id: PlayerId
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

    def __post_init__(self):
        # non-negative sanity
        ints = (
            "minutes","goals","assists","touches","passes_total","passes_completed",
            "ball_recoveries","possessions_lost",
            "aerial_duels_won","aerial_duels_total","ground_duels_won","ground_duels_total"
        )
        for name in ints:
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be >= 0")
        # monotonic constraints
        if self.passes_completed > self.passes_total:
            raise ValueError("passes_completed cannot exceed passes_total")
        if self.aerial_duels_won > self.aerial_duels_total:
            raise ValueError("aerial_duels_won cannot exceed aerial_duels_total")
        if self.ground_duels_won > self.ground_duels_total:
            raise ValueError("ground_duels_won cannot exceed ground_duels_total")

# ---------------------------------------------------------------------------
# Role-specific stats (exactly your stats.* tables; keyed by basic_stats_id)
# All fields Optional[int/float] because DB columns may be NULL.
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class GoalkeeperStats:
    basic_stats_id: int
    goalkeeper_saves: Optional[int] = None
    saves_inside_box: Optional[int] = None
    goals_conceded: Optional[int] = None
    xg_on_target_against: Optional[float] = None
    goals_prevented: Optional[float] = None
    punches_cleared: Optional[int] = None
    high_claims: Optional[int] = None
    clearances: Optional[int] = None
    penalties_received: Optional[int] = None
    penalties_saved: Optional[int] = None
    interceptions: Optional[int] = None
    times_dribbled_past: Optional[int] = None

    def __post_init__(self):
        # counts must be non-negative if present
        for name, val in self.__dict__.items():
            if name == "basic_stats_id": continue
            if isinstance(val, int) and val < 0:
                raise ValueError(f"{name} must be >= 0")

@dataclass(frozen=True, slots=True)
class DefenderStats:
    basic_stats_id: int
    tackles_won: Optional[int] = None
    interceptions: Optional[int] = None
    clearances: Optional[int] = None
    times_dribbled_past: Optional[int] = None
    errors_leading_to_goal: Optional[int] = None
    errors_leading_to_shot: Optional[int] = None
    possessions_won_final_third: Optional[int] = None
    fouls_committed: Optional[int] = None
    tackles_total: Optional[int] = None

    def __post_init__(self):
        if (self.tackles_won is not None and self.tackles_total is not None
                and self.tackles_won > self.tackles_total):
            raise ValueError("tackles_won cannot exceed tackles_total")
        for name, val in self.__dict__.items():
            if name in ("basic_stats_id",): continue
            if isinstance(val, int) and val < 0:
                raise ValueError(f"{name} must be >= 0")

@dataclass(frozen=True, slots=True)
class ForwardStats:
    basic_stats_id: int
    expected_assists: Optional[float] = None
    expected_goals: Optional[float] = None
    xg_from_shots_on_target: Optional[float] = None
    shots_total: Optional[int] = None
    shots_on_target: Optional[int] = None
    shots_off_target: Optional[int] = None
    big_chances: Optional[int] = None
    big_chances_missed: Optional[int] = None
    big_chances_scored: Optional[int] = None
    penalties_won: Optional[int] = None
    penalties_missed: Optional[int] = None
    offside: Optional[int] = None
    key_passes: Optional[int] = None
    dribbles_completed: Optional[int] = None
    dribbles_total: Optional[int] = None
    times_dribbled_past: Optional[int] = None
    fouls_committed: Optional[int] = None
    fouls_suffered: Optional[int] = None
    woodwork: Optional[int] = None

    def __post_init__(self):
        # basic monotonic checks when both sides are present
        if (self.shots_on_target is not None and self.shots_total is not None
                and self.shots_on_target > self.shots_total):
            raise ValueError("shots_on_target cannot exceed shots_total")
        if (self.dribbles_completed is not None and self.dribbles_total is not None
                and self.dribbles_completed > self.dribbles_total):
            raise ValueError("dribbles_completed cannot exceed dribbles_total")
        # non-negative
        for name, val in self.__dict__.items():
            if name == "basic_stats_id": continue
            if isinstance(val, int) and val < 0:
                raise ValueError(f"{name} must be >= 0")
            if isinstance(val, float) and val < 0:
                raise ValueError(f"{name} must be >= 0.0")

@dataclass(frozen=True, slots=True)
class MidfielderStats:
    basic_stats_id: int
    expected_assists: Optional[float] = None
    tackles_won: Optional[int] = None
    tackles_total: Optional[int] = None
    crosses: Optional[int] = None
    fouls_committed: Optional[int] = None
    fouls_suffered: Optional[int] = None
    expected_goals: Optional[float] = None
    xg_from_shots_on_target: Optional[float] = None
    big_chances: Optional[int] = None
    big_chances_missed: Optional[int] = None
    big_chances_scored: Optional[int] = None
    interceptions: Optional[int] = None
    key_passes: Optional[int] = None
    passes_in_final_third: Optional[int] = None
    back_passes: Optional[int] = None
    long_passes_completed: Optional[int] = None
    woodwork: Optional[int] = None
    possessions_won_final_third: Optional[int] = None
    times_dribbled_past: Optional[int] = None
    dribbles_completed: Optional[int] = None
    dribbles_total: Optional[int] = None
    long_passes_total: Optional[int] = None
    crosses_total: Optional[int] = None
    shots_off_target: Optional[int] = None
    shots_on_target: Optional[int] = None
    shots_total: Optional[int] = None

    def __post_init__(self):
        if (self.tackles_won is not None and self.tackles_total is not None
                and self.tackles_won > self.tackles_total):
            raise ValueError("tackles_won cannot exceed tackles_total")
        if (self.long_passes_completed is not None and self.long_passes_total is not None
                and self.long_passes_completed > self.long_passes_total):
            raise ValueError("long_passes_completed cannot exceed long_passes_total")
        if (self.dribbles_completed is not None and self.dribbles_total is not None
                and self.dribbles_completed > self.dribbles_total):
            raise ValueError("dribbles_completed cannot exceed dribbles_total")
        if (self.shots_on_target is not None and self.shots_total is not None
                and self.shots_on_target > self.shots_total):
            raise ValueError("shots_on_target cannot exceed shots_total")
        for name, val in self.__dict__.items():
            if name == "basic_stats_id": continue
            if isinstance(val, int) and val < 0:
                raise ValueError(f"{name} must be >= 0")
            if isinstance(val, float) and val < 0:
                raise ValueError(f"{name} must be >= 0.0")
