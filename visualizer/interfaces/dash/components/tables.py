from __future__ import annotations

from typing import List, Dict, Any
from dash import html
from dash import dash_table
from dash.dash_table import FormatTemplate
from dash.dash_table.Format import Format, Scheme

_percentage_1 = FormatTemplate.percentage(1).nully("—")
_ppg_format   = Format(precision=2, scheme=Scheme.fixed).nully("—")

def _columns_basic() -> List[Dict[str, Any]]:
    return [
        {"name": "Pos",   "id": "position", "type": "numeric"},
        {"name": "Equipo","id": "team_name","type": "text"},
        {"name": "MP",    "id": "played",   "type": "numeric"},
        {"name": "W",     "id": "win",      "type": "numeric"},
        {"name": "D",     "id": "draw",     "type": "numeric"},
        {"name": "L",     "id": "loss",     "type": "numeric"},
        {"name": "GF",    "id": "gf",       "type": "numeric"},
        {"name": "GA",    "id": "ga",       "type": "numeric"},
        {"name": "GD",    "id": "gd",       "type": "numeric"},
        {"name": "Pts",   "id": "points",   "type": "numeric"},
        {"name": "PPG",   "id": "ppg",      "type": "numeric", "format": _ppg_format},
        {"name": "GiH",   "id": "gih",      "type": "numeric"},
    ]

def _columns_advanced() -> List[Dict[str, Any]]:
    return [
        {"name": "Pos",        "id": "position",                 "type": "numeric"},
        {"name": "Equipo",     "id": "team_name",                "type": "text"},
        {"name": "PPG L5",     "id": "ppg_last_5",               "type": "numeric", "format": _ppg_format},
        {"name": "Shadow",     "id": "shadow_rank",              "type": "numeric"},
        {"name": "BTTS%",      "id": "btts_pct",                 "type": "numeric", "format": _percentage_1},
        {"name": "O2.5%",      "id": "over25_pct",               "type": "numeric", "format": _percentage_1},
        {"name": "CS%",        "id": "clean_sheet_pct",          "type": "numeric", "format": _percentage_1},
        {"name": "BothHalves%","id": "goals_both_halves_pct",    "type": "numeric", "format": _percentage_1},
        {"name": "1st+Won%",   "id": "scored_first_and_won_pct", "type": "numeric", "format": _percentage_1},
    ]

_TOOLTIPS = {
    "position": "Posición en la tabla.",
    "team_name": "Nombre del equipo.",
    "played": "Partidos jugados.",
    "win": "Victorias.",
    "draw": "Empates.",
    "loss": "Derrotas.",
    "gf": "Goles a favor.",
    "ga": "Goles en contra.",
    "gd": "Diferencia de gol (GF - GA).",
    "points": "Puntos totales.",
    "ppg": "Puntos por partido (Pts / MP).",
    "gih": "Juegos en mano respecto al máximo de la liga.",
    "ppg_last_5": "PPG en los últimos 5 partidos.",
    "shadow_rank": "Ranking alternativo por PPG (forma).",
    "btts_pct": "Partidos con ambos equipos anotando.",
    "over25_pct": "Partidos con 3+ goles totales.",
    "clean_sheet_pct": "Partidos con portería en cero.",
    "goals_both_halves_pct": "Anotó en ambos tiempos.",
    "scored_first_and_won_pct": "Marcó primero y ganó.",
}

def make_league_table(rows: list[dict], *, view: str = "basic"):
    columns = _columns_basic() if view == "basic" else _columns_advanced()
    table = dash_table.DataTable(
        id="league-table",  # <- este id está bien (es el de la tabla, no del wrap externo)
        data=rows,
        columns=columns,
        sort_action="native",
        page_action="none",
        fixed_rows={"headers": True},
        style_table={"overflowX": "auto", "maxHeight": "700px", "overflowY": "auto"},
        style_header={"border": "none"},
        style_cell={"textAlign": "center", "fontSize": 13, "border": "none", "padding": "8px"},
        tooltip_header=_TOOLTIPS,
        tooltip_delay=0,
        tooltip_duration=None,
        style_data_conditional=[
            {"if": {"filter_query": "{position} <= 4"},
             "backgroundColor": "rgba(16,185,129,.14)", "color": "#d1fae5"},
            {"if": {"filter_query": "{position} >= 18"},
             "backgroundColor": "rgba(239,68,68,.12)", "color": "#fee2e2"},
        ],
        css=[
            {"selector": ".dash-table-container .dash-spreadsheet-container", "rule": "border: none !important;"},
            {"selector": ".dash-header", "rule": "background: rgba(148,163,184,.10) !important; color: #e5e7eb !important; font-weight: 700;"},
            {"selector": ".dash-cell", "rule": "background: rgba(148,163,184,.02) !important; border-bottom: 1px solid rgba(148,163,184,.12) !important;"},
            {"selector": ".dash-row:nth-child(even) .dash-cell", "rule": "background: rgba(148,163,184,.06) !important;"},
        ],
    )
    return table
