# interfaces/dash/pages/standings.py
from __future__ import annotations

from typing import Any, Dict, List, Tuple
import pandas as pd
import plotly.io as pio
from dash import dcc, html, Input, Output, callback, register_page

from interfaces.dash.data import get_data
from interfaces.dash.data.transforms import (
    normalize_standings,
    enrich_with_ppg_gih,
    standings_shadow_by_ppg,
    last_n_ppg,
    market_kpis,
)
from interfaces.dash.components.charts import bar as bar_chart
from interfaces.dash.components.tables import make_league_table
from interfaces.dash.components.leaders import leader_card

# =====================================================================
# CONFIGURACIÓN
# =====================================================================
register_page(__name__, path="/", name="Standings", order=1)
pio.templates.default = "plotly_dark"
DATA = get_data()

# Columnas numéricas para conversión
NUMERIC_COLS = [
    "ppg", "gih", "ppg_last_5", "btts_pct", "over25_pct", "clean_sheet_pct",
    "points", "gd", "g_0_15", "g_76_90p", "yc_pg", "rc_pg", "subs_pg", "wood_pg",
    "goals_both_halves_pct", "scored_first_and_won_pct"
]

# =====================================================================
# LAYOUT
# =====================================================================
def _filters_section() -> html.Div:
    return html.Div(className="card row", children=[
        html.Div(className="col-6", children=[
            html.Label("Season", className="label"),
            dcc.Dropdown(id="season-dd", placeholder="Select season", clearable=False),
        ]),
        html.Div(className="col-6", children=[
            html.Label("Competition", className="label"),
            dcc.Dropdown(id="competition-dd", placeholder="Select competition", clearable=False),
        ]),
    ])

def _charts_section() -> html.Div:
    return html.Div(className="row", children=[
        html.Div(className="col-6", children=[dcc.Graph(id="points-fig")]),
        html.Div(className="col-6", children=[dcc.Graph(id="gd-fig")]),
    ])

def _view_selector() -> html.Div:
    return html.Div(className="card row", children=[
        html.Div(className="col-12", children=[
            html.Span("Standings view:", className="label inline"),
            dcc.RadioItems(
                id="standings-view",
                options=[
                    {"label": "Básico", "value": "basic"},
                    {"label": "Avanzado", "value": "advanced"},
                ],
                value="basic",
                inline=True,
                className="radio-inline",
            )
        ])
    ])

def _leaders_section() -> html.Div:
    return html.Div(className="card", children=[
        html.H3("Líderes de jugadores"),
        html.Div(className="row", children=[
            html.Div(className="col-3", children=[html.Div(id="leaders-scorers")]),
            html.Div(className="col-3", children=[html.Div(id="leaders-assisters")]),
            html.Div(className="col-3", children=[html.Div(id="leaders-gk-saves")]),
            html.Div(className="col-3", children=[html.Div(id="leaders-gk-conceded")]),
        ])
    ])

layout = html.Div(className="container", children=[
    html.Div(className="app-title", children="⚽ FIFTH REFEREE – Resumen de temporada"),

    # Stores necesarios
    dcc.Store(id="season-id"),
    dcc.Store(id="standings-cache"),
    dcc.Store(id="analytics-cache"),

    _filters_section(),
    dcc.Loading(html.Div(id="summary-badges", className="card"), type="circle"),
    _charts_section(),
    _view_selector(),
    html.Div(id="standings-table-wrap"),
    _leaders_section(),
])

# =====================================================================
# HELPERS
# =====================================================================
def _merge_analytics(df: pd.DataFrame, analytics: Dict[str, Any]) -> pd.DataFrame:
    """Merge todas las analíticas en el DataFrame principal."""
    def merge_if_exists(base: pd.DataFrame, key: str, cols: List[str]) -> pd.DataFrame:
        data = analytics.get(key)
        if not data:
            return base
        addon = pd.DataFrame(data)
        if not set(cols).issubset(addon.columns):
            return base
        return base.merge(addon[cols], on="team_id", how="left")

    df = merge_if_exists(df, "shadow", ["team_id", "shadow_rank"])
    df = merge_if_exists(df, "last5", ["team_id", "ppg_last_5"])
    df = merge_if_exists(df, "market", ["team_id", "btts_pct", "over25_pct", "clean_sheet_pct"])
    df = merge_if_exists(df, "ev", [
        "team_id", "g_0_15", "g_76_90p", "yc_pg", "rc_pg", "subs_pg", "wood_pg",
        "goals_both_halves_pct", "scored_first_and_won_pct"
    ])

    return df

def _convert_numeric_columns(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    """Convierte columnas a numéricas de forma segura."""
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def _create_summary_badges(summary: Dict[str, Any]) -> html.Div:
    """Crea los badges de resumen."""
    return html.Div(className="summary row", children=[
        html.Div(className="badge badge-accent col-3",
                 children=f"📅 {summary.get('season_label', 'N/A')}"),
        html.Div(className="badge badge-accent-2 col-3",
                 children=f"🏆 {summary.get('competition_name', 'N/A')}"),
        html.Div(className="badge badge-ok col-3",
                 children=f"👥 {summary.get('team_count', 0)} Teams"),
        html.Div(className="badge badge-md col-3",
                 children=f"🎮 MD {summary.get('last_finalized_matchday', '—')}")
    ])

# =====================================================================
# CALLBACKS - DISCOVERY Y FILTROS
# =====================================================================
@callback(
    Output("season-dd", "options"),
    Output("season-dd", "value"),
    Input("season-dd", "id"),
    prevent_initial_call=False,
)
def load_seasons(_: str) -> Tuple[List[Dict[str, str]], str | None]:
    """Carga las temporadas disponibles."""
    labels = DATA.season_labels()
    options = [{"label": s, "value": s} for s in labels]
    default = labels[0] if labels else None
    return options, default

@callback(
    Output("competition-dd", "options"),
    Output("competition-dd", "value"),
    Input("season-dd", "value"),
)
def load_competitions(season_label: str | None) -> Tuple[List[Dict[str, Any]], int | None]:
    """Carga las competiciones para la temporada seleccionada."""
    if not season_label:
        return [], None

    comps = DATA.competitions_for_label(season_label)
    options = [{"label": c.name, "value": c.id} for c in comps]
    default = comps[0].id if comps else None
    return options, default

# =====================================================================
# CALLBACKS - DATOS
# =====================================================================
@callback(
    Output("season-id", "data"),
    Output("summary-badges", "children"),
    Input("season-dd", "value"),
    Input("competition-dd", "value"),
)
def resolve_season_and_summary(label: str | None, comp_id: int | None):
    """Resuelve el season_id y crea el resumen."""
    if not (label and comp_id):
        return None, html.Div("Selecciona temporada y competencia", className="error")

    season_id = DATA.resolve_season(label, int(comp_id))
    if not season_id:
        return None, html.Div("No se encontró la temporada", className="error")

    summary = DATA.season_summary(season_id)
    badges = _create_summary_badges(summary)

    return season_id, badges

@callback(
    Output("standings-cache", "data"),
    Output("analytics-cache", "data"),
    Input("season-id", "data"),
)
def load_standings_data(season_id: int | None):
    """Carga standings y todas las analíticas."""
    if not season_id:
        return None, None

    print(f"\n=== DEBUGGING STANDINGS DATA ===")
    print(f"Season ID: {season_id}")

    # 1. Standings base
    df = DATA.standings_df(season_id)
    print(f"Raw standings shape: {df.shape}")

    df = normalize_standings(df)
    print(f"Normalized standings shape: {df.shape}")

    if df.empty:
        print("ERROR: Standings vacío")
        return {"rows": []}, {}

    # 2. Enriquecer con PPG y GiH
    df = enrich_with_ppg_gih(df)
    print(f"After PPG enrichment, columns: {list(df.columns)}")

    # 3. Analíticas complementarias
    shadow = standings_shadow_by_ppg(df)
    print(f"Shadow standings shape: {shadow.shape}")

    # Para last_n_ppg y market_kpis necesitamos los matches
    matches = list(DATA.iter_matches(season_id, finalized=True, limit=10_000))
    print(f"Finalized matches count: {len(matches)}")

    last5 = last_n_ppg(matches, n=5)
    print(f"Last 5 PPG shape: {last5.shape}")

    market = market_kpis(matches)
    print(f"Market KPIs shape: {market.shape}")

    # 4. KPIs de eventos - DEBUGGING CRÍTICO
    matches_played_map = dict(zip(df["team_id"], df["played"]))
    print(f"\nMatches played map sample: {dict(list(matches_played_map.items())[:3])}")

    print(f"\n--- Calling events_kpis_df ---")
    events_kpis = DATA.events_kpis_df(season_id, matches_played_map=matches_played_map)

    print(f"Events KPIs shape: {events_kpis.shape}")
    print(f"Events KPIs columns: {list(events_kpis.columns)}")
    print(f"Events KPIs sample (first 3 rows):")
    print(events_kpis.head(3))
    print(f"Events KPIs dtypes:")
    print(events_kpis.dtypes)

    analytics = {
        "shadow": shadow.to_dict("records"),
        "last5": last5.to_dict("records"),
        "market": market.to_dict("records"),
        "ev": events_kpis.to_dict("records"),
    }

    print(f"\nAnalytics 'ev' sample: {analytics['ev'][:2] if analytics['ev'] else 'EMPTY'}")
    print(f"=== END DEBUGGING ===\n")

    return {"rows": df.to_dict("records")}, analytics

# =====================================================================
# CALLBACKS - RENDER
# =====================================================================
@callback(
    Output("points-fig", "figure"),
    Output("gd-fig", "figure"),
    Output("standings-table-wrap", "children"),
    Input("standings-cache", "data"),
    Input("analytics-cache", "data"),
    Input("standings-view", "value"),
)
def render_standings_overview(standings_cache, analytics_cache, view):
    """Renderiza gráficos y tabla de standings."""
    df = pd.DataFrame((standings_cache or {}).get("rows", []))

    if df.empty:
        empty_fig = bar_chart(
            pd.DataFrame({"team": [], "val": []}),
            x="team", y="val", title="Sin datos"
        )
        return empty_fig, empty_fig, html.Div("No hay datos de standings", className="error")

    print(f"\n=== RENDER DEBUGGING ===")
    print(f"Standings cache columns: {list(df.columns)}")
    print(f"Analytics cache keys: {list((analytics_cache or {}).keys())}")

    if analytics_cache and 'ev' in analytics_cache:
        ev_sample = analytics_cache['ev'][:2] if analytics_cache['ev'] else []
        print(f"Analytics 'ev' sample in render: {ev_sample}")

    # 1) Merge analíticas + tipos numéricos
    df = _merge_analytics(df, analytics_cache or {})
    print(f"After merge, columns: {list(df.columns)}")
    print(f"After merge, has goals_both_halves_pct: {'goals_both_halves_pct' in df.columns}")
    print(f"After merge, has scored_first_and_won_pct: {'scored_first_and_won_pct' in df.columns}")

    df = _convert_numeric_columns(df, NUMERIC_COLS)

    # 2) Orden estable por posición
    df_sorted = df.sort_values("position").copy()

    # 3) Gráficos con orden de categorías fijo
    points_fig = bar_chart(
        df_sorted, x="team_name", y="points",
        title="Distribución de Puntos"
    )
    points_fig.update_layout(xaxis={
        "categoryorder": "array",
        "categoryarray": df_sorted["team_name"].tolist()
    })

    gd_fig = bar_chart(
        df_sorted, x="team_name", y="gd",
        title="Diferencia de Gol"
    )
    gd_fig.update_layout(xaxis={
        "categoryorder": "array",
        "categoryarray": df_sorted["team_name"].tolist()
    })

    # 4) Tabla
    table_component = make_league_table(df_sorted.to_dict("records"), view=view)

    # Debug info si faltan columnas en vista avanzada
    debug_note = None
    if view == "advanced":
        expected_advanced = {
            "ppg_last_5", "shadow_rank", "btts_pct", "over25_pct",
            "clean_sheet_pct", "g_0_15", "g_76_90p", "yc_pg", "rc_pg",
            "subs_pg", "wood_pg", "goals_both_halves_pct", "scored_first_and_won_pct"
        }
        missing = sorted([c for c in expected_advanced if c not in df_sorted.columns])
        if missing:
            debug_note = html.Div(
                f"Faltan columnas: {', '.join(missing)}",
                className="muted",
                style={"marginBottom": "8px", "fontSize": "12px", "color": "#ff6b6b"}
            )

    print(f"=== END RENDER DEBUGGING ===\n")

    children = [debug_note, table_component] if debug_note else [table_component]
    table = html.Div(children, className="card", key=f"table-{view}")

    return points_fig, gd_fig, table

# =====================================================================
# CALLBACKS - LÍDERES DE JUGADORES
# =====================================================================
def _build_player_map(season_id: int) -> Dict[int, Tuple[str, str]]:
    """Construye un mapa de player_id -> (nombre, equipo)."""
    df_players = DATA.players_df(season_id)
    if df_players.empty:
        return {}

    return {
        int(row.player_id): (str(row.player_name), str(row.team_name))
        for row in df_players.itertuples(index=False)
    }

def _aggregate_basic_stats(season_id: int) -> pd.DataFrame:
    """Agrega estadísticas básicas por jugador."""
    df_basic = DATA.basic_stats_df(season_id, limit=5000)

    for col in ("goals", "assists", "minutes"):
        if col not in df_basic.columns:
            df_basic[col] = 0
        df_basic[col] = pd.to_numeric(df_basic[col], errors="coerce").fillna(0)

    if df_basic.empty:
        return pd.DataFrame(columns=["player_id", "goals", "assists", "minutes", "ga"])

    aggregated = df_basic.groupby("player_id", as_index=False).agg(
        goals=("goals", "sum"),
        assists=("assists", "sum"),
        minutes=("minutes", "sum"),
    )
    aggregated["ga"] = aggregated["goals"] + aggregated["assists"]

    return aggregated

def _aggregate_goalkeeper_stats(season_id: int, df_basic: pd.DataFrame) -> pd.DataFrame:
    """Agrega estadísticas de arqueros."""
    df_gk = DATA.goalkeeper_stats_df(season_id, limit=5000)

    for col in ("goalkeeper_saves", "goals_conceded"):
        if col not in df_gk.columns:
            df_gk[col] = 0
        df_gk[col] = pd.to_numeric(df_gk[col], errors="coerce").fillna(0)

    if not df_basic.empty and "basic_stats_id" in df_basic.columns:
        id_map = df_basic.set_index("basic_stats_id")["player_id"].to_dict()
        df_gk["player_id"] = df_gk["basic_stats_id"].map(id_map)
        df_gk = df_gk.dropna(subset=["player_id"]).copy()
        df_gk["player_id"] = df_gk["player_id"].astype(int)
    else:
        df_gk["player_id"] = pd.NA

    if df_gk.empty:
        return pd.DataFrame(columns=["player_id", "goalkeeper_saves", "goals_conceded"])

    return df_gk.groupby("player_id", as_index=False).agg(
        goalkeeper_saves=("goalkeeper_saves", "sum"),
        goals_conceded=("goals_conceded", "sum"),
    )

def _format_top_rows(
    df: pd.DataFrame,
    metric: str,
    player_map: Dict[int, Tuple[str, str]],
    k: int = 5,
    reverse: bool = True
) -> List[Tuple[str, str, str]]:
    """Formatea las filas top para un líder."""
    if df.empty or metric not in df.columns:
        return []

    top_df = df.sort_values(metric, ascending=not reverse).head(k)
    rows = []

    for rank, row in enumerate(top_df.itertuples(index=False), start=1):
        player_id = int(getattr(row, "player_id"))
        value = getattr(row, metric)

        name, team = player_map.get(player_id, (f"#{player_id}", "—"))
        value_str = f"{int(value)}" if float(value).is_integer() else f"{value:.1f}"

        rows.append((f"{rank}.", f"{name} | {team}", value_str))

    return rows

@callback(
    Output("leaders-scorers", "children"),
    Output("leaders-assisters", "children"),
    Output("leaders-gk-saves", "children"),
    Output("leaders-gk-conceded", "children"),
    Input("season-id", "data"),
)
def render_player_leaders(season_id: int | None):
    """Renderiza las tarjetas de líderes de jugadores."""
    if not season_id:
        empty = leader_card("—", [])
        return empty, empty, empty, empty

    player_map = _build_player_map(season_id)
    df_basic_stats = _aggregate_basic_stats(season_id)
    df_gk_stats = _aggregate_goalkeeper_stats(
        season_id,
        DATA.basic_stats_df(season_id, limit=5000)
    )

    scorers = leader_card(
        "Goleadores",
        _format_top_rows(df_basic_stats, "goals", player_map)
    )
    assisters = leader_card(
        "Asistidores",
        _format_top_rows(df_basic_stats, "assists", player_map)
    )
    gk_saves = leader_card(
        "Arquero: más atajadas",
        _format_top_rows(df_gk_stats, "goalkeeper_saves", player_map)
    )
    gk_conceded = leader_card(
        "Arquero: más goles recibidos",
        _format_top_rows(df_gk_stats, "goals_conceded", player_map)
    )

    return scorers, assisters, gk_saves, gk_conceded
