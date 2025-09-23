import dash
from dash import dcc, html, Input, Output, callback, dash_table
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import requests
import numpy as np
from datetime import datetime
import json

# Initialize the Dash app
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css']
)

# API base URL - adjust this to your FastAPI server
API_BASE = "http://localhost:8000"

# Helper functions to fetch data from your API
def _normalize_standings_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Alinea columnas del API (mp, pts, ...) a las que usa el dashboard (played, points, ...).
    No inventa W/D/L: si no existen, las deja como NaN para poder condicionar el gráfico.
    """
    if df.empty:
        return df

    df = df.copy()

    # Copias/alias para compatibilidad con el dashboard
    if 'pts' in df and 'points' not in df:
        df['points'] = df['pts']
    if 'mp' in df and 'played' not in df:
        df['played'] = df['mp']

    # Asegura minúsculas que ya usa el dashboard
    rename_map = {
        'GF': 'gf', 'GA': 'ga', 'GD': 'gd', 'Pts': 'points', 'MP': 'played',
        'TeamName': 'team_name', 'Team': 'team_name'
    }
    cols = {c: rename_map[c] for c in df.columns if c in rename_map}
    if cols:
        df = df.rename(columns=cols)

    # Crea columnas W/D/L si no existen (quedarán NaN)
    for k in ('win', 'draw', 'loss'):
        if k not in df.columns:
            df[k] = np.nan

    # Asegura columnas básicas
    for k in ('team_name', 'position', 'played', 'gf', 'ga', 'gd', 'points'):
        if k not in df.columns:
            # No debería ocurrir, pero mejor fallar suave
            df[k] = np.nan

    return df

def get_season_labels():
    """Fetch available season labels"""
    try:
        response = requests.get(f"{API_BASE}/v1/season-labels")
        if response.status_code == 200:
            return response.json()['items']
        return []
    except:
        return ["2023/2024", "2024/2025"]  # Fallback data

def get_competitions(season_label):
    """Fetch competitions for a season label"""
    try:
        response = requests.get(f"{API_BASE}/v1/season-labels/{season_label}/competitions")
        if response.status_code == 200:
            return response.json()['items']
        return []
    except:
        return [{"id": 1, "name": "Premier League"}]  # Fallback data

def resolve_season(season_label, competition_id):
    """Resolve season ID from label and competition"""
    try:
        response = requests.get(f"{API_BASE}/v1/seasons/resolve",
                               params={"season_label": season_label, "competition_id": competition_id})
        if response.status_code == 200:
            return response.json()['season_id']
        return None
    except:
        return 1  # Fallback

def get_season_summary(season_id):
    """Get season summary"""
    try:
        response = requests.get(f"{API_BASE}/v1/seasons/{season_id}/summary")
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return {"season_label": "2024/2025", "competition_name": "Premier League", "team_count": 20}

def get_standings(season_id):
    """Fetch season standings"""
    try:
        response = requests.get(f"{API_BASE}/v1/seasons/{season_id}/standings")
        if response.status_code == 200:
            df = pd.DataFrame(response.json()['rows'])
            df = _normalize_standings_df(df)

            # Merge con W/D/L derivados (si existen)
            wdl = get_wdl_counts(season_id)
            if not wdl.empty and 'team_id' in df.columns:
                df = df.merge(wdl, on='team_id', how='left')
                for c in ('win', 'draw', 'loss'):
                    if c in df.columns:
                        df[c] = df[c].fillna(0).astype(int)

            return df
        return pd.DataFrame()
    except:
        # Fallback data (deja las columnas esperadas por el dashboard)
        return pd.DataFrame({
            'team_id': range(1, 11),
            'team_name': [f'Team {i}' for i in range(1, 10+1)],
            'played': [10] * 10,
            'win': [7, 6, 5, 5, 4, 4, 3, 3, 2, 1],
            'draw': [2, 2, 3, 2, 3, 2, 4, 3, 4, 5],
            'loss': [1, 2, 2, 3, 3, 4, 3, 4, 4, 4],
            'gf': [20, 18, 15, 16, 12, 14, 11, 10, 8, 6],
            'ga': [8, 10, 12, 14, 15, 16, 17, 18, 20, 22],
            'gd': [12, 8, 3, 2, -3, -2, -6, -8, -12, -16],
            'points': [23, 20, 18, 17, 15, 14, 13, 12, 10, 8],
            'position': list(range(1, 10+1)),
        })

def get_teams(season_id):
    """Fetch teams for a season"""
    try:
        response = requests.get(f"{API_BASE}/v1/seasons/{season_id}/teams")
        if response.status_code == 200:
            return response.json()['items']
        return []
    except:
        return [{"team_id": i, "team_name": f"Team {i}"} for i in range(1, 11)]

def get_team_dashboard(season_id, team_id):
    """Fetch team dashboard data"""
    try:
        response = requests.get(f"{API_BASE}/v1/seasons/{season_id}/teams/{team_id}/dashboard")
        if response.status_code == 200:
            return response.json()
        return None
    except:
        # Fallback data
        return {
            "form": [{"match_id": i, "result": np.random.choice(["WIN", "DRAW", "LOSS"])} for i in range(1, 6)],
            "split": {"home_ppg": 2.1, "away_ppg": 1.3, "home_gf": 15, "away_gf": 8, "home_ga": 5, "away_ga": 12}
        }

def get_matches(season_id, **kwargs):
    """Fetch matches for a season with optional filters"""
    try:
        params = {k: v for k, v in kwargs.items() if v is not None}
        response = requests.get(f"{API_BASE}/v1/seasons/{season_id}/matches", params=params)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

# Initialize data
season_labels = get_season_labels()
current_season = season_labels[0] if season_labels else "2024/2025"
competitions = get_competitions(current_season)
current_competition = competitions[0]['id'] if competitions else 1
season_id = resolve_season(current_season, current_competition)

# App layout
app.layout = html.Div([
    html.Div([
        html.H1("⚽ Team Performance Analytics Dashboard",
                style={'textAlign': 'center', 'marginBottom': 30, 'color': '#2c3e50'}),

        # Season and Competition Selection
        html.Div([
            html.Div([
                html.Label("Season:", style={'fontWeight': 'bold', 'marginBottom': 5}),
                dcc.Dropdown(
                    id='season-dropdown',
                    options=[{'label': s, 'value': s} for s in season_labels],
                    value=current_season,
                    style={'marginBottom': 10}
                ),
            ], className='six columns'),

            html.Div([
                html.Label("Competition:", style={'fontWeight': 'bold', 'marginBottom': 5}),
                dcc.Dropdown(
                    id='competition-dropdown',
                    options=[{'label': c['name'], 'value': c['id']} for c in competitions],
                    value=current_competition,
                    style={'marginBottom': 10}
                ),
            ], className='six columns'),
        ], className='row'),

        # Season Summary
        html.Div(id='season-summary', className='row', style={'marginBottom': 20}),

        # Main tabs
        dcc.Tabs(id="main-tabs", value='standings-tab', children=[
            dcc.Tab(label='📊 League Standings', value='standings-tab'),
            dcc.Tab(label='🎯 Team Analysis', value='team-tab'),
            dcc.Tab(label='⚡ Performance Trends', value='trends-tab'),
            dcc.Tab(label='🏟️ Home vs Away', value='split-tab'),
        ], style={'marginBottom': 20}),

        # Tab content
        html.Div(id='tab-content')
    ], className='container')
])

def get_wdl_counts(season_id: int) -> pd.DataFrame:
    """
    Calcula W/D/L por team_id a partir de los partidos finalizados del season.
    Es tolerante a alias: home/local, away/visitor, etc.
    """
    matches = get_matches(season_id, finalized=True, limit=1000)
    dfm = pd.DataFrame(matches)
    if dfm.empty:
        return pd.DataFrame(columns=['team_id', 'win', 'draw', 'loss'])

    # Aliases posibles
    def pick_col(df, *cands):
        for c in cands:
            if c in df.columns:
                return c
        return None

    home_team_col = pick_col(dfm, 'home_team_id', 'local_team_id', 'homeId', 'localId')
    away_team_col = pick_col(dfm, 'away_team_id', 'visitor_team_id', 'awayId', 'visitorId')
    home_score_col = pick_col(dfm, 'home_score', 'local_score', 'homeGoals', 'localGoals')
    away_score_col = pick_col(dfm, 'away_score', 'visitor_score', 'awayGoals', 'visitorGoals')

    needed = {home_team_col, away_team_col, home_score_col, away_score_col}
    if None in needed:
        # No tenemos las columnas mínimas para computar W/D/L
        return pd.DataFrame(columns=['team_id', 'win', 'draw', 'loss'])

    # Filtra partidos con marcador conocido (ambos no nulos)
    dfm = dfm.dropna(subset=[home_score_col, away_score_col]).copy()
    if dfm.empty:
        return pd.DataFrame(columns=['team_id', 'win', 'draw', 'loss'])

    rows = []
    for _, m in dfm.iterrows():
        try:
            ht, at = int(m[home_team_col]), int(m[away_team_col])
            hs, as_ = int(m[home_score_col]), int(m[away_score_col])
        except Exception:
            # Si algún valor no se puede castear, salta ese match
            continue

        if hs > as_:
            rows.append({'team_id': ht, 'win': 1, 'draw': 0, 'loss': 0})
            rows.append({'team_id': at, 'win': 0, 'draw': 0, 'loss': 1})
        elif hs < as_:
            rows.append({'team_id': ht, 'win': 0, 'draw': 0, 'loss': 1})
            rows.append({'team_id': at, 'win': 1, 'draw': 0, 'loss': 0})
        else:
            rows.append({'team_id': ht, 'win': 0, 'draw': 1, 'loss': 0})
            rows.append({'team_id': at, 'win': 0, 'draw': 1, 'loss': 0})

    if not rows:
        return pd.DataFrame(columns=['team_id', 'win', 'draw', 'loss'])

    wdl = pd.DataFrame(rows).groupby('team_id', as_index=False).sum(numeric_only=True)
    # Asegura ints
    for c in ('win', 'draw', 'loss'):
        if c in wdl.columns:
            wdl[c] = wdl[c].astype(int)
    return wdl[['team_id', 'win', 'draw', 'loss']]

# Callback to update competitions based on season
@app.callback(
    Output('competition-dropdown', 'options'),
    Output('competition-dropdown', 'value'),
    Input('season-dropdown', 'value')
)
def update_competitions(selected_season):
    if not selected_season:
        return [], None

    comps = get_competitions(selected_season)
    options = [{'label': c['name'], 'value': c['id']} for c in comps]
    value = comps[0]['id'] if comps else None
    return options, value

# Callback for season summary
@app.callback(
    Output('season-summary', 'children'),
    [Input('season-dropdown', 'value'),
     Input('competition-dropdown', 'value')]
)
def update_season_summary(season_label, competition_id):
    if not season_label or not competition_id:
        return html.Div()

    sid = resolve_season(season_label, competition_id)
    if not sid:
        return html.Div("Season not found", style={'color': 'red'})

    summary = get_season_summary(sid)
    if not summary:
        return html.Div()

    return html.Div([
        html.Div([
            html.H4(f"📅 {summary.get('season_label', 'N/A')}", className='three columns',
                   style={'textAlign': 'center', 'color': '#3498db'}),
            html.H4(f"🏆 {summary.get('competition_name', 'N/A')}", className='three columns',
                   style={'textAlign': 'center', 'color': '#e74c3c'}),
            html.H4(f"👥 {summary.get('team_count', 0)} Teams", className='three columns',
                   style={'textAlign': 'center', 'color': '#27ae60'}),
            html.H4(f"🎮 MD {summary.get('last_finalized_matchday', 'N/A')}", className='three columns',
                   style={'textAlign': 'center', 'color': '#f39c12'}),
        ], className='row', style={'backgroundColor': '#ecf0f1', 'padding': '15px', 'borderRadius': '10px'})
    ])

# Main tab content callback
@app.callback(
    Output('tab-content', 'children'),
    [Input('main-tabs', 'value'),
     Input('season-dropdown', 'value'),
     Input('competition-dropdown', 'value')]
)
def render_tab_content(active_tab, season_label, competition_id):
    if not season_label or not competition_id:
        return html.Div("Please select season and competition")

    sid = resolve_season(season_label, competition_id)
    if not sid:
        return html.Div("Season not found")

    if active_tab == 'standings-tab':
        return render_standings_tab(sid)
    elif active_tab == 'team-tab':
        return render_team_analysis_tab(sid)
    elif active_tab == 'trends-tab':
        return render_trends_tab(sid)
    elif active_tab == 'split-tab':
        return render_split_tab(sid)

    return html.Div("Tab not implemented")

def render_standings_tab(season_id):
    """Render the standings tab"""
    df = get_standings(season_id)
    if df.empty:
        return html.Div("No standings data available")

    # Gráfico de puntos
    points_fig = px.bar(
        df.sort_values('position'),
        x='team_name',
        y='points',
        title='Points Distribution',
        color='points',
        color_continuous_scale='RdYlGn'
    )
    points_fig.update_layout(xaxis_tickangle=-45)

    # Gráfico de diferencia de gol
    gd_fig = px.bar(
        df.sort_values('position'),
        x='team_name',
        y='gd',
        title='Goal Difference',
        color='gd',
        color_continuous_scale='RdYlGn'
    )
    gd_fig.update_layout(xaxis_tickangle=-45)

    # --- W-D-L OPCIONAL ---
    form_section = html.Div()  # por defecto, vacío
    if {'win', 'draw', 'loss'}.issubset(df.columns) and df[['win', 'draw', 'loss']].notna().any().any():
        df_form = df.sort_values('position').copy()
        form_fig = go.Figure()
        form_fig.add_trace(go.Bar(name='Wins',  x=df_form['team_name'], y=df_form['win'],  marker_color='green'))
        form_fig.add_trace(go.Bar(name='Draws', x=df_form['team_name'], y=df_form['draw'], marker_color='orange'))
        form_fig.add_trace(go.Bar(name='Losses',x=df_form['team_name'], y=df_form['loss'], marker_color='red'))
        form_fig.update_layout(barmode='stack', title='Win-Draw-Loss Distribution', xaxis_tickangle=-45)
        form_section = html.Div([dcc.Graph(figure=form_fig)], className='row')

    # --- Layout final ---
    return html.Div([
        html.Div([
            html.Div([dcc.Graph(figure=points_fig)], className='six columns'),
            html.Div([dcc.Graph(figure=gd_fig)], className='six columns'),
        ], className='row'),

        # Aquí usamos la sección opcional (si no hubo W-D-L, queda vacío y no truena)
        form_section,

        html.Div([
            html.H4("League Table", style={'textAlign': 'center'}),
            dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[
                    {'name': 'Pos', 'id': 'position', 'type': 'numeric'},
                    {'name': 'Team', 'id': 'team_name'},
                    {'name': 'P', 'id': 'played', 'type': 'numeric'},
                    {'name': 'W', 'id': 'win', 'type': 'numeric'},
                    {'name': 'D', 'id': 'draw', 'type': 'numeric'},
                    {'name': 'L', 'id': 'loss', 'type': 'numeric'},
                    {'name': 'GF', 'id': 'gf', 'type': 'numeric'},
                    {'name': 'GA', 'id': 'ga', 'type': 'numeric'},
                    {'name': 'GD', 'id': 'gd', 'type': 'numeric'},
                    {'name': 'Pts', 'id': 'points', 'type': 'numeric'},
                ],
                sort_action='native',
                style_cell={'textAlign': 'center', 'fontSize': 12},
                style_data_conditional=[
                    {'if': {'filter_query': '{position} <= 4'}, 'backgroundColor': '#d5f4e6', 'color': 'black'},
                    {'if': {'filter_query': '{position} >= 18'}, 'backgroundColor': '#ffeaa7', 'color': 'black'},
                ]
            )
        ], className='row', style={'marginTop': 20})
    ])


def render_team_analysis_tab(season_id):
    """Render team analysis tab"""
    teams = get_teams(season_id)
    if not teams:
        return html.Div("No teams data available")

    return html.Div([
        html.Div([
            html.Label("Select Team for Analysis:", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='team-select',
                options=[{'label': t['team_name'], 'value': t['team_id']} for t in teams],
                value=teams[0]['team_id'] if teams else None,
                style={'marginBottom': 20}
            )
        ]),

        html.Div(id='team-analysis-content')
    ])

@app.callback(
    Output('team-analysis-content', 'children'),
    [Input('team-select', 'value'),
     Input('season-dropdown', 'value'),
     Input('competition-dropdown', 'value')],
    prevent_initial_call=True  # <- clave
)
def update_team_analysis(team_id, season_label, competition_id):
    if not all([team_id, season_label, competition_id]):
        return html.Div("Please select a team")

    sid = resolve_season(season_label, competition_id)
    dashboard_data = get_team_dashboard(sid, team_id)

    if not dashboard_data:
        return html.Div("No data available for this team")

    # Recent form visualization
    form_data = dashboard_data['form']
    form_df = pd.DataFrame(form_data)

    form_colors = {'WIN': 'green', 'DRAW': 'orange', 'LOSS': 'red'}
    form_fig = go.Figure(data=go.Bar(
        x=[f"Match {i+1}" for i in range(len(form_data))],
        y=[3 if r['result'] == 'WIN' else 1 if r['result'] == 'DRAW' else 0 for r in form_data],
        marker_color=[form_colors[r['result']] for r in form_data],
        text=[r['result'] for r in form_data],
        textposition='inside'
    ))
    form_fig.update_layout(title='Recent Form (Last 5 Matches)', yaxis_title='Points')

    # Home vs Away split
    split_data = dashboard_data['split']
    split_fig = go.Figure()
    split_fig.add_trace(go.Bar(name='Home', x=['PPG', 'Goals For', 'Goals Against'],
                              y=[split_data['home_ppg'], split_data['home_gf'], split_data['home_ga']],
                              marker_color='lightblue'))
    split_fig.add_trace(go.Bar(name='Away', x=['PPG', 'Goals For', 'Goals Against'],
                              y=[split_data['away_ppg'], split_data['away_gf'], split_data['away_ga']],
                              marker_color='lightcoral'))
    split_fig.update_layout(barmode='group', title='Home vs Away Performance')

    return html.Div([
        html.Div([
            html.Div([
                dcc.Graph(figure=form_fig)
            ], className='six columns'),
            html.Div([
                dcc.Graph(figure=split_fig)
            ], className='six columns'),
        ], className='row'),

        html.Div([
            html.H4("Performance Metrics", style={'textAlign': 'center'}),
            html.Div([
                html.Div([
                    html.H5("🏠 Home Performance", style={'color': '#3498db'}),
                    html.P(f"Points per Game: {split_data['home_ppg']:.2f}"),
                    html.P(f"Goals Scored: {split_data['home_gf']}"),
                    html.P(f"Goals Conceded: {split_data['home_ga']}"),
                ], className='six columns', style={'textAlign': 'center', 'backgroundColor': '#ecf0f1', 'padding': '15px'}),

                html.Div([
                    html.H5("✈️ Away Performance", style={'color': '#e74c3c'}),
                    html.P(f"Points per Game: {split_data['away_ppg']:.2f}"),
                    html.P(f"Goals Scored: {split_data['away_gf']}"),
                    html.P(f"Goals Conceded: {split_data['away_ga']}"),
                ], className='six columns', style={'textAlign': 'center', 'backgroundColor': '#ecf0f1', 'padding': '15px'}),
            ], className='row')
        ], style={'marginTop': 20})
    ])

def render_trends_tab(season_id):
    """Render performance trends tab"""
    df = get_standings(season_id)
    if df.empty:
        return html.Div("No data available for trends analysis")

    # Points per game analysis
    df['ppg'] = df['points'] / df['played']

    ppg_fig = px.scatter(
        df, x='played', y='ppg',
        size='points', color='gd',
        hover_name='team_name',
        title='Points per Game vs Games Played',
        labels={'ppg': 'Points per Game', 'played': 'Games Played'}
    )

    # Attack vs Defense
    attack_defense_fig = px.scatter(
        df, x='gf', y='ga',
        size='points', color='position',
        hover_name='team_name',
        title='Attack vs Defense Analysis',
        labels={'gf': 'Goals For', 'ga': 'Goals Against'}
    )
    attack_defense_fig.add_shape(
        type="line", line=dict(dash="dash", color="gray"),
        x0=df['gf'].min(), y0=df['gf'].min(),
        x1=df['gf'].max(), y1=df['gf'].max()
    )

    # Efficiency analysis (points per goal scored)
    df['efficiency'] = df['points'] / (df['gf'] + 0.1)  # Avoid division by zero

    efficiency_fig = px.bar(
        df.sort_values('efficiency', ascending=False),
        x='team_name', y='efficiency',
        title='Points per Goal Scored (Efficiency)',
        color='efficiency',
        color_continuous_scale='RdYlGn'
    )
    efficiency_fig.update_layout(xaxis_tickangle=-45)

    return html.Div([
        html.Div([
            html.Div([
                dcc.Graph(figure=ppg_fig)
            ], className='six columns'),
            html.Div([
                dcc.Graph(figure=attack_defense_fig)
            ], className='six columns'),
        ], className='row'),

        html.Div([
            dcc.Graph(figure=efficiency_fig)
        ], className='row'),
    ])

def render_split_tab(season_id):
    """Render home vs away analysis tab"""
    teams = get_teams(season_id)
    if not teams:
        return html.Div("No teams data available")

    # Collect home/away data for all teams
    split_data = []
    for team in teams[:10]:  # Limit to first 10 teams for demo
        dashboard = get_team_dashboard(season_id, team['team_id'])
        if dashboard:
            split_data.append({
                'team_name': team['team_name'],
                'home_ppg': dashboard['split']['home_ppg'],
                'away_ppg': dashboard['split']['away_ppg'],
                'home_gf': dashboard['split']['home_gf'],
                'away_gf': dashboard['split']['away_gf'],
                'home_ga': dashboard['split']['home_ga'],
                'away_ga': dashboard['split']['away_ga'],
            })

    if not split_data:
        return html.Div("No split data available")

    split_df = pd.DataFrame(split_data)

    # PPG comparison
    ppg_fig = go.Figure()
    ppg_fig.add_trace(go.Bar(name='Home PPG', x=split_df['team_name'], y=split_df['home_ppg'], marker_color='lightblue'))
    ppg_fig.add_trace(go.Bar(name='Away PPG', x=split_df['team_name'], y=split_df['away_ppg'], marker_color='lightcoral'))
    ppg_fig.update_layout(barmode='group', title='Home vs Away Points Per Game', xaxis_tickangle=-45)

    # Goals analysis
    goals_fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Goals Scored', 'Goals Conceded')
    )

    goals_fig.add_trace(go.Bar(name='Home GF', x=split_df['team_name'], y=split_df['home_gf'], marker_color='green'), row=1, col=1)
    goals_fig.add_trace(go.Bar(name='Away GF', x=split_df['team_name'], y=split_df['away_gf'], marker_color='lightgreen'), row=1, col=1)
    goals_fig.add_trace(go.Bar(name='Home GA', x=split_df['team_name'], y=split_df['home_ga'], marker_color='red'), row=1, col=2)
    goals_fig.add_trace(go.Bar(name='Away GA', x=split_df['team_name'], y=split_df['away_ga'], marker_color='lightcoral'), row=1, col=2)

    goals_fig.update_layout(barmode='group', title='Goals For and Against: Home vs Away')
    goals_fig.update_xaxes(tickangle=-45)

    # Home advantage analysis
    split_df['home_advantage'] = split_df['home_ppg'] - split_df['away_ppg']
    advantage_fig = px.bar(
        split_df.sort_values('home_advantage', ascending=False),
        x='team_name', y='home_advantage',
        title='Home Advantage (Home PPG - Away PPG)',
        color='home_advantage',
        color_continuous_scale='RdYlBu'
    )
    advantage_fig.update_layout(xaxis_tickangle=-45)
    advantage_fig.add_hline(y=0, line_dash="dash", line_color="gray")

    return html.Div([
        html.Div([
            dcc.Graph(figure=ppg_fig)
        ], className='row'),

        html.Div([
            dcc.Graph(figure=goals_fig)
        ], className='row'),

        html.Div([
            dcc.Graph(figure=advantage_fig)
        ], className='row'),
    ])

if __name__ == '__main__':
    app.run(debug=True, port=8050)
