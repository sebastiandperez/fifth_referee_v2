# interfaces/dash/services/api.py
from __future__ import annotations

import os
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple
import pandas as pd
import requests

from ..config import API_BASE
from .cache import MemoryCache
from .types import Competition, MatchItem, PlayerItem

_DEFAULT_TIMEOUT = float(os.getenv("FR_HTTP_TIMEOUT", "8.0"))
_RETRY_TIMES = int(os.getenv("FR_HTTP_RETRIES", "2"))
MAX_API_LIMIT = 1000  # contrato del backend: le=1000


class ApiError(RuntimeError):
    pass


class ApiService:
    """
    Servicio de acceso a la API HTTP (FastAPI).
    Encapsula peticiones, normalizaciones y helpers para el Dashboard.
    """

    def __init__(self, base_url: str | None = None, timeout: float = _DEFAULT_TIMEOUT):
        self.base_url = (base_url or API_BASE).rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        self._cache = MemoryCache()

    # --------------------------
    # HTTP core
    # --------------------------
    def _url(self, path: str) -> str:
        if path.startswith("http"):
            return path
        path = path if path.startswith("/") else f"/{path}"
        return f"{self.base_url}{path}"

    def _request(self, method: str, path: str, **kwargs) -> Any:
        url = self._url(path)
        kwargs.setdefault("timeout", self.timeout)
        last_exc: Optional[Exception] = None

        for attempt in range(_RETRY_TIMES + 1):
            try:
                r = self._session.request(method.upper(), url, **kwargs)
                if r.status_code >= 400:
                    try:
                        # FastAPI suele empaquetar errores en {"detail": ...}
                        detail = r.json().get("detail")
                    except Exception:
                        detail = r.text[:200]
                    raise ApiError(f"{r.status_code} {method} {url} :: {detail}")
                if "application/json" in (r.headers.get("Content-Type") or ""):
                    return r.json()
                return r.text
            except Exception as e:
                last_exc = e
                if attempt < _RETRY_TIMES:
                    time.sleep(0.25 * (attempt + 1))
                else:
                    raise ApiError(f"HTTP error {method} {url}: {e}") from e

        if last_exc:
            raise last_exc

    # --------------------------
    # Discovery
    # --------------------------
    def season_labels(self) -> List[str]:
        j = self._request("GET", "/v1/season-labels")
        return list(j.get("items", []))

    def competitions_for_label(self, season_label: str) -> List[Competition]:
        j = self._request("GET", f"/v1/season-labels/{season_label}/competitions")
        items = j.get("items", [])
        return [Competition(id=int(x["id"]), name=str(x["name"])) for x in items]

    def resolve_season(self, season_label: str, competition_id: int) -> Optional[int]:
        j = self._request("GET", "/v1/seasons/resolve", params={"season_label": season_label, "competition_id": competition_id})
        return int(j["season_id"]) if j and "season_id" in j else None

    def season_summary(self, season_id: int) -> Dict[str, Any]:
        j = self._request("GET", f"/v1/seasons/{season_id}/summary")
        return {
            "season_id": j.get("season_id"),
            "season_label": j.get("season_label"),
            "competition_id": j.get("competition_id"),
            "competition_name": j.get("competition_name"),
            "team_count": j.get("team_count", 0),
            "matchday_min": j.get("matchday_min"),
            "matchday_max": j.get("matchday_max"),
            "last_finalized_matchday": j.get("last_finalized_matchday"),
        }

    # --------------------------
    # Standings
    # --------------------------
    def standings_df(self, season_id: int) -> pd.DataFrame:
        j = self._request("GET", f"/v1/seasons/{season_id}/standings")
        rows = j.get("rows", []) if isinstance(j, dict) else (j or [])
        df = pd.DataFrame(rows)
        return df

    def normalize_standings(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df.copy()

        rename_map = {"pts": "points", "mp": "played"}
        df = df.rename(columns=rename_map).copy()

        must_have = [
            "team_id", "team_name", "played", "win", "draw", "loss",
            "gf", "ga", "gd", "points", "position"
        ]
        for col in must_have:
            if col not in df.columns:
                df[col] = 0

        for col in ["team_id", "played", "win", "draw", "loss", "gf", "ga", "gd", "points", "position"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

        df["team_name"] = df["team_name"].astype(str)
        return df

    # --------------------------
    # Matches (paginado)
    # --------------------------
    def iter_matches(
        self,
        season_id: int,
        *,
        finalized: Optional[bool] = None,
        limit: Optional[int] = None,   # None = traer “todo” paginando
        offset: int = 0,
    ) -> Iterable[MatchItem]:
        """
        Itera /v1/seasons/{season_id}/matches respetando el límite del servidor (≤1000),
        paginando con offset. Si limit=None, trae todo lo disponible.
        """
        fetched = 0
        while True:
            if limit is None:
                page_size = MAX_API_LIMIT
            else:
                remaining = max(0, limit - fetched)
                if remaining == 0:
                    break
                page_size = min(MAX_API_LIMIT, remaining)

            params: Dict[str, Any] = {"limit": page_size, "offset": offset}
            if finalized is not None:
                # FastAPI parsea bools en querystring (True/False)
                params["finalized"] = finalized

            j = self._request("GET", f"/v1/seasons/{season_id}/matches", params=params)
            items = j.get("items", []) if isinstance(j, dict) else []

            if not items:
                break

            for m in items:
                yield MatchItem(
                    match_id=int(m["match_id"]),
                    matchday_id=int(m["matchday_id"]),
                    home_team_id=int(m.get("home_team_id", m.get("local_team_id"))),
                    away_team_id=int(m["away_team_id"]),
                    home_score=m.get("home_score", m.get("local_score")),
                    away_score=m.get("away_score"),
                    duration=int(m.get("duration", 90)),
                    stadium=m.get("stadium"),
                )

            n = len(items)
            fetched += n
            offset += n

            if limit is not None and fetched >= limit:
                break
            if n < page_size:
                break

    # --------------------------
    # Players
    # --------------------------
    def players(self, season_id: int) -> List[PlayerItem]:
        j = self._request("GET", f"/v1/seasons/{season_id}/players")
        items = j.get("items", []) if isinstance(j, dict) else []
        out: List[PlayerItem] = []
        for p in items:
            out.append(
                PlayerItem(
                    player_id=int(p["player_id"]),
                    player_name=str(p["player_name"]),
                    team_id=int(p["team_id"]),
                    team_name=str(p["team_name"]),
                    season_team_id=int(p["season_team_id"]),
                    jersey_number=(int(p["jersey_number"]) if p.get("jersey_number") is not None else None),
                )
            )
        return out

    # --------------------------
    # Basic stats (paginado)
    # --------------------------
    def basic_stats_page(
        self,
        season_id: int,
        limit: int = MAX_API_LIMIT,
        offset: int = 0,
        team_id: Optional[int] = None,
        player_id: Optional[int] = None,
        matchday_from: Optional[int] = None,
        matchday_to: Optional[int] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"limit": min(limit, MAX_API_LIMIT), "offset": offset}
        if team_id is not None:
            params["team_id"] = team_id
        if player_id is not None:
            params["player_id"] = player_id
        if matchday_from is not None:
            params["matchday_from"] = matchday_from
        if matchday_to is not None:
            params["matchday_to"] = matchday_to
        return self._request("GET", f"/v1/seasons/{season_id}/stats/basic", params=params)

    def basic_stats_all(
        self,
        season_id: int,
        *,
        team_id: Optional[int] = None,
        player_id: Optional[int] = None,
        matchday_from: Optional[int] = None,
        matchday_to: Optional[int] = None,
        limit: Optional[int] = None,  # None=todo
    ) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        fetched = 0
        offset = 0

        while True:
            if limit is None:
                page_size = MAX_API_LIMIT
            else:
                remaining = max(0, limit - fetched)
                if remaining == 0:
                    break
                page_size = min(MAX_API_LIMIT, remaining)

            page = self.basic_stats_page(
                season_id,
                limit=page_size,
                offset=offset,
                team_id=team_id,
                player_id=player_id,
                matchday_from=matchday_from,
                matchday_to=matchday_to,
            )
            chunk = page.get("items", []) if isinstance(page, dict) else []
            if not chunk:
                break

            items.extend(chunk)
            n = len(chunk)
            fetched += n
            offset += n

            if limit is not None and fetched >= limit:
                break
            if n < page_size:
                break

        return items

    # --------------------------
    # Goalkeeper stats (paginado)
    # --------------------------
    def gk_stats_page(self, season_id: int, limit: int = MAX_API_LIMIT, offset: int = 0) -> Dict[str, Any]:
        return self._request(
            "GET",
            f"/v1/seasons/{season_id}/stats/goalkeeper",
            params={"limit": min(limit, MAX_API_LIMIT), "offset": offset},
        )

    def gk_stats_all(self, season_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        fetched = 0
        offset = 0

        while True:
            if limit is None:
                page_size = MAX_API_LIMIT
            else:
                remaining = max(0, limit - fetched)
                if remaining == 0:
                    break
                page_size = min(MAX_API_LIMIT, remaining)

            page = self.gk_stats_page(season_id, limit=page_size, offset=offset)
            chunk = page.get("items", []) if isinstance(page, dict) else []
            if not chunk:
                break

            items.extend(chunk)
            n = len(chunk)
            fetched += n
            offset += n

            if limit is not None and fetched >= limit:
                break
            if n < page_size:
                break

        return items

    # --------------------------
    # Helpers de caché
    # --------------------------
    def cached_season_labels(self, ttl: float = 60.0) -> List[str]:
        key = "season-labels"
        v = self._cache.get("discovery", key)
        if v is not None:
            return v
        data = self.season_labels()
        self._cache.set("discovery", key, data, ttl=ttl)
        return data

    def cached_competitions(self, season_label: str, ttl: float = 60.0) -> List[Competition]:
        key = f"comps:{season_label}"
        v = self._cache.get("discovery", key)
        if v is not None:
            return v
        data = self.competitions_for_label(season_label)
        self._cache.set("discovery", key, data, ttl=ttl)
        return data

    def events_page(
        self,
        season_id: int,
        *,
        team_id: Optional[int] = None,
        match_id: Optional[int] = None,
        event_type: Optional[str] = None,
        minute_from: Optional[int] = None,
        minute_to: Optional[int] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "limit": min(limit, 5000),
            "offset": offset,
        }
        if team_id is not None:     params["team_id"] = int(team_id)
        if match_id is not None:    params["match_id"] = int(match_id)
        if event_type is not None:  params["event_type"] = str(event_type)
        if minute_from is not None: params["minute_from"] = int(minute_from)
        if minute_to is not None:   params["minute_to"] = int(minute_to)

        items = self._request("GET", f"/v1/seasons/{season_id}/events", params=params)
        # La API ya devuelve lista; la envolvemos en una forma uniforme
        return {"items": (items or [])}

    def events_all(
        self,
        season_id: int,
        *,
        team_id: Optional[int] = None,
        event_type: Optional[str] = None,
        minute_from: Optional[int] = None,
        minute_to: Optional[int] = None,
        page_limit: int = 1000
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        offset = 0
        while True:
            page = self.events_page(
                season_id,
                team_id=team_id,
                event_type=event_type,
                minute_from=minute_from,
                minute_to=minute_to,
                limit=page_limit,
                offset=offset,
            )
            items = page.get("items", [])
            if not items:
                break
            out.extend(items)
            if len(items) < page_limit:
                break
            offset += page_limit
        return out

def iter_events(self, season_id: int,
                batch: int = 1000,
                **filters) -> Iterable[dict]:
    """
    Iterador sobre todos los eventos (pagina hasta agotar).
    """
    offset = 0
    batch = max(1, min(int(batch), 5000))
    while True:
        page = self.events_page(season_id, limit=batch, offset=offset, **filters)
        if not page:
            break
        for e in page:
            yield e
        if len(page) < batch:
            break
        offset += batch



# Singleton conveniente para la UI
_api_singleton: Optional[ApiService] = None


def get_api(base_url: Optional[str] = None) -> ApiService:
    """
    Devuelve un ApiService único. Puedes inyectar otra base URL si lo necesitas.
    """
    global _api_singleton
    if _api_singleton is None:
        _api_singleton = ApiService(base_url=base_url)
    return _api_singleton
