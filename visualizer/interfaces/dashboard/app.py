from __future__ import annotations
import math
from typing import Any, Dict, List, Optional

import dash
from dash import dcc, html, Input, Output, State, callback, ctx
import dash_mantine_components as dmc
import dash_ag_grid as dag
import plotly.graph_objects as go

from .bootstrap import build_container

# ---------- Container / Queries ----------
container = build_container()

# ---------- Helpers UI ----------
def kpi_card(title: str, value: str, tooltip: Optional[str] = None) -> dmc.Card:
    return dmc.Card(
        withBorder=True, radius="md", shadow="sm", p="md",
        children=[
            dmc.Text(title, size="sm", c="dimmed"),
            dmc.Space(h=4),
            dmc.Text(value, size="xl", weight=700),
            dmc.Space(h=tooltip and 6 or 0),
            tooltip and dmc.Text(tooltip, size="xs", c="dimmed"),
        ]
    )

def aggrid_table(rowdata: List[Dict[str, Any]], column_defs: List[Dict[str, Any]], height: int = 420):
    return dag.AgGrid(
        className="ag-theme-alpine",
        columnDefs=column_defs,
        rowData=rowdata,
        defaultColDef={"sortable": True, "filter": True, "resizable": True, "minWidth": 90},
        dashGridOptions={"domLayout": "normal", "animateRows": True},
        style={"height": f"{height}px", "width": "100%"},
    )

def bars_figure(x, y, title: str):
    fig = go.Figure(data=[go.Bar(x=x, y=y)])
    fig.update_layout(title=title, margin=dict(l=20, r=20, t=50, b=20), height=360)
    return fig

def line_figure(x, y, title: str):
    fig = go.Figure(data=[go.Scatter(x=x, y=y, mode="lines+markers")])
    fig.update_layout(title=title, margin=dict(l=20, r=20, t=50, b=20), height=360)
    return fig

# ---------- Preload competitions ----------
_competitions = container.get_competitions.execute()
COMP_OPTIONS = [{"value": c.competition_id, "label": c.competition_name} for c in _competitions]

# ---------- Layout ----------
app = dash.Dash(__name__, title="Fifth Referee — Dashboard", suppress_callback_exceptions=True)
app.layout = dmc.MantineProvider(
    theme={"primaryColor": "blue", "colorScheme": "dark"},
    children=dmc.NotificationsProvider(
        children=dmc.AppShell(
            padding="md",
            navbar=dmc.Navbar(
                width={"base": 320},
                p="md",
                children=[
                    dmc.Title("Fifth Referee", order=3),
                    dmc.Space(h=6),
                    dmc.Text("Explorador de temporadas", size="sm", c="dimmed"),
                    dmc.Divider(my="sm"),
                    dmc.Select(
                        id="sel-competition",
                        label="Competición",
                        data=COMP_OPTIONS,
                        searchable=True,
                        nothingFound="Sin resultados",
                        clearable=False,
                        value=COMP_OPTIONS[0]["value"] if COMP_OPTIONS else None,
                    ),
                    dmc.Select(
                        id="sel-season",
                        label="Temporada",
                        data=[], searchable=True, nothingFound="—", clearable=False,
                    ),
                    dmc.Select(
                        id="sel-team",
                        label="Equipo",
                        data=[], searchable=True, nothingFound="—", clearable=True,
                    ),
                    dmc.NumberInput(
                        id="inp-n",
                        label="N (forma reciente)",
                        value=5, min=3, max=20, step=1,
                    ),
                    dmc.Space(h=12),
                    dmc.Button("Actualizar", id="btn-refresh", leftSection=dmc.ThemeIcon("refresh"), fullWidth=True),
                    dmc.Space(h=18),
                    dmc.Alert("Selecciona competencia y temporada. Opcional: un equipo para vistas específicas.",
                              title="Ayuda", color="blue", variant="light"),
                ],
            ),
            header=dmc.Header(height=56, p="sm", children=dmc.Group([
                dmc.Text("Dashboard de Métricas — v1", fw=700),
            ])),
            children=dmc.Container(
                size="xl",
                children=[
                    dmc.Tabs(
                        id="tabs",
                        value="overview",
                        children=[
                            dmc.TabsList(
                                children=[
                                    dmc.Tab("overview", "Overview"),
                                    dmc.Tab("team", "Equipo"),
                                    dmc.Tab("players", "Jugadores"),
                                    dmc.Tab("keepers", "Porteros"),
                                    dmc.Tab("matchdays", "Jornadas"),
                                ]
                            ),
                            dmc.TabsPanel("overview", children=[
                                dmc.Space(h=8),
                                dmc.SimpleGrid(cols=3, spacing="sm", children=[
                                    kpi_card("Partidos disputados", "-", "Solo finalizados"),
                                    kpi_card("Goles totales", "-", "En la temporada"),
                                    kpi_card("Goles/partido", "-", "Promedio global"),
                                ], id="kpi-overview"),
                                dmc.Space(h=8),
                                html.Div(id="tbl-standings"),
                            ]),
                            dmc.TabsPanel("team", children=[
                                dmc.Space(h=8),
                                dmc.SimpleGrid(cols=4, spacing="sm", children=[
                                    kpi_card("PPG (local)", "-"),
                                    kpi_card("PPG (visitante)", "-"),
                                    kpi_card("GF (H/A)", "-"),
                                    kpi_card("GA (H/A)", "-"),
                                ], id="kpi-team"),
                                dmc.Space(h=8),
                                dmc.SimpleGrid(cols=2, spacing="sm", children=[
                                    dmc.Card(children=[dcc.Graph(id="fig-team-progress")]),
                                    dmc.Card(children=[dcc.Graph(id="fig-team-form")]),
                                ]),
                            ]),
                            dmc.TabsPanel("players", children=[
                                dmc.Space(h=8),
                                dmc.SimpleGrid(cols=2, spacing="sm", children=[
                                    dmc.Card(children=[dcc.Graph(id="fig-top-scorers")]),
                                    dmc.Card(children=[dcc.Graph(id="fig-top-assisters")]),
                                ]),
                                dmc.Space(h=8),
                                html.Div(id="tbl-players"),
                            ]),
                            dmc.TabsPanel("keepers", children=[
                                dmc.Space(h=8),
                                dmc.Card(children=[dcc.Graph(id="fig-keepers")]),
                                dmc.Space(h=8),
                                html.Div(id="tbl-keepers"),
                            ]),
                            dmc.TabsPanel("matchdays", children=[
                                dmc.Space(h=8),
                                dmc.Select(id="sel-matchday", label="Jornada", data=[], clearable=True),
                                dmc.Space(h=8),
                                html.Div(id="tbl-matches"),
                            ]),
                        ],
                    )
                ],
            ),
        )
    ),
)

# ---------- Callbacks ----------

@callback(
    Output("sel-season", "data"),
    Output("sel-season", "value"),
    Input("sel-competition", "value"),
)
def _load_seasons(comp_id):
    if not comp_id:
        return [], None
    seasons = container.get_seasons.execute(comp_id)
    data = [{"value": s.season_id, "label": s.season_label} for s in seasons]
    value = data[0]["value"] if data else None
    return data, value


@callback(
    Output("sel-team", "data"),
    Output("sel-matchday", "data"),
    Input("sel-season", "value"),
)
def _load_teams_and_matchdays(season_id):
    if not season_id:
        return [], []
    teams = container.season_svc.list_teams(season_id)
    teams_data = [{"value": t.team_id, "label": t.team_name} for t in teams]
    mds = container.get_matchdays.execute(season_id)
    md_data = [{"value": m.matchday_id, "label": f"Jornada {m.matchday_number}"} for m in mds]
    return teams_data, md_data


@callback(
    Output("tbl-standings", "children"),
    Output("kpi-overview", "children"),
    Input("btn-refresh", "n_clicks"),
    State("sel-season", "value"),
    prevent_initial_call=True,
)
def _refresh_overview(_, season_id):
    if not season_id:
        return dmc.Alert("Selecciona una temporada", color="yellow"), dash.no_update

    rows = container.get_standings.execute(season_id)
    rowdata = [r.__dict__ for r in rows]

    # KPIs globales
    mp_total = sum(r.MP for r in rows)  # cada equipo cuenta sus partidos
    # partidos disputados reales = mp_total / 2 (cada partido involucra 2 equipos)
    matches_played = mp_total // 2
    goals_total = sum(r.GF for r in rows)  # suma de GF por equipo
    goals_per_match = (goals_total / matches_played) if matches_played else 0.0

    kpis = dmc.SimpleGrid(cols=3, spacing="sm", children=[
        kpi_card("Partidos disputados", f"{matches_played:,}"),
        kpi_card("Goles totales", f"{goals_total:,}"),
        kpi_card("Goles/partido", f"{goals_per_match:.2f}"),
    ])

    coldefs = [
        {"field": "team_name", "headerName": "Equipo", "pinned": "left"},
        {"field": "MP"}, {"field": "Pts"}, {"field": "GF"}, {"field": "GA"},
        {"field": "GD"},
    ]
    table = aggrid_table(rowdata, coldefs, height=520)
    return table, kpis


@callback(
    Output("kpi-team", "children"),
    Output("fig-team-progress", "figure"),
    Output("fig-team-form", "figure"),
    Input("btn-refresh", "n_clicks"),
    State("sel-season", "value"),
    State("sel-team", "value"),
    State("inp-n", "value"),
    prevent_initial_call=True,
)
def _refresh_team(_, season_id, team_id, n):
    if not (season_id and team_id):
        return [
            kpi_card("PPG (local)", "-"),
            kpi_card("PPG (visitante)", "-"),
            kpi_card("GF (H/A)", "-"),
            kpi_card("GA (H/A)", "-"),
        ], go.Figure(), go.Figure()

    split = container.get_team_splits.execute(season_id, team_id)
    kpis = dmc.SimpleGrid(cols=4, spacing="sm", children=[
        kpi_card("PPG (local)", f"{split.home_ppg:.2f}"),
        kpi_card("PPG (visitante)", f"{split.away_ppg:.2f}"),
        kpi_card("GF (H/A)", f"{split.home_gf}/{split.away_gf}"),
        kpi_card("GA (H/A)", f"{split.home_ga}/{split.away_ga}"),
    ])

    form_rows = container.get_team_form.execute(season_id, team_id, n=n)
    # progresión de puntos con base en los últimos N
    pts = []
    cum = 0
    x = list(range(1, len(form_rows) + 1))
    for r in form_rows:
        if r.result == "W":
            cum += 3
        elif r.result == "D":
            cum += 1
        pts.append(cum)

    fig_prog = line_figure(x, pts, f"Progresión de puntos (últimos {n})")
    # barras de forma W/D/L
    counts = {"W": 0, "D": 0, "L": 0}
    for r in form_rows:
        if r.result in counts:
            counts[r.result] += 1
    fig_form = bars_figure(list(counts.keys()), list(counts.values()), f"Forma reciente (N={n})")

    return kpis, fig_prog, fig_form


@callback(
    Output("fig-top-scorers", "figure"),
    Output("fig-top-assisters", "figure"),
    Output("tbl-players", "children"),
    Input("btn-refresh", "n_clicks"),
    State("sel-season", "value"),
    prevent_initial_call=True,
)
def _refresh_players(_, season_id):
    if not season_id:
        return go.Figure(), go.Figure(), dmc.Alert("Selecciona temporada", color="yellow")

    scorers = container.get_top_scorers.execute(season_id, top=15)
    assisters = container.get_top_assisters.execute(season_id, top=15)

    fig_s = bars_figure([s.player_name for s in scorers], [s.goals for s in scorers], "Top goleadores")
    fig_a = bars_figure([a.player_name for a in assisters], [a.assists for a in assisters], "Top asistentes")

    # Tabla combinada (puedes separar si prefieres)
    rows = [
        {"player_id": s.player_id, "player_name": s.player_name, "goals": s.goals, "assists": 0}
        for s in scorers
    ]
    a_map = {a.player_id: a.assists for a in assisters}
    for row in rows:
        row["assists"] = a_map.get(row["player_id"], row["assists"])
    coldefs = [
        {"field": "player_name", "headerName": "Jugador"},
        {"field": "goals", "headerName": "Goles", "type": "rightAligned"},
        {"field": "assists", "headerName": "Asistencias", "type": "rightAligned"},
    ]
    table = aggrid_table(rows, coldefs, height=420)
    return fig_s, fig_a, table


@callback(
    Output("fig-keepers", "figure"),
    Output("tbl-keepers", "children"),
    Input("btn-refresh", "n_clicks"),
    State("sel-season", "value"),
    prevent_initial_call=True,
)
def _refresh_keepers(_, season_id):
    if not season_id:
        return go.Figure(), dmc.Alert("Selecciona temporada", color="yellow")
    kpis = container.get_keeper_kpis.execute(season_id, top=15)

    fig = bars_figure([k.player_name for k in kpis], [k.goalkeeper_saves or 0 for k in kpis], "Porteros — atajadas")

    rows = [
        {
            "player_name": k.player_name,
            "saves": k.goalkeeper_saves,
            "goals_prevented": k.goals_prevented,
            "goals_conceded": k.goals_conceded,
        }
        for k in kpis
    ]
    coldefs = [
        {"field": "player_name", "headerName": "Portero"},
        {"field": "saves", "headerName": "Atajadas"},
        {"field": "goals_conceded", "headerName": "Goles encajados"},
        {"field": "goals_prevented", "headerName": "Goles prevenidos"},
    ]
    table = aggrid_table(rows, coldefs, height=420)
    return fig, table


@callback(
    Output("tbl-matches", "children"),
    Input("btn-refresh", "n_clicks"),
    State("sel-season", "value"),
    State("sel-matchday", "value"),
    prevent_initial_call=True,
)
def _refresh_matches(_, season_id, matchday_id):
    if not season_id:
        return dmc.Alert("Selecciona temporada", color="yellow")
    matches = container.get_matches_by_season.execute(season_id, only_finalized=False)
    rows = []
    for m in matches:
        if matchday_id and m.matchday_id != matchday_id:
            continue
        rows.append({
            "match_id": m.match_id,
            "matchday_id": m.matchday_id,
            "home_team_id": m.home_team_id,
            "away_team_id": m.away_team_id,
            "local_score": m.local_score,
            "away_score": m.away_score,
            "stadium": m.stadium,
        })
    coldefs = [
        {"field": "match_id", "headerName": "ID"},
        {"field": "matchday_id", "headerName": "Jornada"},
        {"field": "home_team_id", "headerName": "Local"},
        {"field": "away_team_id", "headerName": "Visitante"},
        {"field": "local_score", "headerName": "L"},
        {"field": "away_score", "headerName": "V"},
        {"field": "stadium", "headerName": "Estadio"},
    ]
    return aggrid_table(rows, coldefs, height=520)

# ---------- Run ----------
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)
