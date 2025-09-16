from __future__ import annotations
from typing import Any, Mapping, Optional

from domain.models import (
    # IDs / Enums / VOs / Entities / DTOs
    TeamId, PlayerId, CompetitionId, SeasonId, MatchdayId, MatchId, BasicStatsId, EventId,
    Team, Player, Competition, Season, Matchday, Match, Score, Event,
    StandingRow, TeamFormRow, TeamSplit, ScorerRow, AssisterRow, KeeperKPI,
    TeamResult,
)

def row_team(r: Mapping[str, Any]) -> Team:
    return Team(
        team_id=TeamId(int(r["team_id"])),
        team_name=r["team_name"],
        team_city=r.get("team_city"),
        team_stadium=r.get("team_stadium"),
    )

def row_competition(r: Mapping[str, Any]) -> Competition:
    return Competition(
        competition_id=CompetitionId(int(r["competition_id"])),
        competition_name=r["competition_name"],
        default_matchdays=r.get("default_matchdays"),
        is_international=r.get("is_international"),
        continent=r.get("continent"),
    )

def row_season(r: Mapping[str, Any]) -> Season:
    return Season(
        season_id=SeasonId(int(r["season_id"])),
        season_label=r["season_label"],
        competition_id=CompetitionId(int(r["competition_id"])),
        is_completed=r.get("is_completed"),
    )

def row_matchday(r: Mapping[str, Any]) -> Matchday:
    return Matchday(
        matchday_id=MatchdayId(int(r["matchday_id"])),
        season_id=SeasonId(int(r["season_id"])),
        matchday_number=int(r["matchday_number"]),
    )

def row_match(r: Mapping[str, Any]) -> Match:
    score = Score(
        home=r.get("local_score"),
        away=r.get("away_score"),
    )
    return Match(
        match_id=MatchId(int(r["match_id"])),
        matchday_id=MatchdayId(int(r["matchday_id"])),
        local_team_id=TeamId(int(r["local_team_id"])),
        away_team_id=TeamId(int(r["away_team_id"])),
        score=score,
        kickoff_utc=r.get("kickoff_utc"),
        stadium=r.get("stadium"),
        duration_minutes=r.get("duration_minutes") or 90,
    )

def row_event(r: Mapping[str, Any]) -> Event:
    return Event(
        event_id=EventId(int(r["event_id"])),
        match_id=MatchId(int(r["match_id"])),
        event_type=r["event_type"],
        minute=r.get("minute"),
        main_player_id=PlayerId(int(r["main_player_id"])) if r.get("main_player_id") is not None else None,
        extra_player_id=PlayerId(int(r["extra_player_id"])) if r.get("extra_player_id") is not None else None,
        team_id=TeamId(int(r["team_id"])) if r.get("team_id") is not None else None,
    )

def row_standing(r: Mapping[str, Any]) -> StandingRow:
    return StandingRow(
        team_id=TeamId(int(r["team_id"])),
        team_name=r["team_name"],
        MP=int(r["MP"]), Pts=int(r["Pts"]),
        GF=int(r["GF"]), GA=int(r["GA"]),
        GD=int(r["GD"]),
    )

def row_team_form(r: Mapping[str, Any], perspective_team_id: int) -> TeamFormRow:
    # calcula W/D/L desde la perspectiva del equipo consultado
    ls = r.get("local_score")
    as_ = r.get("away_score")
    result: Optional[TeamResult] = None
    if ls is not None and as_ is not None:
        if int(r["home_team_id"]) == perspective_team_id:
            if ls > as_: result = TeamResult.WIN
            elif ls == as_: result = TeamResult.DRAW
            else: result = TeamResult.LOSS
        else:
            if as_ > ls: result = TeamResult.WIN
            elif as_ == ls: result = TeamResult.DRAW
            else: result = TeamResult.LOSS

    return TeamFormRow(
        match_id=MatchId(int(r["match_id"])),
        matchday_number=int(r["matchday_number"]),
        home_team_id=TeamId(int(r["home_team_id"])),
        away_team_id=TeamId(int(r["away_team_id"])),
        local_score=ls,
        away_score=as_,
        result=result,
    )

def row_team_split(home_ppg: float, away_ppg: float,
                   home_gf: int, home_ga: int, away_gf: int, away_ga: int) -> TeamSplit:
    return TeamSplit(
        home_ppg=home_ppg, away_ppg=away_ppg,
        home_gf=home_gf, home_ga=home_ga,
        away_gf=away_gf, away_ga=away_ga,
        home_gd=home_gf - home_ga, away_gd=away_gf - away_ga,
    )

def row_scorer(r: Mapping[str, Any]) -> ScorerRow:
    return ScorerRow(
        player_id=PlayerId(int(r["player_id"])),
        player_name=r["player_name"],
        goals=int(r["goals"]),
    )

def row_assister(r: Mapping[str, Any]) -> AssisterRow:
    return AssisterRow(
        player_id=PlayerId(int(r["player_id"])),
        player_name=r["player_name"],
        assists=int(r["assists"]),
    )

def row_keeper_kpi(r: Mapping[str, Any]) -> KeeperKPI:
    return KeeperKPI(
        player_id=PlayerId(int(r["player_id"])),
        player_name=r["player_name"],
        goalkeeper_saves=r.get("saves"),
        goals_prevented=r.get("goals_prevented"),
        goals_conceded=r.get("goals_conceded"),
    )
