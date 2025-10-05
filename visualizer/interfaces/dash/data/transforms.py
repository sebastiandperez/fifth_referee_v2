from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Optional, Dict, Any

import numpy as np
import pandas as pd

from ..services.types import MatchItem

_GOAL_TYPES = {"Goal", "Own goal"}  # NO contamos 'Disallowed goal' ni 'Penalty' (a menos que tu DB marque 'Penalty' solo si entra)
_FIRST_HALF_MAX = 45  # 0..45 => 1a parte

# ===========================================================
# Normalización de standings
# ===========================================================
def normalize_standings(df_in: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza el DataFrame de standings a un esquema estable:

      team_id (int) | team_name (str) | position (int) |
      played (int)  | win (int) | draw (int) | loss (int) |
      gf (int)      | ga (int)  | gd (int)   | points (int)

    Acepta columnas con nombres alternativos habituales y completa valores faltantes.
    """
    if df_in is None or df_in.empty:
        return pd.DataFrame(
            columns=["team_id", "team_name", "position", "played", "win",
                     "draw", "loss", "gf", "ga", "gd", "points"]
        )

    df = df_in.copy()

    # Mapeos tolerantes a variantes
    col_map = {
        "team_id": ["team_id", "id", "club_id"],
        "team_name": ["team_name", "name", "club_name"],
        "position": ["position", "rank", "pos"],
        "played": ["played", "mp", "matches_played"],
        "win": ["win", "w", "wins"],
        "draw": ["draw", "d", "draws"],
        "loss": ["loss", "l", "losses"],
        "gf": ["gf", "goals_for", "goals_scored"],
        "ga": ["ga", "goals_against", "goals_conceded"],
        "gd": ["gd", "goal_diff", "goal_difference"],
        "points": ["points", "pts", "p"],
    }

    # Resolver primera columna presente para cada clave
    def _resolve(name: str, candidates: list[str]) -> str | None:
        for c in candidates:
            if c in df.columns:
                return c
        return None

    resolved: Dict[str, Optional[str]] = {k: _resolve(k, v) for k, v in col_map.items()}

    out = pd.DataFrame()
    # Copiar/renombrar lo que exista
    for std_col, src_col in resolved.items():
        if src_col is not None:
            out[std_col] = df[src_col]
        else:
            out[std_col] = np.nan

    # Coerción segura de numéricos
    for c in ("team_id", "position", "played", "win", "draw", "loss", "gf", "ga", "gd", "points"):
        out[c] = pd.to_numeric(out[c], errors="coerce")

    # team_name a string
    out["team_name"] = out["team_name"].astype(str)

    # Completar GD si falta
    if out["gd"].isna().all() or "gd" not in out:
        out["gd"] = (out["gf"].fillna(0) - out["ga"].fillna(0))

    # Rellenos por defecto y casting a int donde aplica
    for c in ("position", "played", "win", "draw", "loss", "gf", "ga", "gd", "points", "team_id"):
        out[c] = out[c].fillna(0).astype(int)

    # Orden básico si está disponible
    if "position" in out.columns:
        out = out.sort_values("position").reset_index(drop=True)

    # Columnas finales en orden
    return out[["team_id", "team_name", "position", "played", "win",
                "draw", "loss", "gf", "ga", "gd", "points"]]


# ===========================================================
# Utilidades base / compatibilidad (matches)
# ===========================================================
def _normalize_match_row_dict(m: Dict[str, Any]) -> Dict[str, Any]:
    """Compatibilidad por si llegan dicts 'local_*'/'visitor_*'."""
    return {
        "home_team_id": m.get("home_team_id", m.get("local_team_id")),
        "away_team_id": m.get("away_team_id", m.get("visitor_team_id")),
        "home_score":   m.get("home_score",   m.get("local_score")),
        "away_score":   m.get("away_score",   m.get("visitor_score")),
        "matchday_id":  m.get("matchday_id"),
        "match_id":     m.get("match_id"),
    }

def _normalize_match_item(m: MatchItem) -> Dict[str, Any]:
    return {
        "home_team_id": m.home_team_id,
        "away_team_id": m.away_team_id,
        "home_score":   m.home_score,
        "away_score":   m.away_score,
        "matchday_id":  m.matchday_id,
        "match_id":     m.match_id,
    }


# ===========================================================
# Enrich & standings helpers
# ===========================================================
def enrich_with_ppg_gih(df_stand: pd.DataFrame) -> pd.DataFrame:
    df = df_stand.copy()
    mp = pd.to_numeric(df.get("played", 0), errors="coerce").fillna(0)
    pts = pd.to_numeric(df.get("points", 0), errors="coerce").fillna(0.0)
    df["ppg"] = np.where(mp > 0, pts / mp, 0.0)
    df["gih"] = mp.max() - mp
    return df

def standings_shadow_by_ppg(df_stand: pd.DataFrame) -> pd.DataFrame:
    df = enrich_with_ppg_gih(df_stand)
    if df.empty:
        return pd.DataFrame(columns=["team_id", "shadow_rank"])
    df = df.sort_values(["ppg", "gd", "gf", "team_name"],
                        ascending=[False, False, False, True]).reset_index(drop=True)
    df["shadow_rank"] = np.arange(1, len(df) + 1)
    return df[["team_id", "shadow_rank"]]


# ===========================================================
# Forma reciente, fuerza calendario, KPIs de mercado (básicas)
# ===========================================================
def last_n_ppg(matches_iter: Iterable[MatchItem], n: int = 5) -> pd.DataFrame:
    """
    PPG de los últimos n resultados por equipo.
    matches_iter: iterable de MatchItem (idealmente solo finalizados).
    """
    per_team: dict[int, list[int]] = defaultdict(list)

    # normaliza + ordena temporalmente
    ms = [_normalize_match_item(m) for m in matches_iter]
    ms = [m for m in ms if m["home_team_id"] and m["away_team_id"]]
    ms.sort(key=lambda m: (m.get("matchday_id") or m.get("match_id") or 0,
                           m.get("match_id") or 0))

    for m in ms:
        hs, as_ = m["home_score"], m["away_score"]
        if hs is None or as_ is None:
            continue
        h, a = int(m["home_team_id"]), int(m["away_team_id"])
        if hs > as_:
            per_team[h].append(3); per_team[a].append(0)
        elif hs < as_:
            per_team[h].append(0); per_team[a].append(3)
        else:
            per_team[h].append(1); per_team[a].append(1)

    rows = []
    for tid, pts in per_team.items():
        tail = pts[-n:] if pts else []
        ppg_n = (sum(tail) / len(tail)) if tail else 0.0
        rows.append({"team_id": tid, f"ppg_last_{n}": ppg_n})

    if not rows:
        return pd.DataFrame(columns=["team_id", f"ppg_last_{n}"])
    return pd.DataFrame(rows)[["team_id", f"ppg_last_{n}"]]

def upcoming_strength(
    standings_df: pd.DataFrame,
    future_matches_iter: Iterable[MatchItem],
    next_k: int = 5
) -> pd.DataFrame:
    """
    Fuerza de calendario: PPG medio de los próximos K rivales por equipo.
    standings_df debe tener columnas team_id y ppg (usa enrich_with_ppg_gih antes).
    future_matches_iter: iterable de partidos (mezcla jugados/no jugados), se filtran no jugados.
    """
    if standings_df.empty:
        return pd.DataFrame(columns=["team_id", f"opp_ppg_next_{next_k}", f"fixtures_next_{next_k}"])
    st = enrich_with_ppg_gih(standings_df)
    ppg_map = dict(zip(st["team_id"], st["ppg"]))

    fut_map: dict[int, list[int]] = defaultdict(list)
    ms = [_normalize_match_item(m) for m in future_matches_iter]

    for m in ms:
        # Unplayed → ambos scores None
        if m["home_score"] is not None or m["away_score"] is not None:
            continue
        h, a = m["home_team_id"], m["away_team_id"]
        if not h or not a:
            continue
        fut_map[int(h)].append(int(a))
        fut_map[int(a)].append(int(h))

    rows = []
    for tid, opps in fut_map.items():
        nxt = opps[:next_k]
        mean_opp_ppg = float(np.mean([ppg_map.get(o, 0.0) for o in nxt])) if nxt else 0.0
        rows.append({
            "team_id": tid,
            f"opp_ppg_next_{next_k}": mean_opp_ppg,
            f"fixtures_next_{next_k}": len(nxt)
        })
    if not rows:
        return pd.DataFrame(columns=["team_id", f"opp_ppg_next_{next_k}", f"fixtures_next_{next_k}"])
    return pd.DataFrame(rows)[["team_id", f"opp_ppg_next_{next_k}", f"fixtures_next_{next_k}"]]

def market_kpis(matches_iter: Iterable[MatchItem]) -> pd.DataFrame:
    """
    KPIs estilo “mercado”: BTTS%, Over2.5%, Clean Sheet%.
    Usa solo partidos finalizados y los calcula desde marcadores finales.
    """
    agg: dict[int, dict[str, int]] = defaultdict(lambda: {"gp": 0, "btts": 0, "o25": 0, "cs": 0})
    for m in matches_iter:
        hs, as_ = m.home_score, m.away_score
        h, a = m.home_team_id, m.away_team_id
        if hs is None or as_ is None or not h or not a:
            continue
        h, a = int(h), int(a)
        btts = int(hs > 0 and as_ > 0)
        o25 = int((hs + as_) > 2)
        # Clean sheets
        if as_ == 0:
            agg[h]["cs"] += 1
        if hs == 0:
            agg[a]["cs"] += 1
        for tid in (h, a):
            agg[tid]["gp"] += 1
            agg[tid]["btts"] += btts
            agg[tid]["o25"]  += o25

    rows = []
    for tid, d in agg.items():
        gp = max(1, d["gp"])
        rows.append({
            "team_id": tid,
            "btts_pct": d["btts"] / gp,
            "over25_pct": d["o25"] / gp,
            "clean_sheet_pct": d["cs"] / gp,
        })
    if not rows:
        return pd.DataFrame(columns=["team_id", "btts_pct", "over25_pct", "clean_sheet_pct"])
    return pd.DataFrame(rows)[["team_id", "btts_pct", "over25_pct", "clean_sheet_pct"]]


# ===========================================================
# W-D-L (total, home, away) por equipo
# ===========================================================
def _wdl_from_matches(matches_iter: Iterable[MatchItem]) -> dict[int, dict[str, int]]:
    out: dict[int, dict[str, int]] = defaultdict(lambda: {"W": 0, "D": 0, "L": 0})
    for m in matches_iter:
        if m.home_score is None or m.away_score is None:
            continue
        h, a = int(m.home_team_id), int(m.away_team_id)
        hs, as_ = int(m.home_score), int(m.away_score)
        if hs > as_:
            out[h]["W"] += 1; out[a]["L"] += 1
        elif hs < as_:
            out[h]["L"] += 1; out[a]["W"] += 1
        else:
            out[h]["D"] += 1; out[a]["D"] += 1
    return out

def wdl_totals_for_team(matches_iter: Iterable[MatchItem], team_id: int) -> dict[str, int]:
    """Totales W-D-L para un equipo (partidos finalizados)."""
    agg = _wdl_from_matches(matches_iter)
    return agg.get(int(team_id), {"W": 0, "D": 0, "L": 0})

def wdl_home_for_team(matches_iter: Iterable[MatchItem], team_id: int) -> dict[str, int]:
    """W-D-L en casa."""
    W = D = L = 0
    for m in matches_iter:
        if m.home_team_id != team_id or m.home_score is None or m.away_score is None:
            continue
        if m.home_score > m.away_score: W += 1
        elif m.home_score < m.away_score: L += 1
        else: D += 1
    return {"W": W, "D": D, "L": L}

def wdl_away_for_team(matches_iter: Iterable[MatchItem], team_id: int) -> dict[str, int]:
    """W-D-L fuera de casa."""
    W = D = L = 0
    for m in matches_iter:
        if m.away_team_id != team_id or m.home_score is None or m.away_score is None:
            continue
        if m.away_score > m.home_score: W += 1
        elif m.away_score < m.home_score: L += 1
        else: D += 1
    return {"W": W, "D": D, "L": L}


# ===========================================================
# Línea de desempeño (caminata +1 / 0 / −1)
# ===========================================================
def performance_line_for_team(matches_iter: Iterable[MatchItem], team_id: int) -> pd.DataFrame:
    """
    Devuelve un DataFrame con:
      idx (1..n), step (−1/0/+1), cum (acumulado), match_id, matchday_id
    """
    items = []
    ms = list(matches_iter)
    # Orden temporal robusto
    ms.sort(key=lambda m: (m.matchday_id or m.match_id or 0, m.match_id or 0))

    for m in ms:
        if m.home_score is None or m.away_score is None:
            continue
        step = 0
        if m.home_team_id == team_id:
            if m.home_score > m.away_score: step = +1
            elif m.home_score < m.away_score: step = -1
        elif m.away_team_id == team_id:
            if m.away_score > m.home_score: step = +1
            elif m.away_score < m.home_score: step = -1
        else:
            continue

        items.append({
            "match_id": m.match_id,
            "matchday_id": m.matchday_id,
            "step": step,
        })

    if not items:
        return pd.DataFrame(columns=["idx", "step", "cum", "match_id", "matchday_id"])

    df = pd.DataFrame(items).reset_index(drop=True)
    df["idx"] = np.arange(1, len(df) + 1)
    df["cum"] = df["step"].cumsum()
    return df[["idx", "step", "cum", "match_id", "matchday_id"]]


# ===========================================================
# Extensiones desde eventos: KPIs avanzadas
# ===========================================================
_VALID_GOAL_TYPES = {"Goal", "Penalty", "Own goal"}
_INVALID_FOR_GOALS = {"Disallowed goal", "Penalty missed"}

def _match_team_map_from_matches(matches_iter: Iterable[MatchItem]) -> dict[int, tuple[int, int]]:
    """Mapa match_id -> (home_team_id, away_team_id)."""
    m = {}
    for x in matches_iter:
        if x.match_id is None:
            continue
        m[int(x.match_id)] = (int(x.home_team_id), int(x.away_team_id))
    return m

def _iter_valid_goals(events_iter: Iterable[dict], match_team_map: dict[int, tuple[int, int]]) -> Iterable[dict]:
    """
    Convierte eventos en goles válidos por equipo beneficiado.
    - Own goal → gol para el RIVAL
    - Ignora Disallowed goal y Penalty missed
    Yields: {match_id, scoring_team_id, minute}
    """
    for e in events_iter:
        et = e.get("event_type")
        if et in _INVALID_FOR_GOALS:
            continue
        if et not in _VALID_GOAL_TYPES:
            continue
        mid = e.get("match_id")
        minute = e.get("minute")
        tid = e.get("team_id")
        if mid is None or minute is None or tid is None:
            continue
        if mid not in match_team_map:
            continue
        home_id, away_id = match_team_map[mid]
        if et == "Own goal":
            # el beneficiado es el rival
            if int(tid) == home_id:
                scoring_team_id = away_id
            elif int(tid) == away_id:
                scoring_team_id = home_id
            else:
                continue
        else:
            scoring_team_id = int(tid)
        yield {"match_id": int(mid), "scoring_team_id": scoring_team_id, "minute": int(minute)}

def market_kpis_from_events(
    matches_iter: Iterable[MatchItem],
    events_iter: Iterable[dict],
    first_half_limit: int = 45,
) -> pd.DataFrame:
    """
    KPIs de mercado por equipo a partir de eventos:
      - btts_pct, over25_pct, clean_sheet_pct
      - goals_both_halves_pct, scored_first_and_won_pct
    Todas como fracciones 0..1
    """
    matches = list(matches_iter)
    mm = _match_team_map_from_matches(matches)
    if not mm:
        return pd.DataFrame(columns=[
            "team_id","btts_pct","over25_pct","clean_sheet_pct",
            "goals_both_halves_pct","scored_first_and_won_pct"
        ])

    goals = list(_iter_valid_goals(events_iter, mm))
    gdf = pd.DataFrame(goals) if goals else pd.DataFrame(columns=["match_id","scoring_team_id","minute"])

    rows = []
    for mid, (h, a) in mm.items():
        mg = gdf[gdf["match_id"] == mid] if not gdf.empty else pd.DataFrame(columns=gdf.columns)

        h_goals = int((mg["scoring_team_id"] == h).sum()) if not mg.empty else 0
        a_goals = int((mg["scoring_team_id"] == a).sum()) if not mg.empty else 0

        if not mg.empty:
            h_g1 = int(((mg["scoring_team_id"] == h) & (mg["minute"] <= first_half_limit)).sum())
            h_g2 = int(((mg["scoring_team_id"] == h) & (mg["minute"] >  first_half_limit)).sum())
            a_g1 = int(((mg["scoring_team_id"] == a) & (mg["minute"] <= first_half_limit)).sum())
            a_g2 = int(((mg["scoring_team_id"] == a) & (mg["minute"] >  first_half_limit)).sum())
            first_team = int(mg.sort_values("minute", kind="stable").iloc[0]["scoring_team_id"])
            home_scored_first = 1 if first_team == h else 0
            away_scored_first = 1 if first_team == a else 0
        else:
            h_g1 = h_g2 = a_g1 = a_g2 = 0
            home_scored_first = away_scored_first = 0

        btts = 1 if (h_goals > 0 and a_goals > 0) else 0
        over25 = 1 if (h_goals + a_goals) >= 3 else 0
        home_cs = 1 if a_goals == 0 else 0
        away_cs = 1 if h_goals == 0 else 0
        home_both_halves = 1 if (h_g1 > 0 and h_g2 > 0) else 0
        away_both_halves = 1 if (a_g1 > 0 and a_g2 > 0) else 0

        home_won = (h_goals > a_goals)
        away_won = (a_goals > h_goals)

        rows.append({
            "match_id": mid, "team_id": h, "played": 1,
            "btts": btts, "over25": over25, "cs": home_cs,
            "both_halves": home_both_halves,
            "scored_first_and_won": 1 if (home_scored_first and home_won) else 0
        })
        rows.append({
            "match_id": mid, "team_id": a, "played": 1,
            "btts": btts, "over25": over25, "cs": away_cs,
            "both_halves": away_both_halves,
            "scored_first_and_won": 1 if (away_scored_first and away_won) else 0
        })

    mdf = pd.DataFrame(rows)
    if mdf.empty:
        return pd.DataFrame(columns=[
            "team_id","btts_pct","over25_pct","clean_sheet_pct",
            "goals_both_halves_pct","scored_first_and_won_pct"
        ])

    agg = mdf.groupby("team_id", as_index=False).agg(
        btts_pct=("btts", lambda s: float(s.sum())/max(int(s.count()),1)),
        over25_pct=("over25", lambda s: float(s.sum())/max(int(s.count()),1)),
        clean_sheet_pct=("cs", lambda s: float(s.sum())/max(int(s.count()),1)),
        goals_both_halves_pct=("both_halves", lambda s: float(s.sum())/max(int(s.count()),1)),
        scored_first_and_won_pct=("scored_first_and_won", lambda s: float(s.sum())/max(int(s.count()),1)),
    )
    return agg[[
        "team_id","btts_pct","over25_pct","clean_sheet_pct",
        "goals_both_halves_pct","scored_first_and_won_pct"
    ]]


# ===========================================================
# Extras útiles para UI
# ===========================================================
def last_n_wdl_strip(matches_iter: Iterable[MatchItem], n: int = 5) -> pd.DataFrame:
    """
    Devuelve por equipo una tira textual con los últimos n resultados: "W W D L W"
    Columnas: team_id, wdl_last_n (str)
    """
    per_team: dict[int, list[str]] = defaultdict(list)
    ms = sorted(list(matches_iter), key=lambda m: (m.matchday_id or m.match_id or 0, m.match_id or 0))
    for m in ms:
        if m.home_score is None or m.away_score is None:
            continue
        h, a = int(m.home_team_id), int(m.away_team_id)
        if m.home_score > m.away_score:
            per_team[h].append("W"); per_team[a].append("L")
        elif m.home_score < m.away_score:
            per_team[h].append("L"); per_team[a].append("W")
        else:
            per_team[h].append("D"); per_team[a].append("D")
    rows = []
    for tid, seq in per_team.items():
        tail = seq[-n:] if seq else []
        rows.append({"team_id": tid, f"wdl_last_{n}": " ".join(tail)})
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["team_id", f"wdl_last_{n}"])

def home_away_splits_df(matches_iter: Iterable[MatchItem]) -> pd.DataFrame:
    """
    Retorna métricas por equipo: ppg home/away y GD home/away.
    Columnas: team_id, home_ppg, away_ppg, home_gd, away_gd
    """
    rows = []
    ms = [m for m in matches_iter if m.home_score is not None and m.away_score is not None]
    if not ms:
        return pd.DataFrame(columns=["team_id","home_ppg","away_ppg","home_gd","away_gd"])

    teams = set([int(m.home_team_id) for m in ms]) | set([int(m.away_team_id) for m in ms])

    def _pts(hs: int, as_: int) -> int:
        return 3 if hs > as_ else (1 if hs == as_ else 0)

    for t in sorted(teams):
        hms = [m for m in ms if int(m.home_team_id) == t]
        ams = [m for m in ms if int(m.away_team_id) == t]

        h_pts = sum(_pts(int(m.home_score), int(m.away_score)) for m in hms)
        a_pts = sum(_pts(int(m.away_score), int(m.home_score)) for m in ams)
        h_mp, a_mp = max(1, len(hms)), max(1, len(ams))
        h_ppg = round(h_pts / h_mp, 2)
        a_ppg = round(a_pts / a_mp, 2)

        h_gf = sum(int(m.home_score) for m in hms); h_ga = sum(int(m.away_score) for m in hms)
        a_gf = sum(int(m.away_score) for m in ams); a_ga = sum(int(m.home_score) for m in ams)

        rows.append({
            "team_id": t,
            "home_ppg": h_ppg, "away_ppg": a_ppg,
            "home_gd": int(h_gf - h_ga), "away_gd": int(a_gf - a_ga),
        })
    return pd.DataFrame(rows)

# ------------------------------------------------------------
# Helpers internos sobre eventos
# ------------------------------------------------------------
_GOAL_TYPES = {"Goal", "Own goal"}  # NO contamos 'Disallowed goal' ni 'Penalty' (a menos que tu DB marque 'Penalty' solo si entra)
_FIRST_HALF_MAX = 45  # 0..45 => 1a parte
# 2a parte => >45 (incluye 46..90 y agregado como int >= 91 si viene así)

def _credited_team_id(ev_row: pd.Series, home_id: int, away_id: int,
                      own_goal_team_is_conceding: bool = True) -> Optional[int]:
    """
    Devuelve el team_id al que se le acredita el gol.
    Heurística:
      - Para 'Goal': usamos ev_row['team_id'] tal cual.
      - Para 'Own goal':
          * Si own_goal_team_is_conceding=True, asumimos que team_id es el que CONCEDE;
            por lo tanto se acredita al rival.
          * Si False, se acredita a team_id (la DB ya trae al beneficiado).
    Si algo no cuadra, devolvemos None.
    """
    tid = ev_row.get("team_id")
    if pd.isna(tid):
        return None
    tid = int(tid)

    etype = ev_row.get("event_type")
    if etype == "Goal":
        return tid

    if etype == "Own goal":
        if own_goal_team_is_conceding:
            # Mapear al oponente
            if tid == home_id:
                return away_id
            if tid == away_id:
                return home_id
            # si no coincide con ninguno, dejamos None (DB inconsistente)
            return None
        else:
            return tid

    # Otros tipos no cuentan como gol aquí
    return None


def _first_goal_team_for_match(ev_match_df: pd.DataFrame,
                               home_id: int, away_id: int,
                               own_goal_team_is_conceding: bool) -> Optional[int]:
    """
    Devuelve el team_id al que se le acredita el PRIMER gol del partido.
    Ordena por minute ascendente (y por event_id si lo tienes, opcional).
    """
    if ev_match_df.empty:
        return None

    # Filtro solo eventos de gol (Goal / Own goal) con minuto válido
    tmp = ev_match_df[
        ev_match_df["event_type"].isin(_GOAL_TYPES) & ev_match_df["minute"].notna()
    ].copy()

    if tmp.empty:
        return None

    # Orden robusto
    order_cols = ["minute"]
    if "event_id" in tmp.columns:
        order_cols.append("event_id")
    tmp.sort_values(order_cols, inplace=True)

    for _, ev in tmp.iterrows():
        cred = _credited_team_id(ev, home_id, away_id, own_goal_team_is_conceding)
        if cred is not None:
            return cred
    return None


def _teams_scored_both_halves(ev_match_df: pd.DataFrame,
                              home_id: int, away_id: int,
                              own_goal_team_is_conceding: bool) -> Dict[int, bool]:
    """
    Para un partido, indica si cada equipo anotó al menos un gol en 1ª y 2ª parte.
    Retorna {home_id: True/False, away_id: True/False}
    """
    out = {home_id: False, away_id: False}

    if ev_match_df.empty:
        return out

    tmp = ev_match_df[
        ev_match_df["event_type"].isin(_GOAL_TYPES) & ev_match_df["minute"].notna()
    ].copy()
    if tmp.empty:
        return out

    # Marcar mitad por minuto
    tmp["first_half"] = tmp["minute"].astype(int) <= _FIRST_HALF_MAX

    # Acreditar goles por equipo
    tmp["credited_team"] = tmp.apply(
        lambda r: _credited_team_id(r, home_id, away_id, own_goal_team_is_conceding),
        axis=1
    )
    tmp = tmp.dropna(subset=["credited_team"])
    if tmp.empty:
        return out

    # ¿Anotó en 1ª y 2ª?
    by_team = tmp.groupby("credited_team")["first_half"].agg(
        first_any="any",  # True si marcó en 1ª parte
        count="count"     # total (para control)
    )
    # Necesitamos también saber si marcó en 2ª parte
    # Podemos medir “any en 2ª parte” como: total > goles 1ª parte
    by_team2 = tmp.groupby(["credited_team", "first_half"]).size().unstack(fill_value=0)
    # columnas: False (2ª parte), True (1ª parte)
    for tid in (home_id, away_id):
        fh = bool(by_team2.loc[tid, True]) if (tid in by_team2.index) and (True in by_team2.columns) else False
        sh = bool(by_team2.loc[tid, False]) if (tid in by_team2.index) and (False in by_team2.columns) else False
        out[tid] = bool(fh and sh)

    return out

def events_kpis_corrected(
    matches_iter: Iterable,
    events_df: pd.DataFrame,
    first_half_limit: int = 45,
) -> pd.DataFrame:
    """
    Calcula KPIs basados en eventos:
      - goals_both_halves_pct: % de partidos donde el equipo marcó en ambas mitades
      - scored_first_and_won_pct: % de partidos donde el equipo marcó primero Y ganó

    Args:
        matches_iter: Iterable de MatchItem (solo partidos finalizados)
        events_df: DataFrame con eventos (columnas: event_id, match_id, event_type, minute, team_id)
        first_half_limit: Minuto límite para primera mitad (default 45)

    Returns:
        DataFrame con columnas: team_id, goals_both_halves_pct, scored_first_and_won_pct
    """

    # 1. Crear mapeo de partidos: match_id -> (home_id, away_id, winner_id)
    matches_map = {}
    for m in matches_iter:
        if m.home_score is None or m.away_score is None:
            continue

        match_id = int(m.match_id)
        home_id = int(m.home_team_id)
        away_id = int(m.away_team_id)

        # Determinar ganador (None si empate)
        if m.home_score > m.away_score:
            winner_id = home_id
        elif m.away_score > m.home_score:
            winner_id = away_id
        else:
            winner_id = None

        matches_map[match_id] = {
            'home_id': home_id,
            'away_id': away_id,
            'winner_id': winner_id
        }

    if not matches_map:
        return pd.DataFrame(columns=['team_id', 'goals_both_halves_pct', 'scored_first_and_won_pct'])

    # 2. Filtrar eventos de gol válidos
    ev = events_df.copy()
    ev = ev[
        ev['event_type'].isin(['Goal', 'Own goal']) &
        ev['minute'].notna() &
        ev['match_id'].isin(matches_map.keys())
    ].copy()

    if ev.empty:
        # Si no hay goles, devolver 0% para todos los equipos que jugaron
        all_teams = set()
        for m_info in matches_map.values():
            all_teams.add(m_info['home_id'])
            all_teams.add(m_info['away_id'])

        return pd.DataFrame([
            {'team_id': tid, 'goals_both_halves_pct': 0.0, 'scored_first_and_won_pct': 0.0}
            for tid in sorted(all_teams)
        ])

    # 3. Acreditar goles correctamente (considerar Own Goals)
    def credit_goal(row):
        match_id = int(row['match_id'])
        team_id = int(row['team_id'])
        match_info = matches_map.get(match_id)

        if not match_info:
            return None

        if row['event_type'] == 'Own goal':
            # Own goal: se acredita al RIVAL del equipo que lo anotó
            if team_id == match_info['home_id']:
                return match_info['away_id']
            elif team_id == match_info['away_id']:
                return match_info['home_id']
            else:
                return None
        else:
            # Goal normal
            return team_id

    ev['scoring_team_id'] = ev.apply(credit_goal, axis=1)
    ev = ev.dropna(subset=['scoring_team_id'])
    ev['scoring_team_id'] = ev['scoring_team_id'].astype(int)
    ev['minute'] = ev['minute'].astype(int)

    # Clasificar por mitad
    ev['half'] = np.where(ev['minute'] <= first_half_limit, 'first', 'second')

    # 4. Calcular "Marcó en ambas mitades"
    both_halves_data = defaultdict(lambda: {'matches': set(), 'both_halves': set()})

    for match_id, match_info in matches_map.items():
        home_id = match_info['home_id']
        away_id = match_info['away_id']

        # Registrar que estos equipos jugaron este partido
        both_halves_data[home_id]['matches'].add(match_id)
        both_halves_data[away_id]['matches'].add(match_id)

        # Obtener goles de este partido
        match_goals = ev[ev['match_id'] == match_id]

        for team_id in [home_id, away_id]:
            team_goals = match_goals[match_goals['scoring_team_id'] == team_id]

            if team_goals.empty:
                continue

            # Verificar si marcó en ambas mitades
            scored_first = (team_goals['half'] == 'first').any()
            scored_second = (team_goals['half'] == 'second').any()

            if scored_first and scored_second:
                both_halves_data[team_id]['both_halves'].add(match_id)

    # 5. Calcular "Marcó primero y ganó"
    scored_first_won_data = defaultdict(lambda: {'matches': set(), 'first_and_won': set()})

    for match_id, match_info in matches_map.items():
        home_id = match_info['home_id']
        away_id = match_info['away_id']
        winner_id = match_info['winner_id']

        # Registrar partidos jugados
        scored_first_won_data[home_id]['matches'].add(match_id)
        scored_first_won_data[away_id]['matches'].add(match_id)

        # Obtener el primer gol del partido
        match_goals = ev[ev['match_id'] == match_id].sort_values(['minute', 'event_id'])

        if match_goals.empty or winner_id is None:
            continue

        first_scorer_id = int(match_goals.iloc[0]['scoring_team_id'])

        # Si el primer anotador ganó el partido
        if first_scorer_id == winner_id:
            scored_first_won_data[first_scorer_id]['first_and_won'].add(match_id)

    # 6. Construir DataFrame de resultados
    all_teams = set(both_halves_data.keys()) | set(scored_first_won_data.keys())

    results = []
    for team_id in sorted(all_teams):
        # Obtener conteos
        matches_bh = len(both_halves_data[team_id]['matches'])
        both_halves_count = len(both_halves_data[team_id]['both_halves'])

        matches_sfw = len(scored_first_won_data[team_id]['matches'])
        first_won_count = len(scored_first_won_data[team_id]['first_and_won'])

        # Calcular porcentajes
        both_halves_pct = (both_halves_count / matches_bh) if matches_bh > 0 else 0.0
        first_won_pct = (first_won_count / matches_sfw) if matches_sfw > 0 else 0.0

        results.append({
            'team_id': team_id,
            'goals_both_halves_pct': round(both_halves_pct, 4),
            'scored_first_and_won_pct': round(first_won_pct, 4),
        })

    return pd.DataFrame(results)


def events_simple_kpis(events_df: pd.DataFrame, matches_played_map: Dict[int, int]) -> pd.DataFrame:
    """
    Calcula KPIs simples de eventos (no requieren resultados de partidos):
      - g_0_15, g_76_90p: conteos absolutos de goles en rangos de tiempo
      - yc_pg, rc_pg, subs_pg, wood_pg: eventos por partido

    Args:
        events_df: DataFrame con eventos normalizados
        matches_played_map: dict {team_id: partidos_jugados} para calcular "per game"

    Returns:
        DataFrame con team_id y las métricas simples
    """
    if events_df.empty:
        return pd.DataFrame(columns=[
            "team_id", "g_0_15", "g_76_90p", "yc_pg", "rc_pg", "subs_pg", "wood_pg"
        ])

    ev = events_df.copy()

    # Asegurar tipos numéricos
    for c in ("minute", "team_id"):
        if c in ev.columns:
            ev[c] = pd.to_numeric(ev[c], errors="coerce")

    # Filtrar eventos válidos
    ev = ev[ev["team_id"].notna()].copy()

    # Conteos por tipo de evento
    goals = ev[ev["event_type"] == "Goal"].copy()
    g_0_15   = goals[goals["minute"].between(0, 15, inclusive="both")].groupby("team_id").size()
    g_76_90p = goals[goals["minute"] >= 76].groupby("team_id").size()

    yc   = ev[ev["event_type"] == "Yellow card"].groupby("team_id").size()
    rc   = ev[ev["event_type"] == "Red card"].groupby("team_id").size()
    subs = ev[ev["event_type"] == "Substitution"].groupby("team_id").size()
    wood = ev[ev["event_type"] == "Woodwork"].groupby("team_id").size()

    # Construir resultados
    all_tids = set(ev["team_id"].astype(int).tolist())
    rows = []

    for tid in sorted(all_tids):
        mp = max(1, int(matches_played_map.get(tid, 1)))  # evitar división por 0

        rows.append({
            "team_id":   tid,
            "g_0_15":    int(g_0_15.get(tid, 0)),
            "g_76_90p":  int(g_76_90p.get(tid, 0)),
            "yc_pg":     float(yc.get(tid, 0)) / mp,
            "rc_pg":     float(rc.get(tid, 0)) / mp,
            "subs_pg":   float(subs.get(tid, 0)) / mp,
            "wood_pg":   float(wood.get(tid, 0)) / mp,
        })

    return pd.DataFrame(rows)
