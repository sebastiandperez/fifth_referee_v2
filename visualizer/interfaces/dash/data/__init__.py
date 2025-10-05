# interfaces/dash/data/__init__.py
from __future__ import annotations

import os
from typing import Optional, Iterable

import pandas as pd

from .adapters import DataAdapter
from .transforms import (
    normalize_standings as _normalize_standings,
    enrich_with_ppg_gih as _enrich_with_ppg_gih,
    standings_shadow_by_ppg as _shadow_by_ppg,
    last_n_ppg as _last_n_ppg,
    market_kpis as _market_kpis_basic,
    upcoming_strength as _upcoming_strength,
    home_away_splits_df as _home_away_splits_df,
)

# Import opcional: KPIs ampliadas desde eventos (si aún no existen, caemos al básico)
try:
    from .transforms import market_kpis_from_events as _market_kpis_events
except Exception:
    _market_kpis_events = None

from ..services import get_api, ApiService
from ..services.types import MatchItem


class DataFacade(DataAdapter):
    """
    Façade de datos para la UI (Dash).

    - Puedes inyectar un ApiService existente (api=...).
    - O construir uno indicando base_url=...
    - Si no pasas nada, usa get_api() (singleton de la app).

    Expone transformaciones “amigables” para la UI y gestiona
    automáticamente KPIs desde eventos si están disponibles.
    """

    def __init__(self, api: Optional[ApiService] = None, *, base_url: Optional[str] = None):
        if api is not None:
            svc = api
        elif base_url:
            svc = ApiService(base_url=base_url)
        else:
            svc = get_api()
        super().__init__(api=svc)

    # ----------------------
    # Transforms directos
    # ----------------------
    def normalize_standings(self, df: pd.DataFrame) -> pd.DataFrame:
        return _normalize_standings(df)

    def enrich_with_ppg_gih(self, df: pd.DataFrame) -> pd.DataFrame:
        return _enrich_with_ppg_gih(df)

    def standings_shadow_by_ppg(self, df: pd.DataFrame) -> pd.DataFrame:
        return _shadow_by_ppg(df)

    # ----------------------
    # Helpers internos
    # ----------------------
    def _finalized_matches(self, season_id: int) -> Iterable[MatchItem]:
        """
        Itera todos los partidos finalizados respetando el límite del API (<=1000 por página).
        Nota: ApiService.iter_matches ya pagina internamente (limit/offset).
        """
        return self.iter_matches(season_id, finalized=True, limit=1000)

    def _upcoming_matches(self, season_id: int) -> Iterable[MatchItem]:
        """Itera próximos/no finalizados (para Fixture Difficulty, etc.)."""
        return self.iter_matches(season_id, finalized=False, limit=1000)

    # ----------------------
    # Transforms que requieren datos de la API
    # ----------------------
    def last_n_ppg(self, season_id: int, n: int = 5) -> pd.DataFrame:
        matches = self._finalized_matches(season_id)
        return _last_n_ppg(matches, n=n)

    def market_kpis(self, season_id: int) -> pd.DataFrame:
        """
        KPIs de mercado por equipo.
        - Si hay eventos (iter_events) y la función avanzada está disponible,
          usa `market_kpis_from_events` (Both Halves, Scored-first+Won).
        - Si no, cae a KPIs básicas derivadas del resultado final (BTTS, Over2.5, CS).
        Devuelve fracciones 0..1 (la UI decide si mostrar %).
        """
        matches_iter = self._finalized_matches(season_id)

        events_supported = hasattr(self.api, "iter_events") and (_market_kpis_events is not None)
        if events_supported:
            try:
                # Generador paginado; materializamos una vez.
                events = list(self.api.iter_events(season_id, batch=2000))
            except Exception:
                events = []
            if events:
                df = _market_kpis_events(
                    matches_iter=self._finalized_matches(season_id),  # re-iterable fresco
                    events_iter=events
                )
                if not df.empty:
                    return df[[
                        "team_id",
                        "btts_pct", "over25_pct", "clean_sheet_pct",
                        "goals_both_halves_pct", "scored_first_and_won_pct"
                    ]].copy()

        # Fallback básico
        basic = _market_kpis_basic(matches_iter)
        if basic.empty:
            return pd.DataFrame(columns=[
                "team_id",
                "btts_pct", "over25_pct", "clean_sheet_pct",
                "goals_both_halves_pct", "scored_first_and_won_pct"
            ])
        for col in ("goals_both_halves_pct", "scored_first_and_won_pct"):
            if col not in basic.columns:
                basic[col] = pd.NA
        return basic[[
            "team_id",
            "btts_pct", "over25_pct", "clean_sheet_pct",
            "goals_both_halves_pct", "scored_first_and_won_pct"
        ]].copy()

    def upcoming_strength(self, season_id: int, next_k: int = 5) -> pd.DataFrame:
        """
        PPG medio de los próximos K rivales por equipo.
        Requiere standings enriquecidos (para mapear PPG) + próximos partidos.
        """
        base = self.enrich_with_ppg_gih(self.normalize_standings(self.standings_df(season_id)))
        fut = self._upcoming_matches(season_id)
        return _upcoming_strength(base, fut, next_k=next_k)

    def home_away_splits(self, season_id: int) -> pd.DataFrame:
        """
        Splits por equipo: home_ppg, away_ppg, home_gd, away_gd.
        """
        matches = self._finalized_matches(season_id)
        return _home_away_splits_df(matches)


# ----------------------
# Punto de entrada para la UI
# ----------------------
def get_data(base: Optional[str] = None) -> DataFacade:
    """
    Crea un DataFacade listo para usar desde la UI.
    - Si 'base' es None, intenta FR_API_BASE o usa el ApiService por defecto.
    - Si 'base' está dado, crea un ApiService aislado a esa URL.
    """
    base = base or os.getenv("FR_API_BASE", None)
    if base:
        return DataFacade(base_url=base)
    return DataFacade()


# ----------------------
# Exports funcionales (atajos)
# ----------------------
normalize_standings = _normalize_standings
enrich_with_ppg_gih = _enrich_with_ppg_gih
standings_shadow_by_ppg = _shadow_by_ppg
last_n_ppg = _last_n_ppg
# Nota: este export es el cálculo básico; el façade .market_kpis() decide si usar eventos o no.
market_kpis = _market_kpis_basic
