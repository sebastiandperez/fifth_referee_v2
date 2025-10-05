from __future__ import annotations
from typing import Any, Dict, Iterable, Optional
import pandas as pd

from ..services import get_api, ApiService
from ..services.types import MatchItem
from .transforms import events_kpis_corrected, events_simple_kpis

SPANISH_EVENT_MAP = {
    "Gol": "Goal",
    "Tarjeta amarilla": "Yellow card",
    "Tarjeta roja": "Red card",
    "Pelota al poste": "Woodwork",
    "Woodwork": "Woodwork",
    "Substitution": "Substitution",
    "Own goal": "Own goal",
    "Penalty": "Penalty",
    "Penalty missed": "Penalty missed",
    "Disallowed goal": "Disallowed goal",
}

class DataAdapter:
    """
    Adaptador de datos para el Dashboard:
    - Expone DataFrames listos para usar en la UI.
    - Encapsula el cliente HTTP (ApiService) y normalizaciones básicas.
    """

    def __init__(self, api: Optional[ApiService] = None):
        self.api = api or get_api()

    # ----------------------
    # Discovery / summary
    # ----------------------
    def season_labels(self) -> list[str]:
        return self.api.cached_season_labels()

    def competitions_for_label(self, season_label: str):
        return self.api.cached_competitions(season_label)

    def resolve_season(self, season_label: str, competition_id: int) -> Optional[int]:
        return self.api.resolve_season(season_label, competition_id)

    def season_summary(self, season_id: int) -> Dict[str, Any]:
        return self.api.season_summary(season_id)

    # ----------------------
    # Standings
    # ----------------------
    def standings_df(self, season_id: int) -> pd.DataFrame:
        df = self.api.standings_df(season_id)
        return self.api.normalize_standings(df)

    # ----------------------
    # Matches
    # ----------------------
    def iter_matches(self, season_id: int, finalized: Optional[bool] = None, limit: int = 1000) -> Iterable[MatchItem]:
        return self.api.iter_matches(season_id, finalized=finalized, limit=limit, offset=0)

    def matches_df(self, season_id: int, finalized: Optional[bool] = None, limit: int = 1000) -> pd.DataFrame:
        rows = [m.__dict__ for m in self.iter_matches(season_id, finalized=finalized, limit=limit)]
        if not rows:
            return pd.DataFrame(columns=[
                "match_id", "matchday_id", "home_team_id", "away_team_id",
                "home_score", "away_score", "duration", "stadium"
            ])
        df = pd.DataFrame(rows)
        # Asegurar tipos
        for c in ("match_id", "matchday_id", "home_team_id", "away_team_id", "duration"):
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        return df

    # ----------------------
    # Players
    # ----------------------
    def players_df(self, season_id: int) -> pd.DataFrame:
        players = self.api.players(season_id)
        if not players:
            return pd.DataFrame(columns=[
                "player_id", "player_name", "team_id", "team_name",
                "season_team_id", "jersey_number"
            ])
        return pd.DataFrame([p.__dict__ for p in players])

    # ----------------------
    # Stats
    # ----------------------
    def basic_stats_df(self, season_id: int, limit: int = 5000) -> pd.DataFrame:
        items = self.api.basic_stats_all(season_id, limit=limit)
        return pd.DataFrame(items) if items else pd.DataFrame(columns=[
            "basic_stats_id","match_id","player_id","minutes","goals","assists","touches",
            "passes_total","passes_completed","ball_recoveries","possessions_lost",
            "aerial_duels_won","aerial_duels_total","ground_duels_won","ground_duels_total"
        ])

    def goalkeeper_stats_df(self, season_id: int, limit: int = 5000) -> pd.DataFrame:
        items = self.api.gk_stats_all(season_id, limit=limit)
        return pd.DataFrame(items) if items else pd.DataFrame(columns=[
            "basic_stats_id","goalkeeper_saves","saves_inside_box","goals_conceded",
            "xg_on_target_against","goals_prevented","punches_cleared","high_claims",
            "clearances","penalties_received","penalties_saved","interceptions","times_dribbled_past"
        ])

    def events_df(
        self,
        season_id: int,
        *,
        team_id: Optional[int] = None,
        event_type: Optional[str] = None,
        minute_from: Optional[int] = None,
        minute_to: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Obtiene eventos normalizados desde la API.
        - Convierte nombres de eventos de español a inglés
        - Normaliza tipos de columnas
        """
        items = self.api.events_all(
            season_id,
            team_id=team_id,
            event_type=event_type,
            minute_from=minute_from,
            minute_to=minute_to,
            page_limit=1000,
        )
        if not items:
            return pd.DataFrame(columns=[
                "event_id","match_id","event_type","minute",
                "main_player_id","extra_player_id","team_id"
            ])

        df = pd.DataFrame(items)

        # Normaliza columnas que pueden faltar
        for c in ["event_id","match_id","minute","main_player_id","extra_player_id","team_id"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")

        if "player_id" in df.columns and "main_player_id" not in df.columns:
            df["main_player_id"] = pd.to_numeric(df["player_id"], errors="coerce")

        # Normaliza nombres de evento (ES→EN)
        if "event_type" in df.columns:
            df["event_type"] = df["event_type"].astype(str).map(
                lambda x: SPANISH_EVENT_MAP.get(x, x)
            )

        return df[[
            "event_id","match_id","event_type","minute",
            "main_player_id","extra_player_id","team_id"
        ]].copy()

    def events_kpis_df(
        self,
        season_id: int,
        *,
        matches_played_map: Dict[int, int],
    ) -> pd.DataFrame:
        """
        Devuelve KPIs completos basados en eventos por team_id:

        KPIs simples (sin requerir resultados):
        - g_0_15, g_76_90p: goles en ventanas de tiempo específicas
        - yc_pg, rc_pg, subs_pg, wood_pg: eventos por partido

        KPIs avanzados (requieren analizar resultados):
        - goals_both_halves_pct: % partidos donde marcó en ambas mitades
        - scored_first_and_won_pct: % partidos donde marcó primero Y ganó

        Args:
            season_id: ID de la temporada
            matches_played_map: dict {team_id: partidos_jugados} desde standings

        Returns:
            DataFrame con todas las métricas combinadas
        """
        # 1. Obtener eventos normalizados
        events = self.events_df(season_id)

        if events.empty:
            return pd.DataFrame(columns=[
                "team_id", "g_0_15", "g_76_90p", "yc_pg", "rc_pg", "subs_pg", "wood_pg",
                "goals_both_halves_pct", "scored_first_and_won_pct"
            ])

        # 2. KPIs simples (no requieren resultados)
        simple_kpis = events_simple_kpis(events, matches_played_map)

        # 3. KPIs avanzados (requieren partidos finalizados)
        matches = list(self.iter_matches(season_id, finalized=True, limit=10_000))
        advanced_kpis = events_kpis_corrected(matches, events, first_half_limit=45)

        # 4. Combinar ambos DataFrames
        if simple_kpis.empty and advanced_kpis.empty:
            return pd.DataFrame(columns=[
                "team_id", "g_0_15", "g_76_90p", "yc_pg", "rc_pg", "subs_pg", "wood_pg",
                "goals_both_halves_pct", "scored_first_and_won_pct"
            ])

        # Merge con outer join para capturar todos los equipos
        result = pd.merge(
            simple_kpis,
            advanced_kpis,
            on="team_id",
            how="outer"
        ).fillna(0.0)

        # Asegurar orden de columnas
        final_cols = [
            "team_id", "g_0_15", "g_76_90p", "yc_pg", "rc_pg", "subs_pg", "wood_pg",
            "goals_both_halves_pct", "scored_first_and_won_pct"
        ]

        return result[final_cols].sort_values("team_id").reset_index(drop=True)


# Singleton conveniente
_data_singleton: Optional[DataAdapter] = None

def get_data() -> DataAdapter:
    global _data_singleton
    if _data_singleton is None:
        _data_singleton = DataAdapter()
    return _data_singleton
